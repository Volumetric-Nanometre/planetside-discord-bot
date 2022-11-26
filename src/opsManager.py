# Ops Manager: Manages creating, editing and removing of Ops.

import os
import datetime
import pickle


import discord
from discord.ext import commands


import settings
import botUtils
import botData


class OperationManager():
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
		
	def DeleteOpsData(pOpDataName: str):
		OpFile: str
		for OpFile in OperationManager.GetOps():
			if OpFile.__contains__(pOpDataName):
				vFullPath = f"{settings.botDir}/{settings.opsFolderName}/{pOpDataName}.bin"
				try:
					os.remove(vFullPath)
				except:
					botUtils.BotPrinter.LogError(f"Unable to delete file {vFullPath}")

	# Returns a LIST containing the names of saved default Operations.
	# Does not use SELF to make it callable without constructing an instance.
	# Does not use Async to allow it to be called in function parameters.
	# Does not strip file extension!
	def GetDefaultOpsAsList():
		botUtils.BotPrinter.Debug("Getting Ops list...")
		vOpsDir = f"{settings.botDir}/{settings.defaultOpsDir}/"
		vDataFiles: list = ["Custom"]
		
		for file in os.listdir(vOpsDir):
			if file.endswith(".bin"):
				vDataFiles.append(file)

		if len(vDataFiles) > 1:
			botUtils.BotPrinter.Debug(f"Ops files found: {vDataFiles}")
			return vDataFiles
		else:
			botUtils.BotPrinter.Debug("No ops files!")
			return vDataFiles



	async def createOpsFolder():
		if (not os.path.exists(f"{settings.botDir}/{settings.opsFolderName}") ):
			try:
				os.makedirs(f"{settings.botDir}/{settings.opsFolderName}")
			except:
				botUtils.BotPrinter.LogError("Failed to create folder for Ops data!")



##################################################################
# MESSAGES

class OpsMessage():
	def __init__(self, pOpsData: botData.OperationData, pBot: commands.Bot, pOpsDataFile: str = ""):
		self.opsDataFile = pOpsDataFile
		self.opsData: botData.OperationData = pOpsData
		self.botRef: commands.Bot = pBot
		# botUtils.BotPrinter.Debug("OpsMessage created.  Don't forget to save or load data!")
		# super().__init__(timeout=None)

	def saveToFile(self):
		botUtils.BotPrinter.Debug(f"Attempting to save {self.opsData.name} to file: {self.opsDataFile}")
		try:
			with open(self.opsDataFile, 'wb') as vFile:
				pickle.dump(self.opsData, vFile)
				botUtils.BotPrinter.Debug("Saved data succesfully!")
		except:
			botUtils.BotPrinter.LogError(f"Failed to save {self.opsData.name} to file {self.opsDataFile}!")
		
	def getDataFromFile(self):
		botUtils.BotPrinter.Debug(f"Attempting to load data from file: {self.opsDataFile}")
		try:
			with open(self.opsDataFile, 'rb') as vFile:
				self.opsData = pickle.load(vFile)
				botUtils.BotPrinter.Debug("Loaded data succesfully!")
		except:
			botUtils.BotPrinter.LogError(f"Failed to load Ops data from file: {self.opsDataFile}")


	# Sets this objects embed information from data.
	# Should be called prior to posting or updating the view this object is called from.
	# Returns an embed containing the Ops info.
	async def GenerateEmbed(self):
		vTitleStr = f"{self.opsData.name} {botUtils.DateFormatter.GetDiscordTime(self.opsData.date, botUtils.DateFormat.DateTimeLong)}"
		vEmbed = discord.Embed(colour=botUtils.Colours.editing.value, title=vTitleStr, description=self.opsData.description)

		

		if(self.opsData.customMessage != ""):
			vEmbed.add_field(inline=False, name="Additional Info:", value=self.opsData.customMessage)

		# Generate lists for roles:
		role: botData.OpRoleData
		for role in self.opsData.roles:
			vSignedUpUsers: str = ""
			if len(role.players) == 0:
				vSignedUpUsers = "-"
			for user in role.players:
				# Convert IDs to names for display
				vUserAsName = await self.botRef.get_user(int(user))
				if vUserAsName is not None:
					vSignedUpUsers += f"{vUserAsName}\n"
				else: # If not found, fetch non-cached.
					vUserAsName = await self.botRef.fetch_user(int(user))
					if vUserAsName is not None:
						vSignedUpUsers += f"{vUserAsName}"
					else: # User doesn't exist?
						botUtils.BotPrinter.LogError(f"User ID {user} is not found!")
			
			# Append current/max or just current depending on role settings.
			vRoleName = f"{role.roleName}" 
			if( int(role.maxPositions) > 0 ): 
				vRoleName += f"({len(role.players)}/{role.maxPositions})"
			else:
				vRoleName += f"({len(role.players)})"
				
			vEmbed.add_field(inline=True,
			name=vRoleName,
			value=vSignedUpUsers)

		return vEmbed


	async def PostMessage(self):
		# Sets target channel, creates it if it doesn't exist.
		vTargetChannel: discord.TextChannel = await self.GetTargetOpsChannel()
		vEmbed = await self.GenerateEmbed()
		vView = OpMessageView()

		vMessageID = await vTargetChannel.send(view=vView, embed=vEmbed)
		self.opsData.messageID = vMessageID
		botUtils.BotPrinter.Debug(f"Ops Message ID: {vMessageID}")
		self.saveToFile()


	async def GetTargetOpsChannel(self):
		if self.botRef is None:
			botUtils.BotPrinter("NO BOT REF?!")
			return
		vGuild = self.botRef.get_guild(settings.DISCORD_GUILD)
		if vGuild is None:
			# Try again using non-cache "fetch":
			vGuild = await self.botRef.fetch_guild(settings.DISCORD_GUILD)
			if vGuild is None:
				botUtils.BotPrinter.LogError("Failed to find guild for getting Ops Channel!")
				return

		opsCategory = discord.utils.get(vGuild.categories, name="SIGN UP")
		if "CHN=" in self.opsData.arguments:
			argument: str

			channel = None

			for argument in self.opsData.arguments:
				if argument.find("CHN="):
					channel = await discord.utils.get( vGuild.text_channels, name=argument.strip("CHN=") )
					if channel == None:
						channel = await vGuild.create_text_channel(
							name=argument.strip("CHN="), 
							category=opsCategory, 
						)
		else:
			botUtils.BotPrinter.Debug("Target Ops Channel not specified (or missing preceeding 'CHN=').")
			channel = await vGuild.create_text_channel(
							name=self.opsData.name, 
							category=opsCategory, 
						)
		
		return channel 

	async def UpdateMessage(self):
		self
			


