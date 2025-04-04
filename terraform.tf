terraform {
  backend "s3" {
    bucket = "terraforrm-bucket"
    region = "ru-west-rock-1"
    endpoints = {
        s3 = "https://"
    }
    key = "states/terraform.tfstate"

    skip_credentials_validation = true
    skip_region_validation     = true
    skip_requesting_account_id = true
    skip_metadata_api_check    = true
    use_path_style           = true
    
    access_key = ""
    secret_key = ""
  }
}
