"""
SETTINGS

All settings for the bot are listed below, split into classes which can act as headers for easier finding.
These settings pertain to the overall behaviour of the bot, not individual items.

If you're looking for Emoji Library, see `botUtils.EmojiLibrary`.

For more help:
https://github.com/LCWilliams/planetside-discord-bot/wiki/Bot-Configuration/
"""
from discord import SelectOption
import botData.envVars as Env
from dataclasses import dataclass
from enum import Enum

@dataclass(frozen=True)
class BotSettings:
	# TOKENS LOADED FROM .ENV FILE
	discordToken = Env.DISCORD_TOKEN
	discordGuild = Env.DISCORD_GUILD
	ps2ServiceID = Env.PS2_SVS_ID
	botDir		 = Env.BOT_DIR

	# Admin Chanel: The chanel admin related features are directed to.
	adminChannel = 1049424595750506527 # DEV VALUE
	# adminChannel = 1 # LIVE VALUE

	# Debug Enabled: set to false during live use to reduce console clutter.
	bDebugEnabled = True

	# ID of a channel which users are moved to when their current one is removed; this value is used when otherwise specified channels are not found.
	fallbackVoiceChat = 326783867036106752 # Dev value!
	# fallbackVoiceChat = 710854499782361140 # LIVE value (general)

	# ROLE RESTRICTION LEVELS:
	roleRestrict_level_0 = ["CO"]

	roleRestrict_level_1 = ["Captain", "Lieutenant"]

	roleRestrict_level_2 = ["Sergeant", "Corporal", "Lance-Corporal"]

	roleRestrict_level_3 = ["DrunkenDogs", "Recruits", "The-Washed-Masses", "The-Unwashed-Masses"]

	"""
	Force Role restrictions: when true, hard-coded restrictions prohibit command usage based on the roles in roleRestrict variables.
	users unable to call commands setup within the discord client are still unable to call commands regardless of this setting.
	As such, this is merely a redundancy if security concerned."""
	bForceRoleRestrictions = True


	# Collapse for ease of reading.
	def __repr__(self) -> str:
		vString = "\n	GENERAL BOT SETTINGS\n"
		vString += f"	> DebugEnabled: {self.bDebugEnabled}\n"
		token = self.discordToken[:5] # Always hide most of the token.
		vString += f"	> DiscordToken:	{token}...\n"
		vString += f"	> DiscordGuild:	{self.discordGuild}\n"
		token = self.ps2ServiceID[:5]
		vString += f"	> PS2ServiceID:	{token}\n"
		vString += f"	> BotDirectory:	{self.botDir}\n"
		vString += f"	> AdminChannel:	{self.adminChannel}\n"
		vString += f"	> Force Role Restrictions: {self.bForceRoleRestrictions}\n"
		vString += f"	> Level 0:	{self.roleRestrict_level_0}\n"
		vString += f"	> Level 1:	{self.roleRestrict_level_1}\n"
		vString += f"	> Level 2:	{self.roleRestrict_level_2}\n"
		vString += f"	> Level 3:	{self.roleRestrict_level_3}\n"
		vString += f"	> Fallback VC:	{self.fallbackVoiceChat}\n"
		return vString


@dataclass(frozen=True)
class NewUsers:
	"""
	# NEW USERS
	Settings pertaining to the bot behaviour for `NewUser` cog.
	"""
	# Create Library Entry on Accept: When true, after a user has been accepted, automatically create a user entry for them.
	bCreateLibEntryOnAccept = True

	# Recruit Role: ID of the recruit role.  Used to automatically apply isRecruit to user entry (if above is enabled)
	# recruitRole = 780253442605842472 # LIVE
	recruitRole = 1060009718837411962 # DEV VALUE

	# Auto Assign Roles: A list of role IDs that are always assigned when a user is accepted.
	autoAssignRoles = [818218528372424744] # Currently just "Tags"

	# Gate Channel: Channel (ID) where new user join forms are sent to.
	gateChannelID = 1041860598822096950

	#General Channel: ID of the general channel. (accepted user welcome messages are sent here)
	generalChanelID = 358702477962379274

	# Warn if a user claims a ps2 character name with a rank equal or higher than this (numerical, lower = higher rank.)
	outfitRankWarn = 4

	# New User Date Warning, discord account is less than x months old.
	newAccntWarn = 3

	# Rule Message ID: The id of a message which contains the server rules (if not in an embed, falls back to message content)
	ruleMsgID = 1049631022192537610 # DEV SERVER
	# ruleMsgID = 977888774530932767 # LIVE SERVER

	# Rule Channel ID: The ID of the channel which the Rules message is in.
	ruleChnID = 1049523449867022348 # DEV SERVER 
	# ruleChnID = 913086821263626360 # LIVE SERVER

	# Show Add Roles Button: When true, a button to add roles is shown in the welcome message.
	# It is advisable to ensure the message reflects the presence or lack of this button.
	bShowAddRolesBtn = True


	def __repr__(self) -> str:
		vString = "\n	NEW USER SETTINGS\n"
		vString += f"	> Gate channel:		{self.gateChannelID}\n"
		vString += f"	> General Channel:	{self.generalChanelID}\n"
		vString += f"	> Rule Channel:		{self.ruleChnID}\n"
		vString += f"	> Rule Message:		{self.ruleMsgID}\n"
		vString += f"	> Recruit ID:		{self.recruitRole}\n"
		vString += f"	> AutoAssign Roles:	{self.autoAssignRoles}\n"
		vString += f"\n	> Warnings: Discord Account age: {self.newAccntWarn} months\n"
		vString += f"	> Warnings: Outfit Rank (Ord): {self.outfitRankWarn}\n"
		vString += f"	> Create Library Entry on Accept: {self.bCreateLibEntryOnAccept}\n"
		vString += f"	> Show AddRoles Button:		{self.bShowAddRolesBtn}\n"
		return vString


