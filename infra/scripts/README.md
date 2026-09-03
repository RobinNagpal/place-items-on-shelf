# `infra/scripts/` — day-to-day instance control

Small shell scripts that wrap the AWS CLI calls an operator makes every day, so
nobody has to remember instance IDs or long `aws ec2` commands.

Terraform builds the launch template, the security group, the IAM permissions
and the two guard Lambdas. These scripts do **not** touch any of that. They only
create, power on, power off and delete the machine itself.

## The one thing to understand first

**You create the machine once. After that you only start and stop it.**

```
  ONCE                      EVERY DAY                        RARELY
  ─────                     ─────────                        ──────
  ./launch.sh   ────────▶   ./start.sh   ──▶   ./stop.sh     ./terminate.sh
  creates a new              powers on         powers off     deletes it and
  machine                    the SAME          the SAME       the disk
                             machine           machine
                                 ▲                 │
                                 └─────────────────┘
                                   repeat forever
```

Stopping does **not** destroy anything. Your files, installed packages and
settings are all still there the next morning. You run `launch.sh` again only
if you terminated.

Think of it like a laptop: **launch** = buy one, **start** = open the lid,
**stop** = shut it down, **terminate** = throw it in the bin.

## The scripts

| Script | AWS API call | When | Your files |
|---|---|---|---|
| `./launch.sh` | `RunInstances` | Once, or after terminating | n/a — new machine |
| `./start.sh` | `StartInstances` | Every morning | **kept** |
| `./stop.sh` | `StopInstances` | Every evening | **kept** |
| `./terminate.sh` | `TerminateInstances` | Done for weeks | **lost forever** |
| `./allow-my-ip.sh` | `AuthorizeSecurityGroupIngress` | When you cannot connect | n/a |

`launch.sh` and `start.sh` are easy to mix up, so `launch.sh` refuses to run
when a machine already exists and points you at `start.sh` instead.

## Usage

```bash
cd infra/scripts
chmod +x *.sh        # first time only

./launch.sh          # first time only
./allow-my-ip.sh     # whenever SSH/DCV times out

./start.sh           # each morning
./stop.sh            # each evening

./terminate.sh           # asks you to type the instance ID to confirm
./terminate.sh --force   # skips the question
```

Run them from anywhere — each script `cd`s to its own folder first.

### Settings

Optional, read from the environment:

| Variable | Default | Meaning |
|---|---|---|
| `AWS_REGION` | `us-east-1` | Region the instance lives in |
| `ISAAC_SIM_PROJECT` | `isaac-sim` | Matches `project_name` in the Terraform |

## How they find the instance

There is no hard-coded instance ID anywhere. Every Isaac Sim instance carries
the tag **`Purpose = isaac-sim`**, stamped on it by the launch template. The
scripts search for that tag, exactly like the two Lambdas do. So you can
terminate the instance, launch a new one with a different ID, and every script
keeps working.

## The public IP changes on every start

AWS releases the public IP when an instance stops and assigns a fresh one when
it starts. So the address you used yesterday will not work today — `start.sh`
prints the new one.

Your *own* IP can change too (ISP reset, different wifi). Either change breaks
the security group rule and SSH just hangs. `start.sh` notices and tells you to
run `allow-my-ip.sh`.

Use `./allow-my-ip.sh --replace` to clear out old dead IPs at the same time.
Skip `--replace` if a teammate's IP is also in the list.

## Things the scripts protect you from

- **`launch.sh` refuses to create a second instance.** The single-instance guard
  Lambda terminates every extra instance and keeps only the oldest, so a second
  launch would give you a machine that vanishes a minute later.
- **`terminate.sh` makes you type the full instance ID.** Not `y`, the whole
  `i-0abc...`. It also lists the volumes that will be deleted first.
- **`stop.sh`, `start.sh` and `terminate.sh` refuse to guess** when more than
  one tagged instance exists. That means the guard Lambda has a problem, so they
  point you at its CloudWatch logs instead of acting.
- **They wait for the state change to finish** before returning, so `stop.sh`
  only exits once GPU billing has genuinely ended.
- **`start.sh` handles the `stopping` state**, which AWS will not let you start
  out of. It waits for the stop to complete, then starts.

## Before the first launch works

1. **The Marketplace subscription is accepted.** Otherwise `RunInstances` fails
   with `OptInRequired`.
2. **The G-instance vCPU quota is high enough.** `g6.2xlarge` is 8 vCPUs, so
   "Running On-Demand G and VT instances" must be at least 8, or the launch
   fails with `VcpuLimitExceeded`.
3. **You have the SSH private key.** Terraform generates it; get it with
   `terraform output -raw ssh_private_key_pem`, save as `~/.ssh/isaac-sim-key.pem`,
   then `chmod 400` it.

## Cost

The auto-shutdown Lambda stops the instance after **2 hours** of uptime, or once
the clock passes **3 PM US Eastern**. That is a safety net, not a workflow — run
`./stop.sh` yourself when you finish.

A **stopped** instance still costs about **$40/month** for its 512 GiB disk. If
you will be away for weeks, `./terminate.sh` is the cheaper choice — but
everything on the disk goes with it.
