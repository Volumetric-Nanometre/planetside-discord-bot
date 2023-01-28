"""
SETTINGS

All settings for the bot are listed below, split into classes which can act as headers for easier finding.
These settings pertain to the overall behaviour of the bot, not individual items.

If you're looking for Emoji Library, see `botData.utilityData.EmojiLibrary`.

For more help:
https://github.com/LCWilliams/planetside-discord-bot/wiki/Bot-Configuration/
"""
from __future__ import annotations

from discord import SelectOption
import botData.dataObjects
from dateutil.relativedelta import relativedelta
from datetime import time, timezone
import botData.envVars as Env
from dataclasses import dataclass
from enum import Enum
from sys import stderr
import pickle



@dataclass(frozen=True)
class BotSettings:
	# TOKENS LOADED FROM .ENV FILE
	discordToken = Env.DISCORD_TOKEN
	discordGuild = int(Env.DISCORD_GUILD)
	ps2ServiceID = Env.PS2_SVS_ID
	botDir = Env.BOT_DIR


	botFeatures = botData.dataObjects.BotFeatures(
		# Bot Admin: Enables commands specifically for administrative bot tasks (currently, just show config & shutdown)
		BotAdmin= True,

		# New User: Enables a feature that monitors for new users, who are presented with a dialog to enter their PS2 name, read the rules and request access.
		# On requesting access, a request is sent to the bot-admin channel for an admin to review & assign role, or kick/ban the user.  
		NewUser= True,

		# User Library: Cog which saves specific data about users to file, including their PS2 name, birthdate (if provided), a mini about, any saved sessions, and admin messages.
		# There is an administative cog associated with the user library, containing administrative commands.
		UserLibrary= True,

		# User Library: Inbox System - Allows sending discreet messages to the user via their own inbox.  A discord-safe alternative since some users may have direct messages disabled.
		userLibraryInboxSystem= True,

		# User Library: Inbox system - Admin: Allows admins to send warnings to users, either about a message, or generally; via right clicking (a message, or the user)
		userLibraryInboxAdmin= True,

		# Fun features of UserLibrary cog.  Fun Features are non-serious and generally just for humour.
		UserLibraryFun = True,

		# Operations:  Cog which contains commands to create, edit and delete operations (live and defaults), and operation commanders.
		Operations= True,

		# Chat Utility: Cog with administrative commands for chats & category manipulation, and linking voice-chat to text-chat channels.
		chatUtility= True,

		# User Roles: Cog which enables users to self-assign roles using a command (or button on newUser, if enabled)
		UserRoles= True,

		# For Fun Cog: Cog that implements 'for fun' features that do not depend on other bot functionality.
		ForFunCog=True,
	)
	"""# BOT FEATURES:  Convenience setting to Enable or Disable Cog functionality.  Any co-dependnacy will behave based on these settings.
	"""

	bDebugEnabled = True
	"""# Debug Enabled: set to false during live use to reduce console clutter.
	"""

	bShowSettingsOnStartup = True
	"""# Show Settings on Startup: When true, the bots settings are displayed in the console.
	"""

	bShowSettingsOnStartup_discord = False
	"""# Show settings on startup: Discord: Same as above, but posts the config into bot-admin channel
	"""

	bForceRoleRestrictions = True
	"""Force Role restrictions: 
	when true, hard-coded restrictions prohibit command usage based on the roles in roleRestrict variables.
	users unable to call commands setup within the discord client are still unable to call commands regardless of this setting.
	As such, this is merely a redundancy if security concerned.
	
	Check Roles below to see the individual levels."""

	errorOutput = stderr
	"""# Error Output: Where error output is sent; if not stderr, must be a file path.
	"""

	bCheckValues = True
	"""# CHECK VALUES: 
	When true, values are sanity checked on bot start, recommended to stay on.
	If Debug is enabled, this prints out any invalid entries, else it prevents bot from continuing."""


	pickleProtocol = pickle.HIGHEST_PROTOCOL
	"""# Pickle Protocol: 
	Int value denoting the pickle protocol to use."""


	bBotAdminCanPurge = False
	"""# Bot Admin Can Purge:
	When true, the bot admin channel can be purged on startup/shutdown.
	Helpful to keep the channel clear of non-functional views after a bot restart."""


	

