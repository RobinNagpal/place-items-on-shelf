aws_region = "us-east-1"

# NVIDIA Isaac Sim Development Workstation (Linux), from the AMI Catalog.
ami_id = "ami-04c0e6d2f07bbddc7"

# The Marketplace product publishes an allow-list of instance types, and
# g6e.xlarge (L40S 48 GB, 4 vCPU, 32 GiB) is the SMALLEST one on it. Anything
# outside that list is refused at launch with:
#
#   UnsupportedOperation: The instance configuration for this AWS Marketplace
#   product is not supported.
#
# The cheaper g6.2xlarge (L4) was set here originally on price alone and is not
# supported - it fails every launch. Check the list on the product's "Continue
# to Configuration" page before changing this.
instance_type = "g6e.xlarge"

developer_user_names = ["robin-robotics", "hassaan-robotics"]
admin_user_names     = ["dodao-admin"]
