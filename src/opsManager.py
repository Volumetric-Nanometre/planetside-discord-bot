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
	OPERATION MANAGER:
	Holds list of saved op file names, and their corresponding opData object.
	Should be used to manage Op related messages, including creation, deletion and editing.

	To ensure there's always one reference and thus avoid weakref objects for pickling, the bot itself should hold an instance (and set botRef).
	"""

	# vOpsList: list = []
	vLiveOps: list = [] # List of Live Ops (botData.OperationData)
	vBotRef: commands.Bot
	
	def __init__(self):
		# Only update lists on first object instantiation (or there's no ops and it occurs each time):
		if len(self.vLiveOps) == 0:
			self.LoadOps()
		BUPrint.Info(f"Operation Manager has been instantited. Live Ops Data: {len(self.vLiveOps)}")

	async def RefreshOps(self):
		"""
		REFRESH OPS
		Recursively 'updates' all active live Ops so that views are refreshed and usable again.
		"""
		vOpData : botData.OperationData
		for vOpData in self.vLiveOps:
			await self.UpdateMessage(vOpData)
			BUPrint.Info(f"Refreshing Op: \n{vOpData}\n")

	def SetBotRef(p_botRef):
		OperationManager.vBotRef = p_botRef


	def GetOps():
		"""
		RETURN - Type: list(str), containing filenames of current saved Ops.
		
		"""
		botUtils.BotPrinter.Debug("Getting Ops list...")
		# vOpsDir = f"{settings.botDir}/{settings.opsFolderName}/"
		return botUtils.FilesAndFolders.GetFiles(botUtils.FilesAndFolders.GetOpsFolder(), ".bin")


	def LoadOps(self):
		"""
		Clear current list of LiveOps, then load from files in opsList. 
		"""
		self.vLiveOps.clear()
		
		for currentFileName in OperationManager.GetOps():
			vFullPath = f"{botUtils.FilesAndFolders.GetOpsFolder()}{currentFileName}"
			self.vLiveOps.append(OperationManager.LoadFromFile(vFullPath))



	def GetDefaults():
		"""
		GET DEFAULTS:
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
		GET DEFAULT OPS AS LIST:
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


	def createOpsFolder():
		if (not os.path.exists(f"{settings.botDir}/{settings.opsFolderName}") ):
			try:
				os.makedirs(f"{settings.botDir}/{settings.opsFolderName}")
			except:
				botUtils.BotPrinter.LogError("Failed to create folder for Ops data!")

	
	def SaveToFile(p_opsData: botData.OperationData):
		"""
		SAVE TO FILE:
		Saves the Operation Data to file.
		DO NOT GetLock or Release, this function does that for you!
		
		NOTE: If filename is empty, the OpData is saved as a default using its name!

		p_opsData: The ops data to save.

		RETURN:
		True on success.  False on Failure.
		"""
		BUPrint.Info(f"Saving Operation Data to file. OpName|FileName: {p_opsData.name} | {p_opsData.fileName}")

		# temp_opToSave = copy.deepcopy(p_opsData)

		
		vFilePath = f"{settings.botDir}/"
		if p_opsData.fileName == "": # No filename, save as new default ops using Name.
			vFilePath += f"{settings.defaultOpsDir}/{p_opsData.name}.bin"
		else:
			vFilePath += f"{settings.opsFolderName}/{p_opsData.fileName}.bin"

		try:
			botUtils.FilesAndFolders.GetLock(botUtils.FilesAndFolders.GetLockFilePath(p_opsData.fileName))
			with open(vFilePath, "wb") as vFile:
				pickle.dump(p_opsData, vFile)
				BUPrint.Info("File saved sucessfully!")
				botUtils.FilesAndFolders.ReleaseLock(botUtils.FilesAndFolders.GetLockFilePath(p_opsData.fileName))
		except:
			BUPrint.LogError("Failed to save Ops Data to file!")
			botUtils.FilesAndFolders.ReleaseLock(botUtils.FilesAndFolders.GetLockFilePath(p_opsData.fileName))
			return False
		
		# Save successful, return True.
		return True


	def LoadFromFile(p_opFilePath):
		"""
		LOAD FROM FILE:
		Does not differentiate between Default or Live ops, it merely loads an OpData and returns the object!

		Creates and Releases lock files.

		p_opFilePath: The FULL filepath to load from.
		"""
		BUPrint.Info(f"Loading Operation Data from file. Path:{p_opFilePath}")

		try:
			botUtils.FilesAndFolders.GetLock( f"{p_opFilePath}{settings.lockFileAffix}" )
			with open(p_opFilePath, "rb") as vFile:
				vLoadedOpData : botData.OperationData = pickle.load(vFile)
			BUPrint.Info("Data loaded sucessfully!")
			botUtils.FilesAndFolders.ReleaseLock(f"{p_opFilePath}{settings.lockFileAffix}")
			return vLoadedOpData

		except EOFError as vError:
			BUPrint.LogErrorExc("Failed to open file. Check to ensure the file has not been overwritten and is not 0 bytes!", p_exception=vError)
			botUtils.FilesAndFolders.ReleaseLock(f"{p_opFilePath}{settings.lockFileAffix}")
			return None

		except Exception as vError:
			botUtils.FilesAndFolders.ReleaseLock(f"{p_opFilePath}{settings.lockFileAffix}")
			BUPrint.LogErrorExc("Failed to open file!", p_exception=vError)
			return None


	async def AddNewLiveOp(self, p_opData: botData.OperationData):
		"""
		ADD NEW LIVE OP:

		Posts a new LIVE operation.
		Adds the provided opData to the list of live ops.
		Saves the provided OpData to file.
		Creates a notification timer for the operation.

		RETURN: True on fully succesful adding, False if a problem occured.
		"""
		BUPrint.Info(f"Adding a new LIVE operation: {p_opData.name}!")

		bCanContinue = await self.AddNewLive_PostOp(p_opData)
		if not bCanContinue: return False

		# Ops Posted, add OpData to list of LIVE data.
		self.vLiveOps.append(p_opData)

		# Save the Ops to file.
		bCanContinue = OperationManager.SaveToFile( self.vLiveOps[-1] )
		if not bCanContinue: return False

		# Create notification here...

		return True


	async def AddNewLive_PostOp(self, p_opData:botData.OperationData):
		"""
		POST OP:  A sub-function for AddNewLiveOp
		Returns TRUE if succesful send message
		"""
		BUPrint.Info("	-> Posting Live Operation Message!")
		
	# Get target channel for posting to.
		vChannel = await self.AddNewLive_GetTargetChannel(p_opData)
		if vChannel == None:
			return False
		
		# Preventative measure, since a live Ops is being posted and SaveToFile assumes a default if no filename is specified, this is called here just in case.
		p_opData.GenerateFileName()

	# Create message elements

		vView = await self.AddNewLive_GenerateView(p_opData)
		vEmbed = await self.AddNewLive_GenerateEmbed(p_opData)

	# Send the Message.
		try:
			vMessage:discord.Message = await vChannel.send(view=vView, embed=vEmbed)
			p_opData.messageID = vMessage.id
		except discord.HTTPException as vError:
			BUPrint.LogErrorExc("Message did not send due to HTTP Exception.", vError)
			return False
		except Exception as vError:
			BUPrint.LogErrorExc("Failed to send message!", vError)
			return False
		
		return True


	async def AddNewLive_GetTargetChannel(self, p_opsData: botData.OperationData):
		"""
		GET TARGET CHANNEL:

		A sub function to AddNewLiveOps, but usable elsewhere.

		PARAMETERS: p_opsData: the ops data used to get the target channel.

		RETURN:
		Existing or newly created channel.  
		None on failure.
		"""
	
		BUPrint.Debug("	-> Obtaining target channel...")

		vGuild = self.vBotRef.guilds[0]
		if vGuild is None:
			# Try again using non-cache "fetch":
			vGuild = await self.vBotRef.fetch_guild(settings.DISCORD_GUILD)
			if vGuild is None:
				botUtils.BotPrinter.LogError("Failed to find guild for getting Ops Channel!")
				return None
		opsCategory = discord.utils.find(lambda items: items.name == "SIGN UP", vGuild.categories)

		if opsCategory == None:
			BUPrint.Info("SIGNUP CATEGORY NOT FOUND!  Check settings and ensure signupCategory matches the name of the category to be used; including capitalisation!")
			return None

		argument: str
		for argument in p_opsData.arguments:
			BUPrint.Debug(f"Parsing argument: {argument}")
			channel = None
			if argument.find("CHN=") != -1:
				BUPrint.Debug("Argument for channel found!")
				vCleanArg = argument.strip("CHN=")
				channel = discord.utils.find(lambda items: items.name == vCleanArg, vGuild.text_channels)
				if channel != None:
					return channel
				else:
					BUPrint.Info(f"No existing matching channel, creating channel {vCleanArg}")
					channel = await vGuild.create_text_channel(
						name=vCleanArg,
						category=opsCategory 
					)
					return channel

		# If code reaches here, no channel was found.
		BUPrint.Info(f"Target Ops Channel not specified (or missing preceeding 'CHN='")
		# BUPrint.Debug(f"Finding {p_opsData.name} in {vGuild.text_channels}.\n\n")
		channel = discord.utils.find(lambda items: items.name == p_opsData.name.lower(), vGuild.text_channels)

		if channel == None:
			channel = await vGuild.create_text_channel(
							name=p_opsData.name,
							category=opsCategory
						)
		
		return channel 

	async def AddNewLive_GenerateEmbed(self, p_opsData: botData.OperationData):
		"""
		GENERATE EMBED
		A sub function to AddNewLiveOps

		Can also be used to regenerate an embed with updated information.

		Returns a discord.Embed with information from p_opsData.
		"""
		BUPrint.Info("	-> Generating Embed...")
		vTitleStr = f"{p_opsData.name.upper()} | {botUtils.DateFormatter.GetDiscordTime(p_opsData.date, botUtils.DateFormat.DateTimeLong)}"

		vEmbed = discord.Embed(colour=botUtils.Colours.openSignup.value,
								title=vTitleStr,
								description=f"Starts {botUtils.DateFormatter.GetDiscordTime(p_opsData.date, botUtils.DateFormat.Dynamic)}"
							)

		vEmbed.add_field(inline=False,
			name=f"About {p_opsData.name}",
			value=p_opsData.description
		)

		if(p_opsData.customMessage != ""):
			vEmbed.add_field(inline=False,
				name="Additional Info:",
				value=p_opsData.customMessage
			)

		# Generate lists for roles:
		role: botData.OpRoleData
		for role in p_opsData.roles:
			vSignedUpUsers: str = ""
			if len(role.players) == 0:
				vSignedUpUsers = "-"
			for user in role.players:
				# Convert IDs to names for display
				vUserAsName = self.vBotRef.get_user(int(user))
				if vUserAsName is not None:
					vSignedUpUsers += f"{vUserAsName}\n"
				else: # If not found, fetch non-cached.
					vUserAsName = await self.vBotRef.fetch_user(int(user))
					if vUserAsName is not None:
						vSignedUpUsers += f"{vUserAsName}\n"
					else: # User doesn't exist?
						botUtils.BotPrinter.LogError(f"User ID {user} is not found! Removing from data")
						role.players.remove(user)
			
			# Prepend role icon if not None:
			vRoleName = ""
			if role.roleIcon != "-" :
				BUPrint.Debug(f"Role icon for EMBED specified: {role.roleIcon}")
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
		# END of FOR loop.

		# Add builtin RESERVE
		if(p_opsData.options.bUseReserve):
			vReserves = "-"
			if len(p_opsData.reserves) > 0: vReserves = ""
			for reserve in p_opsData.reserves:
				vUserAsName = self.vBotRef.get_user(int(reserve))
				vReserves += f"{vUserAsName}\n"
			vEmbed.add_field(name=f"Reserves ({len(p_opsData.reserves)})", value=vReserves, inline=True )

		return vEmbed

	async def AddNewLive_GenerateView(self, p_opsData: botData.OperationData):
		vView = discord.ui.View(timeout=None)
		vRoleSelector = OpsRoleSelector(p_opsData)
		vRoleSelector.UpdateOptions()

		vView.add_item( vRoleSelector )
		vView.add_item(OpsRoleReserve(p_opsData))
		return vView

	async def UpdateMessage(self, p_opData: botData.OperationData):
		"""
		UPDATE MESSAGE
		
		PARAMETERS:
		p_opData: The Opdata to regenerate a message with.

		RETURN: None
		"""
		BUPrint.Info("	-> Updating Op Message")
		vChannel: discord.TextChannel = await self.AddNewLive_GetTargetChannel(p_opsData=p_opData)
		vMessage: discord.Message = await vChannel.fetch_message(p_opData.messageID)

		vNewEmbed = await self.AddNewLive_GenerateEmbed(p_opData)
		vView = await self.AddNewLive_GenerateView(p_opData)
		await vMessage.edit(embed=vNewEmbed, view=vView)
		
	def RemoveUser(p_opData:botData.OperationData, p_userToRemove:str):
		"""
		REMOVE USER:
		Iterates over all roles (including reserve) and removes the player ID if present.
		"""
		if p_userToRemove in p_opData.reserves:
			p_opData.reserves.remove(p_userToRemove)
		
		for role in p_opData.roles:
			if p_userToRemove in role.players:
				role.players.remove(p_userToRemove)