class PS2EventTrackOptions(Enum):
	"""
	EVENT TRACKING OPTIONS:
	Sets the requirements for when to enable tracking a ps2 event.

	NOTE: To change the setting, See `botData.settings.Commander.trackEvent`.
	"""
	Disabled = 0
	InGameOnly = 10
	InGameAndDiscordVoice = 20


@dataclass(frozen=True)
class Commander:
	"""
	# COMMANDER
	Settings used by Op Commanders.
	"""
	# Track Event: Setting to determine which participants of a ps2 event are tracked
	trackEvent = PS2EventTrackOptions.InGameOnly

	# Marked Present: Setting to determine when a participant is considered part of the event and their userLib entry is updated
	markedPresent = PS2EventTrackOptions.InGameAndDiscordVoice

	# Auto Start Commander: if true, Ops Commanders will automatically *start* their operation at the defined start time.
	bAutoStartEnabled = True

	# Enable Commander Auto Alerts: If true, Op Commanders will periodically alert users a set amount of times (below)
	bAutoAlertsEnabled = True

	# Commander Auto Alert Count: The number of automatic alerts a commander will send. These are distributed throughout the pre-start time.
	autoAlertCount = 2

	# Commander- Auto Move Voice Channel: If enabled, participating users are moved to the standby channel on Ops start if they're in a voice channel.
	bAutoMoveVCEnabled = True

	#Auto MoveBack Channel ID:  Channel ID for the channel users are moved back into (if autoMoveVC is enabled) after an ops is closed.
	autoMoveBackChannelID = 326783867036106752 # DEV SERVER VALUE (General)
	# autoMoveBackChannelID = 1023703124839518338 # LIVE SERVER VALUE (Planetside2)

	# Number of minutes before an ops scheduled start the bot prestarts AutoStart enabled Ops (Non AutoStart enabled Ops require a user to use `/ops-commander` command)
	# A buffer of 5 minutes is added to this time to ensure sufficient time for alerts.
	autoPrestart = 30

	# Sober Feedback ID: The ID of the forum to post a new SoberDogs Debrief message into.
	soberFeedbackID = 1042463290472800317

	# Connection Refresh Interval: time in seconds the connection embed is refreshed. (0 = disabled)
	# For sub-65 seconds, a valid ps2 service id is needed.
	connectionRefreshInterval = 30

	# Icons for the CONNECTIONS embed.
		# Discord
	connIcon_discord = "🖥️"
	connIcon_discordOnline = "🟢"
	connIcon_discordOffline = "🔴"
		# Discord Voice
	connIcon_voice = "🎧" 
	connIcon_voiceConnected = "🟢"
	connIcon_voiceDisconnected = "🔴"
		# Planetside2
	connIcon_ps2 = "🎮"
	connIcon_ps2Online = "🟢"
	connIcon_ps2Offline = "🔴"
	connIcon_ps2Invalid = "❌" # Users who have an invalid/non-matching PS2 name

	def __repr__(self) -> str:
		vString = "\n	OP COMMANDER SETTINGS\n"
		vString += f"	> Auto prestart:	{self.autoPrestart} minutes\n"
		vString += f"	> Auto Start:		{self.bAutoStartEnabled}\n"
		vString += f"	> Live Tracking:	{self.trackEvent.name}\n"
		vString += f"	> Marked Present:	{self.markedPresent.name}\n"
		vString += f"	> Auto Alerts:		{self.bAutoAlertsEnabled}\n"
		vString += f"	> Auto Alert count:	{self.autoAlertCount}\n"
		vString += f"	> Auto Move VC:		{self.bAutoMoveVCEnabled}\n"
		vString += f"	> Automove VC ID:	{self.autoMoveBackChannelID}\n"
		vString += f"	> Soberdogs Feedback:	{self.soberFeedbackID}\n"
		vString += f"	> ConnectionsRefresh:	{self.connectionRefreshInterval} seconds\n"
		return vString		


