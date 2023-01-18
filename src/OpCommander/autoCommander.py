"""
AUTO COMMANDER
Classes related to the starting of an Operation Commander, whether via commands or automatically.
"""

# import discord
# import discord.ext
from discord import app_commands, Interaction, File, Member, VoiceState
from discord.ext import tasks, commands

from botUtils import UserHasCommandPerms, FilesAndFolders
from botUtils import BotPrinter as BUPrint

import botData.settings as BotSettings
from botData.settings import CommandLimit
from botData.dataObjects import OperationData

import opsManager

import OpCommander.commander
from apscheduler.schedulers.asyncio import AsyncIOScheduler

class AutoCommander(commands.Cog):
	"""
	# AUTO COMMANDER

	A cog for holding the Auto Commander scheduler and linking voice chat state changes to refreshing commanders.
	"""

	def __init__(self, p_bot) -> None:
		super().__init__()
		self.botRef = p_bot
		self.scheduler = AsyncIOScheduler()
		self.scheduler.start()
		BUPrint.Info("COG: AutoCommander loaded!")


	@commands.Cog.listener("on_voice_state_update")
	async def VoiceStateChanged(self, p_member:Member, p_before:VoiceState, p_after:VoiceState):
		"""
		# VOICE STATE CHANGED: Listener
		Checks if user is in any live ops, and updates their commander if present.
		"""

		if opsManager.OperationManager.vLiveCommanders.__len__() != 0:
			for commander in opsManager.OperationManager.vLiveCommanders:
				if not commander.bIgnoreStateChange and p_member.id in commander.vOpData.GetParticipantIDs():
					for participant in commander.participants:
						if participant.discordID == p_member.id:
							participant.bInEventChannel = bool(p_member.voice != None and p_member.voice.channel in commander.vCategory.voice_channels)
							break
					
					await commander.UpdateCommanderLive()





class CommanderCommands(commands.Cog, name="commander", description=""):
	def __init__(self, p_bot) -> None:
		super().__init__()
		self.botRef = p_bot
		BUPrint.Info("COG: CommanderCommnads loaded!")


	@app_commands.command(name="open-commander", description="Starts an Ops commander for the specified operation.")
	@app_commands.rename(p_opFile = "operation")
	async def manualcommander(self, p_interaction: Interaction, p_opFile: str):
		# HARDCODED ROLE USEAGE:
		if not await UserHasCommandPerms(p_interaction.user, (BotSettings.CommandLimit.opCommander), p_interaction):
			return
		await p_interaction.response.defer(thinking=True, ephemeral=True)

		vOpData: OperationData
		
		opData: OperationData
		for opData in opsManager.OperationManager.vLiveOps:
			if opData.fileName == p_opFile:
				vOpData = opData
				break

		startResponse = await OpCommander.commander.StartCommander(vOpData)
		if startResponse == 0:
			await p_interaction.edit_original_response(content=f"Starting commander for {vOpData.name}!")
		elif startResponse == 1:
			await p_interaction.edit_original_response(content=f"{vOpData.name} has been started already!")
		elif startResponse == 2:
			await p_interaction.edit_original_response(content=f"Invalid operation data given!")
			


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
		if not await UserHasCommandPerms(p_interaction.user, (BotSettings.CommandLimit.opCommander), p_interaction):
			return

		try:
			vFile = File( f"{BotSettings.Directories.tempDir}{p_typedStr}" )
		except FileNotFoundError:
			await p_interaction.response.send_message("Invalid file choice.", ephemeral=True)
			return

		await p_interaction.response.send_message("Feedback File:", file=vFile, ephemeral=True)



	@GetFeedback.autocomplete("p_typedStr")
	async def AutoCompleteGetFeedback(self, p_interaction: Interaction, p_typedStr:str):
		vFileList =  []
		returnChoices = []

		file:str
		for file in FilesAndFolders.GetFiles(f"{BotSettings.Directories.tempDir}", ".txt"):
			if file.startswith(BotSettings.Directories.feedbackPrefix):
				vFileList.append(file)

		for file in vFileList:
			if file.lower().__contains__(p_typedStr.lower()):
				returnChoices.append( app_commands.Choice(name=file.replace(".txt", "").replace(BotSettings.Directories.feedbackPrefix, ""), value=file) )

		return returnChoices