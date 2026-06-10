# Isaac Sim on AWS — Setup Guide

How to run NVIDIA Isaac Sim on an AWS GPU instance and connect to it from
Windows (WSL terminal + NICE DCV client). Pay-per-use — stop the instance
when you're done.

## Why AWS

This project's host doesn't have an NVIDIA RTX GPU, so Isaac Sim can't run
locally. AWS EC2 gives us a GPU machine on demand: pay only while it's
running, stop it when idle.

## Cost

| State | Per hour | Per month if left this way |
|---|---|---|
| **Running** (`g6e.xlarge`, L40S 48 GB) | ~$1.86 | ~$1,340 |
| **Stopped** (disk only, 512 GB gp3) | ~$0.06 | ~$40 |

Realistic budget: **~$15–20/day** of active work + ~$40/month standby.
Stop the instance whenever you walk away.

## Pre-flight (do these once, in this order)

1. **NVIDIA Developer account** (free) — required by Isaac Sim on first
   launch: <https://developer.nvidia.com/login>
2. **AWS region** — pick **us-east-1** or **us-west-2** (lowest GPU price)
   and stay in it.
3. **vCPU quota** — AWS console → Service Quotas → EC2 → search
   *"Running On-Demand G and VT instances"* → request **8** (covers
   `g6e.xlarge` with headroom). Approval can take hours to 2 days. Submit
   this first.
4. **Key pair** — EC2 → Key Pairs → Create:
   - Name: `isaac-sim-key`, Type: **RSA**, Format: **.pem**.
   - Move it to WSL: `mv /mnt/c/Users/<you>/Downloads/isaac-sim-key.pem ~/.ssh/ && chmod 400 ~/.ssh/isaac-sim-key.pem`.
5. **Security group** — EC2 → Security Groups → Create `isaac-sim-sg`,
   two inbound rules:
   - SSH (port 22), source: **My IP**.
   - Custom TCP (port 8443), source: **My IP**. (NICE DCV.)

## Launch the instance

1. EC2 → AMI Catalog → Marketplace tab → search **"Isaac Sim"** → pick
   **NVIDIA Isaac Sim™ Development Workstation (Linux)** → Subscribe →
   Accept Terms → Continue to Configuration → Continue to Launch → Launch
   from EC2 Console.
2. On the launch wizard:
   - **Name**: `isaac-sim-dev`
   - **Instance type**: `g6e.xlarge` (cheapest the AMI accepts; same L40S
     GPU as the larger `g6e` sizes, just less RAM). NVIDIA's docs suggest
     `g6e.4xlarge` for heavier workloads — start small, scale later.
   - **Key pair**: `isaac-sim-key`
   - **Network → Firewall**: select existing → `isaac-sim-sg`
   - **Storage**: **512 GiB** gp3 (AMI minimum)
3. Launch. Wait for **Running** + **2/2 status checks** (~3 minutes).

## Connect

1. **SSH from WSL** — copy the instance's Public IPv4, then:
   ```bash
   ssh -i ~/.ssh/isaac-sim-key.pem ubuntu@<public-ip>
   nvidia-smi    # should list the L40S
   ```
2. **Set a Linux password** for DCV login (DCV uses OS auth, not AWS):
   ```bash
   sudo passwd ubuntu
   ```
3. **GitHub access** — generate an SSH key on the instance and add it to
   GitHub:
   ```bash
   ssh-keygen -t ed25519 -C "isaac-sim-ec2" -f ~/.ssh/id_ed25519 -N ""
   cat ~/.ssh/id_ed25519.pub   # paste into GitHub → Settings → SSH keys
   git clone git@github.com:RobinNagpal/place-items-on-shelf.git
   ```
4. **NICE DCV client on Windows** (not WSL) — download from
   <https://www.amazondcv.com/> and install.
5. **Connect** — open DCV client, enter `<public-ip>:8443`, log in as
   `ubuntu` with the password from step 2. Full Linux desktop appears.
6. **Launch Isaac Sim** from the remote desktop's terminal:
   ```bash
   ~/isaacsim/isaac-sim.sh   # path varies by AMI version
   ```
   Sanity checks: create a sphere, press Play (physics ticks), enable the
   ROS 2 bridge extension.

