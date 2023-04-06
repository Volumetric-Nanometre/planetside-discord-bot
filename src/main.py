"""
@author Michael O'Donnell & Lee Connor Williams

https://github.com/Volumetric-Nanometre/planetside-discord-bot
https://github.com/LCWilliams/planetside-discord-bot
"""

from planetsidebot import Bot
import asyncio
import asyncio_atexit

from time import sleep

from signal import SIGTERM, signal

from botUtils import FilesAndFolders
from botUtils import BotPrinter as BUPrint
from botData.settings import BotSettings

FilesAndFolders.SetupFolders()

ps2Bot = Bot()
mainLoop = asyncio.new_event_loop()


def HandleTerminateSignal(p_signal: signal, p_frame):
	"""# Handle Terminate Signal
	Mini function for the signal, as it requires a specific signature.

	frame is a stack frame object.
	"""
	BUPrint.Info("Terminate Signal detected!  Raising KeyboardInterrupt to cleanly terminate.")
	raise(KeyboardInterrupt)

# Set up signal for SIGTERM, so the bot may be shutdown cleanly if ran via service, or for other termination calls.
signal(SIGTERM, HandleTerminateSignal)


asyncio.set_event_loop(mainLoop)
asyncio_atexit.register(callback=ps2Bot.ExitCalled, loop=mainLoop)


try:
	mainLoop.create_task(ps2Bot.start(BotSettings.discordToken))

	sleep(0.5) # Ensures the bot finishes initialising, otherwise the setup function may not find the cog.
	mainLoop.create_task(ps2Bot.setupContTracker())
	mainLoop.run_forever()

except KeyboardInterrupt:
	BUPrint.Info("Keyboard interrupt detected.")
	pass

finally:
	mainLoop.close()
	BUPrint.Info("Bot shutdown complete.\n\nThe below error (task was destroyed but is pending) is a known, and unfixed discordpy issue.\nIt does not prevent the bot from shutting down cleanly and is safe to ignore.\n\n")




# asyncio.run( ps2Bot.run(BotSettings.discordToken), debug=BotSettings.bDebugEnabled)