from dotenv import load_dotenv

load_dotenv()

# Bot Core

import os

from classs import FClient

client = FClient()

client.run(os.getenv('BOT_TOKEN'))
