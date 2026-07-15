import logging
import anthropic
from config import ANTHROPIC_API_KEY, WHATSAPP_NUMBER, TELEGRAM_USERNAME
from utils import retry

logger = logging.getLogger(__name__)
client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

SYSTEM_PROMPT = """
You are a professional truck dealership copywriter.
Your job is to take a raw Telegram caption describing a truck for sale
and turn it into a clean, engaging Facebook post.

Rules:
- Extract and clearly present any specs you find: make, model, year, mileage,
  engine, transmission, condition, price, location — whatever is available.
- Use simple section headers like "🚛 Truck Details" and "💰 Price" where relevant.
- Keep the tone professional but warm — this is a marketplace post, not a legal document.
- Do NOT invent specs that are not in the original text.
- Do NOT apply text syling such as bold or italics.
- Do NOT include emojis.
- Always change the brand name to "Truck Sales USA" if you see any other brand name.
- Do NOT include any contact information — that will be appended separately.
- End your composed post ONLY with the truck details and a single blank line.
  Do not add any sign-off or CTA — those are added outside.
- Output ONLY the composed post body. No preamble, no explanation.
""".strip()


@retry(max_retries=3, initial_delay=2.0)
def compose_facebook_post(raw_caption: str) -> str:
    """
    Sends the raw Telegram caption to Claude and returns
    a fully composed Facebook post body (without contact details yet).
    """
    logger.info("Composing Facebook post via Claude API...")

    if not raw_caption or not raw_caption.strip():
        body = "🚛 Truck available for sale. Contact us for full details."
    else:
        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": f"Here is the raw caption:\n\n{raw_caption}"
                }
            ]
        )
        body = message.content[0].text.strip()

    # Append your contact details + CTA
    clean_wa = "".join(c for c in WHATSAPP_NUMBER if c.isdigit())
    clean_tg = TELEGRAM_USERNAME.lstrip("@")

    contact_block = (
        "\n\n📞 Reach out to us to get this truck or learn more:\n"
        f"  • WhatsApp: https://wa.me/{clean_wa}\n"
        f"  • Telegram: https://t.me/{clean_tg}"
    )

    full_post = body + contact_block
    logger.info("Post composed successfully.")
    return full_post
