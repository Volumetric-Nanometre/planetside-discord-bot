"""
AUTO COMMANDER
Classes related to the starting of an Operation Commander, whether via commands or automatically.
"""

# import discord
# import discord.ext
from discord import app_commands, Interaction, File
from discord.ext import tasks, commands

from os import listdir


from botUtils import UserHasCommandPerms, FilesAndFolders
from botUtils import BotPrinter as BUPrint

import botData.settings as BotSettings

from botData.dataObjects import OperationData

import opsManager

import OpCommander.commander
from apscheduler.schedulers.asyncio import AsyncIOScheduler

class AutoCommander(commands.Cog):
	"""
	# AUTO COMMANDER

	A cog that sets up and automatically creates commanders for Operation events, as well as handling commands for manually starting a commander.
	"""

	def __init__(self, p_bot) -> None:
		super().__init__()
		self.botRef = p_bot
		self.scheduler = AsyncIOScheduler()
		BUPrint.Info("COG: AutoCommander loaded!")
		self.scheduler.start()




class CommanderCommands(commands.Cog):
	def __init__(self, p_bot) -> None:
		super().__init__()
		self.botRef = p_bot
		BUPrint.Info("COG: CommanderCommnads loaded!")


	@app_commands.command(name="open-commander", description="Starts an Ops commander for the specified operation.")
	@app_commands.rename(p_opFile = "operation")
	async def manualcommander(self, p_interaction: Interaction, p_opFile: str):
		# HARDCODED ROLE USEAGE:
		if not await UserHasCommandPerms(p_interaction.user, (BotSettings.CommandRestrictionLevels.level2), p_interaction):
			return

		vOpData: OperationData
		
		opData: OperationData
		for opData in opsManager.OperationManager.vLiveOps:
			if opData.fileName == p_opFile:
				vOpData = opData
				break

		BUPrint.Info(f"Starting commander for {vOpData.name}!")
		await p_interaction.response.send_message(f"Starting commander for {vOpData.name}!", ephemeral=True)
		await OpCommander.commander.StartCommander(vOpData)


	@manualcommander.autocomplete("p_opFile")
	async def autocompleteOpFile(self, p_interaction: Interaction, p_typedStr: str):
		choices: list = []
		availableOps:list = opsManager.OperationManager.vLiveOps

		option: OperationData
		for option in availableOps:
			if (p_typedStr.lower() in option.fileName.lower()):
				choices.append(app_commands.Choice(name=option.fileName.replace(".bin", ""), value=option.fileName))
		return choices


	@app_commands.command(name="get_feedback", description="Get the event feedback text file for the specified event.")
	@app_commands.rename(p_typedStr="file")
	async def GetFeedback(self, p_interaction:Interaction, p_typedStr:str):
		"""
		# Sends a message containing the feedback of an event.
		"""
		# HARDCODED ROLE USEAGE:
		if not await UserHasCommandPerms(p_interaction.user, (BotSettings.CommandRestrictionLevels.level2), p_interaction):
			return

		vFile = File( f"{BotSettings.Directories.tempDir}{p_typedStr}" )

		if vFile == None:
			await p_interaction.response.send_message("Invalid file choice.", ephemeral=True)
		else:
			await p_interaction.response.send_message("Feedback File:", file=vFile, ephemeral=True)


	@GetFeedback.autocomplete("p_typedStr")
	async def AutoCompleteGetFeedback(self, p_interaction: Interaction, p_typedStr:str):
		vFileList =  []
		returnChoices = []

		file:str
		for file in FilesAndFolders.GetFiles(f"{BotSettings.Directories.tempDir}", ".txt"):
			if file.__contains__(BotSettings.Directories.feedbackPrefix):
				vFileList.append(file)

		for file in vFileList:
			if file.lower() == p_typedStr.lower():
				returnChoices.append(file)

		return returnChoices