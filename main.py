import logging
import database as db
import telegram_listener  # registers the @app.on_message handler via import

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(stream=open(1, "w", encoding="utf-8", closefd=False)),
        logging.FileHandler("truck_forwarder.log", encoding="utf-8"),
    ],
)

logger = logging.getLogger(__name__)


def main():
    logger.info("🚛 Truck Forwarder starting up...")
    db.init_db()
    logger.info(f"Monitoring channel: {telegram_listener.TELEGRAM_CHANNEL}")
    telegram_listener.app.run()


if __name__ == "__main__":
    main()
