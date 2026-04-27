from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    clerk_jwks_url: str
    clerk_issuer: str

    openai_api_key: str
    openrouter_api_key: str
    pinecone_api_key: str

    pinecone_index: str = "write2style"
    pinecone_cloud: str = "aws"
    pinecone_region: str = "us-east-1"

    gcs_bucket: str
    gcp_project: str

    embedding_model: str = "text-embedding-3-small"
    embedding_dim: int = 1536
    style_model: str = "anthropic/claude-sonnet-4.5"
    draft_model: str = "anthropic/claude-haiku-4.5"

    chunk_size: int = 800
    chunk_overlap: int = 100
    max_sample_chars_for_dna: int = 20000
    top_k_few_shot: int = 5

    cors_origins: str = "*"


settings = Settings()
