resource "google_firestore_database" "default" {
  project         = var.project_id
  name            = "(default)"
  location_id     = "eur3"
  type            = "FIRESTORE_NATIVE"
  deletion_policy = "DELETE"

  depends_on = [google_project_service.apis]
}
