# Class/Module for managing role giving/removals.

import discord
import discord.ext
from discord.ext import commands
import discord.utils
# from discord.ext import commands
# from discord import app_commands
import asyncio

import botData.settings 
from botUtils import BotPrinter


class RoleManager(discord.ui.View):
	def __init__(self, p_bot, p_user: discord.Member, pIsAdding: bool):
		super().__init__()
		self.bot: commands.Bot = p_bot
		self.vUser = p_user
		self.vGuild = discord.Guild
		self.vInteraction: discord.Interaction
		self.lock = asyncio.Lock()

		self.vTDKDRoles = TDKDRoles()
		self.vTDKDRoles.parentView = self
		self.vGameRoles1 = GameRoles1()
		self.vGameRoles1.parentView = self
		self.vGameRoles2 = GameRoles2()
		self.vGameRoles2.parentView = self

		self.bAddRoles = pIsAdding
		BotPrinter.Debug(f"{p_user.name} is updating roles.  Adding new roles: {self.bAddRoles}")
		
		self.add_item(self.vTDKDRoles)
		self.add_item(self.vGameRoles1)
		self.add_item(self.vGameRoles2)

	@discord.ui.button(label="Update", style=discord.ButtonStyle.primary, row=4)
	async def btnUpdateRoles(self, pInteraction: discord.Interaction, vButton: discord.ui.button):
		await self.UpateUserRoles()
		await self.vInteraction.delete_original_response()
		# await self.vInteraction.response.send_message("Roles updated!") 
		await self.vInteraction.followup.send(content="Roles updated!", ephemeral=True)


	async def UpateUserRoles(self):
		# Create a list of all the roles a user can self-assign.
		# This will be used later to check and remove unassigned roles.
		vOptionList = self.vTDKDRoles.options + self.vGameRoles1.options + self.vGameRoles2.options
		vUserRolesList: list(str) = []  #= 
		role: discord.SelectOption
		for role in vOptionList:
			vUserRolesList.append(role.value)

		BotPrinter.Debug(f"User Role List: {vUserRolesList}")

		# Create a list of selected user roles.
		vUserSelectedRoles = self.vTDKDRoles.values + self.vGameRoles1.values + self.vGameRoles2.values
		BotPrinter.Debug(f"Selected Roles: {vUserSelectedRoles}")

		# Ensure we're operating on TDKD server.
		self.vGuild = self.bot.get_guild(botData.settings.BotSettings.discordGuild)
		if self.vGuild is None:
			# Try again using non-cache "fetch":
			self.vGuild = await self.bot.fetch_guild(botData.settings.BotSettings.discordGuild)
			if self.vGuild is None:
				BotPrinter.LogError("Failed to find guild for updating roles!")
				return
		BotPrinter.Debug(f"Guild Object: {self.vGuild}")

		# Get all the roles in the server.
		vServerRoles = await self.vGuild.fetch_roles()
				
		# Assign new:
		for serverRoleIndex in vServerRoles:
			BotPrinter.Debug(f"Current Index- ID:Name : {serverRoleIndex.id} : {serverRoleIndex.name}")

		# New loop
			# Only proceed if role is one a user can add/remove
			if f"{serverRoleIndex.id}" in vUserRolesList:
				# Add roles:
				if self.bAddRoles:
					if f"{serverRoleIndex.id}" in vUserSelectedRoles:
						BotPrinter.Debug("ADDING ROLE")
						await self.vUser.add_roles( serverRoleIndex, reason="User self assigned role with /roles command." )

				# Remove roles:
				else:
					if f"{serverRoleIndex.id}" in vUserSelectedRoles:
						BotPrinter.Debug("REMOVING ROLE")
						await self.vUser.remove_roles( serverRoleIndex, reason="User self unassigned role with /roles command" )
			else:
				BotPrinter.Debug("Role is not user-assignable. Skipping...")



class RoleSelection(discord.ui.Select):
	async def callback(self, pInteraction: discord.Interaction):
		await pInteraction.response.defer(ephemeral=True, thinking=False)

###
# ADDING NEW ROLES
# Label: Displayed to user.
# Value: The ID number of the role.  Breaks if typed but not specified.
# Description: Not needed, descriptive text shown to user.
# Emoji: self explanitory: will break if typed emoji="" but no emoji id given
#
# 'max_values' should always equate to the maximum number of roles available.
# Unless you wish for users to repeateldy run the command to add/remove roles. :p


class TDKDRoles(RoleSelection):
	def __init__(self):
		self.parentView: RoleManager
		vOptions = botData.settings.Roles.addRoles_TDKD

		super().__init__(placeholder="TDKD/PS2 Notification roles", min_values=0, max_values=8, options=vOptions)



class GameRoles1(RoleSelection):
	def __init__(self):
		self.parentView:RoleManager
		vOptions = botData.settings.Roles.addRoles_games1
		super().__init__(placeholder="Other Games roles", min_values=0, max_values=25, options=vOptions)
	
	# async def callback(self, pInteraction: discord.Interaction):
		# await self.parentView.UpateUserRoles()


class GameRoles2(RoleSelection):
	def __init__(self):
		vOptions = botData.settings.Roles.addRoles_games2
		super().__init__(placeholder="Other Games roles", min_values=0, max_values=2, options=vOptions)
	#  Make sure "max values" matches the number of roles.  It bugs out if higher than the actual amount of roles available.