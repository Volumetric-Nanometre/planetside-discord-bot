"""
@author Michael O'Donnell
"""
import asyncio
import atexit

import discord
from discord.ext import commands

import botUtils
from botUtils import BotPrinter as BUPrint
import newUser
from botData import settings
import roleManager
import opsManager
from OpCommander.autoCommander import AutoCommander
from OpCommander.autoCommander import CommanderCommands
from OpCommander.commander import Commander


# import chatlinker

BUPrint.Info(f"Starting bot with settings:\n{settings.BotSettings()}\n{settings.Directories()}\n{settings.SignUps()}\n{settings.NewUsers()}\n{settings.Commander()}")

botUtils.FilesAndFolders.SetupFolders()

class Bot(commands.Bot):

    def __init__(self):
        super(Bot, self).__init__(command_prefix=['!'], intents=discord.Intents.all())
        self.vGuildObj: discord.Guild

		# Objects with BOT refs
        self.vOpsManager = opsManager.OperationManager()
        opsManager.OperationManager.SetBotRef(self)
        Commander.vBotRef = self


    async def setup_hook(self):
        BUPrint.Info("Setting up hooks...")
        # Needed for later functions, which want a discord object instead of a plain string.
        self.vGuildObj = await botUtils.GetGuild(p_BotRef=self)
# COGS
        await self.add_cog(newUser.NewUser(pBot=self))
        await self.add_cog(roleManager.UserRoles(p_bot=self))
        await self.add_cog(opsManager.Operations(p_bot=self))
        await self.add_cog(AutoCommander(p_bot=self))
        await self.add_cog(CommanderCommands(p_bot=self))
        # await self.add_cog(chatlinker.ChatLinker(self))

        self.tree.copy_global_to(guild=self.vGuildObj)
        await self.tree.sync(guild=self.vGuildObj)


    async def on_ready(self):
        BUPrint.Info(f'Logged in as {self.user.name} ({self.user.id}) on Guild {self.vGuildObj.name}\n')
        await self.vOpsManager.RefreshOps()
        await botUtils.ChannelPermOverwrites.Setup(p_botRef=self)
        await botUtils.RoleDebug(self.vGuildObj)

        # Setup existing Ops auto-starts:
        if settings.Commander.bAutoAlertsEnabled:
            self.vOpsManager.RefreshAutostarts()

bot = Bot()

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.errors.CheckFailure):
        await ctx.send('You do not have the correct role for this command.', ephemeral=True)


def exit_handler():
	BUPrint.Info("Bot shutting down.")

atexit.register(exit_handler)

# START
BUPrint.Debug("Bot running...")
asyncio.run(bot.run(settings.BotSettings.discordToken), debug=settings.BotSettings.bDebugEnabled)