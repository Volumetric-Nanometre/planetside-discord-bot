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
		vOptions = [
			# discord.SelectOption(label="Planetside", value="TDKD", description="The main role for TDKD planetside.", emoji=''),
			discord.SelectOption(label="Planetside Pings", value="ps2", description="Non-major PS2 events/fellow drunken doggos looking for company"),
			discord.SelectOption(label="Sober Dogs", value="1040751250163122176", description="More serious, coordinated infantry events"),
			discord.SelectOption(label="Base Busters", value="LogiDogs", description="Base building and busting events"),
			discord.SelectOption(label="Armour Dogs", value="ArmourDogs", description="Ground vehicle related events"),
			discord.SelectOption(label="Dog Fighters", value="dogfighter", description="Small aerial vehicle related events"),
			discord.SelectOption(label="Royal Air Woofs", value="RAW", description="Heavy aerial vehicle related events"),
			discord.SelectOption(label="PS2 Twitter", value="Twitter", description="Planetside 2 Twitter posts"),
			discord.SelectOption(label="Jaeger", value="IdontfuckinknowCactusHelp", description="Jeager events")
			# discord.SelectOption(label="", value="", description="", emoji='')
		]

		super().__init__(placeholder="TDKD/PS2 Notification roles", min_values=0, max_values=8, options=vOptions)



class GameRoles1(RoleSelection):
	def __init__(self):
		self.parentView:RoleManager
		vOptions = [
			discord.SelectOption(label="Post Scriptum", value="1"),
			discord.SelectOption(label="Squad", value="2"),
			discord.SelectOption(label="Space Engineers", value="3"),
			discord.SelectOption(label="Deep Rock Galactic", value="4"),
			discord.SelectOption(label="Valheim", value="5"),
			discord.SelectOption(label="Terraria", value="6"),
			discord.SelectOption(label="Apex Legends", value="7"),
			discord.SelectOption(label="Minecraft", value="8"),
			discord.SelectOption(label="Team Fortress 2", value="9"),
			discord.SelectOption(label="Dungeon and Dragons", value="10"),
			discord.SelectOption(label="Warframe", value="11"),
			discord.SelectOption(label="Supreme Commander", value="12"),
			discord.SelectOption(label="Battlefield 2042", value="13"),
			discord.SelectOption(label="Conqueror's Blade", value="14"),
			discord.SelectOption(label="Stellaris", value="15"),
			discord.SelectOption(label="Sea of Thieves", value="16"),
			discord.SelectOption(label="Back 4 Blood", value="17"),
			discord.SelectOption(label="Garrys' Mod", value="18"),
			discord.SelectOption(label="Killing Floor 2", value="19"),
			discord.SelectOption(label="Vermintide", value="20"),
			discord.SelectOption(label="Total War: Warhammer", value="21"),
			discord.SelectOption(label="Factorio", value="22"),
			discord.SelectOption(label="Warthunder", value="23"),
			discord.SelectOption(label="Gates of Hell", value="24"),
			discord.SelectOption(label="Overwatch", value="25")
		]
		super().__init__(placeholder="Other Games roles", min_values=0, max_values=25, options=vOptions)
	
	# async def callback(self, pInteraction: discord.Interaction):
		# await self.parentView.UpateUserRoles()


class GameRoles2(RoleSelection):
	def __init__(self):
		vOptions = [
			discord.SelectOption(label="World of Tanks", value="987"),
			discord.SelectOption(label="Star Citizen", value="654")
			# discord.SelectOption(label="", value="", description="", emoji=""),
			# discord.SelectOption(label="", value="", description="", emoji=""),
			# discord.SelectOption(label="", value="", description="", emoji=""),
			# discord.SelectOption(label="", value="", description="", emoji=""),
			# discord.SelectOption(label="", value="", description="", emoji=""),
			# discord.SelectOption(label="", value="", description="", emoji=""),
			# discord.SelectOption(label="", value="", description="", emoji=""),
			# discord.SelectOption(label="", value="", description="", emoji=""),
			# discord.SelectOption(label="", value="", description="", emoji=""),
			# discord.SelectOption(label="", value="", description="", emoji=""),
			# discord.SelectOption(label="", value="", description="", emoji=""),
			# discord.SelectOption(label="", value="", description="", emoji=""),
			# discord.SelectOption(label="", value="", description="", emoji=""),
			# discord.SelectOption(label="", value="", description="", emoji=""),
			# discord.SelectOption(label="", value="", description="", emoji=""),
			# discord.SelectOption(label="", value="", description="", emoji=""),
			# discord.SelectOption(label="", value="", description="", emoji=""),
			# discord.SelectOption(label="", value="", description="", emoji=""),
			# discord.SelectOption(label="", value="", description="", emoji=""),
			# discord.SelectOption(label="", value="", description="", emoji=""),
			# discord.SelectOption(label="", value="", description="", emoji=""),
			# discord.SelectOption(label="", value="", description="", emoji=""),
			# discord.SelectOption(label="", value="", description="", emoji="")
		]
		super().__init__(placeholder="Other Games roles", min_values=0, max_values=2, options=vOptions)



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
	#  Make sure "max values" matches the number of roles.  It bugs out if higher than the actual amount of roles available.