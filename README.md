# 🚛 Truck Forwarder

Automatically forwards truck listings from a Telegram channel to your Facebook Page.
Acts as a middleman — composes clean posts using AI and appends your contact details.

## How It Works

```
Telegram Channel Post (photos + caption)
        ↓
  Pyrogram (listens as your Telegram account)
        ↓
  Buffer media group (collects all photos, waits 3s)
        ↓
  Claude API (composes clean Facebook post from raw caption)
        ↓
  Facebook Graph API (uploads photos + publishes post)
        ↓
  Your Facebook Page ✅
```

---

## Setup

### 1. Clone & install dependencies

```bash
git clone <your-repo>
cd truck-forwarder
pip install -r requirements.txt
```

### 2. Get your Telegram API credentials

1. Go to https://my.telegram.org/apps
2. Log in with your phone number
3. Create a new application
4. Copy the `api_id` and `api_hash`

### 3. Get your Facebook Page Access Token

1. Go to https://developers.facebook.com
2. Create an app (type: Business)
3. Add the **Pages API** product
4. Generate a **long-lived Page Access Token** for your page
5. Make sure your token has permissions: `pages_manage_posts`, `pages_read_engagement`

### 4. Configure environment

```bash
cp .env.example .env
# Fill in all values in .env
```

### 5. Find your Telegram channel identifier

- For public channels: use `@channelname`
- For private channels: forward a message from the channel to
  @username_to_id_bot to get the numeric ID (e.g. `-1001234567890`)

### 6. Run

```bash
python main.py
```

On first run, Pyrogram will ask for your phone number and an OTP to log in.
After that, a `truck_forwarder_session.session` file is created — you won't
need to log in again.

---

## Deploying to Railway

1. Push this repo to GitHub
2. Go to https://railway.app → New Project → Deploy from GitHub
3. Add all your `.env` values as Railway environment variables
4. Railway will keep it running 24/7

> **Note:** After first login, commit your `.session` file or set it as a
> Railway volume — otherwise Pyrogram will ask for OTP on every redeploy.

---

## File Structure

```
truck-forwarder/
├── main.py                 # Entry point
├── config.py               # Environment variable loader
├── database.py             # SQLite — prevents duplicate posts
├── media_buffer.py         # Buffers Telegram media groups
├── composer.py             # Claude API post composer
├── facebook_publisher.py   # Facebook Graph API publisher
├── telegram_listener.py    # Pyrogram channel listener
├── requirements.txt
└── .env.example
```
