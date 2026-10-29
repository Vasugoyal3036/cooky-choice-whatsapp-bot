import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

BRAND_NAME = os.getenv("BRAND_NAME", "Cooky Choice Rice")
BRAND_TAGLINE = os.getenv("BRAND_TAGLINE", "Purity in Every Grain • Farm to Fork")
BRAND_PHONE = os.getenv("BRAND_PHONE", "+91 98765 43210")
BRAND_EMAIL = os.getenv("BRAND_EMAIL", "support@cookychoice.com")
BRAND_ADDRESS = os.getenv("BRAND_ADDRESS", "Mill & Packing Unit: Industrial Area, GT Road")

META_WA_PHONE_NUMBER_ID = os.getenv("META_WA_PHONE_NUMBER_ID", "").strip()
META_WA_ACCESS_TOKEN = os.getenv("META_WA_ACCESS_TOKEN", "").strip()
META_WA_VERIFY_TOKEN = os.getenv("META_WA_VERIFY_TOKEN", "cooky_choice_webhook_secret_2026").strip()
META_WA_API_VERSION = os.getenv("META_WA_API_VERSION", "v20.0").strip()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()

PORT = int(os.getenv("PORT", 8000))
HOST = os.getenv("HOST", "0.0.0.0")
DEBUG = os.getenv("DEBUG", "True").lower() in ("true", "1", "yes")

DATABASE_PATH = BASE_DIR / "rice_automation.db"
