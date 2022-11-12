# Class/Module for managing role giving/removals.

import discord
import discord.ext
from discord.ext import commands
import discord.utils
# from discord.ext import commands
# from discord import app_commands
import asyncio

import settings
from botUtils import BotPrinter


class RoleManager(discord.ui.View):
	def __init__(self, p_bot, p_user: discord.Member):
		super().__init__()
		self.bot: commands.Bot = p_bot
		self.vUser = p_user
		self.vGuild = discord.Guild
		self.lock = asyncio.Lock()
		self.vTDKDRoles = TDKDRoles()
		self.vTDKDRoles.parentView = self
		self.vGameRoles1 = GameRoles1()
		self.vGameRoles1.parentView = self
		
		self.add_item(self.vTDKDRoles)
		# self.add_item(self.vGameRoles1)
		# self.add_item(discord.Button(custom_id="BTN_updateRoles", label="Update Roles"))

	@discord.ui.button(label="Update", style=discord.ButtonStyle.primary)
	async def btnUpdateRoles(self, pInteraction: discord.Interaction, vButton: discord.ui.button):
		await self.UpateUserRoles()


	async def UpateUserRoles(self):
		# Create a list of all the roles a user can self-assign.
		# This will be used later to check and remove unassigned roles.
		vUserRolesList = []
			
		for role in self.vTDKDRoles.options:
			vUserRolesList.append(role.value)
			# BotPrinter(f"Updating user roles-  Full role list: {vUserRolesList}")
		for role in self.vGameRoles1.options:
			vUserRolesList.append(role.value)


		# Create a list of selected user roles.
		vUserSelectedRoles = self.vTDKDRoles.values + self.vGameRoles1.values
		BotPrinter.Debug(f"Selected Roles: {vUserSelectedRoles}")

		# Ensure we're operating on TDKD server.
		self.vGuild = self.bot.get_guild(settings.DISCORD_GUILD)
		if self.vGuild is None:
			# Try again using non-cache "fetch":
			self.vGuild = await self.bot.fetch_guild(settings.DISCORD_GUILD)
			if self.vGuild is None:
				BotPrinter.LogError("Failed to find guild for updating roles!")
				return
		BotPrinter.Debug(f"Guild Object: {self.vGuild}")

		# Get all the roles in the server.
		vServerRoles = await self.vGuild.fetch_roles()

		BotPrinter.Debug(f"User ({self.vUser}) Roles: {self.vUser.roles}")
				
		# Assign new:
		for serverRoleIndex in vServerRoles:
			BotPrinter.Debug(f"Current Index- ID:Name : {serverRoleIndex.id} : {serverRoleIndex.name}")

			# User has this role!
			if serverRoleIndex in self.vUser.roles:
				# User has deselected this role (or its one they can't assign, don't remove these! )
				BotPrinter.Debug("User has this role.")
				if f"{serverRoleIndex.id}" not in vUserSelectedRoles and f"{serverRoleIndex.id}" in vUserRolesList:
					BotPrinter.Debug("User has this role, and deselected it!  Removing from user.")
					await self.vUser.remove_roles( serverRoleIndex )
			# User doesn't have, and has selected this role
			elif f"{serverRoleIndex.id}" in vUserSelectedRoles:
				BotPrinter.Debug("User has selected this role, and doesn't have it.  Adding to user...")
				await self.vUser.add_roles( serverRoleIndex )
			else:
				BotPrinter.Debug("Invalid role?")
		BotPrinter.Debug("user roles updated!")
		self.stop()


# class RoleSelection(discord.ui.Select):
# 	def __init__(self):
# 		self.parentView: RoleManager
		

# 	async def callback(self, pInteraction: discord.Interaction):
# 		await self.parentView.UpateUserRoles()


class TDKDRoles(discord.ui.Select):
	def __init__(self):
		self.parentView: RoleManager
		vOptions = [
			# discord.SelectOption(label="Planetside", value="TDKD", description="The main role for TDKD planetside.", emoji=''),
			discord.SelectOption(label="Planetside Pings", value="ps2", description="Get Pings for non-major PS2 events (your fellow drunken doggos looking for company!)"),
			discord.SelectOption(label="Sober Dogs", value="1040751250163122176", description="Get pings for more serious, coordinated infantry gameplay events!"),
			discord.SelectOption(label="Base Busters", value="LogiDogs", description="Get pings for base building and busting events!"),
			discord.SelectOption(label="Armour Dogs", value="ArmourDogs", description="Get pings for ground vehicle related events!"),
			discord.SelectOption(label="Dog Fighters", value="dogfighter", description="Get pings for small aerial vehicle related events!"),
			discord.SelectOption(label="Royal Air Woofs", value="RAW", description="Get pings for heavy aerial vehicle related events!"),
			discord.SelectOption(label="PS2 Twitter", value="Twitter", description="Get pinged when the planetside 2 twitter is updated!"),
			discord.SelectOption(label="Jaeger", value="IdontfuckinknowCactusHelp", description="Get pinged for Jeager events!")
			# discord.SelectOption(label="", value="", description="", emoji='')
		]

		super().__init__(placeholder="Select TDKD roles", min_values=0, max_values=8, options=vOptions)

	async def callback(self, pInteraction: discord.Interaction):
		await self.parentView.UpateUserRoles()
		await pInteraction.response.send_message("Your roles have been updated!", ephemeral=True)



