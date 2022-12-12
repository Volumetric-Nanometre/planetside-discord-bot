"""
SETTINGS

All settings for the bot are listed below, split into classes which can act as headers for easier finding.
These settings pertain to the overall behaviour of the bot, not individual items.
"""
from discord import SelectOption
import botData.envVars as Env
from dataclasses import dataclass
from enum import Enum

@dataclass(frozen=True)
class BotSettings():
	# TOKENS LOADED FROM .ENV FILE
	discordToken = Env.DISCORD_TOKEN
	discordGuild = Env.DISCORD_GUILD
	ps2ServiceID = Env.PS2_SVS_ID
	botDir		 = Env.BOT_DIR

	# Debug Enabled: set to false during live use to reduce console clutter.
	bDebugEnabled = True

	# Force Role restrictions: when true, hard-coded restrictions prohibit command usage based on the roles below; users unable to call commands setup within the client are still unable to call commands regardless of this setting.  As such, this is merely a redundancy.
	bForceRoleRestrictions = True

	# Force Role Restrictions, use ID: set to TRUE if Role IDs are used instead of role names.
	bForceRestrictions_useID = False

	# Role Restrict Level 0 : Used for major bot commands.
	roleRestrict_level_0 = ["CO"]

	# Role Restrict Level 1 : Used for most Operations related commands.
	roleRestrict_level_1 = ["Captain", "Lieutenant"]

	# Role restrict Level 2: Used for commands that should be limited to mid-tier roles.
	roleRestrict_level_2 = ["Sergeant", "Corporal", "Lance-Corporal"]

	# Role Restrict Level 3: Used for commands that should be usable by base roled members.
	roleRestrict_level_3 = ["DrunkenDogs", "Recruits", "The-Washed-Masses"]

# USED PRIMARILY BY NEW USER
	# New User Admin Chanel: the channel (ID) new user join requests are sent to.
	newUser_adminChannel = 1049424595750506527

	# Gate Channel: Channel (ID) where new user join forms are sent to.
	newUser_gateChannelID = 1041860598822096950

	#General Channel: ID of the general channel.
	generalChanelID = 358702477962379274

	# Minimum Read time: The number of minutes a user has to wait (to read the rules) before they are able to request access.
	newUser_readTimer = 1

	# Warn if a user claims a ps2 character name with a rank equal or higher than this (numerical, lower = higher rank.)
	newUser_outfitRankWarn = 4

	# New User Date Warning, discord account is less than x months old.
	newUser_newAccntWarn = 3

	# The Jump URL "rules" leads to (ensure this leads to the rules post!)
	newUser_rulesURL = "https://discord.com/channels/321688140802949120/1049523449867022348/1049523492166565939"

	# Collapse for ease of reading.
	def __repr__(self) -> str:
		vString = "\n	GENERAL BOT SETTINGS\n"
		vString += f"	> DebugEnabled: {self.bDebugEnabled}\n"
		if (self.bDebugEnabled):
			vString += f"	> DiscordToken: {self.discordToken}\n"
		else:
			token = self.discordToken.partition(".")[0]
			vString += f"	> DiscordToken: {token}...\n"
		vString += f"	> DiscordGuild: {self.discordGuild}\n"
		vString += f"	> PS2ServiceID: {self.ps2ServiceID}\n"
		vString += f"	> BotDirectory: {self.botDir}\n"
		vString += f"	> Force Role Restrictions: {self.bForceRoleRestrictions}\n"
		vString += f"	> Role Restriction Using IDs: {self.bForceRestrictions_useID}\n"
		vString += f"	> Level 0: {self.roleRestrict_level_0}\n"
		vString += f"	> Level 1: {self.roleRestrict_level_1}\n"
		vString += f"	> Level 2: {self.roleRestrict_level_2}\n"
		vString += f"	> Level 3: {self.roleRestrict_level_3}\n"
		vString += f"	> New user Admin Channel: {self.newUser_adminChannel}\n"
		vString += f"	> New user Gate channel : {self.newUser_gateChannelID}\n"
		vString += f"	> New user Rules URL: {self.newUser_rulesURL}\n"
		vString += f"	> New user | Read timer:{self.newUser_readTimer} | AccountWarn: {self.newUser_newAccntWarn} | OutfitRank Warn: {self.newUser_outfitRankWarn}\n"
		return vString

