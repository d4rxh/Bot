#!/usr/bin/env python3
import os
import time
import random
import logging
import requests

# ---------- Config (use environment variables on Render) ----------
BOT_TOKEN = os.getenv("BOT_TOKEN")    # set in Render Dashboard -> Environment
OPENAI_KEY = os.getenv("OPENAI_KEY")  # set in Render Dashboard -> Environment
if not BOT_TOKEN or not OPENAI_KEY:
    raise SystemExit("Missing BOT_TOKEN or OPENAI_KEY environment variable. Set them in your Render service settings.")

API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

# Cute assets (keep IDs as-is or change)
STICKER_PACK = [ ... ]  # keep your sticker IDs (omitted here to avoid showing secrets)
VOICE_PACK = [ ... ]
GIF_PACK = [ ... ]

# ---------- Logging ----------
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
logger = logging.getLogger("shinobu_bot")

# ---------- Requests session ----------
session = requests.Session()
session.headers.update({"User-Agent": "ShinobuBot/1.0"})

# ---------- Helper functions ----------
def safe_json_resp(resp):
    try:
        return resp.json()
    except ValueError:
        return {"ok": False, "description": "Invalid JSON from API", "text": resp.text}

def get_bot_info():
    r = session.get(f"{API_URL}/getMe", timeout=10)
    j = safe_json_resp(r)
    if not j.get("ok"):
        logger.error("getMe failed: %s (HTTP %s)", j.get("description") or j.get("text"), r.status_code)
        return None
    return j["result"]

def ask_openai(prompt):
    try:
        headers = {"Authorization": f"Bearer {OPENAI_KEY}", "Content-Type": "application/json"}
        data = {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": "You are Shinobu Kocho — cute, kind, emotional, playful anime girl who gives short sweet replies unless user is sad (then long comforting replies)."},
                {"role": "user", "content": prompt}
            ],
        }
        r = session.post("https://api.openai.com/v1/chat/completions", headers=headers, json=data, timeout=15)
        j = safe_json_resp(r)
        # be defensive
        if not j.get("choices") or not isinstance(j["choices"], list):
            logger.warning("OpenAI unexpected response: %s", j)
            return "Sorry, I couldn't think of a reply right now~"
        return j["choices"][0]["message"]["content"].strip()
    except Exception as e:
        logger.exception("OpenAI request failed")
        return "Hehe~ I can't talk to OpenAI right now, but I'm still cute!"

def send_method(method, payload):
    try:
        r = session.post(f"{API_URL}/{method}", data=payload, timeout=10)
        j = safe_json_resp(r)
        if not j.get("ok"):
            logger.warning("Telegram %s failed: %s", method, j.get("description") or j)
        return j
    except Exception:
        logger.exception("Failed to call Telegram API method %s", method)
        return None

def send_message(chat_id, text):
    return send_method("sendMessage", {"chat_id": chat_id, "text": text})

def send_sticker(chat_id):
    return send_method("sendSticker", {"chat_id": chat_id, "sticker": random.choice(STICKER_PACK)})

def send_voice(chat_id):
    return send_method("sendVoice", {"chat_id": chat_id, "voice": random.choice(VOICE_PACK)})

def send_gif(chat_id):
    return send_method("sendAnimation", {"chat_id": chat_id, "animation": random.choice(GIF_PACK)})

# ---------- Main loop ----------
def main():
    logger.info("🤖 Shinobu Bot starting...")
    bot_info = get_bot_info()
    if not bot_info:
        logger.error("Cannot get bot info. Check BOT_TOKEN and network. Exiting.")
        return
    bot_username = bot_info.get("username", "").lower()
    logger.info("Bot username: @%s", bot_username)

    last_update_id = None
    backoff = 1

    while True:
        try:
            params = {"timeout": 60, "limit": 50}
            if last_update_id:
                params["offset"] = last_update_id + 1

            r = session.get(f"{API_URL}/getUpdates", params=params, timeout=70)
            j = safe_json_resp(r)
            if not j.get("ok"):
                # log the error and wait; do not crash
                logger.warning("getUpdates returned not ok: %s", j.get("description") or j)
                time.sleep(min(backoff, 60))
                backoff = min(backoff * 2, 60)
                continue

            updates = j.get("result", [])
            if updates:
                backoff = 1  # reset backoff on success

            for update in updates:
                uid = update["update_id"]
                if last_update_id is None or uid > last_update_id:
                    last_update_id = uid

                    msg = update.get("message", {})
                    chat = msg.get("chat", {})
                    chat_id = chat.get("id")
                    chat_type = chat.get("type")
                    text = msg.get("text")
                    sticker = msg.get("sticker")
                    animation = msg.get("animation")
                    voice = msg.get("voice")
                    entities = msg.get("entities", [])
                    reply_to = msg.get("reply_to_message")

                    # group message handling
                    if chat_type != "private":
                        is_tagged = False
                        if text and entities:
                            is_tagged = any(
                                e.get("type") == "mention" and bot_username in (text or "").lower()
                                for e in entities
                            )
                        is_reply_to_bot = reply_to and reply_to.get("from", {}).get("username", "").lower() == bot_username
                        if not (is_tagged or is_reply_to_bot):
                            continue

                    # handlers
                    if sticker:
                        desc = f"User sent a sticker with emoji {sticker.get('emoji','')}"
                        reply = ask_openai(f"{desc}\nReply like Shinobu Kocho.")
                        send_message(chat_id, reply)
                        send_sticker(chat_id)
                        send_voice(chat_id)

                    elif animation:
                        reply = ask_openai("User sent a cute GIF animation 💞 Reply like Shinobu Kocho.")
                        send_message(chat_id, reply)
                        send_gif(chat_id)

                    elif voice:
                        reply = "Hehe~ your voice is so sweet 😚 listen to mine~"
                        send_message(chat_id, reply)
                        send_voice(chat_id)

                    elif text:
                        lower_text = (text or "").lower()
                        if "your name" in lower_text or "tumhara naam" in lower_text:
                            reply = "Hehe~ I’m Shinobu Kocho 💜 GOAT + COAT (Greatest + Cutest of All Time!)"
                        elif "owner" in lower_text or "creator" in lower_text:
                            reply = "My cutie creator is @just_shinobuu 💫"
                        else:
                            reply = ask_openai(text)

                        send_message(chat_id, reply)
                        send_voice(chat_id)

            # small sleep to be friendly
            time.sleep(0.1)

        except Exception as e:
            logger.exception("Error in main loop")
            time.sleep(2)  # short pause after unexpected error

if __name__ == "__main__":
    main()
