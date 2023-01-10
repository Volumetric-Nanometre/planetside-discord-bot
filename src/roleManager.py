# Class/Module for managing role giving/removals.

import discord
import discord.ext
from discord.ext import commands
import discord.utils
import asyncio

import botData.settings 
import botUtils
from botUtils import BotPrinter as BUPrint
from botUtils import UserHasCommandPerms
from botData.settings import CommandRestrictionLevels


class UserRoles(commands.GroupCog, name="roles", description="Add or remove user-assignable roles"):
	"""
	# USER ROLES COG
	Responsible for the commands which add and remove user-assignable roles.
	"""
	def __init__(self, p_bot):
		super().__init__()
		self.bot: commands.Bot = p_bot
		BUPrint.Info("COG: User Roles loaded")

	@discord.app_commands.command(name="add", description="Select roles you wish to add.")
	async def adduserrole(self, pInteraction: discord.Interaction):
		"""
		# ADD USER ROLE
		Command enabling a user to select role(s) they wish to add to themselves.
		"""
		# HARDCODED ROLE USEAGE:
		if not await UserHasCommandPerms(pInteraction.user, (CommandRestrictionLevels.level3), pInteraction):
			return

		vView = RoleManager(p_bot=self.bot, p_user=pInteraction.user, pIsAdding=True)
		vView.vInteraction = pInteraction

		await pInteraction.response.send_message(botData.settings.Messages.userAddingRoles, view=vView, ephemeral=True)
	
	@discord.app_commands.command(name="remove", description="Select roles you wish to remove.")
	async def removeuserrole(self, pInteraction: discord.Interaction):
		"""
		# REMOVE USER ROLE
		Command enabling a user to select role(s) they wish to remove from themselves.
		"""
		if not await UserHasCommandPerms(pInteraction.user, (CommandRestrictionLevels.level3), pInteraction):
			return

		vView = RoleManager(p_bot=self.bot, p_user=pInteraction.user, pIsAdding=False)
		vView.vInteraction = pInteraction

		await pInteraction.response.send_message(botData.settings.Messages.userRemovingRoles, view=vView, ephemeral=True)



class RoleManager(discord.ui.View):
	"""
	# ROLE MANAGER:
	A view that displays the role selectors and an update button.
	Requires multiple arguments during creation:

	`p_bot` : Reference to the Bot; needed to get, add and remove roles.
	`p_user`: The user who is being edited.
	`pisAdding`: A boolean to determine whether roles are being added (true) or removed (false) 
	"""
	def __init__(self, p_bot, p_user: discord.Member, pIsAdding: bool):
		super().__init__()
		self.bot: commands.Bot = p_bot
		self.vUser = p_user
		self.vGuild:discord.Guild 
		self.vInteraction: discord.Interaction
		self.lock = asyncio.Lock()

		self.vTDKDRoles = TDKDRoles()
		self.vGameRoles1 = GameRoles( botData.settings.Roles.addRoles_games1 )
		self.vGameRoles2 = GameRoles( botData.settings.Roles.addRoles_games2 )
		self.vGameRoles3 = GameRoles( botData.settings.Roles.addRoles_games3 )

		self.bAddRoles = pIsAdding
		BUPrint.Debug(f"{p_user.name} is updating roles.  Adding new roles: {self.bAddRoles}")
		
		self.add_item(self.vTDKDRoles)
		if len(self.vGameRoles1.options):
			self.add_item(self.vGameRoles1)

		if len(self.vGameRoles2.options):
			self.add_item(self.vGameRoles2)

		if len(self.vGameRoles3.options):
			self.add_item(self.vGameRoles3)



	@discord.ui.button(label="Update", style=discord.ButtonStyle.primary, row=4)
	async def btnUpdateRoles(self, pInteraction: discord.Interaction, vButton: discord.ui.button):
		await self.vInteraction.delete_original_response()
		await self.UpateUserRoles()
		await self.vInteraction.followup.send(content="Roles updated!", ephemeral=True)


	async def UpateUserRoles(self):
		# Create a list of all the roles a user can self-assign.
		# This will be used later to check and remove unassigned roles.
		vOptionList = self.vTDKDRoles.options + self.vGameRoles1.options + self.vGameRoles2.options + self.vGameRoles3.options
		vUserRolesList: list = []
		role: discord.SelectOption
		for role in vOptionList:
			vUserRolesList.append(role.value)

		BUPrint.Debug(f"User Role List: {vUserRolesList}")

		# Create a list of selected user roles.
		vUserSelectedRoles = self.vTDKDRoles.values + self.vGameRoles1.values + self.vGameRoles2.values
		BUPrint.Debug(f"Selected Roles: {vUserSelectedRoles}")

		# Ensure we're operating on TDKD server.
		self.vGuild = await botUtils.GetGuild(self.bot)

		if len(self.vGuild.roles) == 0:
			BUPrint.LogError(p_titleStr="NO ROLES", p_string="UserRoles guild object has no roles.")
			return

		# Roles To Use: list of role objects corresponding to user choices.
		vRolesToUse = []

		if len(vRolesToUse):
			for serverRoleIndex in self.vGuild.roles:
				# Only proceed if role is one a user can add/remove
				if f"{serverRoleIndex.id}" in vUserRolesList:
					if f"{serverRoleIndex.id}" in vUserSelectedRoles:
						vRolesToUse.append(serverRoleIndex)
				else:
					BUPrint.Debug(f"Role: {serverRoleIndex.name} is not user-assignable. Skipping...")


			BUPrint.Debug("Modifying user roles...")
			try:
				if self.bAddRoles:
					await self.vUser.add_roles(*vRolesToUse, reason="User self assigned role with /role command")
				else:
					await self.vUser.remove_roles(*vRolesToUse, reason="User self unassigned roles with /role command")

			except discord.Forbidden as vError:
				BUPrint.LogErrorExc("Invalid permission to modify user roles.", vError)
			except discord.HTTPException as vError:
				BUPrint.LogErrorExc("Unable to modify user roles.", vError)
			
			if self.bAddRoles:
				BUPrint.Info(f"{self.vUser.display_name} added {len(vRolesToUse)} roles to themself.")
			else:
				BUPrint.Info(f"{self.vUser.display_name} removed {len(vRolesToUse)} roles to themself.")
		else:
			BUPrint.Debug("User chose no roles.")



class RoleSelection(discord.ui.Select):
	async def callback(self, pInteraction: discord.Interaction):
		await pInteraction.response.defer(ephemeral=True, thinking=False)

###
# ADDING NEW ROLES : go to botData -> Settings -> class Roles
# 'max_values' should always equate to the maximum number of roles available.
# Unless you wish for users to repeateldy run the command to add/remove roles. :p


class TDKDRoles(RoleSelection):
	def __init__(self):
		vOptions = botData.settings.Roles.addRoles_TDKD

		super().__init__(placeholder="TDKD/PS2 Notification roles", min_values=0, max_values=len(botData.settings.Roles.addRoles_TDKD), options=vOptions)


class GameRoles(RoleSelection):
	def __init__(self, p_options:list):
		super().__init__(placeholder="Other Games roles", min_values=0, max_values=len(p_options), options=p_options)