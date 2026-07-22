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
def _upload_video_unpublished(video_path: str) -> str:
    """
    Upload a single video to the Facebook page as an unpublished video.
    Returns the Facebook video ID.
    """
    url = f"{GRAPH_BASE}/{FB_PAGE_ID}/videos"
    with open(video_path, "rb") as f:
        response = requests.post(
            url,
            data={
                "published": "false",
                "access_token": FB_PAGE_ACCESS_TOKEN,
            },
            files={"source": f},
            timeout=120,
        )
    if not response.ok:
        logger.error(f"Video upload failed {response.status_code}: {response.text}")
    response.raise_for_status()
    video_id = response.json()["id"]
    logger.info(f"Uploaded video → FB ID: {video_id}")
    return video_id


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
def _publish_single_video(video_path: str, message: str) -> str:
    """
    Publish a single video directly to the page feed in one step.
    Returns the Facebook post ID.
    """
    url = f"{GRAPH_BASE}/{FB_PAGE_ID}/videos"
    with open(video_path, "rb") as f:
        response = requests.post(
            url,
            data={
                "description": message,
                "published": "true",
                "access_token": FB_PAGE_ACCESS_TOKEN,
            },
            files={"source": f},
            timeout=120,
        )
    if not response.ok:
        logger.error(f"Video publish failed {response.status_code}: {response.text}")
    response.raise_for_status()
    post_id = response.json()["id"]
    logger.info(f"Facebook video post published! Post ID: {post_id}")
    return post_id


@retry(max_retries=3, initial_delay=2.0)
def _publish_feed_post(attached_media: list[dict], message: str) -> str:
    """
    Publish a feed post referencing all media IDs (photos and/or videos).
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


def publish_post(media_items: list, message: str) -> str:
    """
    Publish media items (photos/videos) to the Facebook page feed with the given message.
    'media_items' can be a list of file paths (strings) or list of tuples: (path, media_type).
    Single media: direct publish via /photos or /videos.
    Multiple media: upload as unpublished then create a combined feed post.
    Returns the new Facebook post ID.
    """
    if not media_items:
        raise ValueError("No media provided for Facebook post.")

    # Normalize items to (path, media_type)
    normalized = []
    for item in media_items:
        if isinstance(item, tuple):
            normalized.append(item)
        else:
            normalized.append((str(item), "photo"))

    if len(normalized) == 1:
        path, m_type = normalized[0]
        if m_type == "video":
            return _publish_single_video(path, message)
        return _publish_single_photo(path, message)

    # Multi-media: Step 1 — upload all items as unpublished
    media_ids = []
    for path, m_type in normalized:
        try:
            if m_type == "video":
                pid = _upload_video_unpublished(path)
            else:
                pid = _upload_photo_unpublished(path)
            media_ids.append(pid)
        except Exception as e:
            logger.error(f"Failed to upload {m_type} {path}: {e}")

    if not media_ids:
        raise RuntimeError("All media uploads failed — aborting post.")

    # Multi-photo/video: Step 2 — publish a feed post referencing all media IDs
    attached_media = [{"media_fbid": pid} for pid in media_ids]
    return _publish_feed_post(attached_media, message)
