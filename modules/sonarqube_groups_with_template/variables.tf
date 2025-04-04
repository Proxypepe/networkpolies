variable "admin_group" {
  description = "Base name for the groups that will be created"
  type        = string
}

variable "view_group" {
  description = "Base name for the groups that will be created"
  type        = string
}

variable "permission_pattern" {
  description = ""
  type        = string
  default     = ""
}

variable "project" {
  description = ""
  type        = string
}

variable "description" {
  description = "Description for the groups and permission templates"
  type        = string
  default     = "Created by Terraform"
}
