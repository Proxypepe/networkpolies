terraform {
  required_providers {
    sonarqube = {
      source = "jdamata/sonarqube"
    }
  }
}

resource "sonarqube_group" "view_execute_group" {
  name        = "${var.view_group}"
  description = var.description
}

resource "sonarqube_group" "admin_group" {
  name        = "${var.admin_group}"
  description = var.description
}

resource "sonarqube_permission_template" "group_template" {
  name               = "${var.project}_template"
  description        = "Admin permissions for ${var.project} projects"
  project_key_pattern = "${var.permission_pattern}"
}

resource "sonarqube_permissions" "project_admins" {
  group_name  = "${var.admin_group}"
  template_id = sonarqube_permission_template.group_template.id
  permissions = ["admin"]
}

resource "sonarqube_permissions" "sonar_administrators" {
  group_name  = "sonar-administrators"
  template_id = sonarqube_permission_template.group_template.id
  permissions = ["admin"]
}

resource "sonarqube_permissions" "project_read" {
  group_name  = "${var.view_group}"
  template_id = sonarqube_permission_template.group_template.id
  permissions = ["codeviewer", "scan", "user"]
}

resource "sonarqube_permissions" "admin_user" {
  login_name = "admin"   
  template_id = sonarqube_permission_template.group_template.id
  permissions = ["admin"]
}
