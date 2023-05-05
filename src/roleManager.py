# Class/Module for managing role giving/removals.

import discord
import discord.ext
from discord.ext import commands
import discord.utils
import asyncio
from os import path
import botData.settings 
import botUtils
from botUtils import BotPrinter as BUPrint
from botUtils import UserHasCommandPerms
from botData.settings import CommandRestrictionLevels, SelfAssignableRoles, Directories


class UserRoles(commands.GroupCog, name="roles", description="Add or remove user-assignable roles"):
	"""
	# USER ROLES COG
	Responsible for the commands which add and remove user-assignable roles.
	"""
	def __init__(self, p_bot):
		super().__init__()
		self.bot: commands.Bot = p_bot
		UserAssignableRoleManager().LoadRoles()

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
		self.selectors:list[RoleSelection] = []


		selector = TDKDRoles()
		self.selectors.append(selector)
		self.add_item( selector )


		for sublist in UserAssignableRoleManager().GetGameRoles():
			if bool(len(sublist)):
				selector = self.add_item(GameRoles( sublist ))
				self.selectors.append(selector)

		self.bAddRoles = pIsAdding
		BUPrint.Debug(f"{p_user.name} is updating roles.  Adding new roles: {self.bAddRoles}")
		


	@discord.ui.button(label="Update", style=discord.ButtonStyle.primary, row=4)
	async def btnUpdateRoles(self, pInteraction: discord.Interaction, vButton: discord.ui.button):
		await self.vInteraction.delete_original_response()
		await self.UpateUserRoles()
		await self.vInteraction.followup.send(content="Roles updated!", ephemeral=True)


	async def UpateUserRoles(self):
		"""# UPDATE USER ROLES
		Updates the users roles using the ones selected from the dropdowns.

		Whether the roles are added or removed is dependant on which command was called,
		and the behaviour is managed by a single if statement at the end of this function.
		"""

		# Create a list of all the roles a user can self-assign.
		# This will be used later to check and remove unassigned roles.
		vOptionList = UserAssignableRoleManager().tdkdRoles + UserAssignableRoleManager().gameRoles
		vUserRoleIDs: list[int] = [int(role.value) for role in vOptionList]
		vUserSelectedRoles = [int(selected.values) for selected in self.selectors]

		BUPrint.Debug(f"User Role ID List: {vUserRoleIDs}")
		BUPrint.Debug(f"Selected Roles: {vUserSelectedRoles}")

		# Ensure we're operating on TDKD server.
		self.vGuild = await botUtils.GetGuild(self.bot)

		if len(self.vGuild.roles) == 0:
			BUPrint.LogError(p_titleStr="NO ROLES", p_string="UserRoles guild object has no roles.")
			return

		# Roles To Use: list of role objects corresponding to user choices.
		vRolesToUse = [role for role in self.vGuild.roles if str(role.id) in vUserSelectedRoles]


		if len(vRolesToUse) != 0:
			BUPrint.Debug(f"Adding roles: {vRolesToUse}")
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
		super().__init__(placeholder="TDKD/PS2 Notification roles", min_values=0, max_values=len(UserAssignableRoleManager().tdkdRoles), options=UserAssignableRoleManager.tdkdRoles)


class GameRoles(RoleSelection):
	def __init__(self, p_options:list):
		super().__init__(placeholder="Other Games roles", min_values=0, max_values=len(p_options), options=p_options)



