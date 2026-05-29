from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    pexels_api_key: str = ""
    pixabay_api_key: str = ""
    anthropic_api_key: str = ""
    elevenlabs_api_key: str = ""
    elevenlabs_voice_id: str = ""

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
