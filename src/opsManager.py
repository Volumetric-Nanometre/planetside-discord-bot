# Ops Manager: Manages creating, editing and removing of Ops.

import os
import datetime
import pickle


import discord
from discord.ext import commands


import settings
import botUtils
from botUtils import BotPrinter as BUPrint
import botData


class OperationManager():
	"""
	OPERATION MANAGER
	Holds list of saved op file names, and their corresponding opData object.
	Should be used to manage Op related messages, including creation, deletion and editing.
	"""

	vOpsList: list = []
	vLiveOps: list = [] # List of Live Ops (botData.OperationData)
	
	def init(self):
		# Only update lists on first object instantiation (or there's no ops and it occurs each time):
		if len(self.vOpsList) == 0:
			self.vOpsList = self.GetOps()
		BUPrint.Info(f"Operation Manager has been instantited. Ops Files|Data: {len(self.vOpsList)|{len(self.vLiveOps)}}")



	async def GetOps():
		"""
		RETURN - Type: list(str), containing filenames of current saved Ops.
		
		"""
		botUtils.BotPrinter.Debug("Getting Ops list...")
		vOpsDir = f"{settings.botDir}/{settings.opsFolderName}/"
		return botUtils.FilesAndFolders.GetFiles(vOpsDir, ".bin")


	async def LoadOps(self):
		"""
		Clear current list of LiveOps, then load from files in opsList. 
		"""
		self.vLiveOps.clear()


	def GetDefaults():
		"""
		GET DEFAULTS
		Get the default Ops filenames.
		
		RETURN : list(str)
		"""
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

	def GetDefaultOpsAsList():
		"""
		GET DEFAULT OPS AS LIST
		Expected use - App command auto-fill.
		Additional non-file entries are added to the returned list!

		RETURN: list(str)  Containing the names of saved default Ops.

		Does not use SELF to make it callable without constructing an instance.
		Does not use Async to allow it to be called in function parameters.
		Does not strip file extension!
		"""
		vDataFiles: list = ["Custom"]
		# Merge custom list with list of actual default files.		
		vDataFiles += OperationManager.GetDefaults()

		return vDataFiles


	async def createOpsFolder():
		if (not os.path.exists(f"{settings.botDir}/{settings.opsFolderName}") ):
			try:
				os.makedirs(f"{settings.botDir}/{settings.opsFolderName}")
			except:
				botUtils.BotPrinter.LogError("Failed to create folder for Ops data!")

	
	async def SaveToFile(p_opsData: botData.OperationData):
		"""
		SAVE TO FILE
		Saves the Operation Data to file.
		
		NOTE: If filename is empty, the OpData is saved as a default using its name!

		p_opsData: The ops data to save.
		"""
		BUPrint.Info(f"Saving Operation Data to file. OpName|FileName: {p_opsData.name} | {p_opsData.fileName}")
		vFilePath = f"{settings.botDir}/"
		if p_opsData.fileName == "": # No filename, save as new default ops using Name.
			vFilePath += f"{settings.defaultOpsDir}/{p_opsData.name}.bin"
		else:
			vFilePath += f"{settings.defaultOpsDir}/{p_opsData.fileName}.bin"

		try:
			with open(vFilePath, "wb") as vFile:
				pickle.dump(p_opsData, vFile)
				BUPrint.Info("File saved sucessfully!")
		except:
			BUPrint.LogError("Failed to save Ops Data to file!")


	async def LoadFromFile(p_opFilePath):
		"""
		LOAD FROM FILE
		Does not differentiate between Default or Live ops, it merely loads an OpData and returns the object!

		p_opFilePath: The FULL filepath to load from.
		"""
		BUPrint.Info(f"Loading Operation Data from file. Path:{p_opFilePath}")
		try:
			with open(p_opFilePath, "rb") as vFile:
				vLoadedOpData = pickle.load(vFile)
				BUPrint.Info("Data loaded sucessfully!")
				return vLoadedOpData

		except EOFError as vError:
			BUPrint.LogErrorExc("Failed to open file. Check to ensure the file has not been overwritten and is not 0 bytes!", p_exception=vError)
			return None

		except Exception as vError:
			BUPrint.LogErrorExc("Failed to open file!", p_exception=vError)
			return None




##################################################################
# MESSAGES

