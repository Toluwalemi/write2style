################################
# Runtime service accounts
################################

resource "google_service_account" "backend" {
  account_id   = "${var.backend_service_name}-sa"
  display_name = "Write2Style backend runtime"
}

resource "google_service_account" "frontend" {
  account_id   = "${var.frontend_service_name}-sa"
  display_name = "Write2Style frontend runtime"
}

# Backend: read/write uploads bucket
resource "google_storage_bucket_iam_member" "backend_uploads" {
  bucket = google_storage_bucket.uploads.name
  role   = "roles/storage.objectUser"
  member = "serviceAccount:${google_service_account.backend.email}"
}

# Backend: Firestore user
resource "google_project_iam_member" "backend_firestore" {
  project = var.project_id
  role    = "roles/datastore.user"
  member  = "serviceAccount:${google_service_account.backend.email}"
}

################################
# GitHub Workload Identity Federation
################################

resource "google_iam_workload_identity_pool" "github" {
  workload_identity_pool_id = "github-actions-pool"
  depends_on                = [google_project_service.apis]
}

resource "google_iam_workload_identity_pool_provider" "github" {
  workload_identity_pool_id          = google_iam_workload_identity_pool.github.workload_identity_pool_id
  workload_identity_pool_provider_id = "github-provider"

  attribute_mapping = {
    "google.subject"       = "assertion.sub"
    "attribute.actor"      = "assertion.actor"
    "attribute.repository" = "assertion.repository"
  }

  attribute_condition = "assertion.repository == '${var.github_repo}'"

  oidc {
    issuer_uri = "https://token.actions.githubusercontent.com"
  }
}

################################
# App deployer (narrow: build + deploy Cloud Run)
################################

resource "google_service_account" "app_deployer" {
  account_id   = "gh-app-deployer"
  display_name = "GitHub Actions app deployer"
}

resource "google_service_account_iam_member" "app_deployer_wif" {
  service_account_id = google_service_account.app_deployer.name
  role               = "roles/iam.workloadIdentityUser"
  member             = "principalSet://iam.googleapis.com/${google_iam_workload_identity_pool.github.name}/attribute.repository/${var.github_repo}"
}

resource "google_project_iam_member" "app_deployer_roles" {
  for_each = toset([
    "roles/run.admin",
    "roles/artifactregistry.writer",
  ])

  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.app_deployer.email}"
}

# Needed so the deployer can set the runtime SAs on Cloud Run services
resource "google_service_account_iam_member" "app_deployer_actas_backend" {
  service_account_id = google_service_account.backend.name
  role               = "roles/iam.serviceAccountUser"
  member             = "serviceAccount:${google_service_account.app_deployer.email}"
}

resource "google_service_account_iam_member" "app_deployer_actas_frontend" {
  service_account_id = google_service_account.frontend.name
  role               = "roles/iam.serviceAccountUser"
  member             = "serviceAccount:${google_service_account.app_deployer.email}"
}

################################
# Infra deployer (broad: apply Terraform)
################################

resource "google_service_account" "infra_deployer" {
  account_id   = "gh-infra-deployer"
  display_name = "GitHub Actions infra deployer"
}

resource "google_service_account_iam_member" "infra_deployer_wif" {
  service_account_id = google_service_account.infra_deployer.name
  role               = "roles/iam.workloadIdentityUser"
  member             = "principalSet://iam.googleapis.com/${google_iam_workload_identity_pool.github.name}/attribute.repository/${var.github_repo}"
}

resource "google_project_iam_member" "infra_deployer_roles" {
  for_each = toset([
    "roles/run.admin",
    "roles/artifactregistry.admin",
    "roles/storage.admin",
    "roles/iam.serviceAccountAdmin",
    "roles/iam.workloadIdentityPoolAdmin",
    "roles/resourcemanager.projectIamAdmin",
    "roles/secretmanager.admin",
    "roles/serviceusage.serviceUsageAdmin",
    "roles/datastore.owner",
  ])

  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.infra_deployer.email}"
}
