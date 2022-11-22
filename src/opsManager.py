# Ops Manager: Manages creating, editing and removing of Ops.

import os
import datetime
import pickle

import discord
from discord.ext import commands
import enum

import OpSignup
import opsCommander

import settings
import botUtils
import botData

class OpsManager():
	def init(self):
		# List of ops (file names)
		self.vOpsList: list = self.GetOps()

	# Returns a list of full pathed strings for each 
	async def GetOps():
		botUtils.BotPrinter.Debug("Getting Ops list...")
		vOpsDir = f"{settings.botDir}/{settings.opsFolderName}/"
		return botUtils.FilesAndFolders.GetFiles(vOpsDir, ".bin")

	async def GetDefaults():
		botUtils.BotPrinter.Debug("Getting default Ops...")
		vDir = f"{settings.botDir}/{settings.defaultOpsDir}"
		return botUtils.FilesAndFolders.GetFiles(vDir, ".bin")
		


	# Returns an ENUM containing the names of saved default Operations.
	# Does not use SELF to make it callable without constructing an instance.
	# Does not use Async to allow it to be called in function parameters.
	# Mainly used to provide dynamic 
	def GetDefaultOpsAsEnum():
		botUtils.BotPrinter.Debug("Getting Ops list...")
		vOpsDir = f"{settings.botDir}/{settings.defaultOpsDir}/"
		OpsManager.createDefaultsFolder()

		vDataFiles: list = ["Custom"]
		
		for file in os.listdir(vOpsDir):
			if file.endswith(".bin"):
				vDataFiles.append(file)

		if len(vDataFiles) > 1:
			botUtils.BotPrinter.Debug(f"Ops files found: {vDataFiles}")
			return enum.Enum("OpsType", vDataFiles)
		else:
			botUtils.BotPrinter.Debug("No ops files!")
			return enum.Enum("OpsType", ["Custom", "(noSavedDefaults)"])



	async def createOpsFolder():
		if (not os.path.exists(f"{settings.botDir}/{settings.opsFolderName}") ):
			try:
				os.makedirs(f"{settings.botDir}/{settings.opsFolderName}")
			except:
				botUtils.BotPrinter.LogError("Failed to create folder for Ops data!")


class OpsMessage(discord.ui.View):
	def __init__(self, pOpsDataFile: str):
		self.opsDataFile = pOpsDataFile
		self.opsData: botData.OperationData
		botUtils.BotPrinter.Debug("OpsMessage created.  Don't forget to save or load data!")
		# super().__init__(timeout=None)

	async def saveToFile(self):
		botUtils.BotPrinter.Debug(f"Attempting to save {self.opsData.name} to file: {self.opsDataFile}")
		try:
			with open(self.opsDataFile, 'wb') as vFile:
				pickle.dump(self.opsData, vFile)
				botUtils.BotPrinter.Debug("Saved data succesfully!")
		except:
			botUtils.BotPrinter.LogError(f"Failed to save {self.opsData.name} to file {self.opsDataFile}!")
		
	async def getDataFromFile(self):
		botUtils.BotPrinter.Debug(f"Attempting to load data from file: {self.opsDataFile}")
		try:
			with open(self.opsDataFile, 'rb') as vFile:
				self.opsData = pickle.load(vFile)
				botUtils.BotPrinter.Debug("Loaded data succesfully!")
		except:
			botUtils.BotPrinter.LogError(f"Failed to load Ops data from file: {self.opsDataFile}")

	# Returns a view using the data 
	async def GenerateEmbed(self):
		vEmbed = discord.Embed(colour=botUtils.Colours.editing, title=self.opsData.name, description=self.opsData.description, timestamp=self.opsData.date)

		# Generate lists for roles:
		role: botData.OpRoleData
		for role in self.opsData.roles:
			vSignedUpUsers: str
			for user in role.players:
				vSignedUpUsers += f"{user}\n"
			vEmbed.add_field(inline=True, 
			name=f"{role.roleName}({len(role.players)}/{role.maxPositions})",
			value=vSignedUpUsers)
	
	# async def UpdateView():
	# 	print("Teehee")

