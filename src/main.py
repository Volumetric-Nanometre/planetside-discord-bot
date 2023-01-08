"""
@author Michael O'Donnell & Lee Connor Williams

https://github.com/Volumetric-Nanometre/planetside-discord-bot
https://github.com/LCWilliams/planetside-discord-bot
"""

from planetsidebot import Bot
import asyncio
import atexit

from botUtils import FilesAndFolders
from botUtils import BotPrinter as BUPrint
from botData.settings import BotSettings
import signal

FilesAndFolders.SetupFolders()

ps2Bot = Bot()
atexit.register(ps2Bot.ExitCalled)


mainLoop = asyncio.get_event_loop()

try:
	mainLoop.run_until_complete(ps2Bot.start(BotSettings.discordToken))
except KeyboardInterrupt:
	BUPrint.Info("Keyboard interrupt detected.")
finally:
	mainLoop.close()

BUPrint.Info("Bot shutdown complete.")

# asyncio.run( ps2Bot.run(BotSettings.discordToken), debug=BotSettings.bDebugEnabled)