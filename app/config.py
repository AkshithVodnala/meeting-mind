from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    hf_token: str = ""
    model_id: str = "Qwen/Qwen2.5-7B-Instruct"
    app_env: str = "development"
    database_url: str = "sqlite:///./meetingmind.db"

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