# Class responsible for displaying options, editing and checking.
# pBot: A reference to the bot.
# pOpsData: The operation data to be used.
class OpsEditor(discord.ui.View):
	def __init__(self, pBot: commands.Bot, pOpsData: botData.OperationData):
		self.vBot = pBot
		self.vOpsData = pOpsData # Original data, not edited.
		# self.EditedData = pOpsData # Edited data, applied and saved.
		botUtils.BotPrinter.Debug("Created Blank Editor")
		super().__init__(timeout=None)
		

# # # # # # Edit Buttons
	# Edit Date:
	editButtonStyle = discord.ButtonStyle.grey
	@discord.ui.button( label="Edit Date",
						style=editButtonStyle, 
						custom_id="EditDate",
						row=0)
	async def btnEditDate(self, pInteraction: discord.Interaction, pButton: discord.ui.button):
		vEditModal = EditDates(title="Edit Date/Time", pOpData=self.vOpsData)
		vEditModal.custom_id="EditDateModal"
		await pInteraction.response.send_modal( vEditModal )
	
	# Edit Info
	@discord.ui.button(
						style=editButtonStyle, 
						label="Edit Info",
						custom_id="EditInfo",
						row=1)
	async def btnEditInfo(self, pInteraction: discord.Interaction, pButton: discord.ui.button):
		vEditModal = EditInfo(title="Edit Info", pOpData=self.vOpsData)
		vEditModal.custom_id="EditInfoModal"
		await pInteraction.response.send_modal( vEditModal )

	# Edit Roles
	@discord.ui.button(
						style=editButtonStyle, 
						label="Edit Roles",
						custom_id="EditRoles",
						row=2)
	async def btnEditRoles(self, pInteraction: discord.Interaction, pButton: discord.ui.button):
		vEditModal = EditRoles(title="Edit Roles", pOpData=self.vOpsData)
		# vEditModal.vData = self.vOpsData
		vEditModal.custom_id="EditRolesModal"
		await pInteraction.response.send_modal( vEditModal )
	
# # # # # # # Confirm/Save buttons:
	@discord.ui.button(
						style=discord.ButtonStyle.danger, 
						label="Apply Changes",
						custom_id="EditRolesApply",
						row=4)
	async def btnApplyChanges(self, pInteraction: discord.Interaction, pButton: discord.ui.button):
		self.vOpsData.status = botData.OpsStatus.open
		await pInteraction.response.send_message("Ops data updated!", ephemeral=True)

	@discord.ui.button( 
						style=discord.ButtonStyle.primary, 
						label="New Default",
						custom_id="EditRolesNewDefault",
						row=4)
	async def btnNewDefault(self, pInteraction: discord.Interaction, pButton: discord.ui.button):
		# Set status of Ops back to OPEN.
		self.vOpsData.status = botData.OpsStatus.open
		# Pickle dis shit!
		vNewOpsFilepath = f"{settings.botDir}/{settings.defaultOpsDir}/{self.vOpsData.name}.bin"
		botUtils.BotPrinter.Debug(f"Saving new default: {vNewOpsFilepath}...")
		# Apply opsData object to opsMessage, then save.
		vOpsMessage = OpsMessage(vNewOpsFilepath)
		vOpsMessage.opsData = self.vOpsData
		await vOpsMessage.saveToFile()
		botUtils.BotPrinter.Debug("Saved!")

		# Sync command to update list.
		vGuildObj = await self.vBot.fetch_guild(settings.DISCORD_GUILD)
		botData.AddOpsEnum.GenerateEnum()
		await self.vBot.tree.sync(guild=vGuildObj)
		botUtils.BotPrinter.Debug(f"Guild Tree Synced!")
		await pInteraction.response.send_message(f"Added new default!", ephemeral=True)



###############################
# EDIT DATES

