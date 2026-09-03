# `infra/` — Terraform for the Isaac Sim AWS setup

Terraform code that does the three "account owner" jobs described in
[`../isaac-sim-aws-setup.md`](../isaac-sim-aws-setup.md):

1. **Creates the EC2 instance** from the Isaac Sim Marketplace AMI, so the
   instance ID never has to be copied by hand.
2. **Creates the developer's IAM user** with permissions scoped to exactly that
   one EC2 instance and one security group — nothing else in the account.
3. **Creates an auto-shutdown guard rail** so a forgotten Isaac Sim instance
   cannot run up a bill. A `g6e.xlarge` costs about **$1.86/hour**, so one
   weekend left running is roughly **$130**.

The manager runs this once. The developer never runs it.

## The one manual step

Terraform cannot click **"Subscribe / Accept Terms"** on the AWS Marketplace —
accepting a Marketplace agreement is a legal and billing action that AWS does
not expose through the API. So, once per account, the manager must:

> AWS Console → Marketplace → search **"NVIDIA Isaac Sim"** →
> **NVIDIA Isaac Sim Development Workstation (Linux)** → Subscribe → Accept Terms

Skip it and `terraform apply` fails with **`OptInRequired`**. After that single
click, everything else is code.

## What it does NOT do

It does **not** create the security group or the key pair — make `isaac-sim-sg`
and `isaac-sim-key` in the console first (the **Pre-flight** section of the
setup guide), then paste the security group ID into `terraform.tfvars`.

It also does not raise your **vCPU quota**. A brand-new account often has a
limit of **0** for G-type instances, which makes the launch fail with
`VcpuLimitExceeded`. Check Service Quotas → EC2 → *"Running On-Demand G and VT
instances"* before applying; approval can take up to two days.

## Two modes

| `create_instance` | Who launches the instance | When to use it |
|---|---|---|
| `true` (default) | Terraform | Normal case. No IDs to copy, and `terraform destroy` cleans up. |
| `false` | You, by hand in the console | An instance already exists. Paste its ID into `instance_id`. |

Either way, the instance ID flows into **one** place (`local.instance_id`) which
feeds both the developer's IAM policy and the auto-shutdown Lambda — so the
permissions and the cost guard rail can never drift apart from the real machine.

## The shutdown rules

| Rule | Default | Meaning |
|---|---|---|
| Max uptime | 2 hours | Running longer than this → stop it |
| Daily curfew | 15:00 `America/New_York` | At or after 3 PM Eastern → stop it |
| Check interval | `cron(0 * * * ? *)` | How often the two rules are evaluated |

All three are variables, so you can change them without touching code.

**The check is periodic, not a precise timer.** With hourly checks aligned to
the top of the hour, an instance started at 09:10 crosses the 2-hour limit at
11:10 but is actually stopped at the 12:00 check. That is fine for a cost
guard rail. If you want it tighter, set
`check_schedule_expression = "cron(*/15 * * * ? *)"` — the Lambda is free at
this volume, so a shorter interval costs nothing extra.

**Use `cron(...)`, not `rate(...)`, for this schedule.** EventBridge's
`rate(1 hour)` fires every 60 minutes counting from whenever the rule was
created or last enabled — not from the top of the clock hour. That means the
first check could land at, say, 12:37, 1:37, 2:37... instead of 1:00, 2:00,
3:00, which would push the 3 PM curfew check up to an hour late. `cron(0 * *
* ? *)` fires exactly on the hour (in UTC, but the Lambda itself resolves the
curfew in `curfew_timezone`, so this only affects when the *check* runs, not
what time zone the curfew is measured in).

**Note on the curfew and overnight.** "Stop after 3 PM" covers 15:00 → midnight.
After midnight the local hour resets to 0, so the curfew stops applying and the
2-hour max-uptime rule is what catches a late-night session. That is the
intended behaviour, not a gap being ignored.

**Note on daylight saving.** The default timezone is `America/New_York`, which
is EST in winter and EDT in summer — the curfew always lands at 3 PM local
wall-clock time. If you want a fixed UTC-5 all year (strict "EST"), that is not
what this default gives you.

## How it fits together

