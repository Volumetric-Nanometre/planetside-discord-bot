# A singular file containing ALL data objects used by the bot.
# Mainly to avoid circular references by things that depend on each other; but not always part of the same module.

from __future__ import annotations

from enum import Enum
from discord import Member
from dataclasses import dataclass, field
from datetime import datetime, time
import botData.settings as Settings
import botUtils
from auraxium.ps2 import Character as PS2Character
import pickle



@dataclass
class SanityCheckOptions():
	"""
	# SANITY CHECK OPTIONS
	Specifies what settings to check based on cog usage.
	"""
	UsedByNewUser: bool = True
	UsedByOperations: bool = True
	UsedByCommander : bool = True
	UsedByUserLibrary : bool = True
	RestrictLevels: bool = True
	UsedByUserRoles: bool = True

	def __repr__(self) -> str:
		vString = f"		>[{self.UsedByNewUser}] Used By New user\n"
		vString += f"		>[{self.UsedByOperations}] Used By Operations\n"
		vString += f"		>[{self.UsedByCommander}] Used By Commander\n"
		vString += f"		>[{self.UsedByUserLibrary}] Used By User Library\n"
		vString += f"		>[{self.UsedByUserRoles}] Used By User Roles\n"
		vString += f"		>[{self.RestrictLevels}] Command Retriction Levels\n"
		return vString


@dataclass
class UserSettings:
	"""
	# USER SETTINGS
	Settings pertaining to the User data object.
	"""
	bLockPS2Char = False
	bLockAbout = False
	bTrackHistory = True

	def __repr__(self) -> str:
		vStr = f"	> Lock PS2 Character:	{self.bLockPS2Char}\n"
		vStr += f"	> Lock About:		{self.bLockAbout}\n"
		vStr += f"	> Track History:	{self.bTrackHistory}\n"

		return vStr



@dataclass(frozen=True)
class AutoPromoteRule():
	"""
	# AUTO PROMOTE RULE
	Contains values pertaining to the rules a user must meet before auto-promotion from recruit.

	This should be obtained from `botData.settings`!
	"""
	# Attended Minimum Events: the number of events a user must participate in
	bAttendedMinimumEvents: bool
	bEventsMustBePS2: bool
	minimumEvents: int

	# Length of time a user must be in the outfit.
	bInOutfitForDuration: bool
	outfitDuration: datetime.time

	# Length of time a user must have been in the discord server.
	bInDiscordForDuration: bool
	discordDuration: datetime.time


	def __repr__(self) -> str:
		vString = f"\n		> Attend Minimum Events: {self.bAttendedMinimumEvents} ({self.minimumEvents})\n"
		vString += f"		> Events must be Planetside 2: {self.bEventsMustBePS2}\n"
		vString += f"		> In Outfit for Duration: {self.bInOutfitForDuration} | {self.outfitDuration}\n"
		vString += f"		> In Discord for Duration: {self.bInDiscordForDuration} | {self.discordDuration}\n"

		return vString




@dataclass
class User:
	"""
	# USER (UserLibrary)
	Data object representing a user on the discord.  
	
	Contains their planetside2 character information, and tracked event sessions.
	"""
	discordID: int = -1

	# Users PS2 Character Name
	ps2Name: str = ""
	# Users PS2 Character Outfit
	ps2Outfit: str = ""
	# Users PS2 Char Outfit Rank, if applicable.
	ps2OutfitRank: str = ""
	# Joindate of Ps2 outfit
	ps2OutfitJoinDate: datetime = None

	# Used alongside auto-promote; this is set by newUser or manually.
	bIsRecruit = False

	# Tracked Sessions
	sessions :list[Session] = field(default_factory=list)
	
	# Number of events attended.
	eventsAttended = 0

	# Number of events the user signed up to, and wasn't present for.
	eventsMissed = 0
	
	# Users birthday.
	birthday:datetime = None

	# User provided "about" text.
	aboutMe = ""

	# About loaded from a seperate file, editable only by admins.
	specialAbout = ""

	# Settings object.
	settings: UserSettings = field(default_factory=UserSettings)


	############################################################################
