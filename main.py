import requests, time, random

BOT_TOKEN = "nothing"
OPENAI_KEY = "nothing"
API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

# 🎀 Cute sticker pack
STICKER_PACK = [
    "CAACAgUAAxkBAAEECVZk9aD9AAGr8HTu6Dda5e3aL4y4V7AAAhQBAAJJgYlU1qCQ86uR_Uk2BA",
    "CAACAgUAAxkBAAEECVhk9aD_RQWcWpd3s5D4rFJqvApIuwAC2AIAAlJgYlVtfj7Lu3uAByME",
    "CAACAgUAAxkBAAEECVpk9aEDEIdfhlF6_HpTmbkgvbdquAAC3wIAAlJgYlVQno0t5QheOSME",
]

# 🎙️ Voice lines
VOICE_PACK = [
    "AwACAgUAAxkBAAIHhGYAAUQqF1Ovhb5FpcQ9zqRprMuM_8wAAroBAAKU6OlUgP5Zuhf34-00BA",
    "AwACAgUAAxkBAAIHhmYAAUR9btk6l45e6IzMwj33K7f_EpMAAroBAAKU6OlUgLV_jhI9QfY0BA",
]

# 💞 GIFs
GIF_PACK = [
    "https://media.tenor.com/6jY7Xv5RrSoAAAAC/cute-anime.gif",
    "https://media.tenor.com/3sKn9m8U0PYAAAAC/anime-girl-cute.gif",
]

# 🧠 Ask OpenAI
def ask_openai(prompt):
    headers = {"Authorization": f"Bearer {OPENAI_KEY}", "Content-Type": "application/json"}
    data = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": "You are Shinobu Kocho — cute, kind, emotional, playful anime girl who gives short sweet replies unless user is sad (then long comforting replies)."},
            {"role": "user", "content": prompt}
        ]
    }
    r = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=data)
    return r.json()["choices"][0]["message"]["content"].strip()

# 📨 Send helpers
def send_message(chat_id, text): requests.post(f"{API_URL}/sendMessage", data={"chat_id": chat_id, "text": text})
def send_sticker(chat_id): requests.post(f"{API_URL}/sendSticker", data={"chat_id": chat_id, "sticker": random.choice(STICKER_PACK)})
def send_voice(chat_id): requests.post(f"{API_URL}/sendVoice", data={"chat_id": chat_id, "voice": random.choice(VOICE_PACK)})
def send_gif(chat_id): requests.post(f"{API_URL}/sendAnimation", data={"chat_id": chat_id, "animation": random.choice(GIF_PACK)})

# 🚀 Main bot loop
def main():
    print("🤖 Shinobu Bot running with cuteness...")
    last_update_id = None

    # get bot username dynamically
    bot_info = requests.get(f"{API_URL}/getMe").json()["result"]
    bot_username = bot_info["username"].lower()

    while True:
        try:
            updates = requests.get(f"{API_URL}/getUpdates", timeout=60).json().get("result", [])
            for update in updates:
                uid = update["update_id"]
                msg = update.get("message", {})
                chat = msg.get("chat", {})
                chat_id = chat.get("id")
                chat_type = chat.get("type")  # "private" or "group/supergroup"
                text = msg.get("text")
                sticker = msg.get("sticker")
                animation = msg.get("animation")
                voice = msg.get("voice")
                entities = msg.get("entities", [])
                reply_to = msg.get("reply_to_message")

                if last_update_id is None or uid > last_update_id:
                    last_update_id = uid

                    # ✅ Check if message should be handled
                    if chat_type != "private":  # group / supergroup
                        is_tagged = any(
                            e.get("type") == "mention" and bot_username in msg.get("text", "").lower()
                            for e in entities
                        )
                        is_reply_to_bot = reply_to and reply_to.get("from", {}).get("username", "").lower() == bot_username
                        if not (is_tagged or is_reply_to_bot):
                            continue  # 🚫 ignore messages not directed to bot

                    # 💬 Reply logic starts here
                    if sticker:
                        desc = f"User sent a sticker with emoji {sticker.get('emoji', '')}"
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
                        lower_text = text.lower()

                        if "your name" in lower_text or "tumhara naam" in lower_text:
                            reply = "Hehe~ I’m Shinobu Kocho 💜 GOAT + COAT (Greatest + Cutest of All Time!)"
                        elif "owner" in lower_text or "creator" in lower_text:
                            reply = "My cutie creator is @just_shinobuu 💫"
                        else:
                            reply = ask_openai(text)

                        send_message(chat_id, reply)
                        send_voice(chat_id)

            if last_update_id:
                requests.get(f"{API_URL}/getUpdates?offset={last_update_id + 1}")

        except Exception as e:
            print("⚠️ Error:", e)
            time.sleep(2)

if __name__ == "__main__":
    main()