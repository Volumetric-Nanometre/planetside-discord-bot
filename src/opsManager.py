# Ops Manager: Manages creating, editing and removing of Ops.

import os
import datetime
import pickle

import discord
from discord.ext import commands
import enum

import OpSignup
import opsCommander

import settings
import botUtils
import botData

class OpsManager():
	def init(self):
		# List of ops (file names)
		self.vOpsList: list = self.GetOps()

	# Returns a list of full pathed strings for each 
	async def GetOps():
		botUtils.BotPrinter.Debug("Getting Ops list...")
		vOpsDir = f"{settings.botDir}/{settings.opsFolderName}/"
		vDataFiles: list = []
		
		for file in os.listdir(vOpsDir):
			if file.endswith(".json"):
				vDataFiles.append(file)
		botUtils.BotPrinter.Debug(f"Ops files found: {vDataFiles}")
		
		return vDataFiles


	# Returns an ENUM containing the names of saved default Operations.
	# Does not use SELF to make it callable without constructing an instance.
	# Does not use Async to allow it to be called in function parameters.
	# Mainly used to provide dynamic 
	def GetDefaultOpsAsEnum():
		botUtils.BotPrinter.Debug("Getting Ops list...")
		vOpsDir = f"{settings.botDir}/{settings.defaultOpsDir}/"
		OpsManager.createDefaultsFolder()

		vDataFiles: list = ["Custom"]
		
		for file in os.listdir(vOpsDir):
			if file.endswith(".json"):
				vDataFiles.append(file)

		if len(vDataFiles) > 1:
			botUtils.BotPrinter.Debug(f"Ops files found: {vDataFiles}")
			return enum.Enum("OpsType", vDataFiles)
		else:
			botUtils.BotPrinter.Debug("No ops files!")
			return enum.Enum("OpsType", ["Custom", "(noSavedDefaults)"])



	async def createOpsFolder():
		if (not os.path.exists(f"{settings.botDir}/{settings.opsFolderName}") ):
			try:
				os.makedirs(f"{settings.botDir}/{settings.opsFolderName}")
			except:
				botUtils.BotPrinter.LogError("Failed to create folder for Ops data!")


	def createDefaultsFolder():
		botUtils.BotPrinter.Debug("Creating default ops folder (if non existant)")
		if (not os.path.exists(f"{settings.botDir}/{settings.defaultOpsDir}") ):
			try:
				os.makedirs(f"{settings.botDir}/{settings.defaultOpsDir}")
			except:
				botUtils.BotPrinter.LogError("Failed to create folder for default Ops data!")


class OpsMessage(discord.ui.View):
	def __init__(self, pOpsDataFile: str):
		self.opsDataFile = pOpsDataFile
		self.opsData: botData.OperationData
		botUtils.BotPrinter.Debug("OpsMessage created.  Don't forget to save or load data!")
		# super().__init__(timeout=None)

	async def saveToFile(self):
		botUtils.BotPrinter.Debug(f"Attempting to save {self.opsData.name} to file: {self.opsDataFile}")
		try:
			with open(self.opsDataFile, 'wb') as vFile:
				pickle.dump(self.opsData, vFile)
				botUtils.BotPrinter.Debug("Saved data succesfully!")
		except:
			botUtils.BotPrinter.LogError(f"Failed to save {self.opsData.name} to file {self.opsDataFile}!")
		
	async def getDataFromFile(self):
		botUtils.BotPrinter.Debug(f"Attempting to load data from file: {self.opsDataFile}")
		try:
			with open(self.opsDataFile, 'rb') as vFile:
				self.opsData = pickle.load(vFile)
				botUtils.BotPrinter.Debug("Loaded data succesfully!")
		except:
			botUtils.BotPrinter.LogError(f"Failed to load Ops data from file: {self.opsDataFile}")

	# Returns a view using the data 
	async def GenerateEmbed(self):
		vEmbed = discord.Embed(colour=botUtils.Colours.editing, title=self.opsData.name, description=self.opsData.description, timestamp=self.opsData.date)

		# Generate lists for roles:
		role: botData.OpRoleData
		for role in self.opsData.roles:
			vSignedUpUsers: str
			for user in role.players:
				vSignedUpUsers += f"{user}\n"
			vEmbed.add_field(inline=True, 
			name=f"{role.roleName}({len(role.players)}/{role.maxPositions})",
			value=vSignedUpUsers)
	
	# async def UpdateView():
	# 	print("Teehee")

