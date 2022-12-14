# Ops Manager: Manages creating, editing and removing of Ops.
# For live ops being started, see OpsCommander

import os
import datetime
import pickle

import discord
from discord.ext import commands
from discord import app_commands

from botData import settings as botSettings
import botData.operations as OpData
import botUtils
from botUtils import BotPrinter as BUPrint
# import botData
from botModals.opsManagerModals import *


class Operations(commands.GroupCog):
	def __init__(self, p_bot):
		super().__init__()
		self.bot : commands.Bot = p_bot
		BUPrint.Info("COG: Operations loaded.")

	@app_commands.command(name="add", description="Add a new Ops event")
	@app_commands.describe(optype="Type of Ops to create. If this doesn't match an existing option, defaults to 'custom'!",
							edit="Open Ops Editor before posting this event (Always true if 'Custom')",
							pDay="The day this ops will run.",
							pMonth="The month this ops will run.",
							pHour="The HOUR (24) the ops will run in.",
							pMinute="The MINUTE within an hour the ops starts on",
							pYear="Optional.\nThe Year the ops should run.",
							pArguments="Optional.\nAdditional arguments to control the op behaviour.")
	@app_commands.rename(pDay="day", pMonth="month", pHour="hour", pMinute="minute", pYear="year", pArguments="arguments")
	@app_commands.checks.has_any_role('CO','Captain','Lieutenant','Sergeant')
	async def addopsevent (self, pInteraction: discord.Interaction, 
		optype: str,
		edit: bool, 
		pDay: app_commands.Range[int, 0, 31], 
		pMonth: app_commands.Range[int, 1, 12], 
		pHour: app_commands.Range[int, 1, 23], 
		pMinute:app_commands.Range[int, 0, 59],
		pYear: int  = datetime.datetime.now().year,
		pArguments: str = ""
	):
		# HARDCODED ROLE USEAGE:
		if not await botUtils.UserHasCommandPerms(pInteraction.user, (botSettings.CommandRestrictionLevels.level1), pInteraction):
			return

		botUtils.BotPrinter.Debug(f"Adding new event ({optype}).  Edit after posting: {edit}")
		vDate = datetime.datetime(
			year=pYear,
			month=pMonth,
			day=pDay,
			hour=pHour, minute=pMinute)

		vOpTypeStr = str(optype).replace("OpsType.", "")


		newOpsData : OpData.OperationData = OpData.OperationData()
		vOpManager = OperationManager()
		newOpsData.date = vDate

		if vOpTypeStr not in OperationManager.GetDefaults():
			# USER IS USING A NON-DEFAULT/CUSTOM
			newOpsData.status = OpData.OpsStatus.editing

			vEditor: OpsEditor = OpsEditor(pBot=self.bot, pOpsData=newOpsData)

			botUtils.BotPrinter.Debug(f"Editor: {vEditor}, Type: {type(vEditor)}")

			await pInteraction.response.send_message("**OPS EDITOR**", view=vEditor, ephemeral=True)
			return

		else:
			# MAKE SURE TO SWAP OP DATA FILE LATER, ELSE YOU WILL OVERWRITE THE SAVED DEFAULT
			vFilePath = f"{botSettings.Directories.savedDefaultsDir}{optype}"
			newOpsData = OperationManager.LoadFromFile(vFilePath)

			if newOpsData == None:
				botUtils.FilesAndFolders.DeleteCorruptFile(vFilePath)
				await pInteraction.response.send_message("The default you tried to use is corrupt and has been removed.  Please try again using another Ops, or create a new default.", ephemeral=True)
				return

			# Update date & args to the one given by the command
			newOpsData.date = vDate
			newOpsData.arguments += pArguments

			if(edit):
				vEditor = OpsEditor(pBot=self.bot, pOpsData=newOpsData)
				await pInteraction.response.send_message(f"**Editing OpData for** *{optype}*", view=vEditor, ephemeral=True)
				# vEditor.vMessage = await pInteraction.original_response()

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
		vLiveOpData:OpData.OperationData = OperationManager.LoadFromFile( botUtils.FilesAndFolders.GetOpFullPath(pOpsToEdit))

		if vLiveOpData != None:
			vEditor = OpsEditor(pBot=self.bot, pOpsData=vLiveOpData)
			await pInteraction.response.send_message(f"**Editing OpData for** *{vLiveOpData.fileName}*", view=vEditor, ephemeral=True)
		else:
			botUtils.FilesAndFolders.DeleteCorruptFile( botUtils.FilesAndFolders.GetOpFullPath(pOpsToEdit) )
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
	vBotRef: commands.Bot
	
	def __init__(self):
		# Only update lists on first object instantiation (or there's no ops and it occurs each time):
		if len(self.vLiveOps) == 0:
			self.LoadOps()
		BUPrint.Info(f"Operation Manager has been instantited. Live Ops Data: {len(self.vLiveOps)}")

	async def RefreshOps(self):
		"""
		# REFRESH OPS

		Recursively 'updates' all active live Ops so that views are refreshed and usable again.
		"""
		vOpData : OpData.OperationData
		for vOpData in self.vLiveOps:
			await self.UpdateMessage(vOpData)
			BUPrint.Info(f"Refreshing {vOpData}\n")

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
			vFile: OpData.OperationData = OperationManager.LoadFromFile(vFullPath)
			if vFile is not None:
				self.vLiveOps.append(OperationManager.LoadFromFile(vFullPath))



	def GetDefaults():
		"""
		# GET DEFAULTS:
		Get the default Ops filenames.
		
		## RETURN : list(str)
		"""
		return botUtils.FilesAndFolders.GetFiles(botSettings.Directories.savedDefaultsDir, ".bin")


	async def RemoveOperation(self, p_opData: OpData.OperationData):
		"""
		# REMOVE OPERATION:

		p_opData: The opdata the user wishes to remove.

		## NOTE: Call from an instance.

		Works for both LIVE and DEFAULT ops; it behaves akin to saving a new Operation- if there's no specified fileName, this will remove a DEFAULT, else remove a Live Ops (and its posting)

		## RETURN: Bool
		True : Op Removed (or wasn't a file to begin with.)
		False: Failed to remove.
		"""
		BUPrint.Info(f"Removing Operation: {p_opData}")
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
				findData:OpData.OperationData
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

	# Remove File
		BUPrint.Info("	-> Removing FILE...")
		try:
			os.remove(vFileToRemove)
		except FileNotFoundError:
			BUPrint.Debug("	-> File doesn't exist.  Manually removed?")
		except OSError:
			BUPrint.Info("Unable to remove file!")
			return False


		BUPrint.Info("	-> OPERATION REMOVED!")
		return True



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


	def createOpsFolder():
		if (not os.path.exists( botSettings.Directories.liveOpsDir ) ):
			try:
				os.makedirs( botSettings.Directories.liveOpsDir )
			except:
				botUtils.BotPrinter.LogError("Failed to create folder for Ops data!")

	
	def SaveToFile(p_opsData: OpData.OperationData):
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
		# LOAD FROM FILE:
		Does not differentiate between Default or Live ops, it merely loads an OpData and returns the object!

		Creates and Releases lock files.

		p_opFilePath: The FULL filepath to load from.
		"""
		BUPrint.Debug(f"Loading Operation Data from file. Path:{p_opFilePath}")

		try:
			botUtils.FilesAndFolders.GetLock( f"{p_opFilePath}{botSettings.Directories.lockFileAffix}" )
			with open(p_opFilePath, "rb") as vFile:
				vLoadedOpData : OpData.OperationData = pickle.load(vFile)
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


	async def AddNewLiveOp(self, p_opData: OpData.OperationData):
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

		# Create notification here...

		return True


	async def AddNewLive_PostOp(self, p_opData:OpData.OperationData):
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
			p_opData.messageID = vMessage.id
		except discord.HTTPException as vError:
			BUPrint.LogErrorExc("Message did not send due to HTTP Exception.", vError)
			return False
		except Exception as vError:
			BUPrint.LogErrorExc("Failed to send message!", vError)
			return False
		
		return True


	async def AddNewLive_GetTargetChannel(self, p_opsData: OpData.OperationData):
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

		vGuild = self.vBotRef.guilds[0]
		if vGuild is None:
			BUPrint.Debug("	-> Guild is none, trying fetch instead.")
			# Try again using non-cache "fetch":
			vGuild = await self.vBotRef.fetch_guild(botSettings.BotSettings.discordGuild)
			if vGuild is None:
				botUtils.BotPrinter.LogError("Failed to find guild for getting Ops Channel!")
				return None
			BUPrint.Debug("	-> Guild obtained.")
		opsCategory = discord.utils.find(lambda items: items.name == botSettings.SignUps.signupCategory, vGuild.categories)

		if opsCategory == None:
			BUPrint.Info("SIGNUP CATEGORY NOT FOUND!  Check settings and ensure signupCategory matches the name of the category to be used; including capitalisation!")
			return None

		argument: str
		BUPrint.Debug("	-> Parsing arguments...")
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


	async def AddNewLive_GenerateEmbed(self, p_opsData: OpData.OperationData):
		"""
		# GENERATE EMBED
		A sub function to AddNewLiveOps

		Can also be used to regenerate an embed with updated information.

		## RETURNS 
		discord.Embed with information from p_opsData.
		"""
		BUPrint.Debug("	-> Generating Embed...")
		vTitleStr = f"{p_opsData.name.upper()} | {botUtils.DateFormatter.GetDiscordTime(p_opsData.date, botUtils.DateFormat.DateTimeLong)}"

		vEmbed = discord.Embed(colour=botUtils.Colours.openSignup.value,
								title=vTitleStr,
								description=f"Starts {botUtils.DateFormatter.GetDiscordTime(p_opsData.date, botUtils.DateFormat.Dynamic)}"
							)


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
		role: OpData.OpRoleData
		for role in p_opsData.roles:
			vSignedUpUsers: str = ""
			if len(role.players) == 0:
				vSignedUpUsers = "-"
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
				vUser = self.vBotRef.get_user(int(reserve))
				vReserves += f"{vUser.mention}\n"
			vEmbed.add_field(name=f"Reserves ({len(p_opsData.reserves)})", value=vReserves, inline=True )

		return vEmbed


	async def AddNewLive_GenerateView(self, p_opsData: OpData.OperationData):
		vView = discord.ui.View(timeout=None)
		vRoleSelector = OpsRoleSelector(p_opsData)
		vRoleSelector.UpdateOptions()

		vView.add_item( vRoleSelector )
		vView.add_item(OpsRoleReserve(p_opsData))
		return vView


	async def UpdateMessage(self, p_opData: OpData.OperationData):
		"""
		# UPDATE MESSAGE
		
		## PARAMETERS:
		p_opData: The Opdata to regenerate a message with.

		## RETURN: None
		"""
		BUPrint.Debug("Updating Op Message")
		try:
			vChannel: discord.TextChannel = await self.AddNewLive_GetTargetChannel(p_opsData=p_opData)
		except Exception as error:
			BUPrint.LogErrorExc("Failed to get a channel!", error)
			return
		
		try:
			vMessage: discord.Message = await vChannel.fetch_message(p_opData.messageID)
		except discord.NotFound as error:
				BUPrint.LogErrorExc("Message not found! Posting a new one...", error)
				if not await self.AddNewLive_PostOp(p_opData):
					BUPrint.Info("Failed to add new message. Possibly corrupt data? Removing this Ops file!")
					await self.RemoveOperation(p_opData)
				else:
					OperationManager.SaveToFile(p_opData)
				return

		except discord.Forbidden as error:
			BUPrint.LogErrorExc("Bot does not have correct privilages (post message!", error)
			return
		except discord.HTTPException as error:
			BUPrint.LogErrorExc("Unable to retrieve the message!", error)
			return

		vNewEmbed = await self.AddNewLive_GenerateEmbed(p_opData)
		vView = await self.AddNewLive_GenerateView(p_opData)
		await vMessage.edit(embed=vNewEmbed, view=vView)

	def GetManagedBy(self, p_opData: OpData.OperationData):
		"""
		# GET MANAGED BY
		Returns a mentionable of a user specified to be the person running the Op.
		"""
		vMember: discord.Member = discord.utils.find(lambda member: member.name == p_opData.managedBy, self.vBotRef.guilds[0].members)
		if vMember != None:
			return vMember.mention
		
		return None


	def RemoveUser(p_opData:OpData.OperationData, p_userToRemove:str):
		"""
		# REMOVE USER:
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
	def __init__(self, p_opsData: OpData.OperationData):
		defaultOption = discord.SelectOption(label="Default", value="Default")
		self.vOpsData = p_opsData
		super().__init__(placeholder="Choose a role...", options=[defaultOption])

	async def callback(self, pInteraction: discord.Interaction):
		botUtils.BotPrinter.Debug(f"User {pInteraction.user.name} has signed up to {self.vOpsData.fileName} with role: {self.values[0]}")
		vOpMan = OperationManager()		
		vSelectedRole: OpData.OpRoleData = None
		role: OpData.OpRoleData
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
		role: OpData.OpRoleData

		# Always add a default used to resign players.
		self.add_option(label="Resign", value="Resign", emoji=botSettings.SignUps.resignIcon)

		for role in self.vOpsData.roles:
			if( len(role.players) < int(role.maxPositions) or int(role.maxPositions) <= 0 ):
				# To ensure no errors, only use emoji if its specified

				if role.roleIcon == "-":
					self.add_option(label=role.roleName, value=role.roleName)
				else:
					botUtils.BotPrinter.Debug(f"Icon ({role.roleIcon}) specified, using Icon...")
					self.add_option(label=role.roleName, value=role.roleName, emoji=role.roleIcon)



