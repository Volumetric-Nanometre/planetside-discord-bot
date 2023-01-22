# A singular file containing ALL data objects used by the bot.
# Mainly to avoid circular references by things that depend on each other; but not always part of the same module.

from __future__ import annotations

from enum import Enum
from discord import Member, Message
from dataclasses import dataclass, field
from datetime import datetime, time
import botData.settings as Settings
import botUtils
from auraxium.ps2 import Character as PS2Character
from auraxium.ps2 import MapRegion as PS2Facility
from auraxium.ps2 import OutfitMember as PS2OutfitMember
import pickle


# # # # #  SETTINGS RELATED
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
	UsedByForFun: bool = True

	def __repr__(self) -> str:
		vString = f"		>[{self.UsedByNewUser}] Used By New user\n"
		vString += f"		>[{self.UsedByOperations}] Used By Operations\n"
		vString += f"		>[{self.UsedByCommander}] Used By Commander\n"
		vString += f"		>[{self.UsedByUserLibrary}] Used By User Library\n"
		vString += f"		>[{self.UsedByUserRoles}] Used By User Roles\n"
		vString += f"		>[{self.UsedByForFun}] Used By For Fun\n"
		vString += f"		>[{self.RestrictLevels}] Command Retriction Levels\n"
		return vString



@dataclass(frozen=True)
class BotFeatures:
	"""
	# BOT FEATURES
	A class pertaining to overall features, allowing things to be disabled more gracefully (since some items may tie into one another)
	"""
	BotAdmin:bool
	NewUser: bool
	UserLibrary: bool
	userLibraryInboxSystem: bool
	userLibraryInboxAdmin: bool
	UserLibraryFun: bool
	Operations: bool
	chatUtility: bool
	UserRoles: bool
	ForFunCog: bool


# # # # USER LIBRARY

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


class EntryRetention(Enum):
	"""# ENTRY RETENTION
	Enum for the entry load setting.
	- `always loaded` Entries are always loaded in memory.
	- `unload after` Entries are unloaded afer x minutes.
	- `when needed` Entries are loaded/saved only when needed.
	"""
	alwaysLoaded = 0
	unloadAfter = 10
	whenNeeded = 20


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
class UserInboxItem:
	"""# USER INBOX ITEM
	Data for an inbox item, sent by administrators and some bot features.
	"""
	# Date/Time the inbox item was sent.
	date: datetime
	# Title of the item.
	title: str
	# Message of the item.
	message:str
	# If sent by an admin command, this is true.
	bIsWarning:bool
	# If sent by an admin for a message, this is a snip of the message for context.
	adminContext:str




class LibraryViewPage(Enum):
	"""
	# LIBRARY VIEW: PAGE
	Enum to mark the current page being viewed.
	"""
	general = 0
	ps2Info = 10
	sessions = 20
	individualSession = 25
	inbox = 30




@dataclass
class User:
	"""
	# USER (UserLibrary)
	Data object representing a user on the discord.  
	
	Contains their planetside2 character information, and tracked event sessions.

	NOTE: DO NOT adjust `__version`!
	"""
	__version = -1

	discordID: int = -1

	# PS2 Character ID
	ps2ID: int = -1
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

	# List of top quotes (if enabled)
	topQuotes: list[str] = field(default_factory=list) 

	#Inbox (if enabled)
	inbox:list[UserInboxItem] = field(default_factory=list)

	# Settings object.
	settings: UserSettings = field(default_factory=UserSettings)

	# Used when determining if this entry should be unloaded.
	lastAccessed: datetime = None
	
	# Set to true during events.
	# Save/Load will always revert this to False 
	bKeepLoaded:bool = False

	# Set to true when a recruit has manually requested promotion via library viewer.
	bRecruitRequestedPromotion = False


@dataclass
class NewUserData:
	"""# NEW USER DATA:
	Minimal dataclass to hold data about a new user.
	"""
	userObj : Member = None
	joinMessage : Message = None
	rulesMsg : Message = None
	ps2CharObj: PS2Character = None
	ps2CharID : int = -1
	ps2CharName : str = ""
	ps2OutfitName: str = ""
	ps2OutfitAlias: str = ""
	ps2OutfitCharObj: PS2OutfitMember = None
	bIsRecruit = False


	############################################################################
