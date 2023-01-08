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
from userManager import UserLibraryCog, UserLibraryAdminCog, UserLibrary, UserLib_RecruitValidationRequest
from chatUtility import ChatUtilityCog
from botAdmin import BotAdminCog

from botData.sanityChecker import SanityCheck


class Bot(commands.Bot):

    def __init__(self):
        discord.utils.setup_logging()
        super().__init__(command_prefix=['!'], intents=discord.Intents.all())
        
        if settings.BotSettings.bShowSettingsOnStartup:
            BUPrint.Info(f"Starting bot with settings:\n{botUtils.PrintSettings(True)}\n")

        self.vGuildObj: discord.Guild
        self.vOpsManager = opsManager.OperationManager()

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
        await self.add_cog(ChatUtilityCog(self))
        await self.add_cog(BotAdminCog(self))

        self.tree.copy_global_to(guild=self.vGuildObj)
        await self.tree.sync(guild=self.vGuildObj)


    async def on_ready(self):
        if settings.BotSettings.bCheckValues:
            await SanityCheck.CheckAll(p_botRef=self)
 		
		# Objects with BOT refs
        opsManager.OperationManager.SetBotRef(self)
        Commander.vBotRef = self
        UserLibrary.botRef = self
        UserLib_RecruitValidationRequest.botRef = self


        self.vGuildObj = await botUtils.GetGuild(self)
        await botUtils.ChannelPermOverwrites.Setup(self)
        await self.vOpsManager.RefreshOps()
 

        # Setup existing Ops auto-starts:
        if settings.Commander.bAutoAlertsEnabled:
            self.vOpsManager.RefreshAutostarts()
        
        BUPrint.Info(f'\n\nBOT READY	|	{self.user.name} ({self.user.id}) on: {self.vGuildObj.name}\n')



    async def ExitCalled(self):
        """
		# EXIT CALLED
		Called when an exit signal is sent.
		"""
        BUPrint.Info("Bot shutting down. Performing cleanup...")
        botUtils.FilesAndFolders.CleanupTemp()
        for liveOp in self.vOpsManager.vLiveCommanders:
            await liveOp.EndOperation()
