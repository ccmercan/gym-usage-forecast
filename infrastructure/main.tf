# ──────────────────────────────────────────────────────────────────────────────
# Raider Power Zone — GCP Infrastructure
#
# What this provisions:
#   1. Enables required GCP APIs (Cloud Run, Cloud SQL, Vertex AI, Secret Manager)
#   2. Cloud SQL (Postgres 15) — production database
#   3. Cloud Run service — hosts the FastAPI app
#   4. Secret Manager — stores DATABASE_URL and API keys securely
#   5. IAM — grants Cloud Run access to secrets and Vertex AI
#
# Why Terraform?
#   Infrastructure as code: reproducible, version-controlled, reviewable.
#   One `terraform apply` recreates the entire stack from scratch.
#
# Usage:
#   cd infrastructure
#   terraform init
#   terraform plan -var="project_id=YOUR_PROJECT_ID"
#   terraform apply -var="project_id=YOUR_PROJECT_ID"
# ──────────────────────────────────────────────────────────────────────────────

terraform {
  required_version = ">= 1.5"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

# ── Variables ──────────────────────────────────────────────────────────────────

variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "region" {
  description = "GCP region"
  type        = string
  default     = "us-central1"
}

variable "db_password" {
  description = "PostgreSQL password for the app user"
  type        = string
  sensitive   = true
  default     = "changeme-use-a-strong-password"
}

variable "image" {
  description = "Container image URL (e.g. gcr.io/PROJECT/recapp:latest)"
  type        = string
  default     = "gcr.io/PROJECT_ID/recapp:latest"
}

# ── Provider ───────────────────────────────────────────────────────────────────

provider "google" {
  project = var.project_id
  region  = var.region
}

# ── Enable required APIs ───────────────────────────────────────────────────────
# Why: APIs must be enabled before you can create any resource in that service.

resource "google_project_service" "run" {
  service            = "run.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "sqladmin" {
  service            = "sqladmin.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "aiplatform" {
  service            = "aiplatform.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "secretmanager" {
  service            = "secretmanager.googleapis.com"
  disable_on_destroy = false
}

# ── Service account for Cloud Run ──────────────────────────────────────────────
# Why: Least-privilege — the app only gets exactly the permissions it needs.

resource "google_service_account" "recapp" {
  account_id   = "recapp-runner"
  display_name = "RecApp Cloud Run Service Account"
}

# Allow the service account to call Vertex AI (Gemini)
resource "google_project_iam_member" "vertex_user" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.recapp.email}"
}

# Allow the service account to read secrets
resource "google_project_iam_member" "secret_accessor" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.recapp.email}"
}

# ── Cloud SQL (PostgreSQL 15) ──────────────────────────────────────────────────

resource "google_sql_database_instance" "recapp" {
  name             = "recapp-postgres"
  database_version = "POSTGRES_15"
  region           = var.region
  deletion_protection = false # set to true in production

  settings {
    tier = "db-f1-micro" # cheapest tier — upgrade for production

    backup_configuration {
      enabled = true
    }

    ip_configuration {
      ipv4_enabled    = false
      private_network = "projects/${var.project_id}/global/networks/default"
    }
  }

  depends_on = [google_project_service.sqladmin]
}

resource "google_sql_database" "recapp" {
  name     = "recapp"
  instance = google_sql_database_instance.recapp.name
}

resource "google_sql_user" "recapp" {
  name     = "recapp"
  instance = google_sql_database_instance.recapp.name
  password = var.db_password
}

# ── Secret Manager — store DATABASE_URL ───────────────────────────────────────
# Why: Never put credentials in environment variables as plain text in Cloud Run.

resource "google_secret_manager_secret" "db_url" {
  secret_id = "recapp-database-url"

  replication {
    auto {}
  }

  depends_on = [google_project_service.secretmanager]
}

resource "google_secret_manager_secret_version" "db_url" {
  secret = google_secret_manager_secret.db_url.id
  secret_data = (
    "postgresql://recapp:${var.db_password}@/${google_sql_database.recapp.name}"
    "?host=/cloudsql/${google_sql_database_instance.recapp.connection_name}"
  )
}

# ── Cloud Run service ──────────────────────────────────────────────────────────

resource "google_cloud_run_v2_service" "recapp" {
  name     = "recapp"
  location = var.region

  template {
    service_account = google_service_account.recapp.email

    containers {
      image = var.image

      env {
        name = "DATABASE_URL"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.db_url.secret_id
            version = "latest"
          }
        }
      }

      env {
        name  = "GCP_PROJECT_ID"
        value = var.project_id
      }

      env {
        name  = "GCP_REGION"
        value = var.region
      }

      resources {
        limits = {
          cpu    = "1"
          memory = "512Mi"
        }
      }
    }

    # Connect to Cloud SQL via the Unix socket
    volumes {
      name = "cloudsql"
      cloud_sql_instance {
        instances = [google_sql_database_instance.recapp.connection_name]
      }
    }
  }

  depends_on = [
    google_project_service.run,
    google_project_service.aiplatform,
  ]
}

# Make the Cloud Run service publicly accessible
resource "google_cloud_run_v2_service_iam_member" "public" {
  project  = var.project_id
  location = var.region
  name     = google_cloud_run_v2_service.recapp.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# ── Outputs ────────────────────────────────────────────────────────────────────

output "cloud_run_url" {
  description = "Public URL of the deployed application"
  value       = google_cloud_run_v2_service.recapp.uri
}

output "cloud_sql_connection_name" {
  description = "Cloud SQL connection name (for Cloud Run sidecar)"
  value       = google_sql_database_instance.recapp.connection_name
}
