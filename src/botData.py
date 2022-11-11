#  Contains all DATA types, relating to ops and general bot functionality.
# This includes: Channels, Op defaults, Op Signups

import dataclasses
import dataclasses_json

@dataclasses.dataclass
class TDKDServer:
	guildID : str = 321688140802949120 # TESTING SERVER
	# guildID : str = 697791984445685810 # TDKD LIVE SERVER
	# List of game roles.
	GameRoles_1 = [
		"Planetside 2",
		"Post Scriptum"
		"Squad"
		"Space Enginners"
		"Deep Rock Galactic"
		"Valheim"
		"Terraria"
		"Apex Legends"
		"Minecraft"
		"Team Fortress 2"
		"Dungeons and Dragons"
		"Warframe"
		"Supreme Commander"
		"Battlefield 2042"
		"Conqueror's Blade"
		"Stellaris"
		"Sea of Thieves"
		"Back 4 Blood"
		"Garry's Mod"
		"Killing Floor 2"
		"Vermintide"
		"Total War: Warhammer"
		"Factorio"
		"War Thunder"
	]
	# Continuation of game roles.
	GameRoles_2 = [
		"Gates of Hell"
		"Overwatch"
		"World of Tanks"
		"Star Citizen"
	]


# OpRoleData:  Signup Data pertaining to an individual role on an Operation.
@dataclasses_json
@dataclasses.dataclass
class OpRoleData:
	players : list #User IDs
	roleName : str = ""
	roleIcon : str = ""
	maxPositions : int = -1

#OperationData: Information relating to the Op as a whole, includes a list of OpRoleData objects.
@dataclasses_json
@dataclasses.dataclass
class OperationData:
	# List of OpRoleData objects
	roles : list = []
	reserves : list = [] # Since there's no need for special data for reserves, they just have a simple UserID list.
	# Op Details:
	name : str = ""
	date : str = ""
	description : str = ""
	customMessage : str = ""
	additionalRoles : str = ""
	messageID : str = "" # Stored to make accessing and editing quicker/avoid having to find it.



class DefaultOps_ArmourDogs(OperationData):

	name: str = "Armour Dogs"
	description: str = "It's armour time bishes!"
	roles : list = [
		OpRoleData([], "Vanguard", '<:Icon_Vanguard:795727955896565781>', -1), 
		OpRoleData([], "Sunderer", '<:Icon_Sunderer:795727911549272104>', -1),
		OpRoleData([], "Lightning", '<:Icon_Lightning:795727852875677776>', -1) ,
		OpRoleData([], "Harasser", '<:Icon_Harasser:795727814220840970>', -1)
	]


class DefaultOps_SoberDogs(OperationData):

	name: str = "Sober Dogs"
	description: str = "It's SRS BSNS time bishes!"
	roles: list = [
		OpRoleData([], "Heavy", '<:Icon_Heavy_Assault:795726910344003605>', -1),
		OpRoleData([], "Light", '<:Icon_Light_Assault:795726936759468093>', -1),
		OpRoleData([], "Medic", '<:Icon_Combat_Medic:795726867960692806>', -1),
		OpRoleData([], "Engineer", '<:Icon_Engineer:795726888763916349>', -1) ,
		OpRoleData([], "Infiltrator", '<:Icon_Infiltrator:795726922264215612>', -1),
		OpRoleData([], "MAX", '<:Icon_MAX:795726948365631559>', -1) 
	]
