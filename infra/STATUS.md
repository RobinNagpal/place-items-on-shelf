# Isaac Sim on AWS — where we are

**Last updated:** Friday 4 September 2026
**State:** instance **stopped**, waiting on one PR. Resume Monday 7 September.

## The short version

Everything works except the remote desktop. The desktop fails on a licence
check, and the fix is written but not merged yet.

## The machine

| | |
|---|---|
| Instance | `i-0b1fd779e6663f302` (stopped) |
| Region / type | `us-east-1` / `g6e.xlarge` (NVIDIA L40S, 48 GB) |
| Isaac Sim path | `~/IsaacSim/isaac-sim.sh` (capital I and S) |
| Cost | ~$1.86/hour running, ~$40/month stopped |

The disk is kept while stopped, so the `ubuntu` password and the QUIC change
below are still there. **The public IP changes every time you start it** —
`./start.sh` prints the new one.

## What already works

- Launching, stopping and starting with the scripts in `scripts/`.
- `./connect.sh` — a shell with no SSH key and no open port, over Session
  Manager. The SSH `.pem` is not needed for anything.
- The `ubuntu` Linux password is set. DCV uses it to log in.
- GPU is healthy — `nvidia-smi` shows the L40S.
- A DCV `console` session exists and survives restarts.
- QUIC (UDP 8443) is on, on both the instance and the security group. This
  matters because we are ~250 ms from `us-east-1`.

## What is blocking

The DCV client connects, takes the password, then goes black with:

```
No license available. Please check your EC2 configuration
```

DCV is free on EC2 but still checks a licence in an S3 bucket, and the
instance's IAM role could not read it. **`dcv_license.tf` fixes this** by
adding `s3:GetObject` on `arn:aws:s3:::dcv-license.us-east-1/*` to the
instance role. Nothing needs to be bought and no key is involved.

## Not committed yet

These are local edits only. They need a PR and Robin's merge:

- `dcv_license.tf` — the blocking fix (new file).
- `ssm.tf` — role description updated, no behaviour change.
- `scripts/allow-my-ip.sh` — corrected the QUIC `sed` it prints. The old one
  silently matched nothing, because `dcv.conf` writes `key = value` with
  spaces around the `=`.
- `README.md`, `scripts/README.md`, `../isaac-sim-aws-setup.md` — the black
  screen symptom written down.

## Monday, in order

1. Check the `dcv_license.tf` PR is merged and the `terraform` workflow went
   green. Nothing below works until then.
2. `git pull`
3. `cd infra/scripts && ./start.sh` — note the new public IP it prints.
4. `./allow-my-ip.sh` — your home IP will have changed over the weekend.
5. `./connect.sh`, then on the instance:
   ```bash
   sudo systemctl restart dcvserver
   sudo grep -i licen /var/log/dcv/server.log | tail -20
   ```
   The log is the proof. It should stop saying no licence is available.
6. DCV client -> `<new-ip>:8443`, log in as `ubuntu`.
7. In the desktop: `~/IsaacSim/isaac-sim.sh`. First run asks for the NVIDIA
   Developer login and then compiles shaders for several minutes. It looks
   frozen. Let it run.
8. `./stop.sh` when you finish. Not `./terminate.sh` — that deletes the disk.

## Two things that will bite

- **Auto-shutdown.** The instance stops after 2 hours of uptime, or once it
  is past 3 PM US Eastern — which is **midnight Pakistan time**. A desktop
  that dies suddenly is usually this, not a crash. `./start.sh` brings it
  back with everything intact.
- **GPU capacity.** `g6e.xlarge` in `us-east-1` is scarce. `./launch.sh`
  failed with `InsufficientInstanceCapacity` several times before it worked.
  That is AWS running out of GPUs, not a quota problem, so retrying is the
  fix. This only applies to `launch.sh`; `start.sh` on an existing stopped
  instance is not affected.
