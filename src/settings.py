import os
from dotenv import load_dotenv

load_dotenv()
global TOKEN
global GUILD
global PS2SVSID 

global botDir # The Directory of the bot.
global opsFolderName
global bShowDebug

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
DISCORD_GUILD = os.getenv('DISCORD_GUILD')
PS2_SVS_ID = os.getenv('PS2_SVS_ID')
botDir = os.getcwd()
opsFolderName = "TDKDOps"
defaultOpsDir = "SavedOps"
bShowDebug = True


# print("Tokens loaded")
# print(f"Active Dir: {botDir}")