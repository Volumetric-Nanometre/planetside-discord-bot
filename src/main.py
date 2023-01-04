"""
@author Michael O'Donnell & Lee Connor Williams

https://github.com/Volumetric-Nanometre/planetside-discord-bot
https://github.com/LCWilliams/planetside-discord-bot
"""

from planetsidebot import Bot
import asyncio
import atexit

from botUtils import FilesAndFolders
from botData.settings import BotSettings

FilesAndFolders.SetupFolders()

ps2Bot = Bot()
atexit.register(ps2Bot.ExitCalled)

asyncio.run( ps2Bot.run(BotSettings.discordToken), debug=BotSettings.bDebugEnabled)