# Ops Manager: Manages creating, editing and removing of Ops.
# For live ops being started, see OpsCommander

import os
import datetime, dateutil.relativedelta
import pickle

import discord
from discord.ext import commands
from discord import app_commands
import apscheduler.jobstores.base

from botData.settings import Messages as botMessages
from botData import settings as botSettings
import botData.settings
# import botData.operations as OpData
from botData.dataObjects import OperationData, OpRoleData, OpsStatus

import OpCommander.commander
import OpCommander.autoCommander

import botUtils
from botUtils import BotPrinter as BUPrint

from botModals.opsManagerModals import *


class Operations(commands.GroupCog):
	def __init__(self, p_bot):
		super().__init__()
		self.bot : commands.Bot = p_bot
		BUPrint.Info("COG: Operations loaded.")

	@app_commands.command(name="add", description="Add a new Ops event")
	@app_commands.describe(optype = "Type of Ops to create. If this doesn't match an existing option, defaults to 'custom'!",
							edit = "Open Ops Editor before posting this event (Always true if 'Custom')",
							pDay = "The day this ops will run.",
							pMonth = "The month this ops will run.",
							pHour = "The HOUR (24) the ops will run in.",
							pMinute = "The MINUTE within an hour the ops starts on",
							pYear = "(Optional) The Year the ops should run.",
							pArguments = "(Optional) Additional arguments to control the op behaviour.",
							pManagedBy = "(Optional) The user responsible for running this event",
							pAdditionalInfo = "(Optional) Any additional information about this event: NOTE: Overwrites the default!"
	)
	@app_commands.rename(pDay="day", 
						pMonth="month", 
						pHour="hour", 
						pMinute="minute", 
						pYear="year", 
						pArguments="arguments",
						pManagedBy="managing_user",
						pAdditionalInfo="info",
	)

	async def addopsevent (self, pInteraction: discord.Interaction, 
		optype: str,
		edit: bool, 
		pDay: app_commands.Range[int, 0, 31], 
		pMonth: app_commands.Range[int, 1, 12], 
		pHour: app_commands.Range[int, 1, 23], 
		pMinute:app_commands.Range[int, 0, 59],
		pYear: int  = datetime.datetime.now().year,
		pArguments: str = "",
		pManagedBy: str = "",
		pAdditionalInfo: str = ""
	):
		# HARDCODED ROLE USEAGE:
		if not await botUtils.UserHasCommandPerms(pInteraction.user, (botSettings.CommandRestrictionLevels.level1), pInteraction):
			return

		botUtils.BotPrinter.Debug(f"Adding new event ({optype}).  Edit after posting: {edit}")
		vDate = datetime.datetime(
			year=pYear,
			month=pMonth,
			day=pDay,
			hour=pHour, minute=pMinute,
			tzinfo=datetime.timezone.utc)

		vOpTypeStr = str(optype).replace("OpsType.", "")


		newOpsData : OperationData = OperationData()
		vOpManager = OperationManager()
		newOpsData.date = vDate

		if vOpTypeStr not in OperationManager.GetDefaults():
			# USER IS USING A NON-DEFAULT/CUSTOM
			newOpsData.status = OpsStatus.editing

			vEditor: OpsEditor = OpsEditor(pBot=self.bot, pOpsData=newOpsData)

			botUtils.BotPrinter.Debug(f"Editor: {vEditor}, Type: {type(vEditor)}")

			await pInteraction.response.send_message("**OPS EDITOR**", view=vEditor, ephemeral=True)
			vEditor.vEditorMsg = await pInteraction.original_response()
			return

		else:
			# MAKE SURE TO SWAP OP DATA FILE LATER, ELSE YOU WILL OVERWRITE THE SAVED DEFAULT
			vFilePath = f"{botSettings.Directories.savedDefaultsDir}{optype}"
			newOpsData = OperationManager.LoadFromFile(vFilePath)

			# Update date & args to the one given by the command
			newOpsData.date = vDate

			if pArguments != "":
				newOpsData.arguments = newOpsData.ArgStringToList(pArguments)

			if pManagedBy != "":
				newOpsData.managedBy = pManagedBy

			if pAdditionalInfo != "":
				newOpsData.customMessage = pAdditionalInfo

			if newOpsData == None:
				botUtils.FilesAndFolders.DeleteCorruptFile(vFilePath)
				await pInteraction.response.send_message(botMessages.newOpCorruptData, ephemeral=True)
				return


			if(edit):
				vEditor = OpsEditor(pBot=self.bot, pOpsData=newOpsData)
				await pInteraction.response.send_message(f"**Editing OpData for** *{optype}*", view=vEditor, ephemeral=True)
				vEditor.vEditorMsg = await pInteraction.original_response()

			else:
				if await vOpManager.AddNewLiveOp(p_opData=newOpsData):
					await pInteraction.response.send_message("Ops posted!", ephemeral=True)
				else:
					await pInteraction.response.send_message("Op posting failed, check console for more information.", ephemeral=True)

		# End AddOpsEvent

	@addopsevent.autocomplete('optype')
	async def autocompleteOpTypes(self, pInteraction: discord.Interaction, pTypedStr: str):
		choices: list = []
		vDataFiles: list = ["Custom"]

		vDataFiles =  OperationManager.GetDefaultOpsAsList()

		option: str
		for option in vDataFiles:
			if(pTypedStr.lower() in option.lower()):
				# Add options matching current typed response to a list.
				# Allows bypassing discords max 25 item limit on dropdown lists.
				choices.append(discord.app_commands.Choice(name=option.replace(".bin", ""), value=option))
		return choices


