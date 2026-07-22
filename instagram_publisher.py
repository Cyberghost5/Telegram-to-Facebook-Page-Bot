import os
import json
import time
import logging
import requests
from config import FB_PAGE_ACCESS_TOKEN, INSTAGRAM_ACCOUNT_ID, PUBLIC_BASE_URL
from utils import retry

logger = logging.getLogger(__name__)
GRAPH_BASE = "https://graph.facebook.com/v19.0"


def _get_public_url(local_path: str) -> str:
    """
    Construct a public URL for a local file in the downloads folder.
    """
    filename = os.path.basename(local_path)
    return f"{PUBLIC_BASE_URL}/downloads/{filename}"


def _wait_for_container(container_id: str, timeout: int = 120, check_interval: int = 5):
    """
    Poll container status until FINISHED or ERROR.
    """
    url = f"{GRAPH_BASE}/{container_id}"
    start = time.time()
    while time.time() - start < timeout:
        res = requests.get(
            url,
            params={
                "fields": "status_code,status",
                "access_token": FB_PAGE_ACCESS_TOKEN,
            },
            timeout=15,
        )
        if res.ok:
            data = res.json()
            status = data.get("status_code")
            if status == "FINISHED":
                logger.info(f"Instagram container {container_id} is FINISHED.")
                return
            elif status == "ERROR":
                err_details = data.get("status", "Unknown error")
                raise RuntimeError(f"Instagram container {container_id} error: {err_details}")
            else:
                logger.info(f"Container {container_id} status: {status}. Waiting...")
        time.sleep(check_interval)
    raise TimeoutError(f"Timed out waiting for Instagram container {container_id}")


@retry(max_retries=3, initial_delay=2.0)
def _create_item_container(
    public_url: str,
    media_type: str,
    caption: str = "",
    is_carousel_item: bool = False
) -> str:
    """
    Create a container for a photo, video (Reel), or carousel item.
    """
    url = f"{GRAPH_BASE}/{INSTAGRAM_ACCOUNT_ID}/media"
    payload = {
        "access_token": FB_PAGE_ACCESS_TOKEN,
    }

    if is_carousel_item:
        payload["is_carousel_item"] = "true"
        if media_type == "video":
            payload["media_type"] = "VIDEO"
            payload["video_url"] = public_url
        else:
            payload["image_url"] = public_url
    else:
        if caption:
            payload["caption"] = caption
        if media_type == "video":
            payload["media_type"] = "REELS"
            payload["video_url"] = public_url
        else:
            payload["image_url"] = public_url

    response = requests.post(url, data=payload, timeout=30)
    if not response.ok:
        logger.error(f"Instagram container creation failed {response.status_code}: {response.text}")
    response.raise_for_status()
    container_id = response.json()["id"]
    logger.info(f"Created Instagram container → ID: {container_id}")
    return container_id


@retry(max_retries=3, initial_delay=2.0)
def _create_carousel_container(children_ids: list[str], caption: str) -> str:
    """
    Create a parent Carousel container referencing child container IDs.
    """
    url = f"{GRAPH_BASE}/{INSTAGRAM_ACCOUNT_ID}/media"
    payload = {
        "media_type": "CAROUSEL",
        "children": json.dumps(children_ids),
        "caption": caption,
        "access_token": FB_PAGE_ACCESS_TOKEN,
    }
    response = requests.post(url, data=payload, timeout=30)
    if not response.ok:
        logger.error(f"Instagram carousel container creation failed {response.status_code}: {response.text}")
    response.raise_for_status()
    container_id = response.json()["id"]
    logger.info(f"Created Instagram carousel container → ID: {container_id}")
    return container_id


@retry(max_retries=3, initial_delay=2.0)
def _publish_container(container_id: str) -> str:
    """
    Publish a ready container ID to the Instagram feed.
    """
    url = f"{GRAPH_BASE}/{INSTAGRAM_ACCOUNT_ID}/media_publish"
    response = requests.post(
        url,
        data={
            "creation_id": container_id,
            "access_token": FB_PAGE_ACCESS_TOKEN,
        },
        timeout=30,
    )
    if not response.ok:
        logger.error(f"Instagram publish failed {response.status_code}: {response.text}")
    response.raise_for_status()
    post_id = response.json()["id"]
    logger.info(f"Instagram post published! Post ID: {post_id}")
    return post_id


def publish_instagram_post(media_items: list, message: str) -> str:
    """
    Publish media items (photos/videos) to Instagram.
    'media_items' can be a list of paths or tuples: (local_path, media_type).
    """
    if not INSTAGRAM_ACCOUNT_ID:
        raise ValueError("INSTAGRAM_ACCOUNT_ID is not configured.")
    if not PUBLIC_BASE_URL:
        raise ValueError("PUBLIC_BASE_URL is not configured (required for Instagram API).")
    if not media_items:
        raise ValueError("No media provided for Instagram post.")

    # Normalize items to (path, media_type)
    normalized = []
    for item in media_items:
        if isinstance(item, tuple):
            normalized.append(item)
        else:
            normalized.append((str(item), "photo"))

    # Single Photo or Video
    if len(normalized) == 1:
        path, m_type = normalized[0]
        pub_url = _get_public_url(path)
        logger.info(f"Publishing single {m_type} to Instagram via {pub_url}...")
        container_id = _create_item_container(pub_url, m_type, caption=message, is_carousel_item=False)
        _wait_for_container(container_id)
        return _publish_container(container_id)

    # Carousel (up to 10 items)
    logger.info(f"Publishing Carousel of {len(normalized)} items to Instagram...")
    child_ids = []
    for path, m_type in normalized[:10]:  # Instagram carousel max limit is 10
        pub_url = _get_public_url(path)
        cid = _create_item_container(pub_url, m_type, caption="", is_carousel_item=True)
        _wait_for_container(cid)
        child_ids.append(cid)

    carousel_id = _create_carousel_container(child_ids, caption=message)
    _wait_for_container(carousel_id)
    return _publish_container(carousel_id)