# OP COMMANDER
class CommanderStatus(Enum):
	"""
	# COMMANDER STATUS
	Enum to contain the status of a commander.  
	
	### Values are numerical.
	"""
	Init = -10 
	"""Init: Commander has been created."""
	Standby = 0
	"""Standby: Commander has been set up and waiting."""
	WarmingUp = 10 
	"""Warming Up: Updates the commander post with connections modal."""
	GracePeriod = 15 
	"""Grace Period: The time just before an event properly starts, for event attendance."""
	Started = 20
	"""Started: Ops has been started (either manually or by bot.)"""
	Debrief = 30 
	"""Debrief: Pre-End stage, users are given a reactionary View to provide feedback"""
	Ended = 40
	"""Ended: User has ended Ops,  auto-cleanup."""



class PS2EventAttended(Enum):
	"""# PS2 EVENT ATTENDED:
	An enum with values to denote when a participant of an event is marked attended.
	This is used synonymously with the UserLibrary & session saving.

	NOTE: When evaluating DiscordVC, the user must be in an event channel.

	A user who fails the requirements set by this enum are marked as non attending.
	`NeverCheck`: marks anyone who signed up as attended.
	"""
	NeverCheck = 0
	InGameOnly = 10
	InDiscordVCOnly = 20
	InGameAndDiscordVC = 30


@dataclass
class PS2EventTotals:
	"""# PS2 EVENT TOTALS
	Dataclass that holds stat totals.
	Used to prevent unnessecery iteration calculations while event is running.
	The event totals are added to this stat object at the same time as the current event point & user session stats.
	"""
	eventKDA:PS2SessionKDA = None
	facilityFeed:list[str] = field(default_factory=list)
	facilitiesCaptured:int = 0
	facilitiesDefended:int = 0


# SESSION SUB OBJECTS
@dataclass
class PS2SessionKDA:
	""" # PS2 SESSION: KILLS ASSISTS AND DEATHS
	Data object containing KDA information for a session.

	NOTE: DO NOT adjust `__version`
	"""
	__version:int = -1

	kills:int = 0
	killedAllies:int = 0
	killedSquad:int = 0
	assists:int = 0
	vehiclesDestroyed:int = 0

	deathTotal:int = 0
	deathByEnemies:int = 0
	deathByAllies:int = 0
	deathBySquad:int = 0
	deathBySuicide: int = 0


@dataclass
class PS2SessionEngineer:
	"""
	# PS2 SESSION : ENGINEER SPECIFIC DATA

	Role specific data for Engineers.

	NOTE: DO NOT adjust `__version`.
	"""
	__version:int = -1

	repairScore:int = 0
	resupplyScore:int = 0


@dataclass
class PS2SessionMedic:
	"""
	# PS2 SESSION : MEDIC SPECIFIC DATA

	Role specific data for medics.

	NOTE: DO NOT adjust `__version`.
	"""
	__version:int = -1
	revives:int = 0
	heals:int = 0


@dataclass
class Session:
	"""
	# SESSION
	Dataclass that represents a single user session.
	
	NOTE: KDA, MedicData, and EngineerData must be created and set for the first instance.
	This ensures no uneeded data is saved.

	NOTE: DO NOT adjust version.
	Version will be used to ensure any changes to the Session Data object will be detectable and old data can still be dealt with.
	EG: `if __version < current: User.sessions.remove(Session)`
	"""
	eventName: str = ""
	bIsPS2Event: bool = True
	date: datetime = None
	duration: float = 0 # Set by commander, currently configured to be in hours.
	kda:PS2SessionKDA = None
	medicData:PS2SessionMedic = None
	engineerData:PS2SessionEngineer = None
	score: int = 0
	funEvents:list[str] = field(default_factory=list)
	__version:int = -1