##################################################################
# MESSAGES	



class OpsRoleSelector(discord.ui.Select):
	def __init__(self, p_opsData: botData.OperationData):
		defaultOption = discord.SelectOption(label="Default", value="Default")
		self.vOpsData = p_opsData
		super().__init__(placeholder="Choose a role...", options=[defaultOption])

	async def callback(self, pInteraction: discord.Interaction):
		botUtils.BotPrinter.Debug(f"User {pInteraction.user.name} has signed up to an event with role: {self.values[0]}")
		
		
		await pInteraction.response.send_message(f"You have chosen role: {self.values[0]}", ephemeral=True)
		role: botData.OpRoleData
	# Clear user if existing in other roles
		OperationManager.RemoveUser(p_opData=self.vOpsData, p_userToRemove=pInteraction.user.id)

	# Add user to assigned role.
		for role in self.vOpsData.roles:
			if self.values[0] == role.roleName:
				role.players.append(pInteraction.user.id)
				OperationManager.SaveToFile(self.vOpsData)	

		vOpMan = OperationManager()
		await vOpMan.UpdateMessage(p_opData=self.vOpsData)
	
	
	def UpdateOptions(self):
		self.options.clear()
		role: botData.OpRoleData

		# Always add a default used to resign players.
		self.add_option(label="Resign", value="Resign", emoji=settings.resignIcon)

		for role in self.vOpsData.roles:
			if( len(role.players) < int(role.maxPositions) or int(role.maxPositions) <= 0 ):
				# To ensure no errors, only use emoji if its specified

				if role.roleIcon == "-":
					self.add_option(label=role.roleName, value=role.roleName)
				else:
					botUtils.BotPrinter.Debug(f"Icon ({role.roleIcon}) specified, using Icon...")
					self.add_option(label=role.roleName, value=role.roleName, emoji=role.roleIcon)



