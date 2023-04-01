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
	mainLoop.create_task(ps2Bot.start(BotSettings.discordToken))
	mainLoop.create_task(ps2Bot.setupContTracker())
	mainLoop.run_forever()

except KeyboardInterrupt:
	BUPrint.Info("Keyboard interrupt detected.")
	pass

finally:
	mainLoop.close()
	BUPrint.Info("Bot shutdown complete.\n\nThe below error is a known, and unfixed discordpy issue.\nIt does not prevent the bot from shutting down cleanly and is safe to ignore.\n\n")


# asyncio.run( ps2Bot.run(BotSettings.discordToken), debug=BotSettings.bDebugEnabled)