class OpsMessage():
	def __init__(self, pOpsData: botData.OperationData, pBot: commands.Bot, pOpsDataFile: str = ""):
		self.opsDatafilePath = pOpsDataFile
		self.opsData: botData.OperationData = pOpsData
		self.botRef: commands.Bot = pBot

	def saveToFile(self):
		botUtils.BotPrinter.Debug(f"Attempting to save {self.opsData.name} to file: {self.opsDatafilePath}")

		try:
			with open(self.opsDatafilePath, 'wb') as vFile:
				pickle.dump(self.opsData, vFile)
				botUtils.BotPrinter.Debug("Saved data succesfully!")
		except:
			botUtils.BotPrinter.LogError(f"Failed to save {self.opsData.name} to file {self.opsDatafilePath}!")
		
	def getDataFromFile(self):
		botUtils.BotPrinter.Debug(f"Attempting to load data from file: {self.opsDatafilePath}")
		try:
			with open(self.opsDatafilePath, 'rb') as vFile:
				self.opsData = pickle.load(vFile)
				botUtils.BotPrinter.Debug("Loaded data succesfully!")
		except:
			botUtils.BotPrinter.LogError(f"Failed to load Ops data from file: {self.opsDatafilePath}")

	def SetArguments(self, pArgString:str):
		self.opsData.arguments = pArgString.split(" ")
		botUtils.BotPrinter.Debug(f"Parsed arguments: {self.opsData.arguments}")

	# Sets this objects embed information from data.
	# Should be called prior to posting or updating the view this object is called from.
	# Returns an embed containing the Ops info.
	async def GenerateEmbed(self):
		vTitleStr = f"{self.opsData.name.upper()} | {botUtils.DateFormatter.GetDiscordTime(self.opsData.date, botUtils.DateFormat.DateTimeLong)}"
		vDescriptionText = f"Starts {botUtils.DateFormatter.GetDiscordTime(self.opsData.date, botUtils.DateFormat.Dynamic)}"

		vEmbed = discord.Embed(colour=botUtils.Colours.editing.value, title=vTitleStr, description=vDescriptionText)

		vEmbed.add_field(inline=False, 
			name=f"About {self.opsData.name}", 
			value=f"{self.opsData.description}"
		)

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
				vUserAsName = self.botRef.get_user(int(user))
				if vUserAsName is not None:
					vSignedUpUsers += f"{vUserAsName}\n"
				else: # If not found, fetch non-cached.
					vUserAsName = await self.botRef.fetch_user(int(user))
					if vUserAsName is not None:
						vSignedUpUsers += f"{vUserAsName}"
					else: # User doesn't exist?
						botUtils.BotPrinter.LogError(f"User ID {user} is not found! Removing from data")
						role.players.remove(user)
						OpsMessage(pOpsData=self.opsData, pBot=self.botRef, pOpsDataFile=self.opsDatafilePath).saveToFile()
			
			# Prepend role icon if not None:
			vRoleName = ""
			if role.roleIcon != None:
				vRoleName += f"{role.roleIcon} "

			vRoleName += role.roleName 
			# Append current/max or just current depending on role settings.
			if( int(role.maxPositions) > 0 ): 
				vRoleName += f" ({len(role.players)}/{role.maxPositions})"
			else:
				vRoleName += f" ({len(role.players)})"
				
			vEmbed.add_field(inline=True,
			name=vRoleName,
			value=vSignedUpUsers)

		return vEmbed


	async def PostMessage(self):
		# Sets target channel, creates it if it doesn't exist.
		vTargetChannel: discord.TextChannel = await self.GetTargetOpsChannel()
		if vTargetChannel == None:
			return
		vEmbed = await self.GenerateEmbed()
		vView = OpMessageView()

		vView.vParentMessage = self
		vView.vRoleSelector.UpdateOptions()

		vMessageID = await vTargetChannel.send(view=vView, embed=vEmbed)
		self.opsData.messageID = vMessageID
		botUtils.BotPrinter.Debug(f"Ops Message ID: {self.opsData.messageID}")
		# self.saveToFile() # DON'T CALL FROM HERE, it causes weak ref error.


	async def GetTargetOpsChannel(self):
		botUtils.BotPrinter.Debug("Obtaining target channel...")
		if self.botRef is None:
			botUtils.BotPrinter("NO BOT REF?!")
			return

		vGuild = self.botRef.guilds[0]
		if vGuild is None:
			# Try again using non-cache "fetch":
			vGuild = await self.botRef.fetch_guild(settings.DISCORD_GUILD)
			if vGuild is None:
				botUtils.BotPrinter.LogError("Failed to find guild for getting Ops Channel!")
				return
		opsCategory = discord.utils.find(lambda items: items.name == "SIGN UP", vGuild.categories)
		if opsCategory == None:
			BUPrint.Info("SIGNUP CATEGORY NOT FOUND!  Check settings and ensure signupCategory matches the name of the category to be used; including capitalisation!")
			return None

		argument: str
		for argument in self.opsData.arguments:
			botUtils.BotPrinter.Debug(f"Parsing argument: {argument}")
			channel = None
			if argument.find("CHN=") != -1:
				botUtils.BotPrinter.Debug("Argument for channel found!")
				vCleanArg = argument.strip("CHN=")
				channel = discord.utils.find(lambda items: items.name == vCleanArg, vGuild.text_channels)
				if channel != None:
					return channel
				else:
					botUtils.BotPrinter.Debug(f"No existing matching channel, creating channel {vCleanArg}")
					channel = await vGuild.create_text_channel(
						name=vCleanArg,
						category=opsCategory 
					)
					return channel

		# If code reaches here, no channel was found.
		botUtils.BotPrinter.Debug(f"Target Ops Channel not specified (or missing preceeding 'CHN=')\nFinding {self.opsData.name} in {vGuild.text_channels}.\n\n")
		channel = discord.utils.find(lambda items: items.name == self.opsData.name.lower(), vGuild.text_channels)

		if channel == None:
			channel = await vGuild.create_text_channel(
							name=self.opsData.name,
							category=opsCategory
						)
		
		return channel 

	async def UpdateMessage(self):
		return self
			


