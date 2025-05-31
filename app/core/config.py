from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_host: str = "localhost"
    app_port: int = 8000

    postgres_host: str = "localhost"
    postgres_port: int = 7790
    postgres_db: str = "dataguard"
    postgres_user: str = "postgres"
    postgres_password: str

    pinecone_api_key: str
    pinecone_index: str ='compliguard-index'
    
    chunk_size: int= 1500
    chunk_overlap: int=  300

    google_api_key: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

settings = Settings()