## Daily routine — keep the bill low

- **Start of work**: EC2 → Instances → select → Instance state → Start.
  Public IP may change; re-check it. (Optional: attach an Elastic IP for a
  stable address.)
- **End of work**: Instance state → **Stop**. GPU billing stops
  immediately; only the disk continues.
- **Terminate** only when you're done with Isaac Sim entirely (deletes the
  instance and the disk).

## You are an IAM user (your manager owns the AWS account)

The flow above assumes you control the AWS account. If your manager runs
the account and you're an **IAM user**, the work splits up:

### What your manager does (once)

1. Creates the IAM user for you with **console + programmatic access**.
2. Attaches a policy that lets you operate the Isaac Sim instance. The
   minimum useful set:
   - `AmazonEC2ReadOnlyAccess` — see instances and statuses.
   - `ec2:StartInstances`, `ec2:StopInstances`, `ec2:RebootInstances`
     scoped to the Isaac Sim instance's ARN (so you can't touch other
     instances).
   - `ec2:AuthorizeSecurityGroupIngress`, `ec2:RevokeSecurityGroupIngress`
     scoped to `isaac-sim-sg` (so you can update your home IP yourself).
3. Does all the **Pre-flight** + **Launch the instance** steps above
   (quota, key pair, security group, AMI, launch).
4. Sends you:
   - The `.pem` key file (over a secure channel — never email plaintext).
   - The instance ID and the security group ID.
   - The Linux `ubuntu` password they set with `sudo passwd ubuntu`
     (or tells you to set one on your first SSH).
   - The AWS Console sign-in URL for the account (looks like
     `https://<account-alias>.signin.aws.amazon.com/console`).

### What you do as the IAM user

1. Sign in to the AWS Console with the URL + your IAM credentials.
2. Save the `.pem` to `~/.ssh/isaac-sim-key.pem`, `chmod 400`.
3. **Update the security group with your current home IP**:
   - EC2 → Security Groups → `isaac-sim-sg` → Inbound rules → Edit →
     change both rules' Source to **My IP**. AWS auto-fills the IP it
     sees you from. Save.
   - You'll need to do this whenever your home IP changes (ISP reset,
     coffee shop wifi, etc.). If your manager hasn't granted the
     `ec2:...SecurityGroupIngress` permissions, you'll have to ping them
     each time — get the permissions instead.
4. Start the instance (Instance state → Start).
5. Connect via SSH and NICE DCV the same way as the single-user flow
   above.
6. **Stop the instance** when done. This is the most important habit on a
   shared account — a forgotten `g6e.xlarge` costs ~$45/day.

### Notes for the multi-user case

- **Don't share the `.pem`**. If multiple people need SSH, your manager
  should add a separate key per person (each pastes their public key into
  `~/.ssh/authorized_keys` on the instance during onboarding).
- **DCV password is shared** unless your manager creates a separate Linux
  user per person (`sudo adduser <name>` + grant DCV access).
- **Billing visibility**: ask your manager to set up a Cost Anomaly
  Detection alert or a Budget on the Isaac Sim instance so a forgotten
  one is caught fast.
- **VPN as a cleaner alternative** to "My IP" management: if the company
  has an AWS Client VPN or Site-to-Site VPN, the security group's source
  can be the VPN's CIDR instead of personal home IPs. Doesn't break when
  ISPs reassign addresses.

## Common gotchas

- **Launch fails with `VcpuLimitExceeded`** — vCPU quota not yet
  approved. Wait, or request the increase if you skipped that step.
- **"Connection refused" on DCV** — port 8443 isn't open in the security
  group from your current IP. Update the rule.
- **DCV login rejected** — `ubuntu` user has no password yet. SSH in and
  run `sudo passwd ubuntu`.
- **Isaac Sim won't start** — you skipped the NVIDIA Developer account.
  Create one and log in inside Isaac Sim's first-run dialog.
- **Forgot to stop** — set an AWS Budget alert. A `g6e.xlarge` left
  running for a week is ~$310.
