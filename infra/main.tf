variable "project_id" {}
variable "region" {}
variable "zone" {}

terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "6.8.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
  zone    = var.zone
}

resource "google_compute_network" "vpc_network" {
  name = "scrappingchef-network"
}

resource "google_sql_database_instance" "main" {
  name             = "scrappingchef-db"
  database_version = "POSTGRES_16"
  region           = var.region

  settings {
    tier = "db-f1-micro"
    
    ip_configuration {
      ipv4_enabled = true
      authorized_networks {
        name  = "all"
        value = "0.0.0.0/0"
      }
    }
    
    disk_size = 10
    disk_type = "PD_SSD"
  }
}
