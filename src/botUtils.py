import os
import datetime
import settings
import traceback
import enum
import discord

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
		if(settings.bShowDebug):
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

	Dynamic = ":R" # Dyanmically changes to most appropriate biggest stamp (in X days, in X hours, in x seconds)
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
	def GetFiles(pDir: str, pEndsWith: str = ""):
		vDataFiles: list = []
		for file in os.listdir(pDir):
			if file.endswith(".bin"):
				vDataFiles.append(file)
		BotPrinter.Debug(f"Files ending with: {pEndsWith} In: {pDir} found:\n{vDataFiles}")
		return vDataFiles

	def GenerateDefaultOpsFolder():
		BotPrinter.Debug("Creating default ops folder (if non existant)")
		if (not os.path.exists(f"{settings.botDir}/{settings.defaultOpsDir}") ):
			try:
				os.makedirs(f"{settings.botDir}/{settings.defaultOpsDir}")
			except:
				BotPrinter.LogError("Failed to create folder for default Ops data!")