# EDIT OPS (/editop)
	@app_commands.command(name="edit", description="Edit the values of a current live operation.")
	@app_commands.describe(pOpsToEdit="Select the current live Op data to edit.")
	@app_commands.rename(pOpsToEdit="file")
	async def editopsevent(self, pInteraction: discord.Interaction, pOpsToEdit: str):

		# HARDCODED ROLE USEAGE:
		if not await botUtils.UserHasCommandPerms(pInteraction.user, (botSettings.CommandRestrictionLevels.level1), pInteraction):
			return

		BUPrint.Info(f"**Editing Ops data for** *{pOpsToEdit}*")
		vLiveOpData:OperationData = OperationManager.LoadFromFile( botUtils.FilesAndFolders.GetOpFullPath(pOpsToEdit))

		if vLiveOpData != None:

			# Prevent editing of an operation that's in progress.
			if vLiveOpData.status.value >= OpsStatus.prestart.value:
				await pInteraction.response.send_message("You cannot edit an operation that is in progress!", ephemeral=True)
				return

			vEditor = OpsEditor(pBot=self.bot, pOpsData=vLiveOpData)
			vOpMan = OperationManager()
			vLiveOpData.status = OpsStatus.editing
			await vOpMan.UpdateMessage(vLiveOpData)

			await pInteraction.response.send_message(f"**Editing OpData for** *{vLiveOpData.fileName}*", view=vEditor, ephemeral=True)
			vEditor.vEditorMsg = await pInteraction.original_response()

		else:
			botUtils.FilesAndFolders.DeleteCorruptFile( botUtils.FilesAndFolders.GetOpFullPath(pOpsToEdit) )
			OperationManager.vLiveOps.remove(vLiveOpData)
			await pInteraction.response.send_message("The operation you wished to edit was corrupt and has been removed.", ephemeral=True)
			return


	@editopsevent.autocomplete("pOpsToEdit")
	async def autocompleteFileList(self, pInteraction: discord.Interaction, pTypedStr: str):
		choices: list = []
		vDataFiles: list = OperationManager.GetOps()

		option: str
		for option in vDataFiles:
			if(pTypedStr.lower() in option.lower()):
				# Add options matching current typed response to a list.
				# Allows bypassing discords max 25 item limit on dropdown lists.
				choices.append(discord.app_commands.Choice(name=option.replace(".bin", ""), value=option.replace(".bin", "")))
		return choices
# END- Commands.CogGroup