class OpMessageView(discord.ui.View):
	def __init__(self, timeout= None):
		super().__init__(timeout=timeout)
		self.vParentMessage : OpsMessage
		self.vRoleSelector = OpsRoleSelector(pParent=self)
		self.btnReserve = OpsRoleReserve(pParent=self)
		
		self.add_item(self.btnReserve)
		self.add_item(self.vRoleSelector)
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
		defaultOption = discord.SelectOption(label="Default", value="Default")
		super().__init__(placeholder="Choose a role...", options=[defaultOption], row=0)

	async def callback(self, pInteraction: discord.Interaction):
		botUtils.BotPrinter.Debug(f"User {pInteraction.user.name} has signed up to an event with role: {self.values[0]}")
		await pInteraction.response.send_message(f"You have chosen role: {self.values[0]}", ephemeral=True)

	def UpdateOptions(self):
		self.options.clear()
		role: botData.OpRoleData

		# Always add a default used to resign players.
		self.add_option(label="Resign", value="Resign", emoji=settings.resignIcon)

		for role in self.vParentMessage.vParentMessage.opsData.roles:
			if( len(role.players) < int(role.maxPositions) or int(role.maxPositions) <= 0 ):
				# To ensure no errors, only use emoji if its specified

				if role.roleIcon != None:
					botUtils.BotPrinter.Debug(f"Icon ({role.roleIcon}) specified, using Icon...")
					self.add_option(label=role.roleName, value=role.roleName, emoji=role.roleIcon)
				else:
					self.add_option(label=role.roleName, value=role.roleName)


class OpsRoleReserve(discord.ui.Button):
	def __init__(self, pParent: OpsMessage):
		self.vParentMessage = pParent
		super().__init__(label="Reserve", emoji=settings.reserveIcon, row=0)

	async def callback(self, pInteraction: discord.Interaction):
		pInteraction.response.send_message(content="You have signed up as a reserve!", ephemeral=True)



#########################################################################################
# EDITOR


class OpsEditor(discord.ui.View):
	def __init__(self, pBot: commands.Bot, pOpsData: botData.OperationData):
		self.vBot = pBot
		self.vOpsData = pOpsData # Original data, not edited.
		self.vMessage : discord.Message = None # used to yeetus deleetus when done.
		# self.EditedData = pOpsData # Edited data, applied and saved.
		botUtils.BotPrinter.Debug("Created Blank Editor")
		super().__init__(timeout=None)
		

# # # # # # Edit Buttons
	editButtonStyle = discord.ButtonStyle.grey
	# Edit Date:
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
		vEditModal.custom_id="EditRolesModal"
		await pInteraction.response.send_modal( vEditModal )
	
