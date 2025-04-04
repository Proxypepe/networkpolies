terraform {
  required_providers {
    sonarqube = {
      source = "jdamata/sonarqube"
    }
  }
}

provider "sonarqube" {
  host = "http://"
  token = ""
}

module "app_team_groups" {
  source        = "./modules/sonarqube_groups_with_template"
  admin_group = "app_team_admin"
  view_group = "app_team_view_execute"
  project = "app_team"
  description   = "Groups and permissions for Application Team"
}

module "infra_team_groups" {
  source        = "./modules/sonarqube_groups_with_template"
  admin_group = "infra_team_admin"
  view_group = "infra_team_view_execute"
  project = "infra_team"
  description   = "Groups and permissions for Application Team"
}