class CommandRestrictionLevels(Enum):
	"""
	# COMMAND RESTRICTION LEVELS
	Convenience Enum for setting levels.

	Should be used instead of raw roleRestrict_level_n
	"""
	level0 = BotSettings.roleRestrict_level_0
	level1 = level0 + BotSettings.roleRestrict_level_1
	level2 = level1 + BotSettings.roleRestrict_level_2
	level3 =level2 + BotSettings.roleRestrict_level_3

@dataclass(frozen=True)
class Directories:
	"""
	# DIRECTORIES

	Directories used by the bot.

	If changing the values, make sure slashes are present when needed.
	"""

	# File directory to preceed all directories.
	prefixDir = f"{BotSettings.botDir}/SavedData/"

	# File directory for live Ops.
	liveOpsDir = f"{prefixDir}LiveOps/"

	# File directory for saved defaults.
	savedDefaultsDir = f"{prefixDir}Defaults/"

	# File directory for saved user data.
	userLibrary = f"{prefixDir}Users/"

	# Name used on lock files as an affix.
	lockFileAffix = ".LOCK"

	# Number of attempts to try obtaining a lock before returning.
	lockFileRetry = 5

	# Collapse for ease of reading.
	def __repr__(self) -> str:
		vString = "	BOT DIRECTORY SETTINGS\n"
		vString += f"	> Prefix Dir : {self.prefixDir}\n"
		vString += f"	> LiveOps Dir: {self.liveOpsDir}\n" 
		vString += f"	> DefaultsDir: {self.savedDefaultsDir}\n" 
		vString += f"	> UserLib Dir: {self.userLibrary}\n\n" 
		vString += f"	> LockFile Affix: {self.lockFileAffix} | Retries: {self.lockFileRetry}\n" 
		return vString


@dataclass(frozen=True)
class SignUps:
	"""
	# SIGNUPS

	Settings used by signups.

	NOTE:  These are NOT settings for individual signups! See `botData.operations.operationOptions` for those.
	"""

	# The category name (if using existing category, must match capitalisation!)
	signupCategory = "SIGN UP"

	# Icon used for built in RESIGN role.
	resignIcon = "❌"

	# Icon used for built in RESERVE role
	reserveIcon = "⭕"

	# Number of minutes before an ops scheduled start the bot starts AutoStart enabled Ops (Non AutoStart enabled Ops require a user to open an OpsEditor and open the Commander from there.)
	autoPrestart = 30

	def __repr__(self) -> str:
		vString = "	SIGN UP SETTINGS\n"
		vString += f"	> Signup Cat  : {self.signupCategory}\n"
		vString += f"	> Resign Icon : {self.resignIcon}\n" 
		vString += f"	> Reserve Icon: {self.reserveIcon}\n" 
		vString += f"	> AutoPrestart: {self.autoPrestart} minutes\n" 
		return vString

@dataclass(frozen=True)
class Messages:
	"""
	# MESSAGES
	Messages used throughout the bot, typically for end-users, stored here for convenient editing purposes.
	"""
	
	# Displayed in the GATE channel on bot startup (after purging).
	gateChannelDefaultMsg = "Welcome to TDKD.\nIf a join request has not been created for you, or you have already sent one and it's no longer here, please re-join the server. \nOur bot has been restarted."

	# Displayed in the embed for new users in their gate message.
	newUserInfo = "Use the buttons below to provide your Planetside 2 character name and read the rules.\nThen you can request access, and wait for one of our admins to get you set up!"

	# Displayed in the embed for new users in their gate message, under RULES.
	newUserRuleDeclaration = "By pressing 'REQUEST ACCESS', you are confirming **you have read**, **understand**, and **agree to adhere** by the rules."

	# Displayed after the mention line when a new user joins.
	newUserWelcome = "Make sure to use `/roles` to assign both PS2 and other game related roles (and access related channels)!"

	# Displayed when a user is choosing roles to ADD.
	userAddingRoles = "Select the roles you wish to **ADD** using the dropdowns, then click update."

	# Displayed when a user is choosing roles to REMOVE.
	userRemovingRoles = "Select the roles you wish to **REMOVE** using the dropdowns, then click Update."


