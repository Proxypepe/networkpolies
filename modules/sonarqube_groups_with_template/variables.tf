variable "group_base_name" {
  description = "Base name for the groups that will be created"
  type        = string
}

variable "description" {
  description = "Description for the groups and permission templates"
  type        = string
  default     = "Created by Terraform"
}
