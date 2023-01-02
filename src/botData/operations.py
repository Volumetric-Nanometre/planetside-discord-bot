from enum import Enum
from dataclasses import dataclass, field
import datetime
from botUtils import BotPrinter as BUPrint
import botData.settings

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
	roles : list = field(default_factory=list) # List of OpRoleData objects
	reserves : list = field(default_factory=list) # Since there's no need for special data for reserves, they just have a simple UserID list.
	name : str = ""
	fileName: str = ""
	date : datetime.datetime = datetime.datetime.now()
	description : str = ""
	customMessage : str = ""
	managedBy:str = ""
	pingables : list = field(default_factory=list) # roles to mention/ping in relation to this ops.

	# Backend variables
	messageID : str = "" 
	status : OpsStatus = OpsStatus.open
	targetChannel: str = ""
	options: OperationOptions = OperationOptions()
	jumpURL: str = ""

	# Factory fields
	voiceChannels: list = field(default_factory=list)
	arguments: list = field(default_factory=list)


	def GenerateFileName(self):
		self.fileName = f"{self.name}_{self.date.year}-{self.date.month}-{self.date.day}_{self.date.hour}-{self.date.minute}"
		
		BUPrint.Debug(f"Filename for Op {self.name} generated: {self.fileName}")


	def GetFullFilePath(self):
		return f"{botData.settings.Directories.liveOpsDir}{self.fileName}.bin"


	def GetRoleByName(self, p_roleName):
		"""
		# GET ROLE BY NAME
		### RETURN: 
		`OpRoleData` matching `p_roleName`

		Convenience function to avoid repetition.
		"""
		role: OpRoleData
		for role in self.roles:
			if role.roleName == p_roleName:
				return role


	def ArgStringToList(self, p_string:str, p_deliminator:str = " "):
		"""
		# ARGUMENT STRING TO LIST
		Converts an argument string to a list, then runs Parse.
		A deliminator may be specified, uses ' ' by default.
		"""
		newArgList = p_string.split(p_deliminator)

		if newArgList != None:
			BUPrint.Debug(f"Setting op argument list: {newArgList}")
			self.arguments = newArgList

			BUPrint.Debug(f"OpData Argument list: {self.arguments}")

			self.ParseArguments()

		else:
			BUPrint.Debug("No arguments.")


	def ParseArguments(self):
		"""
		# PARSE ARGUMENTS
		Parses the arguments given and sets their respective options.
		"""
		BUPrint.Debug(f"Parsing opdata arguments: {self.arguments}")
		argument:str
		for argument in self.arguments:

			argInLower = argument.lower().strip()

			# TOGGLE VIEW TYPE
			if argInLower == "compact":
				self.options.bUseCompact = True
				BUPrint.Debug(f"Using viewmode: Compact for {self.name}")
				continue

			elif argInLower == "fullview":
				self.options.bUseCompact = False
				BUPrint.Debug(f"Using viewmode: Full for {self.name}")
				continue


			# TOGGLE RESERVE
			if argInLower == "noreserve":
				self.options.bUseReserve = False
				BUPrint.Debug(f"Setting Reserves: OFF for {self.name}")
				continue

			elif argInLower == "reserveon":
				self.options.bUseReserve = True
				BUPrint.Debug(f"Setting Reserves: ON for {self.name}")
				continue


			# TOGGLE AUTO START
			if argInLower == "noauto":
				self.options.bAutoStart = False
				BUPrint.Debug(f"Setting Automatic Start: OFF for {self.name}")
				continue

			elif argInLower == "autostart":
				self.options.bAutoStart = True
				BUPrint.Debug(f"Setting Automatic Start: ON for {self.name}")
				continue


			# TOGGLE SOBERDOGS FEEDBACK
			if argInLower == "nofeedback":
				self.options.bUseSoberdogsFeedback = False
				BUPrint.Debug(f"Setting Soberdogs Feedback: OFF for {self.name}")
				continue

			elif argInLower == "soberfeedback":
				self.options.bUseSoberdogsFeedback = True
				BUPrint.Debug(f"Setting Soberdogs Feedback: ON for {self.name}")
				continue


			# TOGGLE PS2 EVENT
			if argInLower == "ps2event":
				self.options.bIsPS2Event = True
				BUPrint.Debug(f"Setting PS2 Event: ON for {self.name}")
				continue

			elif argInLower == "notps2":
				self.options.bIsPS2Event = False
				BUPrint.Debug(f"Setting PS2 Event: OFF for {self.name}")
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
	textChannels = []
	# Op Commander Channel: Name of the channel used for the Ops Commander
	opCommander = "Commander"
	# Notification Channel: Name of channel used to send op auto alerts and interactive debrief messages.
	notifChannel = "Notifications"
	# Standby channel- the channel(name) users are moved into if they are connected during Ops soft start
	standByChannel = "Standby"
	# Persistent Voice channels are channels that are ALWAYS created for every operation
	persistentVoice = []
	# If voice channels are not specified in the ops data, these are used instead
	voiceChannels = ["Squad-Alpha", "Squad-Beta", "Squad-Charlie", "Squad-Delta"]
	# Debrief: If not specified in Ops data, this is used instead
	debriefChannel = "debrief"


@dataclass
class UserSession:
	"""
	# USER SESSION
	Dataclass pertaining to a users session statistics.
	"""
	eventName: str = ""
	eventDate: datetime = None
	# Stats Tracked
	kills: int = 0
	deaths: int = 0
	assists: int = 0
	score: int = 0