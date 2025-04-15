from pydantic_settings import BaseSettings  # Cambia la importación

class Settings(BaseSettings):
    API_GPT: str
    PORT: str
    DEBUG: bool = False  

    class Config:
        env_file = ".env"  #el archivo .env

settings = Settings()
