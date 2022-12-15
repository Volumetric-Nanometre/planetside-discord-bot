"""
AUTO COMMANDER COG
Cog that deals with 
"""

import discord
import discord.ext
from discord.ext import tasks, commands
import enum
import sched

import botUtils
from botUtils import BotPrinter as BUPrint
import botData.settings as BotSettings
import botData.operations
from botData.operations import OperationData as OpsData
from opsManager import OperationManager as OpsMan
import OpCommander.status
from OpCommander.commander import Commander as OperationCommander


import time

class AutoCommander(commands.Cog):
	"""
	# AUTO COMMANDER

	A cog that sets up and automatically creates commanders for Operation events, as well as handling commands for manually starting a commander.
	"""
	vOpsScheduler = sched.scheduler()
	def __init__(self, p_bot) -> None:
		super().__init__()
		self.botRef = p_bot
		BUPrint.Info("COG: AutoCommander loaded!")

	async def StartAutoCommander(self, p_opData: botData.operations.OperationData):
		# Use OpsManager to start an ops.
		# Create a Commander.
		# Lookit Sched
		pass

		#datetime - timedelta(minutes=0)
class AutoCommanderInstance():
	def __init__(self) -> None:
		pass

class CommanderCommands(commands.Cog):
	def __init__(self, p_bot) -> None:
		super().__init__()
		self.botRef = p_bot
		BUPrint.Info("COG: CommanderCommnads loaded!")

	@discord.app_commands.command(name="open-commander", description="Starts an Ops commander for the specified operation.")
	@discord.app_commands.rename(p_opFile = "operation")
	async def manualcommander(self, p_interaction: discord.Interaction, p_opFile: str):
		# HARDCODED ROLE USEAGE:
		if not await botUtils.UserHasCommandPerms(p_interaction.user, (BotSettings.CommandRestrictionLevels.level2), p_interaction):
			return

		vOpData: botData.operations.OperationData
		
		opData: botData.operations.OperationData
		for opData in OpsMan.vLiveOps:
			if opData.fileName == p_opFile:
				vOpData = opData

		BUPrint.Debug(f"Start commander for {vOpData}!")
		await p_interaction.response.send_message(f"Starting commander for {vOpData.name}!", ephemeral=True)
		await self.StartCommander(vOpData)

	@manualcommander.autocomplete("p_opFile")
	async def autocompleteOpFile(self, p_interaction: discord.Interaction, p_typedStr: str):
		choices: list = []
		availableOps:list = OpsMan.vLiveOps

		option: botData.operations.OperationData
		for option in availableOps:
			if (p_typedStr.lower() in option.fileName.lower()):
				choices.append(discord.app_commands.Choice(name=option.fileName.replace(".bin", ""), value=option.fileName))
		return choices


	async def StartCommander(self, p_opData: botData.operations.OperationData):
		"""
		# START COMMANDER
		Self explanitory, calling this will start the commander for the given ops file.
		
		Starting a commander does NOT start an Ops.  That is a different event, handled by the commander itself (if bAutoStart is enabled in both op settings and botsettings).
		"""
		BUPrint.Debug(f"Start commander for {p_opData.fileName}!")

		vNewCommander = OperationCommander(p_opData)
		await vNewCommander.CommanderSetup()
		await vNewCommander.GenerateCommander()
