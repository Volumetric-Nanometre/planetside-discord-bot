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
	botDir		 = Env.BOT_DIR

	# BOT FEATURES:  Convenience setting to Enable or Disable Cog functionality.  Any co-dependnacy will behave based on these settings.
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

	# Debug Enabled: set to false during live use to reduce console clutter.
	bDebugEnabled = True

	# Show Settings on Startup: When true, the bots settings are displayed in the console.
	bShowSettingsOnStartup = True

	# Show settings on startup: Discord: Same as above, but posts the config into bot-admin channel
	bShowSettingsOnStartup_discord = False

	"""Force Role restrictions: 
	when true, hard-coded restrictions prohibit command usage based on the roles in roleRestrict variables.
	users unable to call commands setup within the discord client are still unable to call commands regardless of this setting.
	As such, this is merely a redundancy if security concerned.
	
	Check Roles below to see the individual levels."""
	bForceRoleRestrictions = True

	# Error Output: Where error output is sent; if not stderr, must be a file path.
	errorOutput = stderr

	# CHECK VALUES: When true, values are sanity checked on bot start, recommended to stay on.
	# If Debug is enabled, this prints out any invalid entries, else it prevents bot from continuing.
	bCheckValues = True

	# Sanity Check Options: Enable/Disable sanity check for features that may have been disabled
	sanityCheckOpts = botData.dataObjects.SanityCheckOptions(
		UsedByNewUser= True,
		UsedByOperations= True,
		UsedByCommander= True,
		UsedByUserLibrary=True,
		UsedByUserRoles= True,
		RestrictLevels= True
	)

	# Pickle Protocol: Int value denoting the pickle protocol to use.
	pickleProtocol = pickle.HIGHEST_PROTOCOL


	

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
	
	# ROLE RESTRICT: ADMIN	A special role restrict reserved specifically for those entrusted with BotAdmin. While named roleRestrict, only User IDs should be used.
	roleRestrict_ADMIN = [182933627242283008] # LIVE VALUE: Cactus
	
	
	# Recruit: The ID of the RECRUIT role.
	recruit = 780253442605842472

	# Recruit Promotion: The id of the role recruits are promoted to.
	recruitPromotion = 710472193045299260 # DrunkenDog

	# Auto Assign on Promotion: List of role IDs that are always assigned to users when their join request is accepted.
	autoAssignOnAccept = [
		818218528372424744, # Tags
		]


	# Provides a dropdown containing these roles for giving to new users.
	newUser_roles = [ 
		SelectOption(label="Recruit", value=f"{recruit}"),
		SelectOption(label="Drunken Dog", value="710472193045299260"),
		SelectOption(label="The Washed Masses", value="710502581893595166"),
		SelectOption(label="The Unwashed Masses", value="719219680434192405")
	]

	# ADD ROLES - TDKD:  Roles used in the /roles command, "tdkd" role selector 
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
	# New Users (Admin Buttons)
	validateNewuser = CommandRestrictionLevels.level1

	# General User role add/remove user assignable roles (Commands)
	userRoles = CommandRestrictionLevels.level3

	# Op Manager: Add/Edit operations (Commands).
	opManager = CommandRestrictionLevels.level1

	# Op Commander Start/Feedback (Commands)
	opCommander = CommandRestrictionLevels.level2

	# User Library: General users (Commands)
	userLibrary = CommandRestrictionLevels.level3

	# Administrative User Library (Commands)
	userLibraryAdmin = CommandRestrictionLevels.level1

	# Chat Utilities - Administrative (Commands)
	chatUtilities = CommandRestrictionLevels.level1



@dataclass(frozen=True)
class Channels:
	"""
	# CHANNELS
	Channel name/IDs used by the bot. 
	
	Since multiple features may use these, they're stored here to avoid duplicates and messy name inclusions.
	"""
	# Bot Admin: The channel administrative tasks and notifications are sent to.
	botAdminID = -1 # LIVE VALUE

	# Gate Channel: The channel considered to be the servers gate: should be viewable to new users.  It does not require chatting privilages.
	gateID = 1041860598822096950

	# Rule Channel: ID of the rule channel used to fetch the rules Message. 
	ruleID = 913086821263626360

	# General Chat: ID of the general text channel.
	generalID = 710469797439078400 # (general) 

	# Voice Fallback: A channel that users are moved to when their current one is removed (by the bot)
	voiceFallback = 710854499782361140 # (general)

	# Event MoveBack: ID of voice chat users are moved into after an event is over.
	eventMovebackID = 1023703124839518338 # (planetside2)

	# Protected Categories: ID of categories that cannot be deleted by chatMonitor.remove_category
	protectedCategoriesID = [744907524418961438, 710470871214587955, 818212652601966628, 710471344411770881, 734791662798241854, 1026549992829222952, 710470038968205393, 1042450013827117087, 796885440916488252]

	# Quote Channel ID: If this is not found, the event listener is not added.
	quoteID = 1036349723059159040 # LIVE VALUE

	# Sober Feedback: ID of the soberDogs feedback/debrief FORUM.
	soberFeedbackID = 1042463290472800317

	# Planetside2: ID of a planetside 2 text channel.
	ps2TextID = 1063336834324766730 # DEV VALUE
	# ps2TextID = 715337156255809568 # LIVE VALUE

	# scheduleID = 818186731202936843
	scheduleID = 1066527043526860800




