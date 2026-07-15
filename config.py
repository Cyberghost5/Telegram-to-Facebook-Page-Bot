import os
from dotenv import load_dotenv

load_dotenv()

def _require(key: str) -> str:
    value = os.getenv(key)
    if not value:
        raise EnvironmentError(f"Missing required environment variable: {key}")
    return value

# Telegram
TELEGRAM_API_ID       = int(_require("TELEGRAM_API_ID"))
TELEGRAM_API_HASH     = _require("TELEGRAM_API_HASH")
raw_channel           = _require("TELEGRAM_CHANNEL")
try:
    TELEGRAM_CHANNEL  = int(raw_channel)
except ValueError:
    TELEGRAM_CHANNEL  = raw_channel


# Anthropic
ANTHROPIC_API_KEY     = _require("ANTHROPIC_API_KEY")

# Facebook
FB_PAGE_ACCESS_TOKEN  = _require("FACEBOOK_PAGE_ACCESS_TOKEN")
FB_PAGE_ID            = _require("FACEBOOK_PAGE_ID")

# Contact details
WHATSAPP_NUMBER       = _require("WHATSAPP_NUMBER")
TELEGRAM_USERNAME     = _require("TELEGRAM_USERNAME")

# Behaviour
MEDIA_GROUP_BUFFER_SECONDS = float(os.getenv("MEDIA_GROUP_BUFFER_SECONDS", "3"))
