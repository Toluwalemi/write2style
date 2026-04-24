resource "google_artifact_registry_repository" "docker" {
  location      = var.region
  repository_id = "write2style-repo"
  format        = "DOCKER"
  description   = "Docker images for Write2Style"

  depends_on = [google_project_service.apis]
}
