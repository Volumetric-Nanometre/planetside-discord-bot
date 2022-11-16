#  Contains all DATA types, relating to ops and general bot functionality.
# This includes: Channels, Op defaults, Op Signups
from enum import Enum
from dataclasses import dataclass, field


# Enum to assist in making things easier to read.
# Potentially just made this redundant. :p
class OpsTypes(Enum):
	Custom = 0
	SoberDogs = 1
	ArmourDogs = 2
	DogFighter = 3
	RoyalAirWoof = 4
	BaseBusters = 5

# OpRoleData:  Signup Data pertaining to an individual role on an Operation.
# @dataclasses_json
@dataclass
class OpRoleData:
	players : list = field(default_factory=list) #User IDs
	roleName : str = field(default_factory=str)
	roleIcon : str = field(default_factory=str)
	maxPositions : int = field(default_factory=int)

#OperationData: Information relating to the Op as a whole, includes a list of OpRoleData objects.
# @dataclasses_json
@dataclass
class OperationData:
	# List of OpRoleData objects
	roles : list = field(default_factory=list)
	reserves : list = field(default_factory=list) # Since there's no need for special data for reserves, they just have a simple UserID list.
	# Op Details:
	name : str = field(default_factory=str)
	date : str = field(default_factory=str)
	description : str = field(default_factory=str)
	customMessage : str = field(default_factory=str)
	additionalRoles : str = field(default_factory=str)
	messageID : str = field(default_factory=str) # Stored to make accessing and editing quicker/avoid having to find it.





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
