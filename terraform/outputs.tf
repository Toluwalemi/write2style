output "backend_url" {
  value = google_cloud_run_v2_service.backend.uri
}

output "frontend_url" {
  value = google_cloud_run_v2_service.frontend.uri
}

output "artifact_registry" {
  value = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.docker.repository_id}"
}

output "uploads_bucket" {
  value = google_storage_bucket.uploads.name
}

output "backend_service_account" {
  value = google_service_account.backend.email
}

output "frontend_service_account" {
  value = google_service_account.frontend.email
}

output "wif_provider" {
  value = google_iam_workload_identity_pool_provider.github.name
}

output "app_deployer_sa" {
  value = google_service_account.app_deployer.email
}

output "infra_deployer_sa" {
  value = google_service_account.infra_deployer.email
}
