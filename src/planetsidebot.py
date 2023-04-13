"""
@author Michael O'Donnell
"""

import discord
from discord.ext import commands
import asyncio

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
from ps2ContinentTracker import ContinentTrackerCog
from forFun import ForFunCog

from botData.sanityChecker import SanityCheck


class Bot(commands.Bot):

    def __init__(self):
        discord.utils.setup_logging(root=False)
        super().__init__(command_prefix=['!'], intents=discord.Intents.all())
        
        if settings.BotSettings.bShowSettingsOnStartup:
            BUPrint.Info(f"Starting bot with settings:\n")
            botUtils.PrintSettings()

        self.vGuildObj: discord.Guild
        self.vOpsManager = opsManager.OperationManager()
        self.vcontTrackerClient = None
        self.contTrackerCog: ContinentTrackerCog = None

    async def setup_hook(self):

        BUPrint.Info("Setting up hooks...")
        # Needed for later functions, which want a discord object instead of a plain string.
        self.vGuildObj = await botUtils.GetGuild(self)

# COGS	
        if settings.BotSettings.botFeatures.NewUser:
            await self.add_cog(newUser.NewUser(self))

        if settings.BotSettings.botFeatures.UserRoles:
            await self.add_cog(roleManager.UserRoles(self))

        if settings.BotSettings.botFeatures.Operations:
            await self.add_cog(opsManager.Operations(self))
            await self.add_cog(AutoCommander(self))
            await self.add_cog(CommanderCommands(self))

        if settings.BotSettings.botFeatures.UserLibrary:
            await self.add_cog(UserLibraryCog(self))
            await self.add_cog(UserLibraryAdminCog(self))

        if settings.BotSettings.botFeatures.chatUtility:
            await self.add_cog(ChatUtilityCog(self))

        if settings.BotSettings.botFeatures.ForFunCog:
            await self.add_cog(ForFunCog(self))

        if settings.BotSettings.botFeatures.BotAdmin:
            adminCog = BotAdminCog(self)
            await self.add_cog(adminCog)
            adminCog.shutdownFunction = self.ExitCalled


        self.tree.copy_global_to(guild=self.vGuildObj)
        await self.tree.sync(guild=self.vGuildObj)



    async def setupContTracker(self):
        """# Setup ContTracker
        To be called from main as a task.
        Function checks if continent Tracker is enabled.
        """
        if settings.BotSettings.botFeatures.continentTracker:
            self.contTrackerCog = ContinentTrackerCog(self)
            self.vcontTrackerClient = self.contTrackerCog.auraxClient
            await self.contTrackerCog.CreateTriggers()
            await self.add_cog(self.contTrackerCog)

            BUPrint.Info("	> Connecting continent tracker client.")
            await self.contTrackerCog.auraxClient.connect()            



    async def on_ready(self):
        if settings.BotSettings.bCheckValues:
            await SanityCheck.CheckAll(p_botRef=self)

		# Objects with BOT refs
        opsManager.OperationManager.vBotRef = self
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

        BUPrint.Info(f"	> Ending {self.vOpsManager.vLiveCommanders.__len__()} running events...")
        for liveOp in self.vOpsManager.vLiveCommanders:
            try:
                await liveOp.EndEvent()
            except:
                BUPrint.LogError(f"A problem occured while ending {liveOp.vOpData.name}.  Event may need to be removed manually.", "ERROR ENDING EVENT | ")
                continue


        BUPrint.Info("	> Ending task loops")
        if settings.BotSettings.botFeatures.UserLibrary:
            userLibAdmin:UserLibraryAdminCog = self.get_cog("userlib_admin")
            if userLibAdmin.userLibRetentionTask != None:
                userLibAdmin.userLibRetentionTask.stop()

            if userLibAdmin != None:
                userLibAdmin.querySleeperTask.stop()
            

        if settings.BotSettings.botFeatures.continentTracker:
            BUPrint.Info("	> Closing continent tracker client")
            await self.vcontTrackerClient.close()


        BUPrint.Info("	> Closing bot connections")
        await self.close()

        BUPrint.Info("	> Stopping event loop")
        mainLoop = asyncio.get_event_loop()
        
        mainLoop.stop()