class OpsRoleReserve(discord.ui.Button):
	def __init__(self, p_opsData : OpData.OperationData):
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
	def __init__(self, pBot: commands.Bot, pOpsData: OpData.OperationData):
		self.vBot = pBot
		self.vOpsData = pOpsData # Original data, not edited.
		# self.EditedData = pOpsData # Edited data, applied and saved.
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
						row=4)
	async def btnApplyChanges(self, pInteraction: discord.Interaction, pButton: discord.ui.button):
		self.vOpsData.GenerateFileName()
		vOpManager = OperationManager()
		if self.vOpsData.messageID == "":
			BUPrint.Info("Adding new Live Op...")
			bSucsessfulOp = await vOpManager.AddNewLiveOp(self.vOpsData)
			
			if bSucsessfulOp:
				await pInteraction.response.send_message("***SUCCESS!***\nYou can now dismiss the editor if you're done.", ephemeral=True)
				OperationManager.SaveToFile(self.vOpsData)
				BUPrint.Debug(f"	-> Message ID of Ops Editor opdata after send: {self.vOpsData.messageID}")
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
						emoji="💾",
						row=4)
	async def btnNewDefault(self, pInteraction: discord.Interaction, pButton: discord.ui.button):
		BUPrint.Info(f"Saving a new default! {self.vOpsData.name}")
		# Set status of Ops back to OPEN.
		self.vOpsData.status = OpData.OpsStatus.open

		vOldFilename = self.vOpsData.fileName
		# Ensure fileName is empty so its saved as a default
		self.vOpsData.fileName = ""
		OperationManager.SaveToFile(self.vOpsData)
		BUPrint.Debug("	-> Saved!")

		self.vOpsData.fileName = vOldFilename

		await pInteraction.response.send_message(f"Added new default: {self.vOpsData.name}!", ephemeral=True)

# # # # # # DELETE BUTTON
	@discord.ui.button(
						style=discord.ButtonStyle.danger,
						label="Delete",
						custom_id="EditorDelete",
						emoji="⚠️",
						row=4)
	async def btnDelete(self, pInteraction:discord.Interaction, pButton: discord.ui.Button):
		BUPrint.Info("Deleting Operation!")
		vOpMan = OperationManager()
		await vOpMan.RemoveOperation(self.vOpsData)
		await pInteraction.response.send_message("Operation was removed!", ephemeral=True)

class btnHelp(discord.ui.Button):
	def __init__(self):
		super().__init__(
			label="Help",
			style=discord.ButtonStyle.link,
			url="https://github.com/LCWilliams/planetside-discord-bot/wiki/Ops-Editor",
			emoji="❓",
			row=4
		)