@dataclass(frozen=True)
class Directories:
	"""
	# DIRECTORIES

	Directories used by the bot.

	If changing the values, make sure slashes are present when needed.
	"""

	# File directory to preceed all directories.  This is not hard-coded, if you so wish, each directory can be anywhere.
	prefixDir = f"{BotSettings.botDir}/SavedData/"

	# File directory for live Ops.
	liveOpsDir = f"{prefixDir}LiveOps/"

	# File directory for saved defaults.
	savedDefaultsDir = f"{prefixDir}Defaults/"

	# File directory for saved user data.
	userLibrary = f"{prefixDir}Users/"

	# File directory for temporary files.
	tempDir = f"{prefixDir}temp/"

	# Name used on lock files as an affix.
	lockFileAffix = ".LOCK"

	# Number of attempts to try obtaining a lock before returning.
	lockFileRetry = 5

	# Collapse for ease of reading.
	def __repr__(self) -> str:
		vString = "	BOT DIRECTORY SETTINGS\n"
		vString += f"	> Prefix Dir :	{self.prefixDir}\n"
		vString += f"	> LiveOps Dir:	{self.liveOpsDir}\n" 
		vString += f"	> DefaultsDir:	{self.savedDefaultsDir}\n" 
		vString += f"	> UserLib Dir:	{self.userLibrary}\n" 
		vString += f"	> LockFile Affix:	{self.lockFileAffix} | Retries: {self.lockFileRetry}\n" 
		return vString


@dataclass(frozen=True)
class SignUps:
	"""
	# SIGNUPS

	Settings used by signups.

	NOTE:  These are NOT settings for individual signups! See `botData.operations.operationOptions` for those.
	"""

	# The category name (if using existing category, must match capitalisation! Discord always displays categories in upper case, even if its actual name is not.)
	signupCategory = "SIGN UP"

	# Icon used for built in RESIGN role.
	resignIcon = "❌"

	# Icon used for built in RESERVE role
	reserveIcon = "⭕"

	# Auto Prestart Enabled: If true, an Ops commander is created automatically at the auto-prestart adjusted time.
	# This is a global overwrite. Individual ops have an option to disable this.
	bAutoPrestartEnabled = True

	# Show Options in Footer: When true, the ops settings are shown in the footer, in a condensed format;
	# "AS:E|UR:E|UC:D|SDF:D" - AutoStart: Enabled, Use Reserve: Enabled, Use Compact: Disabled, Soberdogs Feedback: Disabled 
	bShowOptsInFooter = True


	def __repr__(self) -> str:
		vString = "	SIGN UP SETTINGS\n"
		vString += f"	> Signup Cat  : {self.signupCategory}\n"
		vString += f"	> Resign Icon : {self.resignIcon}\n" 
		vString += f"	> Reserve Icon: {self.reserveIcon}\n"
		vString += f"	> Auto Prestart:{self.bAutoPrestartEnabled}\n"
		vString += f"	> Show Opts in Footer: {self.bShowOptsInFooter}\n"
		return vString



