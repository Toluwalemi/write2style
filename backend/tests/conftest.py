import os

os.environ.setdefault("CLERK_JWKS_URL", "https://test.example/.well-known/jwks.json")
os.environ.setdefault("CLERK_ISSUER", "https://test.example")
os.environ.setdefault("OPENAI_API_KEY", "test-openai")
os.environ.setdefault("OPENROUTER_API_KEY", "test-openrouter")
os.environ.setdefault("PINECONE_API_KEY", "test-pinecone")
os.environ.setdefault("GCS_BUCKET", "test-bucket")
os.environ.setdefault("GCP_PROJECT", "test-project")
os.environ.setdefault("CORS_ORIGINS", "*")