# OP COMMANDER
class CommanderStatus(Enum):
	"""
	# COMMANDER STATUS
	Enum to contain the status of a commander.  
	
	### Values are numerical.
	"""
	Init = -10		# Init: Commander has been created.
	Standby = 0 	# Standby: Commander has been set up and waiting.
	WarmingUp = 10	# Warming Up: Updates the commander post with connections modal.
	Started = 20 	# Started: Ops has been started (either manually or by bot.)
	Debrief = 30	# Debrief: Pre-End stage, users are given a reactionary View to provide feedback
	Ended = 40		# Ended: User has ended Ops,  auto-cleanup.


class PS2EventTrackOptions(Enum):
	"""
	EVENT TRACKING OPTIONS:
	Sets the requirements for when to enable tracking a ps2 event.
	This enum is also used for marking present, where `InGameOnDisVDAndDuration` may be used.

	NOTE: To change the setting, See `botData.settings.Commander.trackEvent`.
	NOTE: In Game, On Discord Voice And Duration; the value is the time in minutes to be used.
	"""
	Disabled = 0
	InGameOnly = 10
	InGameAndDiscordVoice = 20
	InGameOnDisVCAndDuration = 30




# SESSION SUB OBJECTS
@dataclass
class PS2SessionKDA:
	""" # PS2 SESSION: KILLS ASSISTS AND DEATHS
	Data object containing KDA information for a session.
	"""
	kills = 0
	killedAllies = 0
	killedSquad = 0
	assists = 0
	vehiclesDestroyed = 0

	deathTotal = 0
	deathByEnemies = 0
	deathByAllies = 0
	deathBySquad = 0


class PS2SessionEngineer:
	"""
	# PS2 SESSION : ENGINEER SPECIFIC DATA
	Role specific data 
	"""
	repairScore = 0
	resupplyScore = 0


class PS2SessionMedic:
	"""
	# PS2 SESSION : MEDIC SPECIFIC DATA
	"""
	revives = 0
	heals = 0


@dataclass
class Session:
	"""
	# SESSION
	Dataclass that represents a single user session.
	"""
	eventName: str = ""
	bIsPS2Event: bool = True
	date: datetime = None
	duration: float = 0
	kda = None
	medicData = None
	engineerData = None
	score: int = 0
	funEvents:list[str] = field(default_factory=list)



@dataclass
class Participant:
	"""
	# PARTICIPANT
	Dataclass containing a reference to a `discord.Member`, and a `userLibrary.User` for a participant.
	"""
	# OBJECT REFERENCES
	discordUser : Member = None
	libraryEntry : User = None
	ps2Char : PS2Character = None
	userSession : Session = None

	# DATA
	discordID : int = 0
	bIsTracking : bool = True 
	lastCheckedName : str = "" # Last Checked name: skips searching for a PS2 character if this is the same.

	def __repr__(self) -> str:
		vStr = f"PARTICIPANT: {self.discordID}\n"
		if self.ps2Char != None:
			vStr += f"	PS2 Character: {self.ps2Char}"
		if self.libraryEntry == None:
			vStr += f"	LIBRARY ENTRY NOT SET"
		else:
			vStr += f"	LIBRARY PS2 NAME: {self.libraryEntry.ps2Name}"
		if self.discordUser == None:
			vStr += f"	DISCORD USER UNSET"
		else:
			vStr += f"	DISCORD USER SET :{self.discordUser.display_name}"

		return vStr



	def SaveParticipant(self):
		"""
		# SAVE PARTICIPANT
		Saves the participant libEntry data to file.
		"""
		dataFile = f"{Settings.Directories.userLibrary}{self.discordID}.bin"
		lockFile = botUtils.FilesAndFolders.GetLockPathGeneric(dataFile)

		botUtils.FilesAndFolders.GetLock(lockFile)
		try:
			with open(dataFile, "wb") as vFile:
				self.libraryEntry = pickle.dump(self.libraryEntry, vFile)
			botUtils.FilesAndFolders.ReleaseLock(lockFile)
		except pickle.PickleError as vError:
			botUtils.BotPrinter.LogErrorExc("Failed to save user library entry.", vError)
			botUtils.FilesAndFolders.ReleaseLock(lockFile)