class OpsRoleReserve(discord.ui.Button):
	def __init__(self, p_opsData : botData.OperationData):
		self.vOpsData = p_opsData
		super().__init__(label="Reserve", emoji=settings.reserveIcon)

	async def callback(self, pInteraction: discord.Interaction):
		await pInteraction.response.send_message(content="You have signed up as a reserve!", ephemeral=True)
		OperationManager.RemoveUser(self.vOpsData, pInteraction.user.id)
		self.vOpsData.reserves.append(pInteraction.user.id)

		vOpMan = OperationManager()
		await vOpMan.UpdateMessage(self.vOpsData)





#########################################################################################
# EDITOR


class OpsEditor(discord.ui.View):
	def __init__(self, pBot: commands.Bot, pOpsData: botData.OperationData):
		self.vBot = pBot
		self.vOpsData = pOpsData # Original data, not edited.
		# self.EditedData = pOpsData # Edited data, applied and saved.
		BUPrint.Info("Ops Editor Instantiated")
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
		vOpManager = OperationManager()
		if self.vOpsData.fileName == None:
			BUPrint.Info("Adding new Live Op...")
			bSucsessfulOp = await vOpManager.AddNewLiveOp(self.vOpsData)
			
			if bSucsessfulOp:
				await pInteraction.response.send_message("***SUCCESS!***\nYou can now dismiss the editor if you're done.", ephemeral=True)
				OperationManager.SaveToFile(self.vOpsData)
			else:
				await pInteraction.response.send_message("An error occured when posting the message.  Check console for more information.\n\nTry again, or dismiss the editor.", ephemeral=True)
		else:
			BUPrint.Info(f"Saving updated data for {self.vOpsData.name}")
			OperationManager.SaveToFile(self.vOpsData)
			await pInteraction.response.send_message(f"Operation data for {self.vOpsData.name} saved! Updating signup message...\n You can now dismiss the editor if you're done.", ephemeral=True)
			vOpMan = OperationManager()
			await vOpMan.UpdateMessage(self.vOpsData)



	@discord.ui.button( 
						style=discord.ButtonStyle.primary, 
						label="New Default",
						custom_id="EditorNewDefault",
						row=4)
	async def btnNewDefault(self, pInteraction: discord.Interaction, pButton: discord.ui.button):
		BUPrint.Info(f"Saving a new default! {self.vOpsData.name}")
		# Set status of Ops back to OPEN.
		self.vOpsData.status = botData.OpsStatus.open

		vOldFilename = self.vOpsData.fileName
		# Ensure fileName is empty so its saved as a default
		self.vOpsData.fileName = ""
		OperationManager.SaveToFile(self.vOpsData)
		botUtils.BotPrinter.Debug("Saved!")

		self.vOpsData.fileName = vOldFilename

		# await pInteraction.followup.send(f"Added new default: {self.vOpsData.name}!", ephemeral=True)
		await pInteraction.response.send_message(f"Added new default: {self.vOpsData.name}!", ephemeral=True)



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
				if vCurrentRole.roleIcon == "-" or vCurrentRole.roleIcon == '""' or vCurrentRole.roleIcon == "":
					BUPrint.Debug("Setting role icon to NONE")
					self.vData.roles[vIndex].roleIcon = "-"
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
				vRoleEmojis += '-\n'
			else:
				vRoleEmojis += f"{roleIndex.roleIcon}\n"

	# Set the text inputs to existing values:
		self.txtRoleName.default = vRoleNames.strip()
		self.txtEmoji.default = vRoleEmojis.strip()
		self.txtRoleMaxPos.default = vRoleMaxPos.strip()
		self.txtRolePlayers.default = vRoleMembers.strip()