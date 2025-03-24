terraform {
  required_providers {
    sonarqube = {
      source = "jdamata/sonarqube"
    }
  }
}

resource "sonarqube_group" "view_execute_group" {
  name        = "${var.group_base_name}_view_execute"
  description = var.description
}

resource "sonarqube_group" "admin_group" {
  name        = "${var.group_base_name}_admin"
  description = var.description
}

resource "sonarqube_permission_template" "group_template" {
  name               = "${var.group_base_name}_template"
  description        = "Admin permissions for ${var.group_base_name} projects"
  project_key_pattern = ""
}

resource "sonarqube_permissions" "project_admins" {
  group_name  = "${var.group_base_name}_admin"
  template_id = sonarqube_permission_template.group_template.id
  permissions = ["admin"]
}

resource "sonarqube_permissions" "sonar_administrators" {
  group_name  = "sonar-administrators"
  template_id = sonarqube_permission_template.group_template.id
  permissions = ["admin"]
}

resource "sonarqube_permissions" "project_read" {
  group_name  = "${var.group_base_name}_view_execute"
  template_id = sonarqube_permission_template.group_template.id
  permissions = ["codeviewer", "scan", "user"]
}