class GameRoles1(discord.ui.Select):
	def __init__(self):
		self.parentView:RoleManager
		vOptions = [
			discord.SelectOption(label="", value="", description=""),
			discord.SelectOption(label="", value="", description=""),
			discord.SelectOption(label="", value="", description=""),
			discord.SelectOption(label="", value="", description=""),
			discord.SelectOption(label="", value="", description=""),
			discord.SelectOption(label="", value="", description=""),
			discord.SelectOption(label="", value="", description=""),
			discord.SelectOption(label="", value="", description=""),
			discord.SelectOption(label="", value="", description=""),
			discord.SelectOption(label="", value="", description=""),
			discord.SelectOption(label="", value="", description=""),
			discord.SelectOption(label="", value="", description=""),
			discord.SelectOption(label="", value="", description=""),
			discord.SelectOption(label="", value="", description=""),
			discord.SelectOption(label="", value="", description=""),
			discord.SelectOption(label="", value="", description=""),
			discord.SelectOption(label="", value="", description=""),
			discord.SelectOption(label="", value="", description=""),
			discord.SelectOption(label="", value="", description=""),
			discord.SelectOption(label="", value="", description=""),
			discord.SelectOption(label="", value="", description=""),
			discord.SelectOption(label="", value="", description=""),
			discord.SelectOption(label="", value="", description=""),
			discord.SelectOption(label="", value="", description=""),
			discord.SelectOption(label="", value="", description="")
		]
		super().__init__(placeholder="Select TDKD roles", min_values=0, max_values=25, options=vOptions)
	
	# async def callback(self, pInteraction: discord.Interaction):
		# await self.parentView.UpateUserRoles()


# class GameRoles0(RoleSelection):
# 	def __init__(self):
# 		vOptions = [
# 			discord.SelectOption(label="", value="", description="", emoji=""),
# 			discord.SelectOption(label="", value="", description="", emoji=""),
# 			discord.SelectOption(label="", value="", description="", emoji=""),
# 			discord.SelectOption(label="", value="", description="", emoji=""),
# 			discord.SelectOption(label="", value="", description="", emoji=""),
# 			discord.SelectOption(label="", value="", description="", emoji=""),
# 			discord.SelectOption(label="", value="", description="", emoji=""),
# 			discord.SelectOption(label="", value="", description="", emoji=""),
# 			discord.SelectOption(label="", value="", description="", emoji=""),
# 			discord.SelectOption(label="", value="", description="", emoji=""),
# 			discord.SelectOption(label="", value="", description="", emoji=""),
# 			discord.SelectOption(label="", value="", description="", emoji=""),
# 			discord.SelectOption(label="", value="", description="", emoji=""),
# 			discord.SelectOption(label="", value="", description="", emoji=""),
# 			discord.SelectOption(label="", value="", description="", emoji=""),
# 			discord.SelectOption(label="", value="", description="", emoji=""),
# 			discord.SelectOption(label="", value="", description="", emoji=""),
# 			discord.SelectOption(label="", value="", description="", emoji=""),
# 			discord.SelectOption(label="", value="", description="", emoji=""),
# 			discord.SelectOption(label="", value="", description="", emoji=""),
# 			discord.SelectOption(label="", value="", description="", emoji=""),
# 			discord.SelectOption(label="", value="", description="", emoji=""),
# 			discord.SelectOption(label="", value="", description="", emoji=""),
# 			discord.SelectOption(label="", value="", description="", emoji=""),
# 			discord.SelectOption(label="", value="", description="", emoji="")
# 		]
# 		super().__init__(placeholder="Choose your other game roles!", min_values=0, max_values=25, options=vOptions)

#https://github.com/Rapptz/discord.py/blob/v2.0.1/examples/views/dropdown.py