# Class responsible for displaying options, editing and checking.
class OpsEditor(discord.ui.View):
	def __init__(self, pBot: commands.Bot, pOpsData: botData.OperationData):
		self.vBot = pBot
		self.vOpsData = pOpsData # Original data, not edited.
		# self.EditedData = pOpsData # Edited data, applied and saved.
		botUtils.BotPrinter.Debug("Created Blank Editor")
		super().__init__(timeout=None)
		

	# # Edit Buttons

	# Edit Date:
	editButtonStyle = discord.ButtonStyle.grey
	@discord.ui.button( label="Edit Date",
						style=editButtonStyle, 
						custom_id="EditDate",
						row=0)
	async def btnEditDate(self, pInteraction: discord.Interaction, pButton: discord.ui.button):
		vEditModal = EditDates(title="Edit Date/Time")
		vEditModal.vData = self.vOpsData
		vEditModal.custom_id="EditDateModal"
		await pInteraction.response.send_modal( vEditModal )
	
	# Edit Info
	@discord.ui.button(
						style=editButtonStyle, 
						label="Edit Info",
						custom_id="EditInfo",
						row=1)
	async def btnEditInfo(self, pInteraction: discord.Interaction, pButton: discord.ui.button):
		vEditModal = EditInfo(title="Edit Info")
		vEditModal.vData = self.vOpsData
		vEditModal.custom_id="EditInfoModal"
		await pInteraction.response.send_modal( vEditModal )

	# Edit Roles
	@discord.ui.button(
						style=editButtonStyle, 
						label="Edit Roles",
						custom_id="EditRoles",
						row=2)
	async def btnEditRoles(self, pInteraction: discord.Interaction, pButton: discord.ui.button):
		vEditModal = EditRoles(title="Edit Roles")
		vEditModal.vData = self.vOpsData
		vEditModal.custom_id="EditRolesModal"
		await pInteraction.response.send_modal( vEditModal )
	
	# # Confirm/Save buttons:
	@discord.ui.button(
						style=discord.ButtonStyle.danger, 
						label="Apply Changes",
						custom_id="EditRolesApply",
						row=4)
	async def btnApplyChanges(self, pInteraction: discord.Interaction, pButton: discord.ui.button):
		await pInteraction.response.send_message("Ops data updated!")

	@discord.ui.button( 
						style=discord.ButtonStyle.primary, 
						label="New Default",
						custom_id="EditRolesNewDefault",
						row=4)
	async def btnNewDefault(self, pInteraction: discord.Interaction, pButton: discord.ui.button):
		await pInteraction.response.send_message("Added new default!")



class EditDates(discord.ui.Modal):
	txtDay = discord.ui.TextInput(
		label="Day",
		placeholder="Day of month",
		min_length=1, max_length=2,
		required=False
	)
	txtMonth = discord.ui.TextInput(
		label="Month",
		placeholder="What month?  Numerical value!",
		min_length=1, max_length=2,
		required=False
	)
	txtHour = discord.ui.TextInput(
		label="Hour",
		placeholder="Hour",
		min_length=1, max_length=2,
		required=False
	)
	txtMinute = discord.ui.TextInput(
		label="Minute",
		placeholder="Minute",
		min_length=1, max_length=2,
		required=False
	)
	def __init__(self, *, title: str = "Edit Date/Time"):
		self.title = title
		self.vData : botData.OperationData
		super().__init__()

	async def on_eror(self, pInteraction: discord.Interaction, error: Exception):
		botUtils.BotPrinter.LogError("Error occured on Edit Date Modal.", p_exception=error)

	async def on_timeout(self):
		await self.stop()

	# Where the fun happens!
	async def on_submit(self, pInteraction: discord.Interaction):
		botUtils.BotPrinter.Debug("Edit Dates Modal submitted, creating new date...")

		# Only change values changed
		if self.txtMonth.value != "":
			self.vData.date.month = self.txtMonth.value

		if self.txtDay.value != "":
			self.vData.date.day = self.txtDay.value

		if self.txtHour.value != "":
			self.vData.date.hour = self.txtHour.value

		if self.txtMinute.value != "":
			self.vData.date.minute = self.txtMinute.value

		await pInteraction.response.send_message("Date/Time updated!")



###############################
# EDIT INFO

