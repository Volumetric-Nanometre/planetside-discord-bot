import os
import sys
import datetime
import time
from botData.settings import BotSettings, CommandRestrictionLevels, Directories, Roles, Messages
import botData.utilityData as UtilityData
import traceback
import discord
from discord.ext import commands
# from botData import OperationData



class Singleton(type):
	"""
	# SINGLETON

	Used to ensure singletons via metaclasses.
	"""
	_instances = {}
	def __call__(self, *arguments, **keywords):
		if self not in self._instances:
			self._instances[self] = super().__call__(*arguments, **keywords)
		return self._instances[self]


class BotPrinter():
	"""
	BOT PRINTER
	Convenience class containing functions to print various information to console (and/or file).
	"""

	@staticmethod
	def Debug(p_string):
		"""
		DEBUG
		Prints a pre-formatted message to console IF ShowDebug is enabled.
		"""
		if(BotSettings.bDebugEnabled):
			print(f"{UtilityData.ConsoleStyles.timeStyle}[{datetime.datetime.now()}] {p_string}{UtilityData.ConsoleStyles.reset} ")


	@staticmethod
	def Info(p_string):
		"""
		INFO
		Similar to debug, but doesn't depend on ShowDebug to show.
		Should ideally only be used for displaying status as to not flood the console.
		"""
		print(f"{UtilityData.ConsoleStyles.timeStyle}[{datetime.datetime.now()}]{UtilityData.ConsoleStyles.reset} {p_string}")


	@staticmethod
	def LogError(p_string:str, p_titleStr:str = ""):
		"""
		LOG ERROR
		Displays an error to console.

		p_titleString: String shown in alternate colour.
		p_string : The message to show.
		"""
		print(f"{UtilityData.ConsoleStyles.timeStyle}[{datetime.datetime.now()}]{UtilityData.ConsoleStyles.reset} {UtilityData.ConsoleStyles.colourWarn}ERROR | {p_titleStr}{UtilityData.ConsoleStyles.reset} {UtilityData.ConsoleStyles.ColourInfo}{p_string}{UtilityData.ConsoleStyles.reset}", file=sys.stderr)


	@staticmethod
	def LogErrorExc(p_string: str, p_exception: Exception):
		"""
		Same as LOG ERROR, with addition of Exception parameter.
		"""
		print(f"{UtilityData.ConsoleStyles.timeStyle}[{datetime.datetime.now()}]{UtilityData.ConsoleStyles.reset} {UtilityData.ConsoleStyles.colourWarn}ERROR:{UtilityData.ConsoleStyles.reset} {UtilityData.ConsoleStyles.ColourInfo}{p_string} | {UtilityData.ConsoleStyles.reset}{traceback.print_tb(p_exception.with_traceback())}", file=sys.stderr)





# Used to clear up repeating code
def GetPOSIXTime( pDate: datetime.datetime ):
	return pDate.strftime("%s")	

# Returns a specially formatted time for discord messages, defaults to dynamic type: "in X days. In 30 minutes" etc...
def GetDiscordTime(pDate: datetime.datetime, pFormat: UtilityData.DateFormat = UtilityData.DateFormat.Dynamic):
	return f"<t:{GetPOSIXTime(pDate)}{pFormat.value}>"


