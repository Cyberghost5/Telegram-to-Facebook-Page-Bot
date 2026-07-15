import json
import logging
import requests
from config import FB_PAGE_ACCESS_TOKEN, FB_PAGE_ID
from utils import retry

logger = logging.getLogger(__name__)
GRAPH_BASE = "https://graph.facebook.com/v19.0"


@retry(max_retries=3, initial_delay=2.0)
def _upload_photo_unpublished(image_path: str) -> str:
    """
    Upload a single image to the Facebook page as an unpublished photo.
    Returns the Facebook photo ID.
    """
    url = f"{GRAPH_BASE}/{FB_PAGE_ID}/photos"
    with open(image_path, "rb") as f:
        response = requests.post(
            url,
            data={
                "published": "false",
                "access_token": FB_PAGE_ACCESS_TOKEN,
            },
            files={"source": f},
            timeout=60,
        )
    if not response.ok:
        logger.error(f"Photo upload failed {response.status_code}: {response.text}")
    response.raise_for_status()
    photo_id = response.json()["id"]
    logger.info(f"Uploaded photo → FB ID: {photo_id}")
    return photo_id


@retry(max_retries=3, initial_delay=2.0)
def _publish_single_photo(image_path: str, message: str) -> str:
    """
    Publish a single photo directly to the page feed in one step.
    Returns the Facebook post ID.
    """
    url = f"{GRAPH_BASE}/{FB_PAGE_ID}/photos"
    with open(image_path, "rb") as f:
        response = requests.post(
            url,
            data={
                "caption": message,
                "published": "true",
                "access_token": FB_PAGE_ACCESS_TOKEN,
            },
            files={"source": f},
            timeout=60,
        )
    if not response.ok:
        logger.error(f"Photo publish failed {response.status_code}: {response.text}")
    response.raise_for_status()
    post_id = response.json()["post_id"]
    logger.info(f"Facebook post published! Post ID: {post_id}")
    return post_id


@retry(max_retries=3, initial_delay=2.0)
def _publish_feed_post(attached_media: list[dict], message: str) -> str:
    """
    Publish a feed post referencing all photo IDs.
    """
    url = f"{GRAPH_BASE}/{FB_PAGE_ID}/feed"
    response = requests.post(
        url,
        data={
            "message": message,
            "attached_media": json.dumps(attached_media),
            "access_token": FB_PAGE_ACCESS_TOKEN,
        },
        timeout=30,
    )
    if not response.ok:
        logger.error(f"Feed post failed {response.status_code}: {response.text}")
    response.raise_for_status()
    post_id = response.json()["id"]
    logger.info(f"Facebook post published! Post ID: {post_id}")
    return post_id


def publish_post(image_paths: list[str], message: str) -> str:
    """
    Publish images to the Facebook page feed with the given message.
    Single photo: direct one-step publish via /photos.
    Multiple photos: upload as unpublished then create a combined feed post.
    Returns the new Facebook post ID.
    """
    if not image_paths:
        raise ValueError("No images provided for Facebook post.")

    if len(image_paths) == 1:
        return _publish_single_photo(image_paths[0], message)

    # Multi-photo: Step 1 — upload all photos as unpublished
    photo_ids = []
    for path in image_paths:
        try:
            pid = _upload_photo_unpublished(path)
            photo_ids.append(pid)
        except Exception as e:
            logger.error(f"Failed to upload {path}: {e}")

    if not photo_ids:
        raise RuntimeError("All photo uploads failed — aborting post.")

    # Multi-photo: Step 2 — publish a feed post referencing all photo IDs
    attached_media = [{"media_fbid": pid} for pid in photo_ids]
    return _publish_feed_post(attached_media, message)
