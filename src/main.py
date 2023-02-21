"""
@author Michael O'Donnell & Lee Connor Williams

https://github.com/Volumetric-Nanometre/planetside-discord-bot
https://github.com/LCWilliams/planetside-discord-bot
"""

from planetsidebot import Bot
import asyncio
import asyncio_atexit

from botUtils import FilesAndFolders
from botUtils import BotPrinter as BUPrint
from botData.settings import BotSettings

FilesAndFolders.SetupFolders()

ps2Bot = Bot()
mainLoop = asyncio.new_event_loop()
asyncio.set_event_loop(mainLoop)
asyncio_atexit.register(callback=ps2Bot.ExitCalled, loop=mainLoop)

try:
	mainLoop.run_until_complete(ps2Bot.start(BotSettings.discordToken))
except KeyboardInterrupt:
	BUPrint.Info("Keyboard interrupt detected.")
	pass
finally:
	mainLoop.close()
	BUPrint.Info("Bot shutdown complete.")


# asyncio.run( ps2Bot.run(BotSettings.discordToken), debug=BotSettings.bDebugEnabled)