@dataclass
class OpFeedback:
	"""
	# OPS FEEDBACK
	Class containing variable lists which hold user submitted feedback
	"""
	userID:list[str] = field(default_factory=list) # Saved to allow users to edit their feedback.
	generic:list[str] = field(default_factory=list)
	forSquadmates:list[str] = field(default_factory=list)
	forSquadLead:list[str] = field(default_factory=list)
	forPlatLead:list[str] = field(default_factory=list)

	def SaveToFile(self, p_eventName:str):
		"""
		# SAVE TO FILE

		Saves the feedback to a file, using the event name provided.

		## Returns: 
		The filepath of the saved file.
		Or "" if saving failed.
		"""

		# Save feedback to file.
		filePath = f"{Settings.Directories.tempDir}{p_eventName}_feedback.txt"
		try:
			with open(filePath, "w") as vFile:
				vFile.write("GENERAL FEEDBACK\n")
				for line in self.generic:
					if line != "" or "\n":
						vFile.write(f"{line}\n\n")

				vFile.write("\n\nTO SQUADMATES\n")
				for line in self.forSquadmates:
					if line != "" or "\n":
						vFile.write(f"{line}\n\n")

				vFile.write("\n\nTO SQUAD LEAD\n")
				for line in self.forSquadLead:
					if line != "" or "\n":
						vFile.write(f"{line}\n\n")

				vFile.write("\n\nTO PLATOON LEAD\n")
				for line in self.forPlatLead:
					if line != "" or "\n":
						vFile.write(f"{line}\n\n")
			
			return filePath 

		except:
			botUtils.BotPrinter.LogError("Unable to save a the file!")
			return ""



@dataclass
class EventPoint():
	"""
	# EVENT POINT
	A singular point during an event
	"""
	timestamp: time = None
	users: list = field(default_factory=list)



	#############################################################
# OPERATIONS

class OpsStatus(Enum):
	"""
	# OPS STATUS
	
	Defines the current status of an Operation.
	"""
	editing = -1 # Ops is being edited, users can't signup.
	open = 1 # Open to signups.
	prestart = 10 # set when pre-op setup starts.
	started = 20 # Ops started.
	debriefing = 30 # Probably redundant. 


@dataclass
class OperationOptions:
	"""
	# OPERATION OPTIONS

	Options, typically altered via use of arguments, to determine behaviour of the ops.
	"""
	bUseReserve : bool = True # Only enable built in RESERVE if true.
	bUseCompact : bool = False # If True, does not show a member list for each role.
	bAutoStart : bool = True # If false, someone must use `/commander [OpData]` to start the commander.
	bUseSoberdogsFeedback : bool = False # If true, debriefing opens a new forum thread and send the feedback message there.
	bIsPS2Event : bool = True # If false, treats this event as a non-PS2 event.


@dataclass
class OpRoleData:
	"""
	# OP ROLE DATA
	
	Data pertaining to an individual role on an Operation
	"""
	players : list = field(default_factory=list) #User IDs
	roleName : str = ""
	roleIcon : str = ""
	maxPositions : int = 0

	def GetRoleName(self):
		"""
		# GET ROLE NAME:
		Returns a precompiled string containing the icon if present, and the min/max or just current count, depending on configuration.
		"""
		vRolename = ""

		# Icon
		if self.roleIcon != "-":
			vRolename = f"{self.roleIcon}{self.roleName}"
		else:
			vRolename = self.roleName

		# Signed Up/Positions:
		if self.maxPositions > 0:
			vRolename += f" ({len(self.players)}/{self.maxPositions})"
		else:
			vRolename += f" ({len(self.players)})"

		return vRolename



