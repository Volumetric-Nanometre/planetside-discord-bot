#  Contains all DATA types, relating to ops and general bot functionality.
# This includes: Channels, Op defaults, Op Signups
from enum import Enum
from dataclasses import dataclass, field
import datetime
import settings
import botUtils


# Enum to assist in making things easier to read.
# Potentially just made this redundant. :p
class OpsTypes(Enum):
	Custom = 0
	SoberDogs = 1
	ArmourDogs = 2
	DogFighter = 3
	RoyalAirWoof = 4
	BaseBusters = 5


# class AddOpsEnum(object):
# 	OpsEnum: Enum = Enum("OpsType", ["Custom", "(noSavedDefaults)"])
# 	def __new__(cls):
# 		if not hasattr(cls, 'instance'):
# 			cls.instance = super(AddOpsEnum, cls).__new__(cls)
# 		return cls.instance
		

class OpsStatus(Enum):
	editing = -1 # Ops is being edited, users can't signup.
	open = 1 # Open to signups.
	prestart = 10 # set when pre-op setup starts.
	started = 20 # Ops started.
	debriefing = 30 # Probably redundant. 



@dataclass
class OpRoleData:
	"""
	Data pertaining to an individual role on an Operation
	"""
	players : list = field(default_factory=list) #User IDs
	roleName : str = ""
	roleIcon : str = ""
	maxPositions : int = 0

	def __init__(self, pRoleName, pRoleIcon, pMaxPos) -> None:
		botUtils.BotPrinter.Debug(f"Op Role data initialised.")
		self.players = []
		self.roleName = pRoleName
		self.roleIcon = pRoleIcon
		self.maxPositions = pMaxPos

@dataclass
class OperationOptions:
	"""
	Options, typically altered via use of arguments, to determine behaviour of the ops.
	"""
	bUseReserve : bool = True # Only enable built in RESERVE if true.
	bUseCompact : bool = False # Not yet used, argument: -COMPACT; does not show a member list for each role.


#OperationData: Information relating to the Op as a whole, includes a list of OpRoleData objects.
@dataclass
class OperationData:
	"""
	Data pertaining to an Operation.
	Includes a list of OpRoleData objects.
	"""
	# List of OpRoleData objects
	roles : list = field(default_factory=list)
	reserves : list = field(default_factory=list) # Since there's no need for special data for reserves, they just have a simple UserID list.
	# Op Details:
	name : str = ""
	fileName: str = ""
	date : datetime.datetime = datetime.datetime.now()
	description : str = ""
	customMessage : str = ""
	messageID : str = "" # Stored to make accessing and editing quicker/avoid having to find it.
	status : OpsStatus = OpsStatus.open
	voiceChannels: list = field(default_factory=list)
	arguments: list = field(default_factory=list)
	options: OperationOptions = OperationOptions


	def GenerateFileName(self):
		self.fileName = f"{self.name}_{self.date.year}-{self.date.month}-{self.date.day}_{self.date.hour}-{self.date.minute}"
		
		botUtils.BotPrinter.Debug(f"Filename for Op {self.name} generated: {self.fileName}")

	def GetFullFilePath(self):
		return f"{settings.botDir}/{settings.opsFolderName}/{self.fileName}.bin"

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

	def __init__(self) -> None:
		self.roles = []
		self.reserves = []
		self.voiceChannels = []
		self.arguments = []
		botUtils.BotPrinter.Debug(f"Op Data initialised.")

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


# class DefaultOps_ArmourDogs(OperationData):

# 	name: str = "Armour Dogs"
# 	description: str = "It's armour time bishes!"
# 	roles : list = [
# 		OpRoleData([], "Vanguard", '<:Icon_Vanguard:795727955896565781>', -1), 
# 		OpRoleData([], "Sunderer", '<:Icon_Sunderer:795727911549272104>', -1),
# 		OpRoleData([], "Lightning", '<:Icon_Lightning:795727852875677776>', -1) ,
# 		OpRoleData([], "Harasser", '<:Icon_Harasser:795727814220840970>', -1)
# 	]


# class DefaultOps_SoberDogs(OperationData):

# 	name: str = "Sober Dogs"
# 	description: str = "It's SRS BSNS time bishes!"
# 	roles: list = [
# 		OpRoleData([], "Heavy", '<:Icon_Heavy_Assault:795726910344003605>', -1),
# 		OpRoleData([], "Light", '<:Icon_Light_Assault:795726936759468093>', -1),
# 		OpRoleData([], "Medic", '<:Icon_Combat_Medic:795726867960692806>', -1),
# 		OpRoleData([], "Engineer", '<:Icon_Engineer:795726888763916349>', -1) ,
# 		OpRoleData([], "Infiltrator", '<:Icon_Infiltrator:795726922264215612>', -1),
# 		OpRoleData([], "MAX", '<:Icon_MAX:795726948365631559>', -1) 
# 	]
