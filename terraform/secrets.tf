locals {
  secret_ids = {
    openai     = "write2style-openai-api-key"
    openrouter = "write2style-openrouter-api-key"
    pinecone   = "write2style-pinecone-api-key"
  }
}

resource "google_secret_manager_secret" "openai" {
  secret_id = local.secret_ids.openai
  replication {
    auto {}
  }
  depends_on = [google_project_service.apis]
}

resource "google_secret_manager_secret_version" "openai" {
  secret      = google_secret_manager_secret.openai.id
  secret_data = var.openai_api_key
}

resource "google_secret_manager_secret" "openrouter" {
  secret_id = local.secret_ids.openrouter
  replication {
    auto {}
  }
  depends_on = [google_project_service.apis]
}

resource "google_secret_manager_secret_version" "openrouter" {
  secret      = google_secret_manager_secret.openrouter.id
  secret_data = var.openrouter_api_key
}

resource "google_secret_manager_secret" "pinecone" {
  secret_id = local.secret_ids.pinecone
  replication {
    auto {}
  }
  depends_on = [google_project_service.apis]
}

resource "google_secret_manager_secret_version" "pinecone" {
  secret      = google_secret_manager_secret.pinecone.id
  secret_data = var.pinecone_api_key
}

resource "google_secret_manager_secret_iam_member" "backend_openai" {
  secret_id = google_secret_manager_secret.openai.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.backend.email}"
}

resource "google_secret_manager_secret_iam_member" "backend_openrouter" {
  secret_id = google_secret_manager_secret.openrouter.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.backend.email}"
}

resource "google_secret_manager_secret_iam_member" "backend_pinecone" {
  secret_id = google_secret_manager_secret.pinecone.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.backend.email}"
}