@dataclass
class OperationData:
	"""
	# OPERATION DATA
	Data pertaining to an Operation/Event.
	Includes a list of OpRoleData objects, which hold information specific to individual roles.
	"""

	# Op Details:
	roles : list[OpRoleData] = field(default_factory=list) # List of OpRoleData objects
	reserves : list = field(default_factory=list) # Since there's no need for special data for reserves, they just have a simple UserID list.
	name : str = ""
	fileName: str = ""
	date : datetime = datetime.now()
	description : str = ""
	customMessage : str = ""
	managedBy:str = ""
	pingables : list[str] = field(default_factory=list) # roles to mention/ping in relation to this ops.

	# Backend variables
	messageID : str = "" 
	status : OpsStatus = OpsStatus.open
	targetChannel: str = ""
	options: OperationOptions = OperationOptions()
	jumpURL: str = ""

	# Factory fields
	voiceChannels: list[str] = field(default_factory=list)
	arguments: list[str] = field(default_factory=list)


	def GenerateFileName(self):
		"""
		# GENERATE FILE NAME
		Generates a filename using the operation name, and the date (opName_y-m-d_h-m).
		File name does not include the extension!
		
		NOTE: Sets the fileName variable with the result.  
			It is not returned.
		"""
		self.fileName = f"{self.name}_{self.date.year}-{self.date.month}-{self.date.day}_{self.date.hour}-{self.date.minute}"
		
		botUtils.BotPrinter.Debug(f"Filename for Op {self.name} generated: {self.fileName}")


	def GetFullFilePath(self):
		return f"{Settings.Directories.liveOpsDir}{self.fileName}.bin"


	def PlayerInOps(self, p_playerID:int):
		"""
		# PLAYER IN OPS
		### RETURN: 
		`str`- "" when not in ops, else string of role name.

		Convenience function to avoid repetition.
		"""
		if self.options.bUseReserve:
			if p_playerID in self.reserves:
				return "Reserve"

		for role in self.roles:
			if p_playerID in role.players:
				return role.roleName

		return ""



	def ArgStringToList(self, p_string:str, p_deliminator:str = " "):
		"""
		# ARGUMENT STRING TO LIST
		Converts an argument string to a list, then runs Parse.
		A deliminator may be specified, uses ' ' by default.
		"""
		newArgList = p_string.split(p_deliminator)

		if newArgList != None:
			botUtils.BotPrinter.Debug(f"Setting op argument list: {newArgList}")
			self.arguments = newArgList

			botUtils.BotPrinter.Debug(f"OpData Argument list: {self.arguments}")

			self.ParseArguments()

		else:
			botUtils.BotPrinter.Debug("No arguments.")


	def ParseArguments(self):
		"""
		# PARSE ARGUMENTS
		Parses the arguments given and sets their respective options.
		"""
		botUtils.BotPrinter.Debug(f"Parsing opdata arguments: {self.arguments}")
		argument:str
		for argument in self.arguments:

			argInLower = argument.lower().strip()

			# TOGGLE VIEW TYPE
			if argInLower == "compact":
				self.options.bUseCompact = True
				botUtils.BotPrinter.Debug(f"Using viewmode: Compact for {self.name}")
				continue

			elif argInLower == "fullview":
				self.options.bUseCompact = False
				botUtils.BotPrinter.Debug(f"Using viewmode: Full for {self.name}")
				continue


			# TOGGLE RESERVE
			if argInLower == "noreserve":
				self.options.bUseReserve = False
				botUtils.BotPrinter.Debug(f"Setting Reserves: OFF for {self.name}")
				continue

			elif argInLower == "reserveon":
				self.options.bUseReserve = True
				botUtils.BotPrinter.Debug(f"Setting Reserves: ON for {self.name}")
				continue


			# TOGGLE AUTO START
			if argInLower == "noauto":
				self.options.bAutoStart = False
				botUtils.BotPrinter.Debug(f"Setting Automatic Start: OFF for {self.name}")
				continue

			elif argInLower == "autostart":
				self.options.bAutoStart = True
				botUtils.BotPrinter.Debug(f"Setting Automatic Start: ON for {self.name}")
				continue


			# TOGGLE SOBERDOGS FEEDBACK
			if argInLower == "nofeedback":
				self.options.bUseSoberdogsFeedback = False
				botUtils.BotPrinter.Debug(f"Setting Soberdogs Feedback: OFF for {self.name}")
				continue

			elif argInLower == "soberfeedback":
				self.options.bUseSoberdogsFeedback = True
				botUtils.BotPrinter.Debug(f"Setting Soberdogs Feedback: ON for {self.name}")
				continue


			# TOGGLE PS2 EVENT
			if argInLower == "ps2event":
				self.options.bIsPS2Event = True
				botUtils.BotPrinter.Debug(f"Setting PS2 Event: ON for {self.name}")
				continue

			elif argInLower == "notps2":
				self.options.bIsPS2Event = False
				botUtils.BotPrinter.Debug(f"Setting PS2 Event: OFF for {self.name}")
				continue


	def GetOptionsAsStr(self):
		"""
		# GET OPTIONS AS STRING

		Returns a condensed formatted version of the options as a string, eg:
		AS:E|UR:E|UC:D|SDF:D
		"""
		vOptsStr = "AS:"
		if self.options.bAutoStart:
			vOptsStr += "E"
		else: vOptsStr += "D"


		vOptsStr += "|UR:"
		if self.options.bUseReserve:
			vOptsStr += "E"
		else: vOptsStr += "D"


		vOptsStr += "|UC:"
		if self.options.bUseCompact:
			vOptsStr += "E"
		else: vOptsStr += "D"


		vOptsStr += "|SDF:"
		if self.options.bUseSoberdogsFeedback:
			vOptsStr += "E"
		else: vOptsStr += "D"


		vOptsStr += "|PSE:"
		if self.options.bIsPS2Event:
			vOptsStr += "E"
		else: vOptsStr += "D" 

		return vOptsStr


	def GetParticipantIDs(self):
		"""
		# GET PARTICIPANT IDS
		Returns all roles participants (IDs), including reserve if enabled in a list.
		"""
		vIDList = []

		role: OpRoleData
		for role in self.roles:
			vIDList += role.players

		if self.options.bUseReserve:
			vIDList += self.reserves

		return vIDList



	def __repr__(self) -> str:
		vOutputStr = "	OPERATION DATA\n"
		vOutputStr += f"	-> Name|FileName: {self.name} | {self.fileName}\n"
		vOutputStr += f"	-> Date: {self.date}\n"
		vOutputStr += f"	-> Description: {self.description}\n"
		vOutputStr += f"	-> Additional Info: {self.customMessage}\n"
		vOutputStr += f"	-> Message ID: {self.messageID}\n"
		vOutputStr += f"	-> Arguments: {self.arguments}\n"
		vOutputStr += f"	-> Status: {self.status.value}\n"
		vOutputStr += f"	-> VoiceChannels: {self.voiceChannels}\n"
		vOutputStr += f"	-> Reserves: {self.reserves}\n"
		vOutputStr += f"	-> Options: {self.options}\n"
		vOutputStr += f"	-> Roles: {self.roles}\n"
		return vOutputStr


@dataclass(frozen=True)
class DefaultChannels:
	"""
	# DEFAULT CHANNELS
	Name of channels used during Operations.
	"""
	# Text chanels created for every Op
	textChannels:list
	# Op Commander Channel: Name of the channel used for the Ops Commander
	opCommander:str
	# Notification Channel: Name of channel used to send op auto alerts and interactive debrief messages.
	notifChannel:str
	# Standby channel- the channel(name) users are moved into if they are connected during Ops soft start
	standByChannel:str
	# Persistent Voice channels are channels that are ALWAYS created for every operation
	persistentVoice:list
	# If voice channels are not specified in the ops data, these are used instead
	voiceChannels:list

	def __repr__(self) -> str:
		vString = "\n"
		vString += f"		> Text Channels: {self.textChannels}\n"
		vString += f"		> Voice Channels: {self.voiceChannels}\n"
		vString += f"		> Persistent Voice: {self.persistentVoice}\n"
		vString += f"		> Commander Channel: {self.opCommander}\n"
		vString += f"		> Notifications Channel: {self.notifChannel}\n"
		vString += f"		> Standby Channel: {self.standByChannel}\n"
		return vString		