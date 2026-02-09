from flask import Flask #type: ignore
import threading
import time
import aiohttp #type: ignore
import asyncio

app = Flask(__name__)

@app.route('/')
def health_check():
    return 'Website is running!'

def self_ping_website():
    """
    Periodically pings the website to keep it alive.
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    while True:
        try:
            loop.run_until_complete(ping_website())
        except Exception as err:
            print(f"Self-ping error: {err}")
        time.sleep(600)

async def ping_website():
    """
    Asynchronous function to perform the self-ping.
    """
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get('https://gob-managment.onrender.com/') as response:  # Change to your deployed URL
                if response.status == 200:
                    print('Self-ping successful!')
                else:
                    print(f'Self-ping failed: {response.status}')
        except Exception as err:
            print(f"Self-ping request error: {err}")

def run_flask():
    """
    Runs the Flask app and starts the self-ping in a separate thread.
    """
    # Start self-ping in a background thread
    ping_thread = threading.Thread(target=self_ping_website, daemon=True)
    ping_thread.start()

    # Run the Flask app
    app.run(host='0.0.0.0', port=5000)