@dataclass(frozen=True)
class UserLib:
	"""
	# USER LIBRARY
	Settings pertaining to the behaviour of the user library.
	"""
	# Enable Special Users: when true, user viewer checks for a matching ID .txt file.
	# The contents of this file are added to the General page; only admins are able to modify this text.
	bEnableSpecialUsers = True

	# Commander can Auto Create: When true, new user library entries are created for non-existant entries if a valid ps2 name is found from their username.
	bCommanderCanAutoCreate = True

	# User Can Self Create: When true, if an entry doesn't exist for a user and its themself, a new entry is created.
	bUserCanSelfCreate = True

	# Max Saved Events: The maximum number of saved events a users entry can hold.  -1 for no limit, or 0 to disable.
	maxSavedEvents = -1

	# Auto Promote Enabled: When true, after a user has participated in minAttendedEvents, they are promoted (if appropriate role found)
	bAutoPromoteEnabled = True

	# Min Attended Events: the minimum number of events a recruit has to participate in before promotion.
	minAttendedEvents = 4

	# Promotion Requires Validation: If true, a validation request is sent to the userRequest channel to be confirmed, otherwise they are promoted automatically.
	bPromotionRequiresValidation = True

	# Session Preview Max: The number of saved sessions that are previewed in a libraryViewer general page.
	sessionPreviewMax = 5

	# Remove Entry On Leave: If true, a users entry is removed when they leave the server.
	bRemoveEntryOnLeave = False

	# Remove Special Entry on Leave: If true, a users special entry is remove when they leave the server.
	# If enabled, requires `bRemoveEntryOnLeave` to also be TRUE.
	bRemoveSpecialEntryOnLeave = False

	def __repr__(self) -> str:
		vString = "\n	USER LIBRARY SETTINGS\n"
		vString += f"	> Special Users:	{self.bEnableSpecialUsers}\n"
		vString += f"	> Commander Create Entry: {self.bCommanderCanAutoCreate}\n"
		vString += f"	> User Self Create:	{self.bUserCanSelfCreate}\n"
		vString += f"	> Max Saved Events:	{self.maxSavedEvents}\n"
		vString += f"	> AutoPromote Users:	{self.bAutoPromoteEnabled}\n"
		vString += f"	> Min Attended Events:	{self.minAttendedEvents}\n"
		vString += f"	> Validate AutoPromote:	{self.bPromotionRequiresValidation}\n"
		vString += f"	> Max Session Previews:	{self.sessionPreviewMax}\n"
		vString += f"	> Remove Entry/Special on leave: {self.bRemoveEntryOnLeave}/{self.bRemoveSpecialEntryOnLeave}\n"

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
	newUserInfo = "Use the buttons below to provide your Planetside 2 character name (if you have one) and accept the rules.\nThen you can request access, and wait for one of our admins to get you set up!"

	# Displayed in the embed for new users in their gate message, under ACCEPTANCE OF RULES.
	newUserRuleDeclaration = "By pressing 'ACCEPT', you are confirming **you have read**, **understand**, and **agree to adhere** by the rules."

	# Confirmation message sent to users who have accepted the rules
	newUserAcceptedRules = "Thank you for accepting the rules.  You may now request access!"

	# Displayed after the "Welcome @mention" line when a new user is accepted.
	newUserWelcome = "Make sure to use either the button, or the `/roles add` command to add planetside2 and other game roles!\nWe play more than just planetside, but to keep the server tidy, they are hidden with roles."

	# Displayed when a user is choosing roles to ADD.
	userAddingRoles = "Select the roles you wish to **ADD** using the dropdowns, then click update.\n\nDropdown is multiple choice."

	# Displayed when a user is choosing roles to REMOVE.
	userRemovingRoles = "Select the roles you wish to **REMOVE** using the dropdowns, then click Update."

	# Operations Auto Move warning: Shown on Ops Notifications if autoMoveVC is enabled.
	OpsAutoMoveWarn = "If you are already in a voice channel, you will be moved when the ops starts!"

	# Ops Starting Soon: Message appended to Ops messages when the status is PRESTART.
	OpsStartSoon = "This event is starting soon!  Sign up now to be considered a participant!"

	# Ops Started: Message appended to Ops signup messages when the status is STARTED
	OpsStarted = "Sorry, this event has already started and is no longer taking applicants!"

	# Op Being Edited: Message appended to ops signup messages when being edited.
	OpsBeingEdited = "This event is currently being edited, please wait to sign up!"

	# No Matching PS2 Character name found, sent as a single message tagging participants, telling them no matching PS2 Char name is present.
	noMatchingPS2Char = """No matching Planetside 2 Character was found with your current discord name.
	If you wish for your statistics to be tracked, you can either:
	 - Rename yourself to your Planetside2 Character.
	 - Use `!About` and press `Setup`.
	Make sure you do this BEFORE the event starts, otherwise you will not be tracked!
	"""
	
	# Invalid Command Permission : Displayed to users who don't have the required permissions to run a command.
	invalidCommandPerms = "You do not have the required permission to use that command!"

	# Feedback Overflow: Shown in feedback embeds if characters exceeds the max of 1024.
	feedbackOverflow = "\n**UNABLE TO FIT ENTIRE FEEDBACK WITHIN EMBED!\nDownload Feedback to see it all.**"

	# New Operation- Corrupt Data: Shown when adding a new Op but unable to read the default.
	newOpCorruptData = "The default you tried to use is corrupt and has been removed.  Please try again using another default, or create a new one."

	# COMMANDER AutoStart: Displayed on the commander when autostart is enabled.
	commanderAutoStart = "Auto-Start is enabled.\n> *This Commander will automatically start the operation.*\n> *To start the operation early, press* ***START***."