```
EventBridge rule  ──(every hour, on the hour)──▶  Lambda: isaac-sim-auto-shutdown
"cron(0 * * * ? *)"                                  │
                                        ├─ ec2:DescribeInstances  (is it running? how long?)
                                        └─ ec2:StopInstances      (only if a rule is crossed)
                                                 │
                                                 ▼
                                        the Isaac Sim instance
```

The Lambda can **only stop** the instance. Its IAM role has no permission to
start, reboot, terminate, or touch any other instance in the account.

## Files

| File | What it holds |
|---|---|
| `versions.tf` | Terraform and provider version pins |
| `providers.tf` | AWS provider config and default tags |
| `variables.tf` | Every input, with defaults and descriptions |
| `locals.tf` | ARNs built from the instance / security group IDs |
| `instance.tf` | The EC2 instance and the Marketplace AMI lookup |
| `iam_user.tf` | The developer IAM user and its four scoped policies |
| `auto_shutdown.tf` | Lambda, its IAM role, log group, and the EventBridge schedule |
| `outputs.tf` | Credentials and sign-in URL to hand to the developer |
| `lambda/auto_shutdown.py` | The actual shutdown logic (~90 lines of Python) |
| `terraform.tfvars.example` | Template to copy to `terraform.tfvars` |

## The developer's permissions

Four policies are attached to the IAM user:

1. **`AmazonEC2ReadOnlyAccess`** (AWS managed) — see instances, statuses, and
   the public IP in the console.
2. **`isaac-sim-operate-instance`** — `ec2:StartInstances`, `StopInstances`,
   `RebootInstances`, scoped to the one instance ARN.
3. **`isaac-sim-manage-security-group`** — edit inbound rules on `isaac-sim-sg`
   only, so the developer can refresh their own home IP without asking the
   manager every time their ISP reassigns an address.
4. **`isaac-sim-self-service-credentials`** — change their own password and set
   up their own MFA device.

That is the whole blast radius. They cannot launch instances, cannot terminate
anything, and cannot see or change other people's resources.

## Running it

Prerequisites: Terraform ≥ 1.5, and AWS credentials for a user who can create
IAM users (the account owner / an admin).

```bash
cd infra

# 1. Fill in the security group ID (and instance_id only if you set
#    create_instance = false).
cp terraform.tfvars.example terraform.tfvars
$EDITOR terraform.tfvars

# 2. Download providers.
terraform init

# 3. Read the plan carefully - it creates an IAM user and a GPU instance.
terraform plan

# 4. Apply.
terraform apply
```

### Recommended first run: dry run

For the first day, set `auto_shutdown_dry_run = true` in `terraform.tfvars`.
The schedule still fires every hour and the Lambda still logs exactly what it
*would* stop, but it never calls `StopInstances`. Watch the logs, confirm the
decisions look right, then set it back to `false` and re-apply.

### Getting the credentials out

Terraform hides secrets in normal output. Read them explicitly:

```bash
terraform output developer_console_signin_url
terraform output developer_user_name
terraform output -raw developer_console_password
terraform output -raw developer_access_key_id
terraform output -raw developer_secret_access_key
```

Send these over a secure channel — a password manager or an encrypted message,
never plain email. The console password is single-use: AWS forces a change on
first sign-in.

## Testing the shutdown by hand

Start the instance, then invoke the Lambda directly instead of waiting an hour:

```bash
aws lambda invoke \
  --function-name isaac-sim-auto-shutdown \
  --payload '{}' \
  /dev/stdout
```

The response says what it decided: `none` (under both limits), `dry-run`, or
`stopped` with the reasons. Full history is in CloudWatch:

```bash
aws logs tail /aws/lambda/isaac-sim-auto-shutdown --follow
```

## Pausing the guard rail

Sometimes you genuinely need a long run — a big training job, a demo that goes
past 3 PM. Two options, cheapest first:

```bash
# Option A: pause the schedule, keep everything in place.
terraform apply -var="auto_shutdown_enabled=false"
# ...and remember to turn it back on.

# Option B: raise the limit for a while.
terraform apply -var="max_runtime_hours=8" -var="curfew_hour=22"
```

## State file warning

`terraform.tfstate` contains the developer's console password and secret access
key **in plaintext**. It is gitignored here. Before this is used by more than
one person, move state to an S3 backend with encryption and locking enabled —
local state is fine for a single manager running this once, and not fine for a
team.