@dataclass(frozen=True)
class Roles:
	"""
	# ROLES
	Individual roles used by the bot.

	For convenience, all roles used within selectors are also stored here

	NOTE: Selectors have a MAXIMUM limit of 25 items;
			This is a discord imposed limit.
	"""
	# ROLE RESTRICTION LEVELS:
	roleRestrict_level_0 = ["CO"]

	roleRestrict_level_1 = ["Captain", "Lieutenant"]

	roleRestrict_level_2 = ["Sergeant", "Corporal", "Lance-Corporal"]

	roleRestrict_level_3 = ["DrunkenDogs", "Recruits", "The-Washed-Masses", "The-Unwashed-Masses"]
	
	roleRestrict_ADMIN = [182933627242283008] # LIVE VALUE: Cactus
	"""	# ROLE RESTRICT: ADMIN
	A special role restrict reserved specifically for those entrusted with BotAdmin. While named roleRestrict, only User IDs should be used."""
	
	
	recruit = 780253442605842472
	"""# Recruit
	ID of the recruit role."""

	
	recruitPromotion = 710472193045299260 # DrunkenDog
	"""# recruit Promotion
	The ID of the role recruits are promoted to.
	
	NOTE: If sleeper feature is enabled; 
	this is the role used to check if the user is part of the outfit."""


	sleeperRoleID = 0
	"""# Sleeper Role ID
	ID of a role assigned to users who meet the sleeper requirements."""


	autoAssignOnAccept = [
		818218528372424744, # Tags
		]
	"""# Auto Assign on Accept:
	List of role IDs that are always assigned to users when their join request is accepted."""


	newUser_roles = [ 
		SelectOption(label="Recruit", value=f"{recruit}"),
		SelectOption(label="Drunken Dog", value="710472193045299260"),
		SelectOption(label="The Washed Masses", value="710502581893595166"),
		SelectOption(label="The Unwashed Masses", value="719219680434192405")
	]
	"""New User Roles:  Roles listed in a new user join request that an admin may assign."""


	addRoles_TDKD = [
		SelectOption(label="Planetside Pings", value="977873609815105596", description="Non-major PS2 events/fellow\n drunken doggos looking for company"),
		SelectOption(label="Sober Dogs", value="745004244171620533", description="More serious, coordinated infantry events"),
		SelectOption(label="Base Busters", value="811363100787736627", description="Base building and busting events"),
		SelectOption(label="Armour Dogs", value="781309511532544001", description="Ground vehicle related events"),
		SelectOption(label="Dog Fighters", value="788390750982766612", description="Small aerial vehicle related events"),
		SelectOption(label="Royal Air Woofs", value="848612413943054376", description="Heavy aerial vehicle related events"),
		SelectOption(label="PS2 Twitter", value="832241383326744586", description="Planetside 2 Twitter posts"),
		SelectOption(label="Jaeger", value="1024713062776844318", description="Jeager events")
	]
	"""Add Roles: TDKD:  Roles listed in the "TDKD" selector for the /roles commands."""


	addRoles_games1 = [
		SelectOption(label="Apex Legends", value="825106272856571985"),
		SelectOption(label="Back 4 Blood", value="916804112337756160"),
		SelectOption(label="Battlefield 2042", value="894232796619472987"),
		SelectOption(label="Conqueror's Blade", value="896008973906509885"),
		SelectOption(label="Deep Rock Galactic", value="803340218756366423"),
		SelectOption(label="Dungeon and Dragons", value="864175083152343070"),
		SelectOption(label="Eve Online", value="900009823867916310"),
		SelectOption(label="Factorio", value="939894580688605274"),
		SelectOption(label="Garrys' Mod", value="916803968674439300"),
		SelectOption(label="Gates of Hell", value="1000366778133774528"),
		SelectOption(label="Killing Floor 2", value="916804287370240131"),
		SelectOption(label="Minecraft", value="824708493076201473"),
		SelectOption(label="Post Scriptum", value="791308463241691146"),
		SelectOption(label="Sea of Thieves", value="916802105719783454"),
		SelectOption(label="Stellaris", value="911972761948266547"),
		SelectOption(label="Supreme Commander", value="887338095802982441"),
		SelectOption(label="Space Engineers", value="805234496026050601"),
		SelectOption(label="Squad", value="808413252685529108"),
		SelectOption(label="Team Fortress 2", value="826943611303100496"),
		SelectOption(label="Terraria", value="825106136378245180"),
		SelectOption(label="Total War: Warhammer", value="931201327869079553"),
		SelectOption(label="Valheim", value="818490876631711794"),
		SelectOption(label="Vermintide", value="929376317944791040"),
		SelectOption(label="Warframe", value="872593227734208512"),
		SelectOption(label="Warthunder", value="976598559266857030"),
	]
	"""Add Roles: Games 1:  Roles listed in the "Games 1" selector for the /roles commands."""

	addRoles_games2 = [
		SelectOption(label="Overwatch", value="1029138196518420531"),
		SelectOption(label="Star Citizen", value="1037797784566370318"),
		SelectOption(label="World of Tanks", value="1038125253806788768"),
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
	"""Add Roles: Games 2:  Roles listed in the "Games 2" selector for the /roles commands."""

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
	"""Add Roles: Games 3:  Roles listed in the "Games 3" selector for the /roles commands."""



class CommandRestrictionLevels(Enum):
	"""
	# COMMAND RESTRICTION LEVELS
	Convenience Enum for setting levels, or to get a list of roles.

	Should almost always be used instead of raw roleRestrict_level_n

	Use `botUtils.UserHasCommandPerms` to check if a calling user has valid permissions.

	NOTE: Not to be edited: for changing values, edit `BotSettings.roleRestrict_level_x`
	"""
	level0 = Roles.roleRestrict_level_0
	level1 = level0 + Roles.roleRestrict_level_1
	level2 = level1 + Roles.roleRestrict_level_2
	level3 = level2 + Roles.roleRestrict_level_3




@dataclass(frozen=True)
class CommandLimit:
	"""
	# COMMAND LIMIT
	Settings pertaining to each command and certain button usage in the bot;
	Stored here to avoid needing to hunt down individual files and commands.

	NOTE: Admin cog has no CommandLimit entry, because it uses the direct roleRestrict_ADMIN value.
	"""
	validateNewuser = CommandRestrictionLevels.level1
	"""Command limit for New User validation buttons."""

	userRoles = CommandRestrictionLevels.level3
	"""Command limit for User Roles commands"""

	opManager = CommandRestrictionLevels.level1
	"""Command limit for Op Manager commands."""

	opCommander = CommandRestrictionLevels.level2
	"""Command limit for Op Commander commands."""

	userLibrary = CommandRestrictionLevels.level3
	"""Command limit for User library commands, specific to general users"""

	userLibraryAdmin = CommandRestrictionLevels.level1
	"""Command limit for user library commands, specific to administrative commands."""

	chatUtilities = CommandRestrictionLevels.level1
	"""Command limit for chat utility commands."""



@dataclass(frozen=True)
class Channels:
	"""
	# CHANNELS
	Channel name/IDs used by the bot. 
	
	Since multiple features may use these, they're stored here to avoid duplicates and messy name inclusions.
	"""

	botAdminID = 0
	"""# Bot Admin: 
	The channel administrative tasks and notifications are sent to."""

	
	gateID = 0
	"""# Gate Channel: 
	The channel considered to be the servers gate: should be viewable to new users.  It does not require chatting privilages."""


	ruleID = 913086821263626360
	"""# Rule Channel: 
	ID of the rule channel used to fetch the rules Message. """


	generalID = 710469797439078400 # (general)
	"""	# General Chat: 
	ID of the general text channel."""

	
	voiceFallback = 710854499782361140 # (general)
	"""# Voice Fallback: 
	A channel that users are moved to when their current one is removed (by the bot)"""

	
	eventMovebackID = 1023703124839518338 # (planetside2)
	"""# Event MoveBack: 
	ID of voice chat users are moved into after an event is over."""

	
	protectedCategoriesID = [
		744907524418961438, # Welcome
		710470871214587955, # Important Channels
		818212652601966628, # Sign-up
		710471344411770881, # The Drunken Dogs
		734791662798241854, # Games
		1026549992829222952, # Jaeger
		710470038968205393, # Planetside
		1042450013827117087, # Soberdogs Stuff
		796885440916488252, # Guides
		]
	"""# Protected Categories: 
	ID of categories that cannot be deleted by chatMonitor.remove_category"""


	quoteID = 1036349723059159040
	"""# Quote Channel ID: 
	If this is not found, the event listener is not added."""

	
	soberFeedbackID = 1042463290472800317
	"""# Sober Feedback: 
	ID of the soberDogs feedback/debrief FORUM."""


	ps2TextID = 715337156255809568
	"""# PS" Text ID:
	ID of the planetside 2 TEXT channel."""


	scheduleID = 818186731202936843
	"""# Schedule ID:
	ID of the schedule text channel"""



@dataclass(frozen=True)
class NewUsers:
	"""
	# NEW USERS
	Settings pertaining to the bot behaviour for `NewUser` cog.
	"""

	bPurgeGate = False
	"""# Purge Gate:
	When true, the gate channel is purged on shutdown/startup"""

	bCreateLibEntryOnAccept = True
	"""	# Create Library Entry on Accept: 
	When true, after a user has been accepted, automatically create a user entry for them."""

	
	bLockPS2CharOnAccept = True
	"""# Lock PS2 Character on Accept:
	When true (and user library enabled), disable allowing a user to change their character name via viewer config."""

	
	outfitRankWarn = 4
	"""# Outfit Rank Warning
	Warn if a joining user claims a ps2 character name with a rank equal or higher than this (numerical, lower = higher rank.)"""


	newAccntWarn = 3
	"""# New Account Warning:
	Warn when a joining users account is less than this many months old."""

	
	ruleMsgID = 977888774530932767
	"""# Rule Message ID:
	The id of a message which contains the server rules (if not in an embed, falls back to message content)  Make sure `Channels.ruleID` is also set."""


	bShowAddRolesBtn = True
	"""# Show Add Roles Button:
	When true, a button to add roles is shown in the welcome message.
	It is advisable to ensure the message "NewUserWelcome" reflects the presence (or lack thereof) of this button."""





@dataclass(frozen=True)
class Commander:
	"""
	# COMMANDER
	Settings used by Op Commanders.
	"""
	
	bTrackingIsEnabled = True
	"""# Tracking is Enabled: 
	When true, the PS2 tracker is used for PS2 events."""

	
	markedPresent = botData.dataObjects.PS2EventAttended.InGameOnly
	"""# Marked Present: 
	Setting to determine when a participant is considered part of the event and their userLib entry is updated.
	A present participant has their "attended" value updated and the session stats saved."""

	
	bSaveNonPS2ToSessions = True
	"""# Save Non PS2 Events to Sessions: 
	When true, an entry for non-PS2 events is added to a users session history.
	Because there's no stats to show, only the date, duration and a message informing it isn't for ps2 are shown."""


	
	gracePeriod = 10 # Minutes
	"""# Grace Period: 
	The time after an ops has started before participants are evaluated and marked non attending if they fail the requirements for markedPresent."""

	
	bAutoStartEnabled = True
	"""# Auto Start Commander:
	When true, Ops Commanders will automatically *start* their operation at the defined start time."""

	
	bAutoAlertsEnabled = True
	"""# Enable Commander Auto Alerts: 
	If true, Op Commanders will periodically alert users a set amount of times (below)"""


	autoAlertCount = 3
	"""	# Commander Auto Alert Count: 
	The number of automatic alerts a commander will send. These are distributed throughout the pre-start time."""

	
	bAutoMoveVCEnabled = True
	"""# Commander- Auto Move Voice Channel: 
	If enabled, participating users are moved to the standby channel on Ops start if they're in a voice channel."""

	
	autoPrestart = 45
	"""# Auto Prestart:
	Number of minutes before an ops scheduled start the bot prestarts AutoStart enabled Ops (Non AutoStart enabled Ops require a user to use `/ops-commander` command)
	NOTE: A buffer of 5 minutes is added to this time to ensure sufficient time for setup (especially in the case of a slow connection/bot)."""


	dataPointInterval = 60
	"""	# Data Point Interval:
	Interval in seconds a new data point for event tracking is set."""


	defaultChannels = botData.dataObjects.DefaultChannels(
		# Text Channels: Persistent text channels that are always created.
		textChannels= [],

		# The Name of the channel the COMMANDER is in.
		opCommander = "Commander",

		# Notifications: Name of the channel notifications & feedback messages are sent to.
		notifChannel = "Notifications",

		# Standby Voice Channel: Name of channel users are automatically moved into (if enabled) when ops starts.
		standByChannel= "Standby",

		# Persistent Voice: Same as Text Channels- always created voice channels.
		persistentVoice= [],
		
		# Voice Channels: If custom channels are not specified in the Op Data, these are used instead.
		voiceChannels= ["Squad-Alpha", "Squad-Bravo", "Squad-Charlie", "Squad-Delta"]
	)
	"""# DEFAULT CHANNELS:
	Voice and text channels used by all events."""


	# Icons for the CONNECTIONS embed.
		# Discord
	connIcon_discord = "🖥️"
	connIcon_discordOnline = "🟢"
	connIcon_discordOffline = "🔴"
		# Discord Voice
	connIcon_voice = "🎧" 
	connIcon_voiceConnected = "🟢"
	connIcon_voiceNotEventChan = "🟡"
	connIcon_voiceDisconnected = "🔴"
		# Planetside2
	connIcon_ps2 = "🎮"
	connIcon_ps2Online = "🟢"
	connIcon_ps2Offline = "🔴"
	connIcon_ps2Invalid = "❌" # Users who have an invalid/non-matching PS2 name
	connIcon_ps2Recruit = "🚼" # Shown when user is a recruit (requires User Library)
	




@dataclass(frozen=True)
class SignUps:
	"""
	# SIGNUPS

	Settings used by signups.

	NOTE:  These are NOT settings for individual signups! See `botData.operations.operationOptions` for those.
	"""

	bAutoParseSchedule = True
	"""# Auto Parse Schedule
	When true, messages in the specified SCHEDULE channel are parsed.
	If any matching events are found, the bot will offer to make them."""

	autoParseTimeout = 300
	"""# Auto Parse Timeout:
	The number of seconds before the view and message for an auto-parse message is removed."""

	
	bAutoRemoveOutdated = True
	"""# Auto Remove Outdated: 
	On startup, or any call to Refresh Ops; if the event date is before the current date, remove it. """
	
	
	signupCategory = "SIGN UP"
	"""# Signup Category
	The category name (results are searched in lower, so this is generally case insensitive.)
	If not found, this category is created."""

	
	bResignAsButton = True
	"""# Resign as Button:
	True, Resign is a separate button. False, Resign is added to the role selector."""

	
	resignIcon = "❌"
	"""# Icon used for built in RESIGN role."""

	
	reserveIcon = "⭕"
	"""# Icon used for built in RESERVE role"""

	
	bAutoPrestartEnabled = True
	"""# Auto Prestart Enabled: 
	If true, an Ops commander is created automatically at the auto-prestart adjusted time.
	This is a global overwrite. Individual ops have an option to disable this."""

	
	bShowOptsInFooter = True
	"""# Show Options in Footer: 
	When true, the ops settings are shown in the footer, in a condensed format;
	"AS:E|UR:E|UC:D|SDF:D" - AutoStart: Enabled, Use Reserve: Enabled, Use Compact: Disabled, Soberdogs Feedback: Disabled """

	
	maxRoles = 20
	"""# Max Roles:
	The maximum number of roles a single event can have.  
	Must take into consideration discords limit of 25 embed elements, and 25 max select items."""




@dataclass(frozen=True)
class UserLib:
	"""
	# USER LIBRARY
	Settings pertaining to the behaviour of the user library.
	"""
	
	entryRetention = botData.dataObjects.EntryRetention.alwaysLoaded
	"""# Entry Retention: 
	How user library entries are kept in memory: Always loaded, UnloadAfter, and WhenNeeded.
	NOTE: Unload after hasn't been properly tested."""

	
	entryRetention_unloadAfter = 30 # minutes.
	"""#Entry Retention: Unload after- 
	If `UnloadAfter` is used, entries are removed if they haven't been "got" or "saved" within this period. """

	
	entryRetention_checkInterval = 5 # Minutes
	"""# Entry Retention: Check Interval: 
	The interval the checking task is set to.  If `unloadAfter` is not set, this task is not added."""


	bEnableSpecialUsers = True
	"""# Enable Special Users: 
	when true, user viewer checks for a matching ID .txt file.
	The contents of this file are added to the General page; only admins are able to modify this text."""

	
	bEnableInbox = True
	"""# Enable Inbox: 
	When true, certain bot features may send an item to a users inbox (including admin warns)"""

	
	bCommanderCanAutoCreate = True
	"""# Commander can Auto Create: 
	When true, new user library entries are created for non-existant entries if a valid ps2 name is found from their username during a live operation."""

	
	bUserCanSelfCreate = True
	"""# User Can Self Create: 
	When true, if an entry doesn't exist for a user and its themself, a new entry is created."""

	
	maxSavedEvents = -1
	"""# Max Saved Events:
	The maximum number of saved events a users entry can hold.  -1 for no limit, or 0 to disable."""

	
	autoQueryRecruitTime = [
		time(hour=10, minute=00, tzinfo=timezone.utc)
	]
	"""# Auto Query Recruit Time: 
	The time(s) during the day in which all recruits are queried.
	Querying a recruit checks the recruit requirements, if met; they are promoted/promotion validation request is sent."""

	
	bAutoPromoteEnabled = False
	"""# Auto Promote Enabled: 
	When true, after a user has met the requirements, they are promoted (if appropriate role found).
	If False, a validation request is sent to the admin channel instead."""

	
	bEnforcePS2Rename = True
	"""# Enforce PS2 Rename
	When true, and a user provides a valid PS2 character name in the library viewer setup,
	they are renamed to the newly provided name & outfit (if present)."""

	
	autoPromoteRules = botData.dataObjects.AutoPromoteRule(
		# Attended Minimum Events: When true, a recruit must participate in the specified number of events.
		bAttendedMinimumEvents = True,
		# Whether Events MUST be PS2 to be considerd.
		bEventsMustBePS2= True,
		# The number of events a recruit must participate in.
		minimumEvents = 4,
		
		# In Outfit For Duration: When true, a recruit must be in the ps2 outfit for the specified duration.
		bInOutfitForDuration = True,
		outfitDuration = relativedelta(days=7),

		# In Discord For Duration: When true, a recruit must be in the discord server for the specified duration.
		bInDiscordForDuration = True,
		discordDuration = relativedelta(days=7)
	)
	"""# Auto Promote Rules: 
	A dataclass containing rules/conditions for auto promotion."""
	
	sleeperRules = botData.dataObjects.SleeperRules(
		bIsEnabled= True,
		bSelfOutfitOnly=True,

		bInbRecentEvent=True,
		mostRecentEvent=relativedelta(months=3)
	)
	"""# SLEEPER RULES
	A set of rules to determine when to apply the sleeper role to members.
	"""
	
	sleeperCheckTime = time(hour=4, minute=0, tzinfo=timezone.utc)
	"""# Sleeper Check Time:
	The time of the day all users are queried for being asleep(inactive)."""

	
	sessionPreviewMax = 5
	"""# Session Preview Max:
	The number of saved sessions that are previewed in a libraryViewer general page."""

	
	sessionMaxPerPage = 10
	"""# Session Browser Max Per Page:
	Maximum number of sessions the browser page (and the dropdown) will show.  Cannot go above 25."""

	
	bRemoveEntryOnLeave = False
	"""# Remove Entry On Leave:
	If true, a users entry is removed when they leave the server."""

	
	bRemoveSpecialEntryOnLeave = False
	"""# Remove Special Entry on Leave: 
	If true, a users special entry is removed when they leave the server.
	If enabled, requires `bRemoveEntryOnLeave` to also be TRUE."""

	
	bShowJumpButtonsForGetEvents = True
	"""# Show Jump Buttons for Get Events: 
	When true, when a user uses "/my_events", the result message includes a view with jump buttons to signupable events."""


	# FUN STUFF: Settings here pertain to little funny things: due to their nonserious nature, they're not displayed in /Config or Console output.

	topQuoteReactions = 5
	"""# Top Quote: 
	When a quote receives this amount of reactions, the mentioned user has the quote added to their library entry. 0 or negative value to disable."""

	maxQuotes = 3
	"""# Max Quotes:
	The maximum number of saved/displayed top quotes a user can have in their entry."""




dataclass(frozen=True)
class ForFun:
	"""# FOR FUN
	Settings pertaining to non-serious features that are there "for fun".
	"""
	
# MORNING GREETING SETTINGS
	bMorningGreeting = True
	"""# Morning Greeting: 
	When true, the bot responds to a message containing "morning". (to avoid every instance, the message must have less than 3 space characters.)"""

	bOnlyInGeneral = False
	"""# Only in General: 
	When true, if the channel isn't the specified general channel, don't respond."""

	bMorningGreetingRandomGif = True
	"""# Random Gif: 
	When true, the bots selection of responses includes a list of gifs.  This is implied false if the gif list is empty."""

	morningGreetingMinTime = relativedelta(minutes=5)
	"""# Morning Greeting minimum time: 
	the minimum time since the last greeting was sent, used to prevent spam."""

	morningGreetings = botData.dataObjects.ForFunData.morningGreetings
	"""# Morning Greetings: 
	list of greetings to a user who says "morning", any instance of "_USER" is replaced with a mention.
	Proxy to `DataObjects.ForFunData`"""

	morningGreetingsGif = botData.dataObjects.ForFunData.morningGreetingsGif
	"""# Morning Greetings GIF: 
	list of gif greetings to a user who says "morning",.
	Proxy to `DataObjects.ForFunData`"""	

	flightDeathReason = botData.dataObjects.ForFunData.flightDeathReason
	"""# Flight Death Reason: 
	List of fun flight death reasons for a specific subset of text greetings.
	Proxy to `DataObjects.ForFunData`"""

# PS2 VEHICLE DEATHS:
	bBroadcastPS2VehicleDeath = True
	"""# PlanetSide2 Vehicle Death: 
	When true, if a player is killed by another participants sunderer or galaxy, it's broadcasted to the PS2 text channel.
	This only occurs during tracked events."""

	bPS2VehicleDeathFunEvent = True
	"""# Planetside 2 Vehicle Death: 
	Fun event- when true, same as above except its added to users' UserLibrary.
	This only occurs during tracked events."""




@dataclass(frozen=True)
class Directories:
	"""
	# DIRECTORIES

	Directories used by the bot.

	If changing the values, make sure slashes are present when needed.
	"""

	prefixDir = f"{BotSettings.botDir}/SavedData/"
	"""Prefix Directory:
	File directory to preceed all directories.  This is not hard-coded, if you so wish, each directory can be anywhere."""

	liveOpsDir = f"{prefixDir}LiveOps/"
	"""# Live Ops Dir:
	Directory of saved data for LIVE events"""

	savedDefaultsDir = f"{prefixDir}Defaults/"
	"""# Saved Defaults:
	Directory of saved data for DEFAULT events."""

	userLibrary = f"{prefixDir}Users/"
	"""# User Library:
	Directory of saved data for user library entries"""

	userLibraryRecruits = f"{userLibrary}Recruits/"
	"""# User Library Recruits:
	Directory of saved data for recruit user library entries.  
	Seperated to make finding recruit entries more efficient."""

	tempDir = f"{prefixDir}temp/"
	"""# Temp Directory:
	Directory of a temporary folder which is periodically cleaned out."""

	lockFileAffix = ".LOCK"
	"""# Lock File Affix:
	Name of the affix to use for lock files."""

	feedbackPrefix = "FEEDBACK_"
	"""#Feedback Prefix:
	The prefix to prepend on feedback text files."""

	lockFileRetry = 5
	"""# Lock File Retry:
	Number of tries a function attempts to get a lock on a file- prevents multiple accessing at once."""

	cleanTempEvery = 120 #Hours.
	"""# Clean Temp Every:
	Number of hours between each temp file emptying, starting from when the bot was started."""

	bCleanTempOnShutdown = False
	"""# Clean Temp on Shutdown:
	When true, the bots temp directory is cleaned on shutdown."""




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

	# Displayed when a new user is accepted.  Use _ROLE and _MENTION to have the assigned role and/or mention inserted.
	newUserWelcome = f"""Welcome, _MENTION!
	You have been assigned the role: _ROLE.
	
	Make sure to use either the button, or the `/roles add` command to add planetside2 and other game roles!
	We play more than just planetside, but to keep the server tidy, they are hidden with roles."""

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

	# Dismiss Editor: Shown when a user sends/updates an operation.
	dismissEditor = "You may now dismiss the editor, if it hasn't automatically closed."

	# Editor Error: shown when an error occured while posting an operation.
	editorError = "An error occured while posting the message. Check all modified entries and try again.\nHint: Use the Keyboard Up arrow to retype the command with all but the opType pre-filled."

	# No Matching PS2 Character name found, sent as a single message tagging participants, telling them no matching PS2 Char name is present.
	noMatchingPS2Char = """No matching Planetside 2 Character was found with your current discord name.
	If you wish for your statistics to be tracked, you can either:
	 - Rename yourself to your Planetside2 Character.
	 - Use `!About` and press `Setup`.
	Make sure you do this BEFORE the event starts, otherwise you will not be tracked!
	"""

	# Not Being Tracked: Shown when users aren't being tracked on a non-PS2 event.
	nonPS2TrackReqsNotMet = "This session won't be added to your session history!\nMake sure to be in the events voice channels before it starts to have it added."
	
	# Invalid Command Permission : Displayed to users who don't have the required permissions to run a command.
	invalidCommandPerms = "You do not have the required permission to use that command!"

	# Invalid Birthdate: Displayed to the user when they configure their userLibrary entry and provide an invalid birthdate.
	invalidBirthdate = "The date provided was an invalid format. Make sure to include leading zeros (eg: 03/05), and if providing the year, ensure it's 4 digits not 2!."

	# Feedback Overflow: Shown in feedback embeds if characters exceeds the max of 1024.
	feedbackOverflow = "\n**UNABLE TO FIT ENTIRE FEEDBACK WITHIN EMBED!\nDownload Feedback to see it all.**"

	# New Operation- Corrupt Data: Shown when adding a new Op but unable to read the default.
	newOpCorruptData = "The default you tried to use is corrupt and has been removed.  Please try again using another default, or create a new one."

	# COMMANDER AutoStart: Displayed on the commander when autostart is enabled.
	commanderAutoStart = "Auto-Start is enabled.\n> *This Commander will automatically start the operation.*\n> *To start the operation early, press* ***START***."

	# No Library Entry- Shown when someone tries to view a users library entry and there is none.
	noUserEntry = "This user has no library entry. :("
	
	# No User Entry Self: Shown when a user tries to view their own entry and userAutoCreate is disabled.
	NoUserEntrySelf = "You have no entry.  Ask an administrator to make one for you."

	# No signed up Events: Shown to user when they use "show_events" and they're not in any.
	noSignedUpEvents = f"You're not signed up to any events!\nUse the buttons below to jump to an event listing and sign up!"

	# No Events: Similar to above, except there's no events.
	noEvents = "There are no events to be signed up to."

	# Feature Disabled: Shown when a command that depends on another feature is disabled.
	featureDisabled = "That feature has been disabled."