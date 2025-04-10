from pydantic_settings import BaseSettings  # Cambia la importación

class Settings(BaseSettings):
    API_GPT: str
    PORT: str
    DEBUG: bool = False  # Valor por defecto si no está en el .env

    class Config:
        env_file = ".env"  # Indicamos el archivo .env

settings = Settings()
