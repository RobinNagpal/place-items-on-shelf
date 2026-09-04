# `infra/` — Terraform for the Isaac Sim AWS setup

The manager runs this once. It sets up everything the developers need to run
one Isaac Sim GPU instance, and nothing more.

## What it creates

| Piece | What it does |
|---|---|
| **Security group + key pair** | Ports 22 and 8443 for SSH and NICE DCV, and an RSA key. Operators edit the inbound IPs themselves. |
| **Launch template** | The only recipe for the Isaac Sim instance: AMI, `g6e.xlarge`, key pair, security group, 512 GiB disk, `Purpose = isaac-sim` tag. |
| **Operators group** | The developer users and your admin user. Members can launch from the template and start / stop / reboot / terminate tagged instances. Nothing else. |
| **Developer IAM users** | Up to four, from `developer_user_names`. Each gets a console password + CLI key and can change their own password and MFA. |
| **Session Manager access** | An instance role so the SSM Agent can register, plus `ssm:StartSession` for operators. Gives a shell with no SSH key and no open port. |
| **DCV licence access** | `s3:GetObject` on the regional `dcv-license` bucket, on the same instance role. Without it the remote desktop connects and then goes black. |
| **Single-instance guard** | Lambda. If a second Isaac Sim instance is launched, it is terminated within seconds. |
| **Auto-shutdown** | Lambda. Stops the instance after 2 hours of uptime or after 3 PM Eastern. |

It does **not** subscribe to the Isaac Sim AMI. That needs a manual click in
the Marketplace (see [`../isaac-sim-aws-setup.md`](../isaac-sim-aws-setup.md)).
Terraform can still create everything before that click; only the first launch
needs the subscription in place.

## How changes get applied

Nobody runs `terraform apply` by hand day to day. GitHub Actions does it:

1. Open a pull request that touches `infra/`. The `terraform` workflow runs
   `fmt`, `validate`, and a Lambda syntax check. No AWS access.
2. The repo owner reviews and merges. Only they can merge to `main`.
3. On merge, the workflow assumes the `isaac-sim-github-deploy` role via
   OIDC (no stored AWS keys) and runs `plan` then `apply`.

`terraform.tfvars` is committed on purpose. It holds the AMI ID and user
names, nothing secret. Edit it in a PR to add a developer.

To apply from your laptop instead (owner only, needs the admin profile):

```bash
cd infra
terraform init      # reads state from S3
terraform plan
terraform apply
```

For the first day, set `auto_shutdown_dry_run = true` and
`single_instance_guard_dry_run = true`. Both Lambdas then only log what
they would do. Check the logs, set both to `false`, apply again.

Hand each developer their credentials over a secure channel. The secret
outputs are maps keyed by user name:

```bash
terraform output console_signin_url
terraform output -json developer_console_passwords  | jq -r '."robin-robotics"'
terraform output -json developer_access_key_ids     | jq -r '."robin-robotics"'
terraform output -json developer_secret_access_keys | jq -r '."robin-robotics"'
terraform output -raw ssh_private_key_pem > isaac-sim-key.pem   # same key for everyone
```

The SSH key is now a fallback, not the way in. Operators reach the instance
with `aws ssm start-session`, which needs no key and no inbound port, so you no
longer have to hand the `.pem` to anyone. See `ssm.tf`.

Developers are listed in `developer_user_names` (default
`robin-robotics` and `hassaan-robotics`, at most four). Add a name and apply
to onboard someone. Remove a name and apply to delete their user.

## Create the instance (developer or admin)

```bash
terraform output -raw launch_command
# aws ec2 run-instances --region us-east-1 --launch-template LaunchTemplateId=lt-...
```

Or in the console: EC2 → Launch Templates → `isaac-sim-workstation` →
Actions → **Launch instance from template**. Any other way to launch is
denied.

Easier: `scripts/launch.sh` does the same thing, refuses to create a second
instance, and waits for the SSM Agent so `scripts/connect.sh` works right
after. See [`scripts/README.md`](scripts/README.md).

Terminate the instance when the project pauses. That stops the ~$40/month
disk cost. The disk is deleted with it, so push your work to git first.

## How "only one instance" works

Nothing is keyed on an instance ID. The Isaac Sim instance is whichever
instance carries the `Purpose = isaac-sim` tag. The template stamps that tag
on launch and operators cannot change it.

IAM limits *what* can be launched: only via the template, only
`g6e.xlarge`, only the pinned AMI, key pair and security group. IAM cannot
count, so the guard Lambda limits *how many*: it runs whenever any instance
starts booting, keeps the oldest tagged instance, and terminates the rest.

**Already have a hand-launched instance?** Tag it, or the policies and
Lambdas will not see it:

```bash
aws ec2 create-tags --resources i-XXXX --tags Key=Purpose,Value=isaac-sim
```

## Useful knobs

All in `terraform.tfvars`:

| Variable | Default | Meaning |
|---|---|---|
| `max_runtime_hours` | `2` | Stop after this much uptime |
| `curfew_hour` | `15` | Stop at or after this local hour |
| `curfew_timezone` | `America/New_York` | Timezone for the curfew |
| `instance_type` | `g6e.xlarge` | Changes the template and the IAM limit together. Must be on the Marketplace product's allow-list; `g6e.xlarge` is the smallest permitted. |
| `auto_shutdown_enabled` | `true` | `false` pauses the hourly check |

Need a long run today? `terraform apply -var="max_runtime_hours=8" -var="curfew_hour=22"`.

## Check the guard rails

```bash
aws lambda invoke --function-name isaac-sim-auto-shutdown --payload '{}' /dev/stdout
aws lambda invoke --function-name isaac-sim-single-instance-guard --payload '{}' /dev/stdout
aws logs tail /aws/lambda/isaac-sim-auto-shutdown --follow
```

## Tear it all down

```bash
terraform destroy
```

This removes the users, group, policies, template, and both Lambdas. It does
**not** terminate the instance, because operators create that outside
Terraform. Terminate it by hand first (it is the one tagged
`Purpose = isaac-sim`). The state bucket and deploy role in `bootstrap/`
stay unless you destroy that too.

## Files

| File | Holds |
|---|---|
| `variables.tf` | Every input |
| `network.tf` | Security group and SSH key pair |
| `launch_template.tf` | The instance recipe |
| `iam_operators.tf` | Group, memberships, EC2 policies |
| `ssm.tf` | Instance role for the SSM Agent, and the operators' session policy |
| `dcv_license.tf` | S3 read so the DCV server can validate its licence |
| `iam_user.tf` | Developer users and credentials |
| `single_instance_guard.tf`, `lambda/single_instance_guard.py` | "Keep one" Lambda |
| `auto_shutdown.tf`, `lambda/auto_shutdown.py` | Stop-on-limit Lambda |
| `lambda_package.tf`, `lambda/common.py` | Shared zip and tag lookup |
| `outputs.tf` | Credentials and the launch command |
| `bootstrap/` | One-time: S3 state bucket, lock table, GitHub deploy role |
| `../.github/workflows/terraform.yml` | The check-on-PR, apply-on-merge workflow |

State holds every developer's password, secret key and the SSH private key
in plaintext. It lives in the encrypted, versioned, private S3 bucket that
`bootstrap/` creates, never on disk or in git. Only the account admin and the
GitHub deploy role can read it. `bootstrap/main.tf` explains the one-time
setup for a fresh account.
