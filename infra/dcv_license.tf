# ---------------------------------------------------------------------------
# Amazon DCV licensing
#
# DCV is free to run on EC2, but it is not licence-free. The server works out
# that it is on an EC2 instance and then periodically reads a licence object
# from a regional S3 bucket to confirm it is allowed to serve sessions. Reading
# that object needs an IAM permission on the INSTANCE's role.
#
# Without this policy the desktop fails in a way that looks like anything but a
# permissions problem: the DCV client connects, accepts the password, shows the
# user greeter, and then goes black with
#
#   "DCV licence: No license available. Please check your EC2 configuration"
#
# The security group, the password and the session are all fine at that point -
# it is only the licence check failing.
#
# Two things this needs, both already true here:
#   - The instance can reach the S3 public endpoint. Ours is in a public subnet
#     with open egress, so it can.
#   - The instance role carries the policy below.
#
# Reference:
# https://docs.aws.amazon.com/dcv/latest/adminguide/setting-up-license.html
# ---------------------------------------------------------------------------

data "aws_iam_policy_document" "dcv_license" {
  statement {
    sid     = "ReadTheDcvLicenceObject"
    effect  = "Allow"
    actions = ["s3:GetObject"]

    # AWS owns this bucket and there is one per region, named after the region.
    # Read-only on a single well-known prefix, so it grants nothing else.
    resources = ["arn:aws:s3:::dcv-license.${var.aws_region}/*"]
  }
}

resource "aws_iam_policy" "dcv_license" {
  name        = "${local.name_prefix}-dcv-license"
  description = "Lets the Isaac Sim instance read its Amazon DCV licence object from the regional S3 bucket. Without it the remote desktop refuses every connection."
  policy      = data.aws_iam_policy_document.dcv_license.json
}

# Attaches to the same role the SSM Agent uses - see ssm.tf. That role is now
# the instance's one identity, serving both the shell and the desktop.
resource "aws_iam_role_policy_attachment" "dcv_license" {
  role       = aws_iam_role.instance.name
  policy_arn = aws_iam_policy.dcv_license.arn
}
