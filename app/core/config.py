from pydantic_settings import BaseSettings, SettingsConfigDict

class Setting(BaseSettings):
    
    #Callback
    BASE_BACKEND_URL: str

    #Gemini 
    GEMINI_API_KEY: str

    #Embedding Model
    EMBEDDING_BASE_URL: str 
    
    #Redis
    REDIS_HOST: str
    REDIS_PORT: int
    REDIS_DB: int
    
    LANGSMITH_TRACING: bool
    
    model_config = SettingsConfigDict(env_file_encoding="utf-8",env_file=".env")

settings = Setting()