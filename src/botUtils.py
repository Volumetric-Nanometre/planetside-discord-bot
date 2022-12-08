import os
import datetime
import time
from botData.settings import BotSettings
from botData.settings import Directories
import traceback
import enum
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

# BotPrinter:
# wraps printing around booleans.
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
			print(f"[{datetime.datetime.now()}] {p_string}")

	@staticmethod
	def Info(p_string):
		"""
		INFO
		Similar to debug, but doesn't depend on ShowDebug to show.
		Should ideally only be used for displaying status as to not flood the console.
		"""
		print(f"[{datetime.datetime.now()}] {p_string}")

	# Convenience function to pretty print errors.
	@staticmethod
	def LogError(p_string, p_tracebacks=3):
		"""
		LOG ERROR
		Displays an error to console and includes a traceback.

		p_string : The message to show first.
		p_tracebacks : The number of tracebacks. Default: 3.
		"""
		print(f"[{datetime.datetime.now()}] ERROR: {p_string}  {traceback.print_tb(limit=p_tracebacks)}")

	@staticmethod
	def LogErrorExc(p_string: str, p_exception: Exception):
		"""
		Same as LOG ERROR, with addition of Exception parameter.
		"""
		print(f"[{datetime.datetime.now()}] ERROR: {p_string}\n{traceback.print_tb(p_exception.__traceback__)}")


class DateFormat(enum.Enum):
	"""
	DATE FORMAT
	Used within discord timeformat string to change how a POSIX datetime is displayed.
	"""

	Dynamic = ":R" # Dyanmically changes to most appropriate smallest stamp (in X days, in X hours, in x seconds)
	DateShorthand = ":d" # dd/mm/year
	DateLonghand = ":D" # 00 Month Year
	TimeShorthand = ":t" # Hour:Minute
	TimeLonghand = ":T" # Hour:Minute:Seconds
	DateTimeShort = ":f" # Full date, no day.
	DateTimeLong = ":F" # Full date, includes Day
	Raw = "" # Raw POSIX.


class Colours(enum.Enum):
	openSignup = discord.Colour.from_rgb(0,244,0)
	opsStarted = discord.Colour.from_rgb(255,0,0)
	editing = discord.Colour.from_rgb(204, 102, 0)
	commander = discord.Colour.from_rgb(0, 255, 360)
	userRequest = discord.Colour.from_rgb(106, 77, 255)
	userWarnOkay = discord.Colour.from_rgb(170, 255, 0)
	userWarning = discord.Colour.from_rgb(255, 85, 0)
	
	
		
class DateFormatter():

	# Used to clear up repeating code
	@staticmethod
	def GetPOSIXTime( pDate: datetime.datetime ):
		return pDate.strftime("%s")	

	# Returns a specially formatted time for discord messages, defaults to dynamic type: "in X days. In 30 minutes" etc...
	@staticmethod
	def GetDiscordTime(pDate: datetime.datetime, pFormat: DateFormat = DateFormat.Dynamic):
		return f"<t:{DateFormatter.GetPOSIXTime(pDate)}{pFormat.value}>"


class FilesAndFolders():
	def SetupFolders():
		"""
		# SETUP FOLDERS:

		Create the folders the bot uses.
		"""
		FilesAndFolders.GenerateDefaultOpsFolder()
		FilesAndFolders.GenerateLiveOpsFolder()

	def GetFiles(pDir: str, pEndsWith: str = ""):
		vDataFiles: list = []
		for file in os.listdir(pDir):
			if file.endswith(".bin"):
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
				BotPrinter.LogError("Failed to create folder for default Ops data!")

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
		Returns a compiled string of a full path for opFile lock file.
		"""
		return f"{Directories.liveOpsDir}{p_opFileName}{Directories.lockFileAffix}"

	def IsLocked(p_opLockFile):
		"""
		IS LOCKED:
		Checks if an Op file has an associated lock file. to prevent concurrent load/saving.

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


	def ReleaseLock(p_opLockFile):
		"""
		RELEASE LOCK:

		Removes a lock file for the given Ops File.
		Should be called every time GETLOCK is called.
		
		RETURNS
		True - On success (or file doens't exist)
		False - On Failure (exception)
		"""
		BotPrinter.Debug(f"Releasing lock for {p_opLockFile}")
		# lockFile = f"{FilesAndFolders.GetOpsFolder()}{p_opFileName}{settings.lockFileAffix}"

		if(FilesAndFolders.IsLocked(p_opLockFile)):
			try:
				os.remove(p_opLockFile)
				BotPrinter.Debug(f"	-> Lock file released!")
				return True
			except OSError as vError:
				BotPrinter.LogErrorExc("Failed to remove LOCK file", vError)
				return False
		BotPrinter.Debug("	-> No lock file present")
		return True


async def GetGuild(p_BotRef : commands.Bot):
	"""
	GET GUILD:
	
	p_BotRef: A reference to the bot.

	RETURNS: a discord.Guild using the ID from settings.

	"""
	BotPrinter.Debug("Getting Guild from ID.")
	try:
		return await p_BotRef.fetch_guild( BotSettings.discordGuild )
	except discord.Forbidden as vError:
		BotPrinter.LogErrorExc("Bot has no access to this guild!", p_exception=vError)
		return None
	except discord.HTTPException:
		BotPrinter.LogErrorExc("Unable to get guild.", p_exception=vError)
		return None

class EmojiLibrary(enum.Enum):
	# Infantry Classes
	ICON_LA = ""
	ICON_HA = ""
	ICON_ENG = ""
	ICON_MED = ""
	ICON_INF = ""
	ICON_MAX = ""
	# Ground Vehicles
	ICON_ = ""