class EditDates(discord.ui.Modal):
	txtYear = discord.ui.TextInput(
		label="Year",
		placeholder="Full year",
		min_length=4, max_length=4,
		required=False
	)
	txtDay = discord.ui.TextInput(
		label="Day",
		placeholder="Day of month",
		min_length=1, max_length=2,
		required=False
	)
	txtMonth = discord.ui.TextInput(
		label="Month",
		placeholder="What month?  Numerical value!",
		min_length=1, max_length=2,
		required=False
	)
	txtHour = discord.ui.TextInput(
		label="Hour",
		placeholder="Hour",
		min_length=1, max_length=2,
		required=False
	)
	txtMinute = discord.ui.TextInput(
		label="Minute",
		placeholder="Minute",
		min_length=1, max_length=2,
		required=False
	)
	def __init__(self, *, title: str = "Edit Date/Time", pOpData: botData.OperationData):
		self.title = title
		self.vData : botData.OperationData = pOpData
		self.PresetFields()
		super().__init__()

	async def on_eror(self, pInteraction: discord.Interaction, error: Exception):
		botUtils.BotPrinter.LogError("Error occured on Edit Date Modal.", p_exception=error)

	async def on_timeout(self):
		await self.stop()

	# Where the fun happens!
	async def on_submit(self, pInteraction: discord.Interaction):
		botUtils.BotPrinter.Debug("Edit Dates Modal submitted, creating new date...")

		newDateTime = datetime.datetime(
			year=int(self.txtYear.value),
			month=int(self.txtMonth.value),
			day=int(self.txtDay.value),
			hour=int(self.txtHour.value),
			minute=int(self.txtMinute.value),
			tzinfo=datetime.timezone.utc
		)

		self.vData.date = newDateTime

		await pInteraction.response.defer()

	def PresetFields(self):
		botUtils.BotPrinter.Debug(f"Attempting to preset data with: {self.vData.date}")
		self.txtYear.default = str(self.vData.date.year)
		self.txtDay.default = str(self.vData.date.day)
		self.txtMonth.default = str(self.vData.date.month)
		self.txtHour.default = str(self.vData.date.hour)
		self.txtMinute.default = str(self.vData.date.minute)



###############################
# EDIT INFO

class EditInfo(discord.ui.Modal):
	txtName = discord.ui.TextInput(
		label="Ops Name",
		placeholder="Name of the Ops (used as the defaults name)",
		min_length=3, max_length=50,
		required=True
	)
	txtDescription = discord.ui.TextInput(
		label="Description",
		placeholder="Brief explanation of this Ops",
		style=discord.TextStyle.paragraph,
		max_length=2000,
		required=False
	)
	txtMessage = discord.ui.TextInput(
		label="Details",
		placeholder="A more detailed message about this ops?  Defaults to blank.",
		style=discord.TextStyle.paragraph,
		required=False
	)

	txtVoiceChannels = discord.ui.TextInput(
		label="Voice Channels",
		placeholder="A list of voice channels to create for this Operation.",
		style=discord.TextStyle.paragraph,
		required=False
	)
	txtArguments = discord.ui.TextInput(
		label="Commands",
		placeholder="Optional commands to modify behaviour.",
		style=discord.TextStyle.paragraph,
		required=False
	)


	def __init__(self, *, title: str = "Edit Ops Name/Descriptions", pOpData: botData.OperationData):
		self.title = title
		self.vData : botData.OperationData = pOpData
		self.PresetFields()
		super().__init__()

	async def on_eror(self, pInteraction: discord.Interaction, error: Exception):
		botUtils.BotPrinter.LogError("Error occured on Edit Info Modal", p_exception=error)

	async def on_timeout(self):
		await self.stop()

	# Where the fun happens!
	async def on_submit(self, pInteraction: discord.Interaction):
		botUtils.BotPrinter.Debug("Edit Info Modal submitted...")

		self.vData.name = self.txtName.value
		self.vData.description = self.txtDescription.value
		self.vData.customMessage = self.txtMessage.value

		self.txtVoiceChannels.value.split("\n")
		self.vData.voiceChannels = self.txtVoiceChannels.value.split("\n")
		self.vData.arguments = self.txtArguments.value.split("\n")

		await pInteraction.response.defer()

	def PresetFields(self):
		botUtils.BotPrinter.Debug("Presetting INFO with existing data...")
		self.txtName.default = self.vData.name
		self.txtMessage.default = self.vData.customMessage
		self.txtDescription.default = self.vData.description
		self.txtVoiceChannels.default = self.vData.voiceChannels
		self.txtArguments.default = self.vData.arguments