class FilesAndFolders():
	def SetupFolders():
		"""
		# SETUP FOLDERS:

		Create the folders the bot uses.
		"""
		FilesAndFolders.GenerateDefaultOpsFolder()
		FilesAndFolders.GenerateLiveOpsFolder()
		FilesAndFolders.GenerateUserLibraryFolder()
		FilesAndFolders.GenerateTempFolder()

	def CleanupTemp():
		"""
		# CLEANUP TEMP
		Removes the temp directory.
		"""
		if os.path.exists(Directories.tempDir):
			vFiles = FilesAndFolders.GetFiles(Directories.tempDir)
			for fileName in vFiles:
				try:
					os.remove(f"{Directories.tempDir}{fileName}")
				except OSError as vError:
					BotPrinter.LogErrorExc(f"Unable to remove file: {fileName}", vError)



	def DeleteCorruptFile(pDir: str):
		BotPrinter.Info(f"Corrupt file being removed: {pDir}")
		os.remove(pDir)


	def GetFiles(pDir: str, pEndsWith: str = ""):
		vDataFiles: list = []
		for file in os.listdir(pDir):
			if pEndsWith != "" and file.endswith(pEndsWith):
				vDataFiles.append(file)

			elif pEndsWith == "":
				vDataFiles.append(file)

		BotPrinter.Debug(f"Files ending with: {pEndsWith} In: {pDir} found:\n{vDataFiles}")
		return vDataFiles


	def GenerateDefaultOpsFolder():
		BotPrinter.Debug("Creating default ops folder (if non existant)")
		if (not os.path.exists( Directories.savedDefaultsDir ) ):
			try:
				os.makedirs(f"{ Directories.savedDefaultsDir }")
			except:
				BotPrinter.LogError("Failed to create folder for default Ops data!")


	def GenerateLiveOpsFolder():
		BotPrinter.Debug("Creating live ops folder (if non existant)")
		if (not os.path.exists( Directories.liveOpsDir ) ):
			try:
				os.makedirs(f"{ Directories.liveOpsDir }")
			except:
				BotPrinter.LogError("Failed to create folder for Live Op data!")


	def GenerateUserLibraryFolder():
		BotPrinter.Debug("Creating User Library folder (if non existant)")
		if (not os.path.exists( Directories.userLibrary ) ):
			try:
				os.makedirs(Directories.userLibrary)
			except:
				BotPrinter.LogError("Failed to create folder for User Library!")

		BotPrinter.Debug("Creating User Library: Recruits folder (if non existant)")
		if (not os.path.exists( Directories.userLibraryRecruits ) ):
			try:
				os.makedirs(Directories.userLibraryRecruits)
			except:
				BotPrinter.LogError("Failed to create folder for User Library!")



	def GenerateTempFolder():
		BotPrinter.Debug("Creating Temporary folder (if non existant).")
		if (not os.path.exists( Directories.tempDir ) ):
			try:
				os.makedirs(f"{ Directories.tempDir }")
			except:
				BotPrinter.LogError("Failed to create temporary folder!")


	def GetOpFullPath(p_opFileName):
		"""
		Convenience function that returns a compiled string of botDir/OpsFolderName/{p_opFileName}.bin
		
		Do not use for DEFAULT ops:  
		They use a different path!
		"""
		return f"{Directories.liveOpsDir}{p_opFileName}.bin"


	def GetLockFilePath(p_opFileName):
		"""
		CONVENIENCE FUNCTION:
		Returns a compiled string (liveOpsDir/p_opFileName.lockFileAffix) of a full path for opFile lock file.
		"""
		return f"{Directories.liveOpsDir}{p_opFileName}{Directories.lockFileAffix}"

	
	def GetLockPathGeneric(p_path):
		"""
		# GET LOCK PATH GENERIC
		Returns a compiled string containing the given path and the lockfile affix. 
		"""
		return f"{p_path}{Directories.lockFileAffix}"


	def IsLocked(p_opLockFile):
		"""
		IS LOCKED:
		Checks if the file path given has an associated lock file. to prevent concurrent load/saving.

		RETURNS: 
		TRUE if a file is locked.
		False if a file is lockable.
		"""
		# lockFile = f"{FilesAndFolders.GetOpsFolder}{p_opFileName}{settings.lockFileAffix}"
		if (os.path.exists( p_opLockFile )):
			return True
		else:
			return False


	def GetLock(p_opLockFile):
		"""
		GET LOCK:
		Creates a lock for a file.

		NOTE: Will wait until any existing lock stops existing before creating.
		"""
		BotPrinter.Debug(f"Getting lock file for: {p_opLockFile}")
		attempsLeft = 5
		while FilesAndFolders.IsLocked(p_opLockFile):
			if attempsLeft > 0:
				time.sleep(0.2)
				attempsLeft -= 1
			else:
				BotPrinter.Info(f"Attempted to get lock on file {p_opLockFile}, but ran out of attempts.")
				return False

		# No lock file exists!
		BotPrinter.Debug(f"	-> Creating lock file... ")
		return FilesAndFolders.CreateLock(p_opLockFile)


	def CreateLock(p_opLockFile):
		"""
		CREATE LOCK:

		NOTE Should not be called manually, use GetLock instead!
		
		Creates a lock file for the given Ops file.  

		RETURNS
		True - On success.
		False - On Failure (exception)
		"""
		
		try:
			open(p_opLockFile, 'a').close()
			return True
		except OSError as vError:
			BotPrinter.LogErrorExc("Failed to create LOCK file", vError)
			return False


	def ReleaseLock(p_fileToRelease:str) -> discord.guild.Guild:
		"""
		RELEASE LOCK:

		Removes a lock file for the given File.
		Should be called every time GETLOCK is called.
		
		RETURNS
		True - On success (or file doens't exist)
		False - On Failure (exception)
		"""
		BotPrinter.Debug(f"Releasing lock for {p_fileToRelease}")

		if not p_fileToRelease.__contains__( Directories.lockFileAffix ):
			BotPrinter.Debug("	-> File specified isn't a lock file!")
			return False

		if(FilesAndFolders.IsLocked(p_fileToRelease)):
			try:
				os.remove(p_fileToRelease)
				BotPrinter.Debug(f"	-> Lock file released!")
				return True
			except OSError as vError:
				BotPrinter.LogErrorExc("Failed to remove LOCK file", vError)
				return False
		BotPrinter.Debug("	-> No lock file present")
		return True