@dataclass(frozen=True)
class Roles:
	"""
	# ROLES
	For convenience, all roles used within selectors are stored here

	NOTE: Selectors have a MAXIMUM limit of 25 items;
			This is a discord imposed limit.
	"""
	# Provides a dropdown containing these roles for giving to new users.
	newUser_roles = [ 
		SelectOption(label="Recruit", value="780253442605842472"),
		SelectOption(label="Test Recruit", value="1060009718837411962", description="DEV VALUE!"), # DEV VALUE!
		# SelectOption(label="TDKD", value="1050286811940921344", description="DEV VALUE!"), # Dev server RoleID
		SelectOption(label="TDKD", value="710472193045299260"), # Live server RoleID
		SelectOption(label="The Washed Masses", value="710502581893595166"),
		SelectOption(label="The Unwashed Masses", value="719219680434192405")
	]

	# ADD ROLES - TDKD:  Roles used in the /roles command, "tdkd" role selector 
	addRoles_TDKD = [
		SelectOption(label="Planetside Pings", value="977873609815105596", description="Non-major PS2 events/fellow\n drunken doggos looking for company"),
		# SelectOption(label="Sober Dogs", value="1040751250163122176", description="DEV VALUE"), # Dev value!
		SelectOption(label="Sober Dogs", value="745004244171620533", description="More serious, coordinated infantry events"), # Live value!
		SelectOption(label="Base Busters", value="811363100787736627", description="Base building and busting events"),
		SelectOption(label="Armour Dogs", value="781309511532544001", description="Ground vehicle related events"),
		SelectOption(label="Dog Fighters", value="788390750982766612", description="Small aerial vehicle related events"),
		SelectOption(label="Royal Air Woofs", value="848612413943054376", description="Heavy aerial vehicle related events"),
		SelectOption(label="PS2 Twitter", value="832241383326744586", description="Planetside 2 Twitter posts"),
		SelectOption(label="Jaeger", value="1024713062776844318", description="Jeager events")
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
		SelectOption(label="Star Citizen", value="1037797784566370318"),
		# SelectOption(label="", value=""),
		# SelectOption(label="", value=""),
		# SelectOption(label="", value=""),
		# SelectOption(label="", value=""),
		# SelectOption(label="", value=""),
		# SelectOption(label="", value=""),
		# SelectOption(label="", value=""),
		# SelectOption(label="", value=""),
		# SelectOption(label="", value=""),
		# SelectOption(label="", value=""),
		# SelectOption(label="", value=""),
		# SelectOption(label="", value=""),
		# SelectOption(label="", value=""),
		# SelectOption(label="", value=""),
		# SelectOption(label="", value=""),
		# SelectOption(label="", value=""),
		# SelectOption(label="", value=""),
		# SelectOption(label="", value=""),
		# SelectOption(label="", value=""),
		# SelectOption(label="", value=""),
		# SelectOption(label="", value=""),
		# SelectOption(label="", value="")
	]

	addRoles_games3 = [
		# SelectOption(label="", value=""),
		# SelectOption(label="", value=""),
		# SelectOption(label="", value=""),
		# SelectOption(label="", value=""),
		# SelectOption(label="", value=""),
		# SelectOption(label="", value=""),
		# SelectOption(label="", value=""),
		# SelectOption(label="", value=""),
		# SelectOption(label="", value=""),
		# SelectOption(label="", value=""),
		# SelectOption(label="", value=""),
		# SelectOption(label="", value=""),
		# SelectOption(label="", value=""),
		# SelectOption(label="", value=""),
		# SelectOption(label="", value=""),
		# SelectOption(label="", value=""),
		# SelectOption(label="", value=""),
		# SelectOption(label="", value=""),
		# SelectOption(label="", value=""),
		# SelectOption(label="", value=""),
		# SelectOption(label="", value=""),
		# SelectOption(label="", value=""),
		# SelectOption(label="", value=""),
		# SelectOption(label="", value=""),
		# SelectOption(label="", value="")
	]



class CommandRestrictionLevels(Enum):
	"""
	# COMMAND RESTRICTION LEVELS
	Convenience Enum for setting levels, or to get a list of roles.

	Should almost always be used instead of raw roleRestrict_level_n

	Use `botUtils.UserHasCommandPerms` to check if a calling user has valid permissions.
	"""
	level0 = BotSettings.roleRestrict_level_0
	level1 = level0 + BotSettings.roleRestrict_level_1
	level2 = level1 + BotSettings.roleRestrict_level_2
	level3 = level2 + BotSettings.roleRestrict_level_3


