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
	def __init__(self, p_requiredChannel:str, p_value:str):
		self.message = f"Required Channel: {p_requiredChannel} has an invalid value: {p_value}"
		super().__init__(self.message)


class BadGuild(Exception):
	"""
	# EXCEPTION: BAD GUILD
	Raised when the guild is invalid.
	"""
	def __init__(self, p_value):
		super().__init__(f"Guild not found with ID {p_value}. Check Guild ID")


class BadRole(Exception):
	"""
	# EXCEPTION: BAD ROLE:
	Raised when required roles are not set/invalid.
	"""
	def __init__(self, p_requiredRole:str, p_value:str):
		self.message = f"Required Role: {p_requiredRole} has an invalid value: {p_value}"
		super().__init__(self.message)



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


	def BadRole(p_roleName, p_value):
		"""
		# BAD ROLE
		Convenience function to check if to raise an exception or print to console.
		"""
		if BotSettings.bDebugEnabled:
			BUPrint.LogError(f"{p_roleName}: {p_value}", "INVALID ROLE:")
		else:
			raise BadRole(p_roleName, p_value)


	def BadChannel(p_ChannelName, p_value):
		"""
		# BAD Channel
		Convenience function to check if to raise an exception or print to console.
		"""
		if BotSettings.bDebugEnabled:
			BUPrint.LogError(f"{p_ChannelName}: {p_value}", "INVALID CHANNEL:")
		else:
			raise BadChannel(p_ChannelName, p_value)


	def BadGuild(p_value):
		"""
		# BAD Guild
		Convenience function to check if to raise an exception or print to console.
		"""
		BUPrint.LogError(p_value, "INVALID GUILD ID:")
		raise BadRole(p_value)


	async def CheckGuild(p_botRef:Bot):
		BUPrint.Info("Sanity Checking Guild.")
		vGuild = p_botRef.get_guild(int(BotSettings.discordGuild))
		if vGuild == None:
			SanityCheck.BadGuild(int(BotSettings.discordGuild))



	async def CheckRoles(p_botRef:Bot):
		"""
		# CHECK ROLES:
		Checks if any required roles are invalid.
		"""
		BUPrint.Info("Sanity Checking Roles.")
		guild = p_botRef.get_guild(int(BotSettings.discordGuild))
		allRoles = guild.roles
		checkOptions = BotSettings.sanityCheckOpts

		# BOT SETTINGS: Role restrict values
		if checkOptions.RestrictLevels:
			for roleStr in BotSettings.roleRestrict_level_0:
				if not SanityCheck.RoleInRoles(roleStr, allRoles):
					SanityCheck.BadRole("Role Retriction level 0", roleStr)

			for roleStr in BotSettings.roleRestrict_level_1:
				if not SanityCheck.RoleInRoles(roleStr, allRoles):
					SanityCheck.BadRole("Role Retriction level 1", roleStr)

			for roleStr in BotSettings.roleRestrict_level_2:
				if not SanityCheck.RoleInRoles(roleStr, allRoles):
					SanityCheck.BadRole("Role Retriction level 2", roleStr)

			for roleStr in BotSettings.roleRestrict_level_3:
				if not SanityCheck.RoleInRoles(roleStr, allRoles):
					SanityCheck.BadRole("Role Retriction level 3", roleStr)

		if checkOptions.UsedByNewUser or checkOptions.UsedByUserLibrary:
			# AUTO ASSIGN ROLES
			for autoRoleID in NewUsers.autoAssignRoles:
				if not SanityCheck.RoleInRoles(autoRoleID, allRoles):
					SanityCheck.BadRole("New User: AutoRole:", str(autoRoleID))

			# RECRUIT ROLE
			if not SanityCheck.RoleInRoles(NewUsers.recruitRole, allRoles):
				SanityCheck.BadRole( "New User: Recruit", str(NewUsers.recruitRole) )

		if checkOptions.UsedByNewUser:
			for selectOpt in Roles.newUser_roles:
				if not SanityCheck.RoleInRoles(selectOpt.value, allRoles):
					SanityCheck.BadRole("Roles|NewUser", str(selectOpt.value))


		if checkOptions.UsedByUserLibrary:
			# PROMOTION ROLE
			if not SanityCheck.RoleInRoles(UserLib.promotionRoleID, allRoles):
				SanityCheck.BadRole( "User Lib: Promotion", str(UserLib.promotionRoleID) )

		if checkOptions.UsedByUserRoles:
			# TDKD ROLES
			for selectOpt in Roles.addRoles_TDKD:
				if not SanityCheck.RoleInRoles(selectOpt.value, allRoles):
					SanityCheck.BadRole("Role Selector: TDKD", selectOpt.value)

			for selectOpt in Roles.addRoles_games1:
				if not SanityCheck.RoleInRoles(selectOpt.value, allRoles):
					SanityCheck.BadRole("Role Selector: Games1", selectOpt.value)

			for selectOpt in Roles.addRoles_games2:
				if not SanityCheck.RoleInRoles(selectOpt.value, allRoles):
					SanityCheck.BadRole("Role Selector: Games2", selectOpt.value)

			for selectOpt in Roles.addRoles_games3:
				if not SanityCheck.RoleInRoles(selectOpt.value, allRoles):
					SanityCheck.BadRole("Role Selector: Games3", selectOpt.value)




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

		if checkOptions.UsedByNewUser or checkOptions.UsedByUserLibrary:
			# ADMIN CHANNEL
			checkChannel = vGuild.get_channel( BotSettings.adminChannel )
			if checkChannel == None:
				SanityCheck.BadChannel("Bot Settings: Invalid ADMIN channel", str(BotSettings.adminChannel))

		if checkOptions.UsedByCommander:
			# FALLBACK VOICE CHAT
			checkChannel = vGuild.get_channel( BotSettings.fallbackVoiceChat )
			if checkChannel == None:
				SanityCheck.BadChannel("Bot Settings: Invalid FALLBACK Voice channel", str(BotSettings.fallbackVoiceChat))

			# COMMANDER MOVEBACK CHANNEL
			if Commander.bAutoMoveVCEnabled:
				checkChannel = vGuild.get_channel( Commander.autoMoveBackChannelID )
				if checkChannel == None:
					SanityCheck.BadChannel("Commander: Invalid COMMANDER invalid automoveback channel", str(Commander.autoMoveBackChannelID))

			# SOBER FEEDBACK
			checkChannel = vGuild.get_channel( Commander.soberFeedbackID )
			if checkChannel == None:
				SanityCheck.BadChannel("Commander: Invalid SOBER FEEDBACK channel", str(Commander.soberFeedbackID))


		if checkOptions.UsedByNewUser:
			# GATE CHANNEL
			checkChannel = vGuild.get_channel( NewUsers.gateChannelID )
			if checkChannel == None:
				SanityCheck.BadChannel("NewUsers: Invalid GATE Channel ID", str(NewUsers.gateChannelID))

			# GENERAL CHANNEL
			checkChannel = vGuild.get_channel( NewUsers.generalChanelID )
			if checkChannel == None:
				SanityCheck.BadChannel("NewUsers: Invalid ADMIN channel", str(NewUsers.generalChanelID))