@dataclass
class Participant:
	"""
	# PARTICIPANT
	Dataclass containing a reference to a `discord.Member`, and a `userLibrary.User` for a participant.
	"""
	# OBJECT REFERENCES
	discordUser : Member = None
	libraryEntry : User = None
	ps2CharID : int = -1
	"""Used regardless of user library setting.  If library is enabled, this value is obtained from there when applicable."""
	userSession : Session = None

	# DATA
	discordID : int = 0
	bAttended: bool = False
	bWasLate: bool = False
	bPS2Online : bool = False # Set to true by aurax event.
	bInEventChannel: bool = False # Set to true when a user is in one of the event channels.
	lastCheckedName : str = "" # Last Checked name: skips searching for a PS2 character if this is the same.

	def __repr__(self) -> str:
		vStr = f"\nPARTICIPANT: {self.discordID}\n"
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




@dataclass(frozen=True)
class EventID:
	"""
	# EVENT IDs
	Matches event IDs to human readable variable names.
	Where an event has multiple sub-events, the variable is a list for iteration purposes.

	All events included are for squad only and thus will not track general events. 
		eg: 'med_heal' only counts heals to squad-members, not blueberries.
	"""
	med_heal = 4
	med_revive = 53

	eng_maxRepair = 142
	eng_vehicleRepair = [28, 129, 132, 133, 134, 138, 140, 141, 302, 505, 656]
	eng_resupply = 55

	kill = 1
	killAssist = 2




@dataclass
class FacilityData:
	"""# FACILITY DATA
	Information pertaining to a facility defense or capture.
	"""
	facilityID:int = 0
	timestamp:datetime = None
	facilityObj:PS2Facility = None
	participants:int = 0



@dataclass
class EventPoint():
	"""
	# EVENT POINT
	A singular point during an event, used to plot graphs.

	These are updated individually to user statistics.
	"""
	timestamp: datetime
	activeParticipants: int

	captured:int = 0
	defended:int = 0

	deaths: int = 0
	kills: int = 0

	revives: int = 0
	repairs: int = 0


@dataclass
class ForFunVehicleDeath:
	"""# FOR FUN VEHICLE DEATH
	Small data object for vehicle death for-fun events: 
	Used to ensure only one event is broadcast since the DEATH trigger will be called for each participants death.
	"""
	# Killer/Driver Vehicle ID: Probably redundant, but here anyway.
	driverVehicleID:int = -1
	# Killer/Driver Character ID: PS2 Character ID of the killer.
	driverCharID: int = -1

	# For discord purposes: Killer and Killed mentions.
	driverMention:str = ""
	killedMentions:str = ""

	# Message: the randomly message chosen randomly by the OpsEventTracker
	message:str = ""

	# Has Set Schedule Task: Should be set to true on first call, creates a delayed task on the Commander to post a message.
	# Delay is to ensure all (or most of) the users involved has their death event register.
	bHasSetSchedTask = False


	#############################################################
# OPERATIONS SIGNUP

@dataclass
class SchedulerOpInfo:
	"""# OP INFO: 
	
	A miniture operation info dataclass used soley for parsing the schedule.
	"""
	matchingOp: str = ""
	eventName: str = ""
	date: datetime = None
	managingUser:str = ""
	bCanPost:bool = False


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
		"""
		# GET FULL FILE PATH (LIVE ONLY)
		Convenience function to get the filepath of the live event.
		"""
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


	def GetParticipantIDs(self) -> list[int]:
		"""
		# GET PARTICIPANT IDS
		Returns all roles participants (Discord IDs), including reserve if enabled in a list.
		"""
		vIDList = [playerID for role in self.roles if self.roles.__len__() != 0 for playerID in role.players]
		vIDList = vIDList + self.reserves
		
		botUtils.BotPrinter.Debug(f"PARTICIPANT IDS: {vIDList}")

		return  vIDList


	def __repr__(self) -> str:
		vOutputStr = "	OPERATION DATA\n"
		vOutputStr += f"	-> Name|FileName: {self.name} | {self.fileName}\n"
		vOutputStr += f"	-> Date: {self.date}\n"
		vOutputStr += f"	-> Description: {self.description}\n"
		vOutputStr += f"	-> Additional Info: {self.customMessage}\n"
		vOutputStr += f"	-> Message ID: {self.messageID}\n"
		vOutputStr += f"	-> Arguments: {self.arguments}\n"
		vOutputStr += f"	-> Status: {self.status.name}\n"
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
	textChannels:list[str]
	# Op Commander Channel: Name of the channel used for the Ops Commander
	opCommander:str
	# Notification Channel: Name of channel used to send op auto alerts and interactive debrief messages.
	notifChannel:str
	# Standby channel- the channel(name) users are moved into if they are connected during Ops soft start
	standByChannel:str
	# Persistent Voice channels are channels that are ALWAYS created for every operation
	persistentVoice:list[str]
	# If voice channels are not specified in the ops data, these are used instead
	voiceChannels:list[str]

	def __repr__(self) -> str:
		vString = "\n"
		vString += f"		> Text Channels: {self.textChannels}\n"
		vString += f"		> Voice Channels: {self.voiceChannels}\n"
		vString += f"		> Persistent Voice: {self.persistentVoice}\n"
		vString += f"		> Commander Channel: {self.opCommander}\n"
		vString += f"		> Notifications Channel: {self.notifChannel}\n"
		vString += f"		> Standby Channel: {self.standByChannel}\n"
		return vString