def GetGuildNF(p_botRef: commands.Bot) -> discord.guild.Guild:
	"""
	# GET GUILD: No Fetch.
	Similar to GetGuild, but does not fetch if no guild found.
	
	### RETURNS
	The `discord.guild` using the id specified in settings or `none` if not found.
	"""
	BotPrinter.Debug("Getting Guild from ID.")
	try:
		guild = p_botRef.get_guild( int(BotSettings.discordGuild) )
		if guild != None:
			return guild

	except discord.Forbidden as vError:
		BotPrinter.LogErrorExc("Bot has no access to this guild!", p_exception=vError)
		return None

	except discord.HTTPException:
		BotPrinter.LogErrorExc("Unable to get guild.", p_exception=vError)
		return None


async def GetGuild(p_BotRef : commands.Bot):
	"""
	# GET GUILD:
	
	`p_BotRef`: A reference to the bot.

	RETURNS: a discord.Guild using the ID from settings.

	Tries get first, then fetch.
	"""
	BotPrinter.Debug("Getting Guild from ID.")
	try:
		guild = p_BotRef.get_guild( int(BotSettings.discordGuild) )
		if guild != None:
			return guild

		BotPrinter.Debug(f"	-> Failed to GET, attempting fetch instead.")
		guild = await p_BotRef.fetch_guild( int(BotSettings.discordGuild) )
		if guild == None:
			BotPrinter.Info("Unable to fetch guild!  Ensure you have the right ID.")
			return None
	
		BotPrinter.Debug(f"Guild found with Fetch!  Chunked: {guild.chunked}")
		return guild

	except discord.Forbidden as vError:
		BotPrinter.LogErrorExc("Bot has no access to this guild!", p_exception=vError)
		return None

	except discord.HTTPException:
		BotPrinter.LogErrorExc("Unable to get guild.", p_exception=vError)
		return None




async def UserHasCommandPerms(p_callingUser:discord.Member, p_requiredLevel:CommandRestrictionLevels, p_interaction: discord.Interaction):
	"""
	# USER HAS VALID PERMS
	Checks if the user provided has any role within restriction level.

	NOTE: If `settings.bForceRoleRestrictions` is false, this always returns true.
	"""
	if not BotSettings.bForceRoleRestrictions:
		return True

	bHasPermission = UserHasPerms(p_callingUser, p_requiredLevel)
	
	if not bHasPermission and p_interaction != None:
		await p_interaction.response.send_message(Messages.invalidCommandPerms, ephemeral=True)
	
	return bHasPermission



def UserHasPerms(p_user:discord.Member, p_requiredLevel:CommandRestrictionLevels):
	"""
	# USER HAS PERMS
	Similar to UserHasCommandPerms, except does not check `settings.bForceRoleRestrictions`.
	Expected to be used outside of command/button checks, but still utilise the `CommandRestrictionLevels`.
	"""
	for role in p_user.roles:
		if str(role.id) in p_requiredLevel.value or role.name in p_requiredLevel.value:
			return True
	
	return False

	
