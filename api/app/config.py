import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    AWS_REGION = os.environ.get("AWS_REGION", "eu-west-1")
    AWS_PRICING_API_REGION = os.environ.get("AWS_PRICING_API_REGION", "us-east-1")
    PRICE_CACHE_TTL_HOURS = int(os.environ.get("PRICE_CACHE_TTL_HOURS", "24"))
    INACTIVE_THRESHOLD_DAYS = int(os.environ.get("INACTIVE_THRESHOLD_DAYS", "14"))

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get("TEST_DATABASE_URL", "sqlite:///:memory:")


config_by_name = {
    "development" : DevelopmentConfig,
    "testing" : TestingConfig,
    "production" : ProductionConfig
}