"""
SETTINGS

All settings for the bot are listed below, split into classes which can act as headers for easier finding.
These settings pertain to the overall behaviour of the bot, not individual items.
"""
from discord import SelectOption

import botData.envVars as Env

from enum import Enum
from dataclasses import dataclass

@dataclass(frozen=True)
class BotSettings():
	# TOKENS LOADED FROM .ENV FILE
	discordToken = Env.DISCORD_TOKEN
	discordGuild = Env.DISCORD_GUILD
	ps2ServiceID = Env.PS2_SVS_ID
	botDir		 = Env.BOT_DIR

	# Debug Enabled: set to false
	bDebugEnabled = False

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

	# Provides a dropdown containing these roles.
	newUser_roles = [ 
		SelectOption(label="Guest", value="roleIDHere_123"),
		SelectOption(label="Recruit", value="roleIDHere_566"),
		SelectOption(label="TDKD", value="1050286811940921344"),
		SelectOption(label="The Washed Masses", value="roleIDHere_741"),
		SelectOption(label="The Unwashed Masses", value="roleIDHere_963")
	]

	# The Jump URL "rules" leads to (ensure this leads to the rules post!)
	newUser_rulesURL = "https://discord.com/channels/321688140802949120/1049523449867022348/1049523492166565939"


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
		return vString


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


	def __repr__(self) -> str:
		vString = "	BOT DIRECTORY SETTINGS\n"
		vString += f"	> Prefix Dir : {self.prefixDir}\n"
		vString += f"	> LiveOps Dir: {self.liveOpsDir}\n" 
		vString += f"	> DefaultsDir: {self.savedDefaultsDir}\n" 
		vString += f"	> UserLib Dir: {self.userLibrary}\n\n" 
		vString += f"	> LockFile Affix: {self.lockFileAffix}\n" 
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
	#MESSAGES
	Messages used throughout the bot, typically for end-users, stored here for convenient editing purposes.
	"""
	
	# Displayed in the GATE channel on bot startup (after purging).
	gateChannelDefaultMsg = "Welcome to TDKD.\nIf a join request has not been created for you, or you have already sent one and it's no longer here, please re-join the server. Our bot has been restarted."

	# Displayed in the embed for new users in their gate message.
	newUserInfo = "Use the buttons below to provide your Planetside 2 character name and read the rules.\nThen you can request access, and wait for one of our admins to get you set up!"

	# Displayed in the embed for new users in their gate message, under RULES.
	newUserRuleDeclaration = "By pressing 'REQUEST ACCESS', you are confirming **you have read**, **understand**, and **agree to adhere** by the rules."

	# Displayed after the mention line when a new user joins.
	newUserWelcome = "Make sure to use `/roles` to assign both PS2 and other game related roles (and access related channels)!"
