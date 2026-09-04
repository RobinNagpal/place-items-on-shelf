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
| `./connect.sh` | `ssm:StartSession` | To get a shell, or tunnel DCV | n/a |
| `./allow-my-ip.sh` | `AuthorizeSecurityGroupIngress` | When the desktop times out | n/a |

`launch.sh` and `start.sh` are easy to mix up, so `launch.sh` refuses to run
when a machine already exists and points you at `start.sh` instead.

## Two ways in, and they do different jobs

Isaac Sim is a GUI application, so the goal is always the **desktop**. But a
brand new machine will not let you log in to that desktop until it has a Linux
password, and setting one needs a terminal. Hence two channels:

| | What you get | Needs an open port? | Needs the SSH key? |
|---|---|---|---|
| `./connect.sh` | text terminal | no | no |
| **NICE DCV** on 8443 | **full GPU desktop** | yes, TCP+UDP 8443 | no |

`connect.sh` works through AWS Session Manager. The instance's SSM Agent dials
*out* to AWS, your CLI dials out too, and AWS joins the two ends. Nothing is
listening on the instance, so this keeps working even when the security group
has no inbound rules at all — which is exactly the state a fresh account is in.

DCV is the real destination. It renders the desktop on the instance's L4 GPU,
encodes it as video, and streams it to your Mac. Your Mac only decodes video,
so it does not need a GPU of its own. Use the native client from
<https://www.amazondcv.com/> rather than the browser one — it handles 3D input
far better.

So the first-run order is: `connect.sh` → `sudo passwd ubuntu` → `exit` →
`allow-my-ip.sh` → DCV client. After that first time you only need DCV, and
`connect.sh` is just a convenient shell.

`./connect.sh --forward` tunnels DCV through Session Manager so port 8443 never
opens. It is the safer option and the slower one: the tunnel is TCP only, so
DCV cannot use its faster UDP transport, and traffic takes an extra hop. Keep
it for networks where you cannot pin a stable IP.

## Usage

```bash
cd infra/scripts
chmod +x *.sh        # first time only

./launch.sh          # first time only
./connect.sh         # a shell on the machine, no SSH key needed
./allow-my-ip.sh     # whenever the DCV desktop times out

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
| `ISAAC_SIM_SSM_WAIT` | `180` | Seconds to wait for the SSM Agent after a launch |

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
the security group rule and the DCV desktop just hangs. `start.sh` notices and
tells you to run `allow-my-ip.sh`. `connect.sh` is unaffected — it never touches
the security group.

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
3. **The Session Manager plugin is installed locally.** On macOS:
   `brew install --cask session-manager-plugin`. Without it `./connect.sh`
   cannot run the session it just opened.

You do **not** need the SSH private key. `./connect.sh` reaches the machine
through Session Manager instead. The key still exists for `--with-ssh`, but
nothing in the normal flow uses it.

## Cost

The auto-shutdown Lambda stops the instance after **2 hours** of uptime, or once
the clock passes **3 PM US Eastern**. That is a safety net, not a workflow — run
`./stop.sh` yourself when you finish.

A **stopped** instance still costs about **$40/month** for its 512 GiB disk. If
you will be away for weeks, `./terminate.sh` is the cheaper choice — but
everything on the disk goes with it.
