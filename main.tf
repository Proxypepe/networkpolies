terraform {
  required_providers {
    sonarqube = {
      source = "jdamata/sonarqube"
    }
  }
}

provider "sonarqube" {
  host = ""
  token = ""
}

module "app_team_groups" {
  source        = "./modules/sonarqube_groups_with_template"
  group_base_name = "app_team"
  description   = "Groups and permissions for Application Team"
}

