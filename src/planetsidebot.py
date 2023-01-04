"""
@author Michael O'Donnell
"""

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
from userManager import UserLibraryCog, UserLibraryAdminCog
from chatMonitor import ChatMonitorCog



botUtils.FilesAndFolders.SetupFolders()

class Bot(commands.Bot):

    def __init__(self):
        super().__init__(command_prefix=['!'], intents=discord.Intents.all())
        BUPrint.Info(f"Starting bot with settings:\n{settings.BotSettings()}\n{settings.Directories()}\n{settings.SignUps()}\n{settings.NewUsers()}\n{settings.Commander()}\n{settings.UserLib()}\n")

        self.vGuildObj: discord.Guild

		# Objects with BOT refs
        self.vOpsManager = opsManager.OperationManager()
        opsManager.OperationManager.SetBotRef(self)
        Commander.vBotRef = self


    async def setup_hook(self):
        BUPrint.Info("Setting up hooks...")
        # Needed for later functions, which want a discord object instead of a plain string.
        self.vGuildObj = await botUtils.GetGuild(self)
# COGS
        await self.add_cog(newUser.NewUser(self))
        await self.add_cog(roleManager.UserRoles(self))
        await self.add_cog(opsManager.Operations(self))
        await self.add_cog(AutoCommander(self))
        await self.add_cog(CommanderCommands(self))
        await self.add_cog(UserLibraryCog(self))
        await self.add_cog(UserLibraryAdminCog(self))
        await self.add_cog(ChatMonitorCog(self))

        self.tree.copy_global_to(guild=self.vGuildObj)
        await self.tree.sync(guild=self.vGuildObj)


    async def on_ready(self):
        self.vGuildObj = await botUtils.GetGuild(self)
        await botUtils.ChannelPermOverwrites.Setup(self)
        await botUtils.RoleDebug(self.vGuildObj, p_showOnLive=False)
        await self.vOpsManager.RefreshOps()

        # Setup existing Ops auto-starts:
        if settings.Commander.bAutoAlertsEnabled:
            self.vOpsManager.RefreshAutostarts()
        BUPrint.Info(f'Logged in as {self.user.name} ({self.user.id}) on Guild {self.vGuildObj.name}\n')



    def ExitCalled(self):
        BUPrint.Info("Bot shutting down.")
		