###############################
# EDIT ROLES

class EditRoles(discord.ui.Modal):
	txtEmoji = discord.ui.TextInput(
		label="Emoji",
		placeholder="EmojiID String per line",
		style=discord.TextStyle.paragraph,
		required=True
	)
	txtRoleName = discord.ui.TextInput(
		label="Role Name",
		placeholder="Light Assault\nHeavy Assault\nEtc...",
		style=discord.TextStyle.paragraph,
		required=True
	)
	txtRoleMaxPos = discord.ui.TextInput(
		label="Max Positions",
		placeholder="Max positions.",
		style=discord.TextStyle.paragraph,
		required=True
	)
	txtRolePlayers = discord.ui.TextInput(
		label="Players",
		placeholder="Player IDs",
		style=discord.TextStyle.paragraph,
		required=False
	)
	def __init__(self, *, title: str = "Edit Roles", pOpData: botData.OperationData):
		self.title = title
		self.vData = pOpData
		self.PresetFields
		super().__init__()

	async def on_eror(self, pInteraction: discord.Interaction, error: Exception):
		botUtils.BotPrinter.LogError("Error occured on Edit Roles modal.", p_exception=error)

	async def on_timeout(self):
		await self.stop()

	# Where the fun happens!
	async def on_submit(self, pInteraction: discord.Interaction):
		botUtils.BotPrinter.Debug("Edit Roles Modal submitted...")
		vRoleNames = self.txtRoleName.value.splitlines()
		vRoleEmoji = self.txtEmoji.value.splitlines()
		vRoleMax = self.txtRoleMaxPos.value.splitlines()
		
		# If user made an error, don't proceed- inconstsent lengths!
		if len(vRoleNames) != len(vRoleEmoji) != len(vRoleMax):
			await pInteraction.response.send_message("Inconsistent array lengths in fields!  \nMake sure the number of lines matches in all three fields.")
			return

		vIndex = 0
		botUtils.BotPrinter.Debug(f"Size of array: {len(vRoleEmoji)}")
		while vIndex < len(vRoleEmoji):

			vCurrentRole = botData.OpRoleData(roleName=vRoleNames[vIndex], roleIcon=vRoleEmoji[vIndex], maxPositions=vRoleMax[vIndex])
			if vIndex < len(self.vData.roles) :
				# Index is on an existing role, adjust values to keep any signed up users.
				self.vData.roles[vIndex].roleName = vCurrentRole.roleName
				self.vData.roles[vIndex].roleIcon = vCurrentRole.roleIcon
				self.vData.roles[vIndex].maxPositions = vCurrentRole.maxPositions
			else:
				# Index is a new role, append!
				self.vData.roles.append(vCurrentRole)

			vIndex += 1
		# End of while loop.
		botUtils.BotPrinter.Debug("Roles updated!")
		await pInteraction.response.defer()


	# Prefill fields:
	def PresetFields(self):
		botUtils.BotPrinter.Debug("Prefilling options with existing values...")
		
		vRoleNames: str
		vRoleEmojis: str
		vRoleMembers: str
		vRoleMaxPos: str

		roleIndex: botData.OpRoleData
		for roleIndex in self.vData.roles:
			vRoleNames += roleIndex.roleName
			vRoleEmojis += roleIndex.roleIcon
			vRoleMembers += roleIndex.players
			vRoleMaxPos += roleIndex.maxPositions

	# Set the text inputs to existing values:
		self.txtRoleName.default = vRoleNames
		self.txtEmoji.default = vRoleEmojis
		self.txtRoleMaxPos.default = vRoleMaxPos
		self.txtRolePlayers.default = vRoleMembers