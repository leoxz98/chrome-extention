from pydantic_settings import BaseSettings  

class Settings(BaseSettings):
    API_GPT: str
    API_GOOGLE: str
    ID_GOOGLE: str
    PORT: str
    DEBUG: bool = False  

    class Config:
        env_file = ".env"  # el archivo .env

settings = Settings()
