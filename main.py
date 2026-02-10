import requests
import os
import time
from dotenv import load_dotenv
import threading
from health_check import run_flask

load_dotenv()

# --- CONFIG ---
TWITCH_BROADCASTER_ID = os.getenv("TWITCH_BROADCASTER_ID")
TWITCH_MODERATOR_ID = os.getenv("TWITCH_MODERATOR_ID")
TWITCH_CLIENT_ID = os.getenv("TWITCH_CLIENT_ID")
TWITCH_CLIENT_SECRET = os.getenv("TWITCH_CLIENT_SECRET")

TWITCH_TOKEN = os.getenv("TWITCH_TOKEN")
TWITCH_REFRESH_TOKEN = os.getenv("TWITCH_REFRESH_TOKEN")

DISCORD_WEBHOOK = os.getenv("DISCORD_WEBHOOK")

WATCHLIST = {
    "arky", "bonnie", "itsoddo", "nobodyx_", "barky4l", "zoil",
    "cinna", "1jdab1", "santipulgaz", "yugi2x", "bigmonraph",
    "nosiiree", "emiru", "rosii"
}

CHECK_INTERVAL = 10
alerted_users = set()


# --- TOKEN MANAGEMENT ---

def update_env_tokens(access_token, refresh_token):
    if not os.path.exists(".env"):
        return

    with open(".env", "r") as f:
        lines = f.readlines()

    with open(".env", "w") as f:
        for line in lines:
            if line.startswith("TWITCH_TOKEN="):
                f.write(f"TWITCH_TOKEN={access_token}\n")
            elif line.startswith("TWITCH_REFRESH_TOKEN="):
                f.write(f"TWITCH_REFRESH_TOKEN={refresh_token}\n")
            else:
                f.write(line)


def refresh_twitch_token():
    global TWITCH_TOKEN, TWITCH_REFRESH_TOKEN

    print("🔄 Refreshing Twitch access token...")

    url = "https://id.twitch.tv/oauth2/token"
    params = {
        "grant_type": "refresh_token",
        "refresh_token": TWITCH_REFRESH_TOKEN,
        "client_id": TWITCH_CLIENT_ID,
        "client_secret": TWITCH_CLIENT_SECRET,
    }

    response = requests.post(url, params=params)
    response.raise_for_status()
    data = response.json()

    TWITCH_TOKEN = data["access_token"]
    TWITCH_REFRESH_TOKEN = data["refresh_token"]

    update_env_tokens(TWITCH_TOKEN, TWITCH_REFRESH_TOKEN)

    print("✅ Twitch token refreshed successfully")


# --- TWITCH API ---

def get_chatters():
    url = (
        "https://api.twitch.tv/helix/chat/chatters"
        f"?broadcaster_id={TWITCH_BROADCASTER_ID}"
        f"&moderator_id={TWITCH_MODERATOR_ID}"
    )

    headers = {
        "Authorization": f"Bearer {TWITCH_TOKEN}",
        "Client-Id": TWITCH_CLIENT_ID
    }

    response = requests.get(url, headers=headers)

    # Token expired or revoked
    if response.status_code == 401:
        refresh_twitch_token()
        headers["Authorization"] = f"Bearer {TWITCH_TOKEN}"
        response = requests.get(url, headers=headers)

    response.raise_for_status()
    data = response.json()

    return {user["user_login"].lower() for user in data.get("data", [])}


# --- DISCORD ---

def send_to_discord(username):
    payload = {"content": f"🚨 **{username}** is in chat now!"}
    requests.post(DISCORD_WEBHOOK, json=payload)


# --- MAIN LOOP ---

def main():
    print("👀 Twitch chat watcher started")

    while True:
        try:
            viewers = get_chatters()
            print("Viewers:", viewers)

            for user in WATCHLIST:
                if user in viewers and user not in alerted_users:
                    print(f"🚨 {user} is in chat!")
                    send_to_discord(user)
                    alerted_users.add(user)

            # Remove users who left chat
            alerted_users.intersection_update(viewers)

        except Exception as e:
            print("❌ Error:", e)

        time.sleep(CHECK_INTERVAL)

flask_thread = threading.Thread(target=run_flask, daemon=True)
flask_thread.start()

if __name__ == "__main__":
    main()