class OperationManager():
	"""
	# OPERATION MANAGER:

	Holds list of saved op file names, and their corresponding opData object.
	Should be used to manage Op related messages, including creation, deletion and editing.
	"""
	vLiveOps: list = [] # List of Live Ops (botData.OperationData)
	vLiveCommanders = []
	vBotRef: commands.Bot = None
	
	def __init__(self):
		# Only update lists on first object instantiation (or there's no ops and it occurs each time):
		if len(self.vLiveOps) == 0:
			self.LoadOps()


	async def RefreshOps(self):
		"""
		# REFRESH OPS

		Recursively 'updates' all active live Ops so that views are refreshed and usable again.
		"""
		vOpData : OperationData
		for vOpData in self.vLiveOps:
			await self.UpdateMessage(vOpData)
			if botSettings.BotSettings.bDebugEnabled:
				BUPrint.Info(f"Refreshing {vOpData}\n")
			else:
				BUPrint.Info(f"Refreshing {vOpData.fileName}")


	def SetBotRef(p_botRef):
		OperationManager.vBotRef = p_botRef



	def GetOps():
		"""
		RETURN - Type: list(str), containing filenames of current Live Ops.
		
		"""
		botUtils.BotPrinter.Debug("Getting Ops list...")
		return botUtils.FilesAndFolders.GetFiles( botSettings.Directories.liveOpsDir, ".bin")


	
	def LoadOps(self):
		"""
		Clear current list of LiveOps, then load from files in opsList. 
		"""
		self.vLiveOps.clear()
		BUPrint.Debug("Loading Ops...")
		for currentFileName in OperationManager.GetOps():
			BUPrint.Debug(f"Loading data from {currentFileName}")
			vFullPath = f"{botSettings.Directories.liveOpsDir}{currentFileName}"
			vFile: OperationData = OperationManager.LoadFromFile(vFullPath)
			if vFile is not None:
				self.vLiveOps.append(OperationManager.LoadFromFile(vFullPath))



	def GetDefaults():
		"""
		# GET DEFAULTS:
		Get the default Ops filenames.
		
		## RETURN : list(str)
		"""
		return botUtils.FilesAndFolders.GetFiles(botSettings.Directories.savedDefaultsDir, ".bin")



	async def RemoveOperation(self, p_opData: OperationData):
		"""
		# REMOVE OPERATION:

		p_opData: The opdata the user wishes to remove.

		## NOTE: Call from an instance.

		Works for both LIVE and DEFAULT ops; it behaves akin to saving a new Operation- if there's no specified fileName, this will remove a DEFAULT, else remove a Live Ops (and its posting)

		## RETURN: Bool
		True : Op Removed (or wasn't a file to begin with.)
		False: Failed to remove.
		"""
		BUPrint.Info(f"Removing Operation: {p_opData.fileName}")
		vFileToRemove : str = ""
		bIsDefault = False # Convenience bool to avoid having to check messageID repeatedly

		if p_opData.messageID == "":
			vFileToRemove = f"{botSettings.Directories.savedDefaultsDir}{p_opData.name}.bin"
			bIsDefault = True
		else:
			vFileToRemove = botUtils.FilesAndFolders.GetOpFullPath(p_opData.fileName)
			bIsDefault = False

	# Remove Message first.
		if not bIsDefault: # Defaults have no message!
			BUPrint.Info("	-> Removing MESSAGE...")
			vChannel: discord.TextChannel = await self.AddNewLive_GetTargetChannel(p_opsData=p_opData)
			vMessage: discord.Message = await vChannel.fetch_message(p_opData.messageID)
			try:
				await vMessage.delete()
			except discord.Forbidden as error:
				BUPrint.LogErrorExc("Unable to remove File!", error)
				return False
			except discord.NotFound as error:
				BUPrint.LogErrorExc("No message found.", error)
				return False

			# Remove OpData from LiveOps list
			BUPrint.Info("	-> Removing OpData from LiveOps...")
			try:
				self.vLiveOps.remove(p_opData)
			except ValueError:
				BUPrint.Debug("	-> Couldn't remove OpData from LiveList.  Trying manual recursive find...")
				findData:OperationData
				for findData in self.vLiveOps:
					if findData.name == p_opData.name:
						if findData.date == p_opData.date:
							try:
								self.vLiveOps.remove(findData)
							except ValueError:
								BUPrint.Info("	-> Unable to remove OpData from Live list!")

			# Remove channel if empty
			chanMessages = [message async for message in vChannel.history()]
			if ( len(chanMessages) == 0 ):
				await vChannel.delete(reason="Auto removal of empty signup channel")
		
			else:
				# Check to see if other messages are from the bot, if not, remove the channel.
				message:discord.Message
				bBotPostFound = False
				for message in chanMessages:
					if message.author == self.vBotRef.user:
						bBotPostFound = True
						break

				if not bBotPostFound:
					await vChannel.delete(reason="Auto removal of empty signup channel")

	# Remove File
		BUPrint.Info("	-> Removing FILE...")
		try:
			os.remove(vFileToRemove)
		except FileNotFoundError:
			BUPrint.Debug("	-> File doesn't exist.  Manually removed?")
		except OSError:
			BUPrint.Info("Unable to remove file!")
			return False


	# Remove Autostart entry if op status is not started.
		if p_opData.status.value < OpsStatus.started.value:
			BUPrint.Debug("	-> Removing scheduled AutoStart.")
			try:
				autoComCog: OpCommander.autoCommander.AutoCommander = self.vBotRef.get_cog("AutoCommander")
				if autoComCog == None:
					BUPrint.Info("Unable to get Auto Commander Cog to remove an auto-start.")
					pass
				
				autoComCog.scheduler.remove_job(p_opData.messageID)
			except apscheduler.jobstores.base.JobLookupError as vError:
				BUPrint.LogErrorExc("Unable to remove scheduled job.  No Matching ID found.", vError)

		BUPrint.Info("	-> OPERATION REMOVED!")
		return True


	def FindOpData(self, p_opData:OperationData):
		"""
		# FIND OP DATA (Live only!)
		Returns a matching opData from the Live ops.
		If none are found, recursively searches through live ops and returns one with matching messageIDs.
		"""
		opData:OperationData
		if p_opData in self.vLiveOps:
			for opData in self.vLiveOps:
				if opData == p_opData:
					return opData
		else:
			for opData in self.vLiveOps:
				if opData.messageID == p_opData.messageID:
					return opData


	def GetDefaultOpsAsList():
		"""
		# GET DEFAULT OPS AS LIST:
		Expected use - App command auto-fill.
		Additional non-file entries are added to the returned list!

		## RETURN: 
		list(str)  Containing the names of saved default Ops.

		Does not use SELF to make it callable without constructing an instance.
		Does not use Async to allow it to be called in function parameters.
		Does not strip file extension!
		"""
		vDataFiles: list = ["Custom"]
		# Merge custom list with list of actual default files.		
		vDataFiles += OperationManager.GetDefaults()

		return vDataFiles

	
	def SaveToFile(p_opsData: OperationData):
		"""
		# SAVE TO FILE:
		Saves the Operation Data to file.
		DO NOT GetLock or Release, this function does that for you!
		
		## NOTE: If filename is empty, the OpData is saved as a default using its name!

		p_opsData: The ops data to save.

		## RETURN:
		True on success.  False on Failure.
		"""
		BUPrint.Info(f"Saving Operation Data to file. OpName|FileName: {p_opsData.name} | {p_opsData.fileName}")

		# temp_opToSave = copy.deepcopy(p_opsData)

		
		vFilePath = ""
		if p_opsData.fileName == "": # No filename, save as new default ops using Name.
			vFilePath += f"{botSettings.Directories.savedDefaultsDir}{p_opsData.name}.bin"
		else:
			vFilePath += f"{botSettings.Directories.liveOpsDir}{p_opsData.fileName}.bin"
		BUPrint.Debug(f"Saving file: {vFilePath}")
		try:
			botUtils.FilesAndFolders.GetLock(f"{vFilePath}.{botSettings.Directories.lockFileAffix}")
			with open(vFilePath, "wb") as vFile:
				pickle.dump(p_opsData, vFile)
				BUPrint.Info("File saved sucessfully!")
				botUtils.FilesAndFolders.ReleaseLock(f"{vFilePath}.{botSettings.Directories.lockFileAffix}")
		except:
			BUPrint.LogError("Failed to save Ops Data to file!")
			botUtils.FilesAndFolders.ReleaseLock(f"{vFilePath}.{botSettings.Directories.lockFileAffix}")
			return False
		
		# Save successful, return True.
		return True


	def LoadFromFile(p_opFilePath):
		"""
		# LOAD FROM FILE:
		Does not differentiate between Default or Live ops, it merely loads an OpData and returns the object!

		Creates and Releases lock files.

		p_opFilePath: The FULL filepath to load from.
		"""
		BUPrint.Debug(f"Loading Operation Data from file. Path:{p_opFilePath}")

		try:
			botUtils.FilesAndFolders.GetLock( f"{p_opFilePath}{botSettings.Directories.lockFileAffix}" )
			with open(p_opFilePath, "rb") as vFile:
				vLoadedOpData : OperationData = pickle.load(vFile)
			botUtils.FilesAndFolders.ReleaseLock(f"{p_opFilePath}{botSettings.Directories.lockFileAffix}")
			BUPrint.Info(f"Operation: {vLoadedOpData.fileName} loaded sucessfully!")
			return vLoadedOpData

		except EOFError as vError:
			BUPrint.LogErrorExc("Failed to open file. Check to ensure the file has not been overwritten and is not 0 bytes!", p_exception=vError)
			botUtils.FilesAndFolders.ReleaseLock(f"{p_opFilePath}{botSettings.Directories.lockFileAffix}")
			return None

		except Exception as vError:
			botUtils.FilesAndFolders.ReleaseLock(f"{p_opFilePath}{botSettings.Directories.lockFileAffix}")
			BUPrint.LogErrorExc("Failed to open file!", p_exception=vError)
			return None



	async def AddNewLiveOp(self, p_opData: OperationData):
		"""
		# ADD NEW LIVE OP:

		Posts a new LIVE operation.
		Adds the provided opData to the list of live ops.
		Saves the provided OpData to file.
		Creates a notification timer for the operation.

		## RETURN: 
		# True on fully succesful adding, False if a problem occured.
		"""
		BUPrint.Info(f"Adding a new LIVE operation: {p_opData.name}!")

		bCanContinue = await self.AddNewLive_PostOp(p_opData)
		if not bCanContinue: return False

		# Ops Posted, add OpData to list of LIVE data.
		self.vLiveOps.append(p_opData)

		# Save the Ops to file.
		bCanContinue = OperationManager.SaveToFile( self.vLiveOps[-1] )
		if not bCanContinue: return False

		# Add AutoStart		
		if p_opData.options.bAutoStart and botSettings.Commander.bAutoStartEnabled:
			self.AddNewAutoStart(p_opData)

		return True


	
	async def AddNewLive_PostOp(self, p_opData:OperationData):
		"""
		# POST OP:  
		A sub-function for AddNewLiveOp
		
		# Returns 
		TRUE if succesful send message
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
			p_opData.messageID = str(vMessage.id)
			p_opData.jumpURL = vMessage.jump_url

		except discord.HTTPException as vError:
			BUPrint.LogErrorExc("Message did not send due to HTTP Exception.", vError)
			return False
		except Exception as vError:
			BUPrint.LogErrorExc("Failed to send message!", vError)
			return False
		
		return True



	async def AddNewLive_GetTargetChannel(self, p_opsData: OperationData):
		"""
		# GET TARGET CHANNEL:

		A sub function to AddNewLiveOps, but usable elsewhere.

		## PARAMETERS: 
		p_opsData: the ops data used to get the target channel.

		## RETURN:
		Existing or newly created channel.  
		None on failure.
		"""
	
		BUPrint.Debug("	-> Obtaining target channel...")

		vGuild:discord.Guild = await botUtils.GetGuild(self.vBotRef)

		if vGuild == None:
			return None

		opsCategory = discord.utils.find(lambda items: items.name.lower() == botSettings.SignUps.signupCategory.lower(), vGuild.categories)

		if opsCategory == None:
			BUPrint.Info("SIGNUP CATEGORY NOT FOUND!  Check settings and ensure signupCategory matches the name of the category to be used; including capitalisation!")
			return None

		channel = None
		if p_opsData.targetChannel != "":
			channel = discord.utils.find(lambda items: items.name == p_opsData.targetChannel.lower().replace(" ", "-"), vGuild.text_channels)
			if channel != None:
				return channel
			else:
				BUPrint.Info(f"	-> No existing matching channel, creating channel: {p_opsData.targetChannel}")
				try:
					channel = await vGuild.create_text_channel(
					name=p_opsData.targetChannel,
					category=opsCategory 
					)
					return channel
				except discord.HTTPException as vError:
					BUPrint.LogErrorExc("Failed to create channel", vError)
					return None
		else:
			BUPrint.Debug(f"	-> Target Ops Channel not specified")
			channel = discord.utils.find(lambda items: items.name == p_opsData.name.lower().replace(" ", "-"), vGuild.text_channels)
			if channel == None:
				BUPrint.Debug("	-> No existing chanel, creating new one.")
				channel = await vGuild.create_text_channel(
								name=p_opsData.name,
								category=opsCategory
							)
			return channel 


	
	async def AddNewLive_GenerateEmbed(self, p_opsData: OperationData):
		"""
		# GENERATE EMBED
		A sub function to AddNewLiveOps

		Can also be used to regenerate an embed with updated information.

		## RETURNS 
		`discord.Embed` with information from `p_opsData`.
		"""
		BUPrint.Debug("	-> Generating Embed...")
		vTitleStr = f"{p_opsData.name.upper()} | {botUtils.DateFormatter.GetDiscordTime(p_opsData.date, botUtils.DateFormat.DateTimeLong)}"

		vEmbed = discord.Embed(colour=botUtils.Colours.openSignup.value,
								title=vTitleStr,
								description=f"Starts {botUtils.DateFormatter.GetDiscordTime(p_opsData.date, botUtils.DateFormat.Dynamic)}"
							)


		if p_opsData.status == OperationData.status.prestart:
			vEmbed.title += f"\n\n**{botMessages.OpsStartSoon}**"
			vEmbed.colour = botUtils.Colours.opsStarting.value

		if p_opsData.status == OperationData.status.started:
			vEmbed.title += f"\n\n**{botMessages.OpsStarted}**"
			vEmbed.colour = botUtils.Colours.opsStarted.value

		if p_opsData.status == OperationData.status.editing:
			vEmbed.title += f"\n\n**{botMessages.OpsBeingEdited}**"
			vEmbed.colour = botUtils.Colours.editing.value


		vEmbed.add_field(inline=False,
			name=f"About {p_opsData.name}",
			value=p_opsData.description
		)

		if p_opsData.managedBy != "":
			vEmbed.add_field(inline=False,
				name="Managed By:",
				value=self.GetManagedBy(p_opsData))

		if(p_opsData.customMessage != ""):
			vEmbed.add_field(inline=False,
				name="Additional Info:",
				value=p_opsData.customMessage
			)

		# Generate lists for roles:
		role: OpRoleData
		for role in p_opsData.roles:

			# Only display role if max position is not 0.
			if role.maxPositions != 0:

				vSignedUpUsers: str = ""
				if len(role.players) == 0:
					vSignedUpUsers = "-"

				# Compact View:
				if p_opsData.options.bUseCompact:
					vSignedUpUsers = f"Players: {len(role.players)}"

				else: # Normal View:
					for user in role.players:
						# Convert IDs to names for display
						vUser:discord.User = self.vBotRef.get_user(int(user))
						if vUser is not None:
							vSignedUpUsers += f"{vUser.mention}\n"
						else: # If not found, fetch non-cached.
							vUser = await self.vBotRef.fetch_user(int(user))
							if vUser is not None:
								vSignedUpUsers += f"{vUser.mention}\n"
							else: # User doesn't exist?
								botUtils.BotPrinter.LogError(f"User ID {user} is not found! Removing from data")
								role.players.remove(user)

				# Prepend role icon if not None:
				vRoleName = ""
				if role.roleIcon != "-" :
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
				vUser = self.vBotRef.get_user(int(reserve))
				vReserves += f"{vUser.mention}\n"
			vEmbed.add_field(name=f"{botData.settings.SignUps.reserveIcon} Reserves ({len(p_opsData.reserves)})", value=vReserves, inline=True )


		# Add Options into footer.
		if botSettings.SignUps.bShowOptsInFooter:
			vEmbed.set_footer(text=f"\n{p_opsData.GetOptionsAsStr()}")

		return vEmbed



	async def AddNewLive_GenerateView(self, p_opsData: OperationData):
		"""
		# GENERATE VIEW
		A subfunction of AddNewLive.
		Creates a view suitable for the current status of the operation and its settings.
		"""
		vView = discord.ui.View(timeout=None)
		vRoleSelector = OpsRoleSelector(p_opsData)
		vRoleSelector.UpdateOptions()

		btnReserve = OpsRoleReserve(p_opsData)

		vView.add_item( vRoleSelector )
		if p_opsData.options.bUseReserve:
			vView.add_item( btnReserve )
		
		if p_opsData.status == OpsStatus.started or p_opsData.status == OpsStatus.editing:
			vRoleSelector.disabled = True
			btnReserve.disabled = True

		return vView



	async def UpdateMessage(self, p_opData: OperationData):
		"""
		# UPDATE MESSAGE:
		The main function to call to post and update a message.
		
		## PARAMETERS:
		`p_opData`: The Opdata to regenerate a message with.
		"""
		BUPrint.Debug("Updating Op Message")
		try:
			vChannel: discord.TextChannel = await self.AddNewLive_GetTargetChannel(p_opsData=p_opData)
		except Exception as error:
			BUPrint.LogErrorExc("Failed to get a channel!", error)
			return
		
		try:
			vMessage: discord.Message = await vChannel.fetch_message(p_opData.messageID)
		
			# Update JumpURL if not set.
			if p_opData.jumpURL == "":
				p_opData.jumpURL = vMessage.jump_url

		except discord.NotFound as error:
				BUPrint.LogErrorExc("Message not found! Posting a new one...", error)
				if not await self.AddNewLive_PostOp(p_opData):
					BUPrint.Info("Failed to add new message. Possibly corrupt data? Removing this Ops file!")
					await self.RemoveOperation(p_opData)
				else:
					OperationManager.SaveToFile(p_opData)
				return

		except discord.Forbidden as error:
			BUPrint.LogErrorExc("Bot does not have correct privilages (post message!)", error)
			return
		except discord.HTTPException as error:
			BUPrint.LogErrorExc("Unable to retrieve the message!", error)
			return

		vNewEmbed = await self.AddNewLive_GenerateEmbed(p_opData)
		vView = await self.AddNewLive_GenerateView(p_opData)
		await vMessage.edit(embed=vNewEmbed, view=vView)


		if p_opData.status == OpsStatus.prestart:
			commander: OpCommander.commander.Commander = OperationManager.FindCommander(p_opData)
			if commander == None:
				BUPrint.Debug("Unable to get Commander for this event.")
				return

			await commander.GenerateInfo()



	def GetManagedBy(self, p_opData: OperationData):
		"""
		# GET MANAGED BY
		Returns a mentionable of a user specified to be the person running the Op.
		"""
		vGuild = self.vBotRef.get_guild(int(botSettings.BotSettings.discordGuild))
		
		vMember: discord.Member = discord.utils.find(lambda member: member.name == p_opData.managedBy, vGuild.members)
		if vMember == None:
			vMember: discord.Member = discord.utils.find(lambda member: member.display_name == p_opData.managedBy, vGuild.members)

		if vMember != None:
			return vMember.mention
		
		return None


	def RemoveUser(p_opData:OperationData, p_userToRemove:str):
		"""
		# REMOVE USER:
		Iterates over all roles (including reserve) and removes the player ID if present.
		"""
		if p_userToRemove in p_opData.reserves:
			p_opData.reserves.remove(p_userToRemove)
		
		for role in p_opData.roles:
			if p_userToRemove in role.players:
				role.players.remove(p_userToRemove)
				return


	def FindCommander(p_opdata:OperationData):
		"""
		# FIND COMMANDER
		Will iterate through the live commanders for a matching opdata and return the found commander.
		"""
		if len(OperationManager.vLiveCommanders):
			commander: OpCommander.commander.Commander
			
			for commander in OperationManager.vLiveCommanders:
				if commander.vOpData.messageID == p_opdata.messageID:
					return commander
			
			BUPrint.Debug("No matching commander found.")
			return None

		else:
			BUPrint.Debug("No live commanders.")

# SCHEDULER RELATED FUNCTIONS
	def RefreshAutostarts(self):
		"""
		# REFRESH AUTO-STARTS
		Clears out the currently scheduled auto-starts, then uses the list of OpData's in the OperationManager to re-create the scheduled starts.
		"""
		if not botSettings.Commander.bAutoStartEnabled:
			BUPrint.Debug("Global Autostart setting is disabled. Not refreshing auto-starts.")
			return

		autoCommanderCog: OpCommander.autoCommander.AutoCommander = self.vBotRef.get_cog("AutoCommander")
		if autoCommanderCog == None:
			BUPrint.Info("Auto Commander Cog not found. Unable to continue.")

		autoCommanderCog.scheduler.remove_all_jobs()

		opData : OperationData
		for opData in self.vLiveOps:
			self.AddNewAutoStart(opData)


	def ReconfigureAutoStart(self, p_opData: OperationData):
		"""
		# RECONFIGURE AUTO START

		Used after an event has been edited, re-configures the scheduled job with the updated time.
		## RETURNS
		True- Success.
		False- Failure.
		"""

		if not botSettings.Commander.bAutoStartEnabled:
			BUPrint.Debug("Autostart is globally disabled.")
			return

		startTime = p_opData.date - dateutil.relativedelta.relativedelta(minutes=botSettings.Commander.autoPrestart + 5)

		autoCommanderCog: OpCommander.autoCommander.AutoCommander = self.vBotRef.get_cog("AutoCommander")
		if autoCommanderCog == None:
			BUPrint.Info("Auto Commander Cog not found. Unable to continue.")


		if not p_opData.options.bAutoStart:
			vJob = autoCommanderCog.scheduler.get_job(p_opData.messageID)
			if vJob != None:
				try:
					autoCommanderCog.scheduler.remove_job(p_opData.messageID)
					return True
				except apscheduler.jobstores.base.JobLookupError as vError:
					BUPrint.LogErrorExc("Unable to remove scheduled job", vError)
					return False

		BUPrint.Info(f"Rescheduling autostart of {p_opData.name} to: {startTime}")

		try:
			autoCommanderCog.scheduler.reschedule_job(p_opData.messageID, None, "date", run_date=startTime)
			return True

		except apscheduler.jobstores.base.JobLookupError:
			BUPrint.Info("Unable to reschedule autostart job: No Matching ID found. Creating new autostart entry")
			self.AddNewAutoStart(p_opData)
			return True


	def AddNewAutoStart(self, p_opdata: OperationData):
		"""
		# ADD NEW AUTO START

		Adds an Operation to the scheduler to be automatically started.
		"""

		if not botSettings.Commander.bAutoStartEnabled:
			BUPrint.Debug("Auto-Start is globally disabled.")
			return

		if not p_opdata.options.bAutoStart:
			BUPrint.Debug(f"Operation {p_opdata.fileName} has auto-start disabled. Skipping")
			return


		autoCommanderCog: OpCommander.autoCommander.AutoCommander = self.vBotRef.get_cog("AutoCommander")
		if autoCommanderCog == None:
			BUPrint.Info("Auto Commander Cog not found. Unable to continue.")


		startTime = p_opdata.date - dateutil.relativedelta.relativedelta(minutes=botSettings.Commander.autoPrestart + 5)

		BUPrint.Info(f"Adding auto-start entry for: {p_opdata.fileName}, using message ID: {p_opdata.messageID} Scheduled for: {startTime}")

		autoCommanderCog.scheduler.add_job( OpCommander.commander.StartCommander, "date", run_date=startTime, args=[p_opdata], id=p_opdata.messageID )



##################################################################
# MESSAGES	

class OpsRoleSelector(discord.ui.Select):
	def __init__(self, p_opsData: OperationData):
		defaultOption = discord.SelectOption(label="Default", value="Default")
		self.vOpsData = p_opsData
		super().__init__(placeholder="Choose a role...", options=[defaultOption])

	async def callback(self, pInteraction: discord.Interaction):
		botUtils.BotPrinter.Debug(f"User {pInteraction.user.name} has signed up to {self.vOpsData.fileName} with role: {self.values[0]}")
		vOpMan = OperationManager()		
		vSelectedRole: OpRoleData = None
		role: OpRoleData
		for role in self.vOpsData.roles:
			if self.values[0] == role.roleName:
				vSelectedRole = role

		if vSelectedRole == None:
			# Player selected RESIGN
			OperationManager.RemoveUser(p_opData=self.vOpsData, p_userToRemove=pInteraction.user.id)
			OperationManager.SaveToFile(self.vOpsData)
			await vOpMan.UpdateMessage(p_opData=self.vOpsData)
			await pInteraction.response.send_message(f"You have resigned from {self.vOpsData.name}({botUtils.DateFormatter.GetDiscordTime(self.vOpsData.date, botUtils.DateFormat.DateShorthand)})!", ephemeral=True)
			# No need to continue further.
			return


		if pInteraction.user.id not in vSelectedRole.players:
			OperationManager.RemoveUser(p_opData=self.vOpsData, p_userToRemove=pInteraction.user.id)
			vSelectedRole.players.append( pInteraction.user.id )
			await vOpMan.UpdateMessage(p_opData=self.vOpsData)
			OperationManager.SaveToFile(self.vOpsData)	
			await pInteraction.response.send_message(f"You have signed up as {self.values[0]} for {self.vOpsData.name} on {botUtils.DateFormatter.GetDiscordTime(self.vOpsData.date, botUtils.DateFormat.DateShorthand)}!", ephemeral=True)
		else:
			await pInteraction.response.send_message(f"You're already signed up as {self.values[0]} for {self.vOpsData.name} on {botUtils.DateFormatter.GetDiscordTime(self.vOpsData.date, botUtils.DateFormat.DateShorthand)}!", ephemeral=True)

	
	
	def UpdateOptions(self):
		self.options.clear()
		role: OpRoleData

		# Always add a default used to resign players.
		self.add_option(label="Resign", value="Resign", emoji=botSettings.SignUps.resignIcon)
		

		for role in self.vOpsData.roles:
			if( len(role.players) < int(role.maxPositions) and int(role.maxPositions) != 0 ):
				# To ensure no errors, only use emoji if its specified

				if role.roleIcon == "-":
					self.add_option(label=role.roleName, value=role.roleName)
				else:
					botUtils.BotPrinter.Debug(f"Icon ({role.roleIcon}) specified, using Icon...")
					self.add_option(label=role.roleName, value=role.roleName, emoji=role.roleIcon)



class OpsRoleReserve(discord.ui.Button):
	def __init__(self, p_opsData : OperationData):
		self.vOpsData = p_opsData
		super().__init__(label="Reserve", emoji=botSettings.SignUps.reserveIcon)

	async def callback(self, pInteraction: discord.Interaction):
		
		if pInteraction.user.id not in self.vOpsData.reserves:
			await pInteraction.response.send_message(content=f"You have signed up as a reserve for {self.vOpsData.name} on {botUtils.DateFormatter.GetDiscordTime(self.vOpsData.date, botUtils.DateFormat.DateShorthand)}!", ephemeral=True)
			OperationManager.RemoveUser(self.vOpsData, pInteraction.user.id)
			self.vOpsData.reserves.append(pInteraction.user.id)

			vOpMan = OperationManager()
			await vOpMan.UpdateMessage(self.vOpsData)
		else:
			await pInteraction.response.send_message(f"You have already signed up as a reserve for {self.vOpsData.name} on {botUtils.DateFormatter.GetDiscordTime(self.vOpsData.date, botUtils.DateFormat.DateShorthand)}!", ephemeral=True)





#########################################################################################
# EDITOR


class OpsEditor(discord.ui.View):
	def __init__(self, pBot: commands.Bot, pOpsData: OperationData):
		self.vBot = pBot
		self.vOpsData = pOpsData # Original data, not edited.
		# Used to check if file renaming needs to occur.
		self.vOldName = pOpsData.name
		self.vOldDate = pOpsData.date
		self.vOldFileName = pOpsData.fileName
		self.vEditorMsg :discord.Message = None

		BUPrint.Info("Ops Editor Instantiated")
		super().__init__(timeout=None)
		helpBtn = btnHelp()
		self.add_item(helpBtn)

# # # # # # Edit Buttons
	editButtonStyle = discord.ButtonStyle.grey
	# Edit Date:
	@discord.ui.button( label="Edit Date/Time",
						style=editButtonStyle, 
						custom_id="EditDate",
						row=0)
	async def btnEditDate(self, pInteraction: discord.Interaction, pButton: discord.ui.button):
		vEditModal = editDates.EditDates(p_opData=self.vOpsData)
		vEditModal.custom_id="EditDateModal"
		await pInteraction.response.send_modal( vEditModal )
	
	# Edit Info
	@discord.ui.button(
						style=editButtonStyle, 
						label="Edit Op Info",
						custom_id="EditInfo",
						row=0)
	async def btnEditInfo(self, pInteraction: discord.Interaction, pButton: discord.ui.button):
		vEditModal = editInfo.EditInfo(p_OpData=self.vOpsData)
		vEditModal.custom_id="EditInfoModal"
		await pInteraction.response.send_modal( vEditModal )

	# Edit Roles
	@discord.ui.button(
						style=editButtonStyle, 
						label="Edit Roles",
						custom_id="EditRoles",
						row=0)
	async def btnEditRoles(self, pInteraction: discord.Interaction, pButton: discord.ui.button):
		vEditModal = editRoles.EditRoles(p_opData=self.vOpsData)
		vEditModal.custom_id="EditRolesModal"
		await pInteraction.response.send_modal( vEditModal )


	# Edit Channels
	@discord.ui.button(
						style=editButtonStyle, 
						label="Edit Channels",
						custom_id="EditChannels",
						row=0)
	async def btnEditChannels(self, pInteraction: discord.Interaction, pButton: discord.ui.button):
		vEditModal = editChannels.EditChannels(p_OpData=self.vOpsData)
		vEditModal.custom_id="EditChannelsModal"
		await pInteraction.response.send_modal( vEditModal )
	
# # # # # # # Confirm/Save buttons:
	@discord.ui.button(
						style=discord.ButtonStyle.green, 
						label="Apply/Send",
						custom_id="EditorApply",
						emoji="📨",
						row=3)
	async def btnApplyChanges(self, pInteraction: discord.Interaction, pButton: discord.ui.button):
		vOpManager = OperationManager()
		
		if self.vOpsData.messageID == "":
			BUPrint.Info("Adding new Live Op...")
			self.vOpsData.GenerateFileName()
			bSucsessfulOp = await vOpManager.AddNewLiveOp(self.vOpsData)
			
			if bSucsessfulOp:
				await pInteraction.response.send_message("***SUCCESS!***\nYou may now dismiss the editor.", ephemeral=True)
				OperationManager.SaveToFile(self.vOpsData)
				BUPrint.Debug(f"	-> Message ID of Ops Editor opdata after send: {self.vOpsData.messageID}")
			else:
				await pInteraction.response.send_message("An error occured when posting the message.  Check console for more information.\n\nTry again, or close the editor.", ephemeral=True)

		else:
			if not self.vOpsData.options.bUseReserve:
				self.vOpsData.reserves.clear()

			if self.vOpsData.name != self.vOldName or self.vOpsData.date != self.vOldDate:
				vOriginalData = OperationManager.LoadFromFile( botUtils.FilesAndFolders.GetOpFullPath(self.vOpsData.fileName) )
				await vOpManager.RemoveOperation(vOriginalData)


				self.vOpsData.GenerateFileName()
				self.vOpsData.status = OpsStatus.open
				await vOpManager.AddNewLiveOp(self.vOpsData)
				
				await pInteraction.response.send_message(f"Operation data for {self.vOldName} has been recreated with updated information", ephemeral=True)

			else:
				BUPrint.Info(f"Saving updated data for {self.vOpsData.name}")

				self.vOpsData.status = OperationData.status.open
				OperationManager.SaveToFile(self.vOpsData)
				await pInteraction.response.send_message(f"Operation data for {self.vOpsData.name} saved! Updating signup message...\nMake sure to `Finish` before you dismiss the editor!", ephemeral=True)
				await vOpManager.UpdateMessage(self.vOpsData)

		try:
			await self.vEditorMsg.delete()
		except discord.errors.NotFound:
			BUPrint.Info("Unable to delete Op Editor message; most likely due to the channel being removed. Safe to ignore.")



	@discord.ui.button( 
						style=discord.ButtonStyle.primary, 
						label="New Default",
						custom_id="EditorNewDefault",
						emoji="💾",
						row=3)
	async def btnNewDefault(self, pInteraction: discord.Interaction, pButton: discord.ui.button):
		BUPrint.Info(f"Saving a new default! {self.vOpsData.name}")
		# Set status of Ops back to OPEN.
		self.vOpsData.status = OpsStatus.open

		vOldFilename = self.vOpsData.fileName
		# Ensure fileName is empty so its saved as a default
		self.vOpsData.fileName = ""

		# Ensure roles is empty. 
		vOrigRoles = self.vOpsData.roles
		vOrigReserves = self.vOpsData.reserves

		role:OpRoleData
		for role in self.vOpsData.roles:
			role.players.clear()
		self.vOpsData.reserves.clear()

		# Save File
		OperationManager.SaveToFile(self.vOpsData)

		# Check old name and rename if needed.
		bWasRenamed = False
		if self.vOldName != self.vOpsData.name and self.vOldName != "":
			try:
				vOriginal = f"{botSettings.Directories.savedDefaultsDir}{self.vOldName}.bin"
				vNew = f"{botSettings.Directories.savedDefaultsDir}{self.vOpsData.name}.bin"

				if os.path.exists( vOriginal ):
					os.rename( vOriginal, vNew )
					bWasRenamed = True

				self.vOldName = self.vOpsData.name

			except OSError as vError:
				BUPrint.LogErrorExc(f"Unable to rename Saved Default from {vOriginal} to {vNew}", vError)


		BUPrint.Debug("	-> Saved!")

		# Re-Add old data to Op Data.
		self.vOpsData.roles = vOrigRoles
		self.vOpsData.reserves = vOrigReserves
		self.vOpsData.fileName = vOldFilename
		
		if bWasRenamed:
			await pInteraction.response.send_message(f"Saved default: {self.vOpsData.name}\nOriginal Op was renamed:\nFrom:{vOriginal}\nTo:{vNew}")
		else:
			await pInteraction.response.send_message(f"Added new default: {self.vOpsData.name}!", ephemeral=True)

# # # # # # DELETE BUTTON
	@discord.ui.button(
						style=discord.ButtonStyle.danger,
						label="Delete",
						custom_id="EditorDelete",
						emoji="⚠️",
						row=3)
	async def btnDelete(self, pInteraction:discord.Interaction, pButton: discord.ui.Button):
		BUPrint.Info("Deleting Operation!")
		vOpMan = OperationManager()
		await vOpMan.RemoveOperation(self.vOpsData)
		await pInteraction.response.send_message("Operation was removed!", ephemeral=True)


# # # # # # CLOSE BUTTON
	@discord.ui.button(
						label="Close/Cancel",
						style=discord.ButtonStyle.success,
						emoji="🔓",
						row=4)
	async def btnFinish(self, pInteraction:discord.Interaction, pButton: discord.ui.Button):		
		if self.vOpsData.messageID != "":
			vOpMan = OperationManager()

			vOriginalData = OperationManager.LoadFromFile( botUtils.FilesAndFolders.GetOpFullPath( self.vOpsData.fileName ) )
			vOriginalData.status = OpsStatus.open
			OperationManager.SaveToFile(vOriginalData)
			await vOpMan.UpdateMessage(vOriginalData)

		await pInteraction.response.send_message("You may now dismiss the editor if it hasn't automatically closed.", ephemeral=True)
		await self.vEditorMsg.delete()


# # # # # # HELP BUTTON
class btnHelp(discord.ui.Button):
	def __init__(self):
		super().__init__(
			label="Help",
			style=discord.ButtonStyle.link,
			url="https://github.com/LCWilliams/planetside-discord-bot/wiki/Ops-Editor",
			emoji="❓",
			row=3
		)