async def RoleDebug(p_guild:discord.Guild, p_showOnLive=False):
	"""
	# ROLE DEBUG
	Goes through all editable roles.
	If any are not matching, they're listed.

	Returns immediately if Debug is not enabled.

	Bypass this with `p_showOnLive=True`
	"""
	if not BotSettings.bDebugEnabled and not p_showOnLive:
		return

	guildRoles = await p_guild.fetch_roles()
	guildRoleNames = []
	guildRoleIDs = []
	vMessageStr = "ROLE DEBUG:\n"

	role: discord.Role
	for role in guildRoles:
		guildRoleNames.append(role.name)
		guildRoleIDs.append(role.id)


	vMessageStr += "\n"
	option:discord.SelectOption
	for option in Roles.addRoles_TDKD:
		if option.value not in guildRoleNames or option.value not in guildRoleIDs:
			vMessageStr += f"\nTDKD ROLE SELECTOR | Invalid Value: {option.value} for {option.label}"

	if len(Roles.addRoles_games1):
		vMessageStr += "\n"
		for option in Roles.addRoles_games1:
			if option.value not in guildRoleNames or option.value not in guildRoleIDs:
				vMessageStr += f"\nGAME ROLES 1 | Invalid Value: {option.value} for {option.label}"

	if len(Roles.addRoles_games2):
		vMessageStr += "\n"
		for option in Roles.addRoles_games2:
			if option.value not in guildRoleNames or option.value not in guildRoleIDs:
				vMessageStr += f"\nnGAME ROLES 2 | Invalid Value: {option.value} for {option.label}"

	if len(Roles.addRoles_games3):
		vMessageStr += "\n"
		for option in Roles.addRoles_games3:
			if option.value not in guildRoleNames or option.value not in guildRoleIDs:
				vMessageStr += f"\nGAME ROLES 3 | Invalid Value: {option.value} for {option.label}"

	vMessageStr += "\n\n"

	if not p_showOnLive:
		BotPrinter.Debug(vMessageStr)
	else:
		BotPrinter.Info(vMessageStr)


class ChannelPermOverwrites():
	"""
	# CHANNEL PERM OVERWRITES
	A class containing overwrite variables relating to the 4 restrictLevels, one `invisible` variable for hiding channels and a single function to set them (ideally on startup!).
	"""
	level0 = {}
	level1 = {}
	level2 = {}
	level3 = {}
	level3_readOnly = {}
	invisible = {}
	def __init__(self) -> None:
		pass
	
	async def Setup(p_botRef:commands.Bot):
		guild = await p_botRef.fetch_guild(BotSettings.discordGuild)
		roles = await guild.fetch_roles()
		# Defaults:

		ChannelPermOverwrites.level3[guild.default_role] = discord.PermissionOverwrite(read_messages=False)

		ChannelPermOverwrites.level2[guild.default_role] = discord.PermissionOverwrite(read_messages=False)

		ChannelPermOverwrites.level1[guild.default_role] = discord.PermissionOverwrite(read_messages=False)

		ChannelPermOverwrites.level0[guild.default_role] = discord.PermissionOverwrite(read_messages=False)

		role : discord.Role
		for role in roles:
			# SETUP LEVEL 3
			if role.name in CommandRestrictionLevels.level3.value or role.id in CommandRestrictionLevels.level3.value:
				ChannelPermOverwrites.level3[role] = discord.PermissionOverwrite(
					read_messages=True,
					send_messages=True,
					connect=True
				)

				ChannelPermOverwrites.invisible[role] = discord.PermissionOverwrite(
					read_messages=False
				)

				ChannelPermOverwrites.level3_readOnly[role] = discord.PermissionOverwrite(
					read_messages=True,
					send_messages=False
				)


			# SEUP LEVEL 2
			if role.name in CommandRestrictionLevels.level2.value or role.id in CommandRestrictionLevels.level2.value:
				ChannelPermOverwrites.level2[role] = discord.PermissionOverwrite(
					read_messages=True,
					send_messages=True,
					connect=True
				)


			# SEUP LEVEL 1
			if role.name in CommandRestrictionLevels.level1.value or role.id in CommandRestrictionLevels.level1.value:
				ChannelPermOverwrites.level1[role] = discord.PermissionOverwrite(
					read_messages=True,
					send_messages=True,
					connect=True
				)


			# SEUP LEVEL 0
			if role.name in CommandRestrictionLevels.level0.value or role.id in CommandRestrictionLevels.level0.value:
				ChannelPermOverwrites.level0[role] = discord.PermissionOverwrite(
					read_messages=True,
					send_messages=True,
					connect=True
				)

		BotPrinter.Info("ChannelPermOverwrites have been configured!")