class UserAssignableRoleManager():
	"""#User Assignable Role Manager:
	A class for self assignable roles that allow game roles to be added and removed at run-time.
	"""

	gameRoles:list[discord.SelectOption] = []
	"""List of SelectOptions for GAME roles.
	Set and specified within the saved file.
	"""

	tdkdRoles: list[discord.SelectOption] = []
	"""List of selectOptions for TDKD/PS2 roles."""


	tdkdFilePath = f"{Directories.runtimeConfigurable}tdkd_{SelfAssignableRoles.fileNameAffix}"
	"""Filepath for the tdkd/ps2 roles."""
	
	gameFilePath = f"{Directories.runtimeConfigurable}games_{SelfAssignableRoles.fileNameAffix}"
	"""File path for the game roles."""


	def __init__(self) -> None:
		if not path.exists(self.tdkdFilePath):
			BUPrint.Info("TDKD roles file not found.  Creating empty file.")
			self.WriteRolesToFile(self.tdkdFilePath, self.tdkdRoles)

		if not path.exists(self.gameFilePath):
			BUPrint.Info("Game roles file not found.  Creating empty file.")
			self.WriteRolesToFile(self.gameFilePath, self.gameRoles)


	def GetGameRoles(self) -> list[list]:
		"""# Get Game Roles: 
		
		Returns a list of lists, containing selectOptions.
		
		Due to the limitation of 25 items per list, the results are split into lists of 25."""
		returnList = []

		currentList = []
		indexCount = 0
		for currentIndex in self.gameRoles:
			if indexCount == 25:
				currentList.append(currentIndex)
				returnList.append(currentList)
				
				indexCount = 0
				currentList = list()

			else:
				indexCount += 1
				currentList.append(currentIndex)


		if bool( len(currentList) ):
			returnList.append(currentList)

		return returnList


	
	def AddNewRole(self, p_isTDKDRole:bool, p_roleName:str, p_roleID:str, p_emoji:str = ""):
		"""# Add New Role:
		Function to add a new role and saves the modified file.

		Returns FALSE if unable to add a new role (over limit)

		### PARAMETERS
		- `p_roleName` : Name of the displayed role/select item.
		- `p_roleID` : ID of the self-assignable role.
		- `p_emoji` : Optional emoji string.
		"""

		BUPrint.Info(f"Adding new assignable role: {p_roleName} | {p_roleID} | {p_emoji}")

		if p_isTDKDRole:
			if len(self.tdkdRoles) == 25:
				return False

			if p_emoji != "":
				self.tdkdRoles.append(discord.SelectOption(label=p_roleName, value=p_roleID, emoji=p_emoji))
			else:
				self.tdkdRoles.append(discord.SelectOption(label=p_roleName, value=p_roleID))


		else:
			if len(self.gameRoles) == 75:
				return False

			if p_emoji != "":
				self.gameRoles.append(discord.SelectOption(label=p_roleName, value=p_roleID, emoji=p_emoji))
			else:
				self.gameRoles.append(discord.SelectOption(label=p_roleName, value=p_roleID))

		
		self.SaveRoles()




	def LoadRoles(self):
		"""# Load Roles:
		Loads roles from the files and assigns them to the respective variables.
		"""
		BUPrint.Info("Loading roles from file...")

		self.ReadRolesFile(self.tdkdFilePath, self.tdkdRoles)

		self.ReadRolesFile(self.gameFilePath, self.gameRoles)




	def ReadRolesFile(self, p_filePath:str, p_roleArray:list) -> bool:
		"""Read Roles File:
		Loads and reads the role file given, then parses passed strings and sets the array with the new options.

		Returns False if an error occurs.
		"""
		roleTextLines = ""
		try:
			with open(p_filePath, "rt") as openFile:
				roleTextLines = openFile.readlines()
		
		except FileNotFoundError:
			BUPrint.LogError(p_titleStr="File not found", p_string=f"Unable to load roles. (file: {p_filePath})")
			return False

		except OSError:
			BUPrint.LogError(p_titleStr="Error reading file", p_string=f"Unable to load roles from {p_filePath}")
			return False

		if roleTextLines != None:
			p_roleArray.clear()

			for roleTxtLine in roleTextLines:
				BUPrint.Debug(f"		-> {roleTxtLine.strip()}")
				roleOption = self.GetRoleFromLine(roleTxtLine)

				if roleOption != None:
					p_roleArray.append( roleOption )

		return True



	def SaveRoles(self):
		"""# Save Roles:
		Convenience function:
		Saves all the roles to file using `WriteRoleToFile`"""

		BUPrint.Info("Saving modified user assignable roles to file...")
		self.WriteRolesToFile(self.tdkdFilePath, self.tdkdRoles)
		self.WriteRolesToFile(self.gameFilePath, self.gameRoles)



	def WriteRolesToFile(self, p_filePath:str, p_array:list[discord.SelectOption]):
		"""# Write Roles to File:
		
		Takes all user assignable roles currently in the passed array and saves them to file.
		"""
		linesToWrite = []
		try:
			with open(p_filePath, "wb") as savedFile:
				for role in p_array:
					linesToWrite.append(f"{role.label}{SelfAssignableRoles.deliminator}{role.value}{SelfAssignableRoles.deliminator}{role.emoji}\n")
			
				savedFile.writelines(linesToWrite)
		
		except OSError:
			BUPrint.LogError(p_titleStr="Failed to write file", p_string=f"{p_filePath}")



	def GetRoleFromLine(self, p_string:str) -> discord.SelectOption:
		"""#Get Role from Line
		Convenience function to create and return a SelectOption from a string.
		
		returns NONE if:
		 - Invalid value is present.
		 - Index error occurs (incorrectly manually adjusted file)
		"""

		splitString = p_string.split(SelfAssignableRoles.deliminator)

		try:
			nameString = splitString[0]
			valueString = splitString[1]
			emojiString = splitString[2]
		
		except IndexError:
			return None
		
		if not valueString.isnumeric():
			return None


		if len(emojiString):	
			return discord.SelectOption(label=nameString, value=valueString)
				
		else:
			return discord.SelectOption(label=nameString, value=valueString, emoji=emojiString)