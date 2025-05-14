import os
from dotenv import load_dotenv

if os.getenv('IS_DOCKER') is None:
    load_dotenv()

# Bot Core

from classs import FClient

client = FClient()

client.run(os.getenv('BOT_TOKEN'))
