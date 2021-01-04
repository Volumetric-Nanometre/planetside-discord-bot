import os
from dotenv import load_dotenv

load_dotenv()
global TOKEN
global GUILD
global PS2SVSID 

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
DISCORD_GUILD = os.getenv('DISCORD_GUILD')
PS2_SVS_ID = os.getenv('PS2_SVS_ID')

print("Tokens loaded")