"""
Telegram sends each photo in a media group as a separate event.
This module buffers them by media_group_id for BUFFER_SECONDS,
then fires a callback with the complete list of messages.
"""
import asyncio
import logging
from collections import defaultdict
from typing import Callable, Awaitable

from config import MEDIA_GROUP_BUFFER_SECONDS

logger = logging.getLogger(__name__)

# { media_group_id: [message, ...] }
_buffers: dict[str, list] = defaultdict(list)

# { media_group_id: asyncio.TimerHandle }
_timers: dict[str, asyncio.Task] = {}


async def add_to_group(
    message,
    on_group_ready: Callable[[list], Awaitable[None]]
):
    """
    Add a message to its media group buffer.
    Resets the flush timer each time a new message arrives.
    """
    gid = message.media_group_id
    _buffers[gid].append(message)

    # Cancel existing timer for this group (new photo just arrived)
    if gid in _timers:
        _timers[gid].cancel()

    async def _flush():
        await asyncio.sleep(MEDIA_GROUP_BUFFER_SECONDS)
        messages = _buffers.pop(gid, [])
        _timers.pop(gid, None)
        if messages:
            # Sort by message_id to preserve original order
            messages.sort(key=lambda m: m.id)
            logger.info(
                f"Media group {gid} ready with {len(messages)} photo(s)."
            )
            await on_group_ready(messages)

    _timers[gid] = asyncio.create_task(_flush())
