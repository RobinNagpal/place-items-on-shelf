# This state lives in the bucket main.tf creates, under its own key. Rename
# this file to backend.tf.off for the very first apply (see main.tf).
terraform {
  backend "s3" {
    bucket         = "isaac-sim-tfstate-729763663166"
    key            = "bootstrap/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "isaac-sim-tfstate-lock"
    encrypt        = true
  }
}
