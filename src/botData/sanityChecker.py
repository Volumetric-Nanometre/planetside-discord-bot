"""
SANITY CHECKER

Class, functions and exceptions for checking sanity of settings.
If critical settings are invalid, prevents the bot from running.
"""
from __future__ import annotations

from discord import Role, SelectOption
from discord.ext.commands import Bot
from botData.settings import BotSettings, NewUsers, Commander, UserLib, Roles
from botUtils import BotPrinter as BUPrint

class BadChannel(Exception):
	"""
	# EXCEPTION: BAD CHANNEL:
	Raised when required channels are not set.
	"""
	def __init__(self):
		super().__init__("An invalid channel name or ID was set.  See above for more details.")


class BadGuild(Exception):
	"""
	# EXCEPTION: BAD GUILD
	Raised when the guild is invalid.
	"""
	def __init__(self):
		super().__init__(f"Guild not found with ID {BotSettings.discordGuild}. Check Guild ID is correct and bot is present in the guild.")


class BadRole(Exception):
	"""
	# EXCEPTION: BAD ROLE:
	Raised when required roles are not set/invalid.
	"""
	def __init__(self):
		super().__init__("An invalid role name or ID was set.  See above for more details.")



class SanityCheck():
	"""
	# SANITY CHECK
	Class with functions to check sanity of setting values.
	If botSettings.bEnableDebug` is true, this only prints warnings.
	"""

	async def CheckAll(p_botRef:Bot):
		"""
		# CHECK ALL
		Runs all check functions.
		"""
		if BotSettings.bDebugEnabled:
			BUPrint.Info("\n\nATTENTION: Debug is enabled.  Sanity check will only inform of invalid values\n\n")
		else:
			BUPrint.Info("Performing settings sanity check...")

		await SanityCheck.CheckGuild(p_botRef)
		await SanityCheck.CheckRoles(p_botRef)
		SanityCheck.CheckChannels(p_botRef)

		if not BotSettings.bDebugEnabled:
			BUPrint.Info("	-> Settings Sanity Check Passed!")



	async def CheckGuild(p_botRef:Bot):
		BUPrint.Info("Sanity Checking Guild.")
		vGuild = p_botRef.get_guild(int(BotSettings.discordGuild))
		if vGuild == None:
			BUPrint.LogError(f"{BotSettings.discordGuild}", "INVALID GUILD ID:")
			raise BadGuild()


	async def CheckRoles(p_botRef:Bot):
		"""
		# CHECK ROLES:
		Checks if any required roles are invalid.
		"""
		BUPrint.Info("Sanity Checking Roles.")
		guild = p_botRef.get_guild(int(BotSettings.discordGuild))
		allRoles = guild.roles
		checkOptions = BotSettings.sanityCheckOpts
		bFailedCheck = False

		if len(BotSettings.roleRestrict_ADMIN):
			for adminID in BotSettings.roleRestrict_ADMIN:
				adminUser = p_botRef.get_user(adminID)
				if adminUser == None:
					BUPrint.LogError(p_titleStr="INVALID ROLE |  ADMINISTRATOR", p_string=str(adminID))
					bFailedCheck = True

		# BOT SETTINGS: Role restrict values
		if checkOptions.RestrictLevels:
			for roleStr in BotSettings.roleRestrict_level_0:
				if not SanityCheck.RoleInRoles(roleStr, allRoles):
					BUPrint.LogError(p_titleStr="INVALID ROLE |  Role Restriction Level 0", p_string=roleStr)
					bFailedCheck = True

			for roleStr in BotSettings.roleRestrict_level_1:
				if not SanityCheck.RoleInRoles(roleStr, allRoles):
					BUPrint.LogError(p_titleStr="INVALID ROLE |  Role Restriction Level 1", p_string=roleStr)
					bFailedCheck = True

			for roleStr in BotSettings.roleRestrict_level_2:
				if not SanityCheck.RoleInRoles(roleStr, allRoles):
					BUPrint.LogError(p_titleStr="INVALID ROLE |  Role Restriction Level 2", p_string=roleStr)
					bFailedCheck = True

			for roleStr in BotSettings.roleRestrict_level_3:
				if not SanityCheck.RoleInRoles(roleStr, allRoles):
					BUPrint.LogError(p_titleStr="INVALID ROLE |  Role Restriction Level 3", p_string=roleStr)
					bFailedCheck = True

		if checkOptions.UsedByNewUser or checkOptions.UsedByUserLibrary:
			# AUTO ASSIGN ROLES
			for autoRoleID in NewUsers.autoAssignRoles:
				if not SanityCheck.RoleInRoles(autoRoleID, allRoles):
					BUPrint.LogError(p_titleStr="INVALID ROLE |  NewUsers: AutoAssign", p_string=str(autoRoleID))
					bFailedCheck = True

			# RECRUIT ROLE
			if not SanityCheck.RoleInRoles(NewUsers.recruitRole, allRoles):
				BUPrint.LogError(p_titleStr="INVALID ROLE |  NewUsers: Recruit", p_string=str(NewUsers.recruitRole))
				bFailedCheck = True

		if checkOptions.UsedByNewUser:
			for selectOpt in Roles.newUser_roles:
				if not SanityCheck.RoleInRoles(selectOpt.value, allRoles):
					BUPrint.LogError(p_titleStr="INVALID ROLE |  New User Role Select Option", p_string=str(selectOpt.value))
					bFailedCheck = True


		if checkOptions.UsedByUserLibrary:
			# PROMOTION ROLE
			if not SanityCheck.RoleInRoles(UserLib.promotionRoleID, allRoles):
				BUPrint.LogError(p_titleStr="INVALID ROLE |  UserLib: Promotion", p_string=str(UserLib.promotionRoleID))
				bFailedCheck = True

		if checkOptions.UsedByUserRoles:
			# TDKD ROLES
			for selectOpt in Roles.addRoles_TDKD:
				if not SanityCheck.RoleInRoles(selectOpt.value, allRoles):
					BUPrint.LogError(p_titleStr="INVALID ROLE |  Role Selector: TDKD", p_string=selectOpt.value)
					bFailedCheck = True

			for selectOpt in Roles.addRoles_games1:
				if not SanityCheck.RoleInRoles(selectOpt.value, allRoles):
					BUPrint.LogError(p_titleStr="INVALID ROLE |  Role Selector: Games 1", p_string=selectOpt.value)
					bFailedCheck = True

			for selectOpt in Roles.addRoles_games2:
				if not SanityCheck.RoleInRoles(selectOpt.value, allRoles):
					BUPrint.LogError(p_titleStr="INVALID ROLE |  Role Selector: Games 2", p_string=selectOpt.value)
					bFailedCheck = True

			for selectOpt in Roles.addRoles_games3:
				if not SanityCheck.RoleInRoles(selectOpt.value, allRoles):
					BUPrint.LogError(p_titleStr="INVALID ROLE |  Role Selector: Games 3", p_string=selectOpt.value)
					bFailedCheck = True

		if bFailedCheck:
			if BotSettings.bDebugEnabled:
				BUPrint.LogError(p_titleStr="ROLES FAILED CHECK", p_string="One or more roles has an invalid value.")
			else:
				raise BadRole


	def RoleInRoles(p_roleNameOrID:str, p_RolesList:list[Role]):
		"""
		Checks if role is in list of roles.

		roleName or ID can be provided.

		Returns TRUE if found. False if not.
		"""
		for role in p_RolesList:
			if role.name == p_roleNameOrID:
				return True

			try:
				if p_roleNameOrID.isnumeric():
					if role.id == p_roleNameOrID:
						return True
			except AttributeError:
				if role.id == p_roleNameOrID:
					return True


		return False


	def CheckChannels(p_botRef:Bot):
		""" # CHECK CHANNELS:
		Checks if required channels are present.
		"""
		checkOptions = BotSettings.sanityCheckOpts
		checkChannel = None
		vGuild = p_botRef.get_guild(int(BotSettings.discordGuild))
		bFailedCheck = False

		if checkOptions.UsedByNewUser or checkOptions.UsedByUserLibrary:
			# ADMIN CHANNEL
			checkChannel = vGuild.get_channel( BotSettings.adminChannel )
			if checkChannel == None:
				BUPrint.LogError(p_titleStr="INVALID CHANNEL ID | ", p_string="Admin Channel")
				bFailedCheck = True

		if checkOptions.UsedByCommander:
			# FALLBACK VOICE CHAT
			checkChannel = vGuild.get_channel( BotSettings.fallbackVoiceChat )
			if checkChannel == None:
				BUPrint.LogError(p_titleStr="INVALID CHANNEL ID | ", p_string="Commander: Fallback")
				bFailedCheck = True

			# COMMANDER MOVEBACK CHANNEL
			if Commander.bAutoMoveVCEnabled:
				checkChannel = vGuild.get_channel( Commander.autoMoveBackChannelID )
				if checkChannel == None:
					BUPrint.LogError(p_titleStr="INVALID CHANNEL ID | ", p_string="Commander: AutoMoveback")
					bFailedCheck = True

			# SOBER FEEDBACK
			checkChannel = vGuild.get_channel( Commander.soberFeedbackID )
			if checkChannel == None:
				BUPrint.LogError(p_titleStr="INVALID CHANNEL ID | ", p_string="Commander: Sober Feedback")
				bFailedCheck = True


		if checkOptions.UsedByNewUser:
			# GATE CHANNEL
			checkChannel = vGuild.get_channel( NewUsers.gateChannelID )
			if checkChannel == None:
				BUPrint.LogError(p_titleStr="INVALID CHANNEL ID | ", p_string="New Users: Gate")
				bFailedCheck = True

			# GENERAL CHANNEL
			checkChannel = vGuild.get_channel( NewUsers.generalChanelID )
			if checkChannel == None:
				BUPrint.LogError(p_titleStr="INVALID CHANNEL ID | ", p_string="New Users: General")
				bFailedCheck = True

		if bFailedCheck:
			if BotSettings.bDebugEnabled:
				BUPrint.LogError(p_titleStr="CHANNELS FAILED CHECK", p_string="One or more channels has an invalid value.")
			else:
				raise BadChannel