@dataclass(frozen=True)
class NewUsers:
	"""
	# NEW USERS
	Settings pertaining to the bot behaviour for `NewUser` cog.
	"""
	# Create Library Entry on Accept: When true, after a user has been accepted, automatically create a user entry for them.
	bCreateLibEntryOnAccept = True

	# Lock PS2 Character on Accept: When true (and user library enabled), disable allowing a user to change their character name via viewer config.
	bLockPS2CharOnAccept = True

	# Warn if a user claims a ps2 character name with a rank equal or higher than this (numerical, lower = higher rank.)
	outfitRankWarn = 4

	# New User Date Warning, discord account is less than x months old.
	newAccntWarn = 3

	# Rule Message ID: The id of a message which contains the server rules (if not in an embed, falls back to message content)  Make sure `Channels.ruleID` is also set.
	ruleMsgID = 977888774530932767

	# Show Add Roles Button: When true, a button to add roles is shown in the welcome message.
	# It is advisable to ensure the message "NewUserWelcome" reflects the presence (or lack thereof) of this button.
	bShowAddRolesBtn = True





@dataclass(frozen=True)
class Commander:
	"""
	# COMMANDER
	Settings used by Op Commanders.
	"""
	# Tracking is Enabled: When true, the PS2 tracker is used.
	bTrackingIsEnabled = True

	# Marked Present: Setting to determine when a participant is considered part of the event and their userLib entry is updated.
	# A present participant has their "attended" value updated and the session stats saved.
	markedPresent = botData.dataObjects.PS2EventAttended.InGameAndDiscordVC

	# Save Non PS2 Events to Sessions: When true, an entry for non-PS2 events is added to a users session history.
	# Because there's no stats to show, only the date, duration and a message informing it isn't for ps2 are shown.
	bSaveNonPS2ToSessions = True

	# Grace Period: The time after an ops has started before participants are evaluated and marked non attending if they fail the requirements for markedPresent.
	gracePeriod = 1 # Minutes

	# Auto Start Commander: if true, Ops Commanders will automatically *start* their operation at the defined start time.
	bAutoStartEnabled = True

	# Enable Commander Auto Alerts: If true, Op Commanders will periodically alert users a set amount of times (below)
	bAutoAlertsEnabled = True

	# Commander Auto Alert Count: The number of automatic alerts a commander will send. These are distributed throughout the pre-start time.
	autoAlertCount = 3

	# Commander- Auto Move Voice Channel: If enabled, participating users are moved to the standby channel on Ops start if they're in a voice channel.
	bAutoMoveVCEnabled = True

	# Number of minutes before an ops scheduled start the bot prestarts AutoStart enabled Ops (Non AutoStart enabled Ops require a user to use `/ops-commander` command)
	# A buffer of 5 minutes is added to this time to ensure sufficient time for setup (especially in the case of a slow connection/bot).
	autoPrestart = 45

	# Data Point Interval:  Interval in seconds a new data point for event tracking is set.
	dataPointInterval = 60

	# These channels are created for EVERY event, inside its own category, which are then removed when the event ends.
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

	# File directory for saved recruit user data.  Separated to make getting just recruits less intensive.
	userLibraryRecruits = f"{userLibrary}Recruits/"

	# File directory for temporary files.
	tempDir = f"{prefixDir}temp/"

	# Name used on lock files as an affix.
	lockFileAffix = ".LOCK"

	# Feedback Prefix: The string prefixed to a saved feedback file.
	feedbackPrefix = "FEEDBACK_"

	# Number of attempts to try obtaining a lock before returning.
	lockFileRetry = 5

	# Clean Temp Every: Interval for cleanup utility task.
	cleanTempEvery = 120 #Hours.

	# Clean Temp on Shutdown: When the bot is closed, if True the temp directory is cleared.
	bCleanTempOnShutdown = False




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

	# Auto Remove Outdated: On startup, or any call to Refresh Ops; if the event date is before the current date, remove it. 
	bAutoRemoveOutdated = True
	
	# The category name (results are searched in lower, so this is generally case insensitive.)
	# If not found, this category is created.
	signupCategory = "SIGN UP"

	# Resign as Button: True, Resign is a separate button. False, Resign is added to the role selector.  
	bResignAsButton = True

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

	# The maximum number of roles a single event can have.  Must take into consideration discords limit of 25 embed elements, and 25 max select items.
	maxRoles = 20




