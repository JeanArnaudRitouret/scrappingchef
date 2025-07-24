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
        # TODO: Replace with the IP of the local machine or the IP of the Cloud SQL Auth Proxy
        name  = "all"
        value = "0.0.0.0/0"
      }
    }
    
    disk_size = 10
    disk_type = "PD_SSD"
  }
}

resource "google_project_service" "secret_manager" {
  service = "secretmanager.googleapis.com"
}

resource "google_secret_manager_secret" "DB_HOST" {
  secret_id = "DB_HOST"
  replication {
    auto {}
  }
  depends_on = [google_project_service.secret_manager]
}

resource "google_secret_manager_secret" "DB_PORT" {
  secret_id = "DB_PORT"
  replication {
    auto {}
  }
  depends_on = [google_project_service.secret_manager]
}

resource "google_secret_manager_secret" "DB_NAME" {
  secret_id = "DB_NAME"
  replication {
    auto {}
  }
  depends_on = [google_project_service.secret_manager]
}

resource "google_secret_manager_secret" "DB_USER" {
  secret_id = "DB_USER"
  replication {
    auto {}
  }
  depends_on = [google_project_service.secret_manager]
}

resource "google_secret_manager_secret" "DB_PASSWORD" {
  secret_id = "DB_PASSWORD"
  replication {
    auto {}
  }
  depends_on = [google_project_service.secret_manager]
}

resource "google_secret_manager_secret" "PASSWORD_ADC" {
  secret_id = "PASSWORD_ADC"
  replication {
    auto {}
  }
  depends_on = [google_project_service.secret_manager]
}

resource "google_secret_manager_secret" "URL_ADC" {
  secret_id = "URL_ADC"
  replication {
    auto {}
  }
  depends_on = [google_project_service.secret_manager]
}

resource "google_secret_manager_secret" "URL_ADC_COURSE" {
  secret_id = "URL_ADC_COURSE"
  replication {
    auto {}
  }
  depends_on = [google_project_service.secret_manager]
}

resource "google_secret_manager_secret" "URL_LOGIN_ADC" {
  secret_id = "URL_LOGIN_ADC"
  replication {
    auto {}
  }
  depends_on = [google_project_service.secret_manager]
}

resource "google_secret_manager_secret" "URL_LOGIN_NEW_PLATFORM" {
  secret_id = "URL_LOGIN_NEW_PLATFORM"
  replication {
    auto {}
  }
  depends_on = [google_project_service.secret_manager]
}

resource "google_secret_manager_secret" "URL_NEW_PLATFORM" {
  secret_id = "URL_NEW_PLATFORM"
  replication {
    auto {}
  }
  depends_on = [google_project_service.secret_manager]
}

resource "google_secret_manager_secret" "URL_NEW_PLATFORM_TRAINING" {
  secret_id = "URL_NEW_PLATFORM_TRAINING"
  replication {
    auto {}
  }
  depends_on = [google_project_service.secret_manager]
}

resource "google_secret_manager_secret" "USERNAME_ADC" {
  secret_id = "USERNAME_ADC"
  replication {
    auto {}
  }
  depends_on = [google_project_service.secret_manager]
}