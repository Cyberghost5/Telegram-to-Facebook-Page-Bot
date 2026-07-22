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

raw_target_channel    = os.getenv("TARGET_TELEGRAM_CHANNEL")
if raw_target_channel:
    try:
        TARGET_TELEGRAM_CHANNEL = int(raw_target_channel)
    except ValueError:
        TARGET_TELEGRAM_CHANNEL = raw_target_channel
else:
    TARGET_TELEGRAM_CHANNEL = None



# Anthropic
ANTHROPIC_API_KEY     = _require("ANTHROPIC_API_KEY")

# Facebook
FB_PAGE_ACCESS_TOKEN  = _require("FACEBOOK_PAGE_ACCESS_TOKEN")
FB_PAGE_ID            = _require("FACEBOOK_PAGE_ID")

# Instagram (Optional)
INSTAGRAM_ACCOUNT_ID  = os.getenv("INSTAGRAM_ACCOUNT_ID")
PUBLIC_BASE_URL       = os.getenv("PUBLIC_BASE_URL", "").rstrip("/")

# Contact details
WHATSAPP_NUMBER       = _require("WHATSAPP_NUMBER")
TELEGRAM_USERNAME     = _require("TELEGRAM_USERNAME")

# Behaviour
MEDIA_GROUP_BUFFER_SECONDS = float(os.getenv("MEDIA_GROUP_BUFFER_SECONDS", "3"))