@dataclass(frozen=True)
class UserLib:
	"""
	# USER LIBRARY
	Settings pertaining to the behaviour of the user library.
	"""
	# Entry Retention: How user library entries are kept in memory: Always loaded, UnloadAfter, and WhenNeeded.
	entryRetention = botData.dataObjects.EntryRetention.alwaysLoaded

	#Entry Retention: Unload after- If `UnloadAfter` is used, entries are removed if they haven't been "got" or "saved" within this period. 
	entryRetention_unloadAfter = 30 # minutes.

	# Entry Retention: Check Interval: the interval the checking task is set to.  If `unloadAfter` is not set, this task is not added.
	entryRetention_checkInterval = 5 # Minutes

	# Enable Special Users: when true, user viewer checks for a matching ID .txt file.
	# The contents of this file are added to the General page; only admins are able to modify this text.
	bEnableSpecialUsers = True

	# Enable Inbox: When true, certain bot features may send an item to a users inbox (including admin warns)
	bEnableInbox = True

	# Commander can Auto Create: When true, new user library entries are created for non-existant entries if a valid ps2 name is found from their username during a live operation.
	bCommanderCanAutoCreate = True

	# User Can Self Create: When true, if an entry doesn't exist for a user and its themself, a new entry is created.
	bUserCanSelfCreate = True

	# Max Saved Events: The maximum number of saved events a users entry can hold.  -1 for no limit, or 0 to disable.
	maxSavedEvents = -1

	# Auto Query Recruit Time: The time(s) during the day in which all recruits are queried.
	# Querying a recruit checks the recruit requirements, if met; they are promoted/promotion validation request is sent.
	autoQueryRecruitTime = [
		time(hour=10, minute=00, tzinfo=timezone.utc)
	]

	# Auto Promote Enabled: When true, after a user has met the requirements, they are promoted (if appropriate role found).
	# If False, a validation request is sent to the admin channel instead.
	bAutoPromoteEnabled = True

	# Auto Promote Rules: A dataclass containing rules/conditions for auto promotion.
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

	# Session Preview Max: The number of saved sessions that are previewed in a libraryViewer general page.
	sessionPreviewMax = 5

	# Session Browser Max Per Page: Maximum number of sessions the browser page (and the dropdown) will show.  Cannot go above 25.
	sessionMaxPerPage = 10

	# Remove Entry On Leave: If true, a users entry is removed when they leave the server.
	bRemoveEntryOnLeave = False

	# Remove Special Entry on Leave: If true, a users special entry is removed when they leave the server.
	# If enabled, requires `bRemoveEntryOnLeave` to also be TRUE.
	bRemoveSpecialEntryOnLeave = False

	# Show Jump Buttons for Get Events: When true, when a user uses "/my_events", the result message includes a view with jump buttons to signupable events.
	bShowJumpButtonsForGetEvents = True


	# FUN STUFF: Settings here pertain to little funny things: due to their nonserious nature, they're not displayed in /Config or Console output.

	# Top Quote: When a quote receives this amount of reactions, the mentioned user has the quote added to their library entry. 0 or negative value to disable.
	topQuoteReactions = 1

	# The maximum number of saved/displayed quotes.
	maxQuotes = 3




dataclass(frozen=True)
class ForFun:
	"""# FOR FUN
	Settings pertaining to non-serious features that are there "for fun".
	"""
	
	# MORNING GREETING SETTINGS

	# Morning Greeting: When true, the bot responds to a message containing "morning". (to avoid every instance, the message must have less than 3 space characters.)
	bMorningGreeting = True

	# Random Gif: When true, the bot sends one of the specified gifs instead of a message.  This is implied false if the gif list is empty.
	bMorningGreetingRandomGif = True

	# Morning Greeting minimum time: the minimum time since the last greeting was sent, used to prevent spam.
	morningGreetingMinTime = relativedelta(minutes=5)

	# Morning Greetings: list of greetings to a user who says "morning", any instance of "_USER" is replaced with a mention.
	# Proxy to `DataObjects.ForFunData`
	morningGreetings =  botData.dataObjects.ForFunData.morningGreetings

	morningGreetingsGif = botData.dataObjects.ForFunData.morningGreetingsGif

	flightDeathReason = botData.dataObjects.ForFunData.flightDeathReason

	# PlanetSide2 Vehicle Death: When true, if a player is killed by another participants sunderer or galaxy, it's broadcasted to the PS2 text channel. 
	bBroadcastPS2VehicleDeath = True

	# Planetside 2 Vehicle Death: Fun event- when true, same as above except its added to users' UserLibrary.
	bPS2VehicleDeathFunEvent = True




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