# # # # # # # Confirm/Save buttons:
	@discord.ui.button(
						style=discord.ButtonStyle.danger, 
						label="Apply/Send",
						custom_id="EditorApply",
						row=4)
	async def btnApplyChanges(self, pInteraction: discord.Interaction, pButton: discord.ui.button):
		self.vOpsData.GenerateFileName()
		vOpsFilepath = f"{settings.botDir}/{settings.opsFolderName}/{self.vOpsData.fileName}.bin"
		self.vOpsData.status = botData.OpsStatus.open
		
		vOpsMessage = OpsMessage(pOpsDataFile=vOpsFilepath, pOpsData=self.vOpsData, pBot=self.vBot)
		await vOpsMessage.PostMessage()

		# TODO: Add Update and call it here.
		# await vOpsMessage.UpdateMessage()


		# await pInteraction.delete_original_response()
		# vOpsMessage.saveToFile()
		await self.vMessage.delete()
		await pInteraction.response.send_message("Successful", ephemeral=True)

	@discord.ui.button( 
						style=discord.ButtonStyle.primary, 
						label="New Default",
						custom_id="EditorNewDefault",
						row=4)
	async def btnNewDefault(self, pInteraction: discord.Interaction, pButton: discord.ui.button):
		# Set status of Ops back to OPEN.
		self.vOpsData.status = botData.OpsStatus.open

		vNewOpsFilepath = f"{settings.botDir}/{settings.defaultOpsDir}/{self.vOpsData.name}.bin"
		botUtils.BotPrinter.Debug(f"Saving new default: {vNewOpsFilepath}...")
		vOpsMessage = OpsMessage(pOpsDataFile=vNewOpsFilepath, pOpsData=self.vOpsData, pBot=self.vBot)
		vOpsMessage.saveToFile()
		botUtils.BotPrinter.Debug("Saved!")

		await pInteraction.followup.send(f"Added new default!", ephemeral=True)



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
		max_length=400,
		required=True
	)
	txtMessage = discord.ui.TextInput(
		label="Details",
		placeholder="Optional detailed message about this ops.",
		style=discord.TextStyle.paragraph,
		max_length=800,
		required=False
	)

	txtVoiceChannels = discord.ui.TextInput(
		label="Voice Channels",
		placeholder="A list of voice channels (per line) to create for this Operation.",
		style=discord.TextStyle.paragraph,
		required=False
	)
	txtArguments = discord.ui.TextInput(
		label="Commands",
		placeholder="Optional commands (per line) to modify behaviour.",
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
		self.txtVoiceChannels.default = vTempStr.strip()
		
		vTempStr = ""
		for argument in self.vData.arguments:
			BUPrint.Debug(f"Adding Arg {argument} to modal.")
			vTempStr += f"{argument}\n"
		self.txtArguments.default = vTempStr.strip()

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
			await pInteraction.response.send_message('Inconsistent array lengths in fields!  \nMake sure the number of lines matches in all three fields.\n\nFor empty Emojis, use "".', ephemeral=True)
			return

		vIndex = 0
		botUtils.BotPrinter.Debug(f"Size of array: {len(vRoleNames)}")
		while vIndex < len(vRoleNames):

			vCurrentRole = botData.OpRoleData(pRoleName=vRoleNames[vIndex], pRoleIcon=vRoleEmoji[vIndex], pMaxPos=int(vRoleMax[vIndex]))
			if vIndex < len(self.vData.roles) :
				# Index is on an existing role, adjust values to keep any signed up users.
				self.vData.roles[vIndex].roleName = vCurrentRole.roleName
				self.vData.roles[vIndex].maxPositions = vCurrentRole.maxPositions
				if vCurrentRole.roleIcon == "-":
					BUPrint.Debug("Setting role icon to NONE")
					self.vData.roles[vIndex].roleIcon = None
				else:
					self.vData.roles[vIndex].roleIcon = vCurrentRole.roleIcon
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
		vRoleMembers: str = "DISPLAY PURPOSES ONLY\n"
		vRoleMaxPos: str = ""

		roleIndex: botData.OpRoleData
		for roleIndex in self.vData.roles:
			vRoleNames += f"{roleIndex.roleName}\n"
			vRoleMembers += f"{roleIndex.players}\n"
			vRoleMaxPos += f"{roleIndex.maxPositions}\n"
			if roleIndex.roleIcon == None:
				vRoleEmojis += '""\n'
			else:
				vRoleEmojis += f"{roleIndex.roleIcon}\n"

	# Set the text inputs to existing values:
		self.txtRoleName.default = vRoleNames.strip()
		self.txtEmoji.default = vRoleEmojis.strip()
		self.txtRoleMaxPos.default = vRoleMaxPos.strip()
		self.txtRolePlayers.default = vRoleMembers.strip()