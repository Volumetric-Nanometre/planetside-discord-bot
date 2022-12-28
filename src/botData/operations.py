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
	bUseCompact : bool = False # Not yet used, argument: -COMPACT; does not show a member list for each role.
	bAutoStart : bool = True # If false, someone must use `/op-commander [OpData]` to start the commander.
	bUseSoberdogsFeedback : bool = False # If true, debriefing opens a new forum thread and send the feedback message there.


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

	# Backend variables
	messageID : str = "" 
	status : OpsStatus = OpsStatus.open
	targetChannel: str = ""
	options: OperationOptions = OperationOptions()

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
		GET ROLE BY NAME
		RETURN: OpRoleData matching p_roleName

		Convenience function to avoid repetition.
		"""
		role: OpRoleData
		for role in self.roles:
			if role.roleName == p_roleName:
				return role


	def ParseArguments(self):
		"""
		# PARSE ARGUMENTS
		Parses the arguments given and sets their respective options.
		"""
		BUPrint.Debug("Parsing opdata arguments")
		argument:str
		for argument in self.arguments:
			argInLower = argument.lower()
			# TOGGLE VIEW TYPE
			if argInLower.__contains__("compact"):
				self.options.bUseCompact = True
				BUPrint.Debug(f"Using viewmode: Compact for {self.name}")

			elif argInLower.__contains__("fullview"):
				self.options.bUseCompact = False
				BUPrint.Debug(f"Using viewmode: Full for {self.name}")


			# TOGGLE RESERVE
			if argInLower.__contains__("noreserve"):
				self.options.bUseReserve = False
				BUPrint.Debug(f"Setting Reserves: ON for {self.name}")

			elif argInLower.__contains__("reserveson"):
				self.options.bUseReserve = True
				BUPrint.Debug(f"Setting Reserves: OFF for {self.name}")


			# TOGGLE AUTO START
			if argInLower.__contains__("noauto"):
				self.options.bAutoStart = False
				BUPrint.Debug(f"Setting Automatic Start: OFF for {self.name}")

			elif argInLower.__contains__("autostart"):
				self.options.bAutoStart = True
				BUPrint.Debug(f"Setting Automatic Start: ON for {self.name}")


			# TOGGLE SOBERDOGS FEEDBACK
			if argInLower.__contains__("nofeedback"):
				self.options.bUseSoberdogsFeedback = False
				BUPrint.Debug(f"Setting Soberdogs Feedback: OFF for {self.name}")

			elif argInLower.__contains__("soberfeedback"):
				self.options.bUseSoberdogsFeedback = True
				BUPrint.Debug(f"Setting Soberdogs Feedback: ON for {self.name}")


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