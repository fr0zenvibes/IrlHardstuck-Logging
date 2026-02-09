import requests
import os
import time
from dotenv import load_dotenv
import threading
from health_check import run_flask

load_dotenv()

# --- CONFIG ---
TWITCH_BROADCASTER_ID = os.getenv("TWITCH_BROADCASTER_ID")  # e.g., 123456
TWITCH_MODERATOR_ID = os.getenv("TWITCH_MODERATOR_ID")      # e.g., your bot or mod ID
TWITCH_TOKEN = os.getenv("TWITCH_TOKEN")                    # OAuth token
TWITCH_CLIENT_ID = os.getenv("TWITCH_CLIENT_ID")            # Twitch App Client ID
DISCORD_WEBHOOK = os.getenv("DISCORD_WEBHOOK")              # Discord webhook URL

WATCHLIST = {"arky", "bonnie", "itsoddo", "nobodyx_", "barky4l", "zoil", "cinna", "1jdab1", "santipulgaz", "yugi2x", "bigmonraph", "nosiiree", "emiru", "rosii"}

CHECK_INTERVAL = 30  # seconds between API calls

alerted_users = set()

def get_chatters():
    url = f"https://api.twitch.tv/helix/chat/chatters?broadcaster_id={TWITCH_BROADCASTER_ID}&moderator_id={TWITCH_MODERATOR_ID}"
    headers = {
        "Authorization": f"Bearer {TWITCH_TOKEN}",
        "Client-Id": TWITCH_CLIENT_ID
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    data = response.json()
    
    # The response has 'data' field which is a list of chatters
    viewers = {user["user_login"].lower() for user in data.get("data", [])}
    return viewers

def send_to_discord(username):
    payload = {"content": f"🚨 **{username}** is in chat now!"}
    requests.post(DISCORD_WEBHOOK, json=payload)

def main():
    while True:
        try:
            viewers = get_chatters()
            print(viewers)
            for user in WATCHLIST:
                if user in viewers and user not in alerted_users:
                    print(f"{user} is in chat!")
                    send_to_discord(user)
                    alerted_users.add(user)

            alerted_users.intersection_update(viewers)

        except Exception as e:
            print("Error fetching chatters:", e)

        time.sleep(CHECK_INTERVAL)


flask_thread = threading.Thread(target=run_flask, daemon=True)
flask_thread.start()

if __name__ == "__main__":
    main()