class EditInfo(discord.ui.Modal):
	txtName = discord.ui.TextInput(
		label="Ops Name",
		placeholder="Name of the Ops (used as the defaults name)",
		min_length=3, max_length=50,
		required=True
	)
	txtDescription = discord.ui.TextInput(
		label="Description",
		placeholder="Brief explanation of this Ops",
		style=discord.TextStyle.paragraph,
		max_length=2000,
		required=False
	)
	txtMessage = discord.ui.TextInput(
		label="Details",
		placeholder="A more detailed message about this ops?  Defaults to blank.",
		style=discord.TextStyle.paragraph,
		required=False
	)
	def __init__(self, *, title: str = "Edit Ops Name/Descriptions"):
		self.title = title
		self.vData : botData.OperationData
		super().__init__()

	async def on_eror(self, pInteraction: discord.Interaction, error: Exception):
		botUtils.BotPrinter.LogError("Error occured on Edit Info Modal", p_exception=error)

	async def on_timeout(self):
		await self.stop()

	# Where the fun happens!
	async def on_submit(self, pInteraction: discord.Interaction):
		botUtils.BotPrinter.Debug("Edit Dates Modal submitted, creating new date...")

		# Only change values changed
		if self.txtName.value != "":
			self.vData.name = self.txtName.value

		if self.txtDescription.value != "":
			self.vData.description = self.txtDescription.value

		if self.txtMessage.value != "":
			self.vData.customMessage = self.txtMessage.value

		await pInteraction.response.send_message("Info updated!")


###############################
# EDIT ROLES

class EditRoles(discord.ui.Modal):
	txtEmoji = discord.ui.TextInput(
		label="Emoji",
		placeholder="EmojiID String per line",
		style=discord.TextStyle.paragraph,
		required=True
	)
	txtRoleName = discord.ui.TextInput(
		label="Role Name",
		placeholder="Light Assault",
		style=discord.TextStyle.paragraph,
		required=True
	)
	txtRoleMaxPos = discord.ui.TextInput(
		label="Max Positions",
		placeholder="Max positions, per line.",
		style=discord.TextStyle.paragraph,
		required=True
	)
	def __init__(self, *, title: str = "Edit Roles"):
		self.title = title
		self.vData : botData.OperationData
		super().__init__()

	async def on_eror(self, pInteraction: discord.Interaction, error: Exception):
		botUtils.BotPrinter.LogError("Error occured on Edit Roles modal.", p_exception=error)

	async def on_timeout(self):
		await self.stop()

	# Where the fun happens!
	async def on_submit(self, pInteraction: discord.Interaction):
		botUtils.BotPrinter.Debug("Edit Roles Modal submitted...")
		vRoleNames = self.txtRoleName.value.splitlines()
		vRoleEmoji = self.txtEmoji.value.splitlines()
		vRoleMax = self.txtRoleMaxPos.value.splitlines()
		
		# If user made an error, don't proceed- inconstsent lengths!
		if len(vRoleNames) != len(vRoleEmoji) != len(vRoleMax):
			await pInteraction.response.send_message("Inconsistent array lengths in fields!  \nMake sure the number of lines matches in all three fields.")
			return
		
		# role: botData.OpRoleData
		# for role in self.vData.roles:
		# 	if role.roleName in vRoleNames:


		vIndex = 0
		botUtils.BotPrinter.Debug(f"Size of array: {len(vRoleEmoji)}")
		while vIndex < len(vRoleEmoji):
			# Check existing role
			# If role exists, update its data, else its a new role.
			# Iterate over existing roles first.

			## OOOOR, make opROleDatas, and compare & add those!
			vCurrentRole = botData.OpRoleData(roleName=vRoleNames[vIndex], roleIcon=vRoleEmoji[vIndex], maxPositions=vRoleMax[vIndex])
			if vIndex < len(self.vData.roles) :
				# Index is on an existing role, adjust values to keep any signed up users.
				self.vData.roles[vIndex].roleName = vCurrentRole.roleName
				self.vData.roles[vIndex].roleIcon = vCurrentRole.roleIcon
				self.vData.roles[vIndex].maxPositions = vCurrentRole.maxPositions
			else:
				# Index is a new role, append!
				self.vData.roles.append(vCurrentRole)

			vIndex += 1
		# End of while loop.
		await pInteraction.response.send_message(f"Roles updated!\n{self.vData.roles}")

	# Prefill fields:
	async def PresetFields(self):
		print("Woop") ##  DO THIS THINGYDOODER!!!
	
	# Create Role lists.
