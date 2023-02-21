"""
@author Michael O'Donnell
"""

import discord
from discord.ext import commands

import botUtils
from botUtils import BotPrinter as BUPrint
from botData import settings

import roleManager

import opstart
import opsignup
import chatlinker

from botData.sanityChecker import SanityCheck


class Bot(commands.Bot):

    def __init__(self):
        discord.utils.setup_logging(root=False)
        super().__init__(command_prefix=['!'], intents=discord.Intents.all())
        
        if settings.BotSettings.bShowSettingsOnStartup:
            BUPrint.Info(f"Starting bot with settings:\n")
            botUtils.PrintSettings()

        self.vGuildObj: discord.Guild

    async def setup_hook(self):
        BUPrint.Info("Setting up hooks...")
        # Needed for later functions, which want a discord object instead of a plain string.
        self.vGuildObj = await botUtils.GetGuild(self)
# COGS	
        if settings.BotSettings.botFeatures.UserRoles:
            await self.add_cog(roleManager.UserRoles(self))
        await self.add_cog(opstart.opschannels(self))
        await self.add_cog(opsignup.OpSignUp(self))
        await self.add_cog(chatlinker.ChatLinker(self))

        self.tree.copy_global_to(guild=self.vGuildObj)
        await self.tree.sync(guild=self.vGuildObj)


    async def on_ready(self):
        if settings.BotSettings.bCheckValues:
            await SanityCheck.CheckAll(p_botRef=self)
        
        BUPrint.Info(f'\n\nBOT READY	|	{self.user.name} ({self.user.id}) on: {self.vGuildObj.name}\n')

        if settings.BotSettings.bShowSettingsOnStartup_discord:
            vAdminChannel = self.get_channel(settings.Channels.botAdminID)
            if vAdminChannel != None and settings.BotSettings.bShowSettingsOnStartup_discord:
                vSettingStr = botUtils.PrintSettings(True)
                splitString = [(vSettingStr[index:index+1990]) for index in range(0, len(vSettingStr), 1990)]
                for segment in splitString:
                    segment = f"```{segment}```"
                    await vAdminChannel.send( f"{segment}\n" )



    async def ExitCalled(self):
        """
		# EXIT CALLED
		Called when an exit signal is sent.
		"""
        if self._closed:
            return
        vAdminChan = self.get_channel(settings.Channels.botAdminID)
        if vAdminChan != None:
            await vAdminChan.send("**Bot shutting down.**")

        BUPrint.Info("Bot shutting down. Performing cleanup...")
        botUtils.FilesAndFolders.CleanupTemp()

        BUPrint.Info("Closing bot connections")
        await self.close()
