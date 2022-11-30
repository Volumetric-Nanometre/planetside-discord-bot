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
# NOTE: The below Directory variables are APPENDED to botDir in use.
opsFolderName = "TDKDOps" # Foldername/Dir for CREATED (live) Ops
defaultOpsDir = "SavedOps" # Foldername/Dir for DEFAULT Ops

signupCategory = "SIGN UP" # The category name (must match capitalisation!)
resignIcon = "❌" # The icon to use for the RESIGN role. 🔳 ❌
reserveIcon = "⭕" # The icon to use for the RESERVE role.
bShowDebug = True # Set to FALSE in live environment to keep console clean.


# print("Tokens loaded")
# print(f"Active Dir: {botDir}")