class OpMessageView(discord.ui.View):
	def __init__(self, timeout= None):
		super().__init__(timeout=timeout)
		self.vParentMessage : OpsMessage
		self.vRoleSelector = OpsRoleSelector


	# def UpdateOptions(self):
	# 	# self.remove_item(self.vRoleSelector)
	# 	self.vRoleSelector.options.clear()
	# 	role: botData.OpRoleData
	# 	vNewButton = discord.ui.Select(custom_id=f"{self.vParentMessage.opsData.messageID}_RoleSelector")
	# 	for role in self.vParentMessage.opsData.roles:
	# 		if( len(role.players) < role.maxPositions ):
	# 			vNewButton.add_option(label=role.roleName, value=role.roleName, emoji=role.roleIcon)
	# 	self._refresh()


class OpsRoleSelector(discord.ui.Select):
	def __init__(self, pParent: OpsMessage):
		self.vParentMessage:OpsMessage = pParent
		super.__init__(placeholder="Choose a role...")

	async def callback(self, pInteraction: discord.Interaction):
		botUtils.BotPrinter.Debug(f"User has chosen {self.values[0]}")
		await pInteraction.response.send_message(f"You have chosen role: {self.values[0]}", ephemeral=True)

	def UpdateOptions(self):
		self.options.clear()
		role: botData.OpRoleData
		for role in self.vParentMessage.opsData.roles:
			if( len(role.players) < role.maxPositions ):
				self.add_option(label=role.roleName, value=role.roleName, emoji=role.roleIcon)





#########################################################################################
# EDITOR


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
		vOpsFilepath = f"{settings.botDir}/{settings.opsFolderName}/{self.vOpsData.name}.bin"
		self.vOpsData.status = botData.OpsStatus.open
		
		vOpsMessage = OpsMessage(pOpsDataFile=vOpsFilepath, pOpsData=self.vOpsData)
		vOpsMessage.saveToFile()
		await vOpsMessage.PostMessage()
		# TODO: Add Update and call it here.
		# await vOpsMessage.UpdateMessage()
		
		await pInteraction.delete_original_response()
		await pInteraction.response.send_message("Ops data updated!", ephemeral=True)

	@discord.ui.button( 
						style=discord.ButtonStyle.primary, 
						label="New Default",
						custom_id="EditRolesNewDefault",
						row=4)
	async def btnNewDefault(self, pInteraction: discord.Interaction, pButton: discord.ui.button):
		# Set status of Ops back to OPEN.
		self.vOpsData.status = botData.OpsStatus.open

		vNewOpsFilepath = f"{settings.botDir}/{settings.defaultOpsDir}/{self.vOpsData.name}.bin"
		botUtils.BotPrinter.Debug(f"Saving new default: {vNewOpsFilepath}...")
		vOpsMessage = OpsMessage(pOpsDataFile=vNewOpsFilepath, pOpsData=self.vOpsData, pBot=self.vBot)
		vOpsMessage.saveToFile()
		botUtils.BotPrinter.Debug("Saved!")

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
		botUtils.BotPrinter.Debug(f"Auto-filling modal (DATE) with existing data: {self.vData.date}")
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
		botUtils.BotPrinter.Debug("Auto-filling modal (INFO) with existing data.")
		self.txtName.default = self.vData.name
		self.txtMessage.default = self.vData.customMessage
		self.txtDescription.default = self.vData.description
		
		vTempStr: str = ""
		for channel in self.vData.voiceChannels:
			vTempStr += f"{channel}\n"		
		self.txtVoiceChannels.default = vTempStr
		
		vTempStr = ""
		for argument in self.vData.arguments:
			vTempStr += f"{argument}\n"
		self.txtArguments.default = vTempStr


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
		self.PresetFields()
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
		botUtils.BotPrinter.Debug("Auto-filling modal (ROLES) with existing data.")
		
		vRoleNames: str = ""
		vRoleEmojis: str = ""
		vRoleMembers: str = ""
		vRoleMaxPos: str = ""

		roleIndex: botData.OpRoleData
		for roleIndex in self.vData.roles:
			vRoleNames += f"{roleIndex.roleName}\n"
			vRoleEmojis += f"{roleIndex.roleIcon}\n"
			vRoleMembers += f"{roleIndex.players}\n"
			vRoleMaxPos += f"{roleIndex.maxPositions}\n"

	# Set the text inputs to existing values:
		self.txtRoleName.default = vRoleNames
		self.txtEmoji.default = vRoleEmojis
		self.txtRoleMaxPos.default = vRoleMaxPos
		self.txtRolePlayers.default = vRoleMembers