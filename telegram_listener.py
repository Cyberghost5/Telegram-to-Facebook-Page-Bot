import os
import asyncio
import logging
from pyrogram import Client, filters
from pyrogram.types import Message, InputMediaPhoto

import database as db
from media_buffer import add_to_group
from composer import compose_facebook_post
from facebook_publisher import publish_post
from config import TELEGRAM_API_ID, TELEGRAM_API_HASH, TELEGRAM_CHANNEL, TARGET_TELEGRAM_CHANNEL

logger = logging.getLogger(__name__)

DOWNLOADS_DIR = "downloads"
os.makedirs(DOWNLOADS_DIR, exist_ok=True)

app = Client(
    "truck_forwarder_session",
    api_id=TELEGRAM_API_ID,
    api_hash=TELEGRAM_API_HASH,
)


async def handle_group(messages: list[Message]):
    """
    Called when a complete media group has been buffered.
    Downloads images, composes post, publishes to Facebook.
    """
    gid = messages[0].media_group_id

    if db.is_group_processed(gid):
        logger.info(f"Group {gid} already processed — skipping.")
        return

    # Extract caption from whichever message in the group has one
    raw_caption = next(
        (m.caption for m in messages if m.caption),
        ""
    )
    logger.info(
        f"Processing group {gid} | {len(messages)} photo(s) | "
        f"caption length: {len(raw_caption)} chars"
    )

    # Download all photos
    image_paths = []
    for msg in messages:
        try:
            path = await msg.download(
                file_name=f"{DOWNLOADS_DIR}/{gid}_{msg.id}.jpg"
            )
            if path:
                image_paths.append(path)
                logger.info(f"Downloaded: {path}")
            else:
                logger.error(f"Failed to download photo from message {msg.id}: download returned None")
        except Exception as e:
            logger.error(f"Failed to download photo from message {msg.id}: {e}")

    if not image_paths:
        logger.error(f"No images downloaded for group {gid} — skipping.")
        return

    try:
        # Compose post text via Claude (offloaded to thread to avoid blocking event loop)
        post_text = await asyncio.to_thread(compose_facebook_post, raw_caption)

        # Publish to Facebook (offloaded to thread to avoid blocking event loop)
        post_id = await asyncio.to_thread(publish_post, image_paths, post_text)
        logger.info(f"Successfully published to Facebook. Post ID: {post_id}")

        # Optional: Forward the AI-rewritten post to target Telegram channel
        if TARGET_TELEGRAM_CHANNEL:
            try:
                media = [InputMediaPhoto(path) for path in image_paths]
                if media:
                    media[0].caption = post_text
                await app.send_media_group(chat_id=TARGET_TELEGRAM_CHANNEL, media=media)
                logger.info(f"Successfully posted media group to target Telegram channel: {TARGET_TELEGRAM_CHANNEL}")
            except Exception as tg_err:
                logger.error(f"Failed to post media group to target Telegram channel: {tg_err}")

        # Mark as processed to prevent duplicates
        db.mark_group_processed(gid)

    except Exception as e:
        logger.exception(f"Error publishing group {gid}: {e}")

    finally:
        # Clean up downloaded files
        for path in image_paths:
            try:
                os.remove(path)
            except OSError:
                pass


async def handle_single_photo(message: Message):
    """
    Called for a single photo message (no media_group_id).
    """
    if db.is_message_processed(message.id):
        logger.info(f"Message {message.id} already processed — skipping.")
        return

    raw_caption = message.caption or ""
    logger.info(
        f"Processing single photo message {message.id} | "
        f"caption length: {len(raw_caption)} chars"
    )

    try:
        path = await message.download(
            file_name=f"{DOWNLOADS_DIR}/{message.id}.jpg"
        )
        if not path:
            logger.error(f"Failed to download photo from message {message.id}: download returned None")
            return
    except Exception as e:
        logger.error(f"Failed to download photo from message {message.id}: {e}")
        return

    try:
        # Compose post text via Claude (offloaded to thread to avoid blocking event loop)
        post_text = await asyncio.to_thread(compose_facebook_post, raw_caption)
        
        # Publish to Facebook (offloaded to thread to avoid blocking event loop)
        post_id = await asyncio.to_thread(publish_post, [path], post_text)
        logger.info(f"Successfully published to Facebook. Post ID: {post_id}")

        # Optional: Forward the AI-rewritten post to target Telegram channel
        if TARGET_TELEGRAM_CHANNEL:
            try:
                await app.send_photo(chat_id=TARGET_TELEGRAM_CHANNEL, photo=path, caption=post_text)
                logger.info(f"Successfully posted single photo to target Telegram channel: {TARGET_TELEGRAM_CHANNEL}")
            except Exception as tg_err:
                logger.error(f"Failed to post single photo to target Telegram channel: {tg_err}")

        db.mark_message_processed(message.id)

    except Exception as e:
        logger.exception(f"Error publishing message {message.id}: {e}")

    finally:
        try:
            if path:
                os.remove(path)
        except OSError:
            pass


@app.on_message(
    filters.chat(TELEGRAM_CHANNEL) & filters.photo
)
async def on_photo(client: Client, message: Message):
    """
    Fires on every photo message in the monitored channel.
    Routes to group buffer or single-photo handler.
    """
    if message.media_group_id:
        await add_to_group(message, handle_group)
    else:
        await handle_single_photo(message)
