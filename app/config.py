from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Restaurant & Food Delivery Management System"

    
    database_url: str = (
        "mysql+pymysql://root:Root123@localhost:3306/food_delivery"
    )

    # JWT Configuration
    secret_key: str = "restaurant-food-delivery-super-secret-key-2026-change-this"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 7

    
    tax_rate: float = 0.05
    cors_origins: str = "*"

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )


settings = Settings()