#################################

dataclass(frozen=True)
class ForFunData:
	"""# FOR FUN DATA
	Contains data objects relating to 'For Fun'
	
	Strings may contian the following special replaceable substrings:
	`_USER`: The user the string is typically about.
	`_USERBY`: If the string is caused by another user, this is included; variable name is affixed with "By".
	`_VEHICLE`: If the string relates to a flight death, this should be replaced with the offending vehicle (Valk/Galaxy/Lib?)
	`_FLIGHTDEATHREASON` - Specific to morning greetings, for a little extra fun. :)
	"""

	# Party Death Bus: intended for the user library fun entries.
	partyBusDeath = [
		"Bought a one way ticket to Death Valley on _USER's bus.",
		"Met an unfortunate ending when _USER's bus spontaneously exploded.",
		"Received a lesson in 'how not to drive' by _USER.",
	]
	
	# Party Bus Death By: when a user(s) is killed by being in someone elses sunderer.
	partyBusDeathBy =[
		"_USER took a one way trip to DeathVille on a party bus driven by _USERBY!",
		"_USERBY should return their bus drivers license! They killed _USER!",
		"Attention _USER, your bus to Alive City took an unfortunate detour to Death Valley, on account of _USERBY",
		"_USERBY forgot how to drive.  _USER found that out the hard way.",
		"_USER made the *grave* mistake of getting into _USERBY's party bus.",
		"Attention _USERBY!\nYou have been enrolled on a Sunderer driving course, courtesy of _USER",
		"_USERBY forgot that wheels are supposed to touch the ground. __USER had to make use of the emergency bucket.",
		"Dear _USERBY.\nI would like to inform you that sunderers do not fly, nor are their wheels supposed to aim upwards.\n\nSincerely, _USER",
	]


	flightDeath =[
		"Met an unfortunate end when _USER's _VEHICLE spontaneously exploded.",
		"Waiting for a bonus check after _USER crashed their _VEHICLE... again.",
		"Died to _USER's inability to fly a skybus.",
		"Got in _USER's _VEHICLE.  That was a *grave* mistake.",
		"Received a lesson in 'How not to fly' by _USER."
	]
	#################
	"""# FLIGHT DEATH:
	Intended for user library entries (for fun).
	When the player has been killed by a squadmate's (`_USER`) dying vehicle"""


	flightDeathBy = [
		"_USER just went splat after _USERBY forgot which way is up.",
		"_USER is awaiting a bonus check after _USERBY crashed their _VEHICLE.\n\n**Again.**",
		"_USERBY forgot how to fly.  _USER paid the price.",
		"_USERBY forgot how to fly. _USER found that out the hard way.",
		"RIP _USER.  There's no funeral service since _USERBY is still paying their _VEHICLE Insurance Premium.",
		"Really, _USER?  Next time you're in _USERBY's _VEHICLE, familiarise yourself with the eject feature.  If you get in their _VEHICLE again, that is.",
		"ATTENTION!  _USERBY just obliterated _USER!\nHow you ask?  _USERBY had one too many to drink and crashed their _VEHICLE.",
		"_USERBY hit a stray branch with their _VEHICLE and rooted _USER's death!",
		"_USERBY hit a stray branch with their _VEHICLE and killed _USER in a fiery inferno!",
		"Who let _USERBY drink?  They did 3 loop-de-loops, flew upside down, went sideways and crashed backwards into a resupply tower.  Don't believe me?  Ask _USER!  Perhaps wait until they finish using the bucket, though.",
		"After much deliberation, NC headquarters has deemed it appropriate to revoke _USERBY's _VEHICLE flying privilages.\n_USER, you will be sent a bonus check in due time for this incident.\n\nPlease alert us if _USERBY is seen flying a _VEHICLE again!",
		"_USER got too comfortable in _USERBYs _VEHICLE...  \n\nCan I have some of those marshmellows?",
		"_USER just became part of the scenery.  You can find their 'additions' right next to the burning remains of _USERBY's _VEHICLE.",
		"Attention, _USERBY.\nYou have been enrolled on a _VEHICLE Flight training course, courtesy of _USER",
	]
	############
	"""# Flight Death by:
	When a user(s) (`_USER`) is killed by being in someone elses(`_USERBY`) galaxy/Valk (`_VEHICLE`)"""



	morningGreetings = [
		"G'Mornin', _USER!",
		"Morning! :D",
		"It is?",
		"Is it?",
		"Top o' the mornin' to ya, _USER!",
		"Afternoon. :)",
		"Hello there _USER!",
		"_USER, it's too early.  Go back to bed.",
		"And a glorious morning to you, too, _USER!",
		"Why are you awake? Why are you awake?!",
		"I've checked with my bar clock, and I have to disagree with you, Sir.",
		"I've checked with my bar clock, and I must say you're positively delirious, Sir.",
		"... You've had one too many drinks today, _USER",
		"Are you sure?",
		"I'm going back to bed...",
		"Glorious pleasantries to you too, _USER!",
		"It's 5 o'Clock somewhere. 🍷",
		"Morning, _USER. \nI heard you flown with Cactus recently... how was it?  Did he _FLIGHTDEATHREASON?",
		"Morning, _USER. \nI heard you flown with DoubleD recently... how was it?  Did he _FLIGHTDEATHREASON?",
		"¿ɹǝpun uʍop ǝɟıl s,ʍoɥ  ¡ƃuıuɹoɯ pooƃ",
	]


	morningGreetingsGif = [
		"https://giphy.com/gifs/hello-hi-wave-xT9IgG50Fb7Mi0prBC",
		"https://giphy.com/gifs/halloween-morning-grumpy-4rKr0feK7xfO0",
		"https://tenor.com/bAFsa.gif",
		"https://tenor.com/rvIY.gif",
		"https://tenor.com/blv8V.gif",
		"https://media.tenor.com/PZf33FwKn-0AAAAd/good-morning-funny.gif",
		"https://giphy.com/gifs/warnerarchive-warner-archive-julie-christie-petulia-26uf05j0KemLdP58A",
		"https://media3.giphy.com/media/j6BdaJIYXPSkUOF33H/giphy.gif",
		"https://media.tenor.com/vL8iJNn7tjcAAAAM/awake-woke.gif",
		"https://media.tenor.com/Pb2FdndScvgAAAAd/good-morning-unhappy.gif",
		"https://media.tenor.com/lzNPKl40wigAAAAM/figaro-pinocchio.gif",
		"https://media.tenor.com/bT5Ha1rqXpkAAAAM/no-u-michael-scott-no-u.gif",
		"http://giphygifs.s3.amazonaws.com/media/ANbD1CCdA3iI8/200.gif",
	]


	# Specific to morning greeting.
	flightDeathReason = [
		"prematurely explode",
		"crash into a stray tree and die in a fiery inferno",
		"forget which way is up",
		"have one too many to drink",
		"manage to not crash it this time"
	]