import os
from dotenv import load_dotenv
import botUtils

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
bShowDebug = True


botUtils.BotPrinter.Debug("Tokens loaded")
botUtils.BotPrinter.Debug(f"Active Dir: {botDir}")
# print (f"Active Dir: {botDir}")