@dataclass(frozen=True)
class Roles():
	"""
	# ROLES
	For convenience sake, all roles used within selectors are stored here

	NOTE: Selectors have a MAXIMUM limit of 25 items;
			This is a discord imposed limit.
	"""
	# SelectOption(label="", value="", description="", emoji=""),

	# Provides a dropdown containing these roles for giving to new users.
	newUser_roles = [ 
		SelectOption(label="Guest", value="roleIDHere_123"), # Couldn't find someone with this role to copy the ID from.
		SelectOption(label="Recruit", value="780253442605842472"),
		SelectOption(label="TDKD", value="710472193045299260"), # 1050286811940921344 <- Dev server RoleID | 710472193045299260 <- Live server RoleID
		SelectOption(label="The Washed Masses", value="710502581893595166"),
		SelectOption(label="The Unwashed Masses", value="719219680434192405")
	]

	# ADD ROLES - TDKD:  Roles used in the /roles command, "tdkd" role selector 
	addRoles_TDKD = [
		#SelectOption(label="Planetside", value="TDKD", description="The main role for TDKD planetside.", emoji=''),
		SelectOption(label="Planetside Pings", value="977873609815105596", description="Non-major PS2 events/fellow\n drunken doggos looking for company"),
		SelectOption(label="Sober Dogs", value="745004244171620533", description="More serious, coordinated infantry events"), # Dev value: 1040751250163122176 | Live value 745004244171620533
		SelectOption(label="Base Busters", value="811363100787736627", description="Base building and busting events"),
		SelectOption(label="Armour Dogs", value="781309511532544001", description="Ground vehicle related events"),
		SelectOption(label="Dog Fighters", value="788390750982766612", description="Small aerial vehicle related events"),
		SelectOption(label="Royal Air Woofs", value="848612413943054376", description="Heavy aerial vehicle related events"),
		SelectOption(label="PS2 Twitter", value="832241383326744586", description="Planetside 2 Twitter posts"),
		SelectOption(label="Jaeger", value="1024713062776844318", description="Jeager events")
		# discord.SelectOption(label="", value="", description="", emoji='')
	]

	# ADD ROLES - GAMES : Role selectors used in the /roles command.
	addRoles_games1 = [
		SelectOption(label="Post Scriptum", value="791308463241691146"),
		SelectOption(label="Squad", value="808413252685529108"),
		SelectOption(label="Space Engineers", value="805234496026050601"),
		SelectOption(label="Deep Rock Galactic", value="803340218756366423"),
		SelectOption(label="Valheim", value="818490876631711794"),
		SelectOption(label="Terraria", value="825106136378245180"),
		SelectOption(label="Apex Legends", value="825106272856571985"),
		SelectOption(label="Minecraft", value="824708493076201473"),
		SelectOption(label="Team Fortress 2", value="826943611303100496"),
		SelectOption(label="Dungeon and Dragons", value="864175083152343070"),
		SelectOption(label="Warframe", value="872593227734208512"),
		SelectOption(label="Supreme Commander", value="887338095802982441"),
		SelectOption(label="Battlefield 2042", value="894232796619472987"),
		SelectOption(label="Conqueror's Blade", value="896008973906509885"),
		SelectOption(label="Stellaris", value="911972761948266547"),
		SelectOption(label="Eve Online", value="900009823867916310"),
		SelectOption(label="Sea of Thieves", value="916802105719783454"),
		SelectOption(label="Back 4 Blood", value="916804112337756160"),
		SelectOption(label="Garrys' Mod", value="916803968674439300"),
		SelectOption(label="Killing Floor 2", value="916804287370240131"),
		SelectOption(label="Vermintide", value="929376317944791040"),
		SelectOption(label="Total War: Warhammer", value="931201327869079553"),
		SelectOption(label="Factorio", value="939894580688605274"),
		SelectOption(label="Warthunder", value="976598559266857030"),
		SelectOption(label="Gates of Hell", value="1000366778133774528")
	]

	addRoles_games2 = [
		SelectOption(label="Overwatch", value="1029138196518420531"),
		SelectOption(label="World of Tanks", value="1038125253806788768"),
		SelectOption(label="Star Citizen", value="1037797784566370318")		
	]