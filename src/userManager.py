import discord
import discord.ext
from discord.ext import commands, tasks
# from discord.ext.commands import Context
from discord import app_commands
from discord import SelectMenu, SelectOption

from auraxium import Client as AuraxClient
import auraxium.ps2 as AuraxPS2

import os

import pickle

from datetime import datetime, timezone, timedelta
from dateutil.relativedelta import relativedelta

from enum import Enum

from botUtils import BotPrinter as BUPrint
from botUtils import DateFormatter, DateFormat, FilesAndFolders, GetGuild, UserHasCommandPerms

import botData.settings as settings
from botData.settings import CommandRestrictionLevels
from botData.users import User
from botData.operations import UserSession


class UserLibraryCog(commands.GroupCog, name="user_library"):
	"""
	# USER LIBRARY COG
	Commands related to the user library, for regular users.
	"""
	def __init__(self, p_botRef):
		self.botRef = p_botRef
		BUPrint.Info("COG: User Library loaded!")


	@app_commands.command(name="about", description="Show information about a user, or see your own!")
	@app_commands.describe(p_userToFind="The user you want to see information about;  Leave empty to see your own!")
	@app_commands.rename(p_userToFind="user")
	async def AboutUser(self, p_interaction:discord.Interaction, p_userToFind:discord.Member = None):
		# HARDCODED ROLE USEAGE:
		if not await UserHasCommandPerms(p_interaction.user, (settings.CommandRestrictionLevels.level3), p_interaction):
			return
		userID = -1

		bViewingSelf = bool(p_userToFind == None or p_userToFind.id == p_interaction.user.id)

		if bViewingSelf:
			userID = p_interaction.user.id
		else:
			userID = p_userToFind.id

		if UserLibrary.HasEntry(userID):
			vLibViewer = LibraryViewer(userID, bViewingSelf)
			await vLibViewer.SendViewer(p_interaction)
	
		elif not bViewingSelf:
			await p_interaction.response.send_message(settings.Messages.noUserEntry, ephemeral=True)
	
		elif settings.UserLib.bUserCanSelfCreate:
			newEntry = User(discordID=p_interaction.user.id)
			UserLibrary.SaveEntry(newEntry)
			
			vLibViewer = LibraryViewer(p_interaction.user.id, True)
			await vLibViewer.SendViewer(p_interaction)
		
		else:
			await p_interaction.response.send_message(settings.Messages.NoUserEntrySelf)




class UserLibraryAdminCog(commands.GroupCog, name="userlib_admin"):
	"""
	# USER LIBRARY ADMIN COG
	Administrative commands and listeners for managing the user library.
	"""
	def __init__(self, p_botRef):
		self.adminLevel = CommandRestrictionLevels.level1
		self.botRef:commands.Bot = p_botRef
		self.contextMenu_setAsRecruit = app_commands.ContextMenu(
			name="Set as Recruit",
			callback=self.SetUserAsRecruit
		)
		self.botRef.tree.add_command(self.contextMenu_setAsRecruit)
		BUPrint.Info("COG: User Library Admin loaded!")

	async def cog_unload(self) -> None:
		self.botRef.tree.remove_command(self.contextMenu_setAsRecruit)
		return await super().cog_unload()


	async def SetUserAsRecruit(self, p_interaction:discord.Interaction, p_User:discord.Member):
		# HARDCODED ROLE USEAGE:
		if not await UserHasCommandPerms(p_interaction.user, self.adminLevel, p_interaction):
			return		
		
		vRecruitRole = p_interaction.guild.get_role(settings.NewUsers.recruitRole)
		vNormalRole = p_interaction.guild.get_role(settings.UserLib.promotionRoleID)
		vUserEntry = UserLibrary.LoadEntry( p_User.id )
		vResultMessage = ""

		if vRecruitRole != None:
			try:
				await p_User.add_roles(vRecruitRole, reason=f"{p_interaction.user.display_name} set {p_User.display_name} to recruit.")
				await p_User.remove_roles(vNormalRole, reason=f"{p_interaction.user.display_name} set {p_User.display_name} to recruit.")

			except discord.Forbidden:
				vResultMessage += "Bot has invalid permissions.\n"
			except discord.HTTPException:
				vResultMessage += "Discord failed to update roles.\n"

		if vUserEntry == None:
			vNewEntry = User(discordID=p_User.id)
			vNewEntry.bIsRecruit = True
			UserLibrary.SaveEntry(vNewEntry)
			vResultMessage += "User had no library entry! Entry was created.\n"
		
		else:
			vUserEntry.bIsRecruit = True
			vResultMessage += "User library has been updated."

		vAdminChn = p_interaction.guild.get_channel( settings.BotSettings.adminChannel )

		if vAdminChn != None:
			try:
				await vAdminChn.send(vResultMessage)
			except:
				BUPrint.Info(vResultMessage)
		else:
			BUPrint.Info(vResultMessage)



	@app_commands.command(name="edit_user", description="Opens the Edit modal for the specified user entry, if they have one.")
	@app_commands.describe(p_userToEdit="Choose the user to edit.", p_createNew="If no entry exists, create a new entry (Default: True)")
	@app_commands.rename(p_userToEdit="user", p_createNew="create_if_none")
	async def ConfigureUser(self, p_interaction:discord.Interaction, p_userToEdit:discord.Member, p_createNew:bool = True):
		# HARDCODED ROLE USEAGE:
		if not await UserHasCommandPerms(p_interaction.user, self.adminLevel, p_interaction):
			return

		if p_userToEdit == None:
			await p_interaction.response.send_message("Invalid user!", ephemeral=True)
			return


		vEntry = None
		if UserLibrary.HasEntry(p_userToEdit.id):
			vEntry = UserLibrary.LoadEntry(p_userToEdit.id)

		elif p_createNew:
			vEntry = User( discordID=p_userToEdit.id )
		
		if vEntry != None:
			await p_interaction.response.send_modal( LibViewer_ConfigureModal(p_adminEditEntry=vEntry) )
		else:
			await p_interaction.response.send_message("No entry was found. If you want to create a new one, ensure `Create_if_none` is true (default!)")



	@app_commands.command(name="get_recruits", description="Returns a message containing recruits and their statistics.")
	async def GetRecruits(self, p_interaction:discord.Interaction):
		# HARDCODED ROLE USEAGE:
		if not await UserHasCommandPerms(p_interaction.user, self.adminLevel, p_interaction):
			return

		await p_interaction.response.defer(ephemeral=True, thinking=True)
		

		vUserEntries = UserLibrary.GetAllEntries()
		vRecruitEntries = []

		if vUserEntries == None:
			await p_interaction.response.send_message("No user entries are saved.", ephemeral=True)
			return

		entry:User
		for entry in vUserEntries:
			if entry.bIsRecruit:
				vRecruitEntries.append(entry)

		if len(vRecruitEntries) == 0:
			await p_interaction.response.send_message("No recruits found.", ephemeral=True)
			return

		vMessage = f"**RECRUITS ({len(vRecruitEntries)})**"

		for entry in vRecruitEntries:
			vUser = p_interaction.guild.get_member( entry.discordID )
			vMessage += f"\n\n{vUser.mention}:\n{UserLibrary.GetRecruitRequirements(entry)}"

		await p_interaction.edit_original_response(content=vMessage)

	

	@commands.Cog.listener("on_raw_member_remove")
	async def UserLeft(self, p_Event:discord.RawMemberRemoveEvent):
		"""
		# USER LEFT
		Listener function, if the appropriate settings are set, removes the User Library entry files.
		"""
		BUPrint.Info(f"User {p_Event.user.display_name} has left.  Removing Entry:Special - {settings.UserLib.bRemoveEntryOnLeave}:{settings.UserLib.bRemoveSpecialEntryOnLeave}")

		if settings.UserLib.bRemoveEntryOnLeave:
			BUPrint.Info(f"User {p_Event.user.display_name} has left, removing their library entries.")
			UserLibrary.RemoveEntry(p_Event.user.id, settings.UserLib.bRemoveSpecialEntryOnLeave)

	
	@tasks.loop(time=settings.UserLib.autoQueryRecruitTime)
	async def AutoQueryRecruits(self):
		BUPrint.Info("Automatic query of all recruits starting...")
		await UserLibrary.QueryAllRecruits()





class UserLibrary():
	"""
	# USER LIBRARY OBJECT
	Contains functions relating to the entries.
	Functions will not require an instance.
	"""
	botRef:commands.Bot
	def __init__(self):
		pass



	def GetEntryPath(p_userID:int):
		"""
		# GET ENTRY PATH
		Convenience function to return a pre-compiled path of an entry.
		"""
		return f"{settings.Directories.userLibrary}{p_userID}.bin"

	def GetRecruitEntryPath(p_userID:int):
		"""
		# GET ENTRY PATH: RECRUIT
		Same as GetEntryPath, but for recruits.
		"""
		return f"{settings.Directories.userLibraryRecruits}{p_userID}.bin"


	def HasEntry(p_UserID:int):
		"""
		# HAS LIBRARY ENTRY
		Checks if an entry (both normal and recruits) for the user ID exists.

		### RETURNS
		`True` if an entry exists.

		`False` if no entry exists.
		"""
		bPathExists = False
		if os.path.exists(f"{UserLibrary.GetEntryPath(p_UserID)}"):
			return True

		if os.path.exists(f"{UserLibrary.GetRecruitEntryPath(p_UserID)}"):
			return True

		return False

	def IsRecruitEntry(p_userID:int):
		"""
		# IS RECRUIT ENTRY
		Checks if a file exists for a user in recruit directory.
		Typically used after HasEntry to determine the entry type.
		"""
		if os.path.exists(f"{UserLibrary.GetRecruitEntryPath(p_userID)}"):
			return True
		else:
			return False


	def SaveEntry(p_entry:User):
		"""
		# SAVE LIBRARY ENTRY
		Saves the passed entry to file.
		"""
		vFilePath = ""
		vLockFile = ""


		# Recruits User entry is saved in wrong directory, remove it.
		if p_entry.bIsRecruit and os.path.exists(UserLibrary.GetEntryPath(p_entry.discordID)):
			try:
				os.remove(vFilePath)
			except OSError as vError:
				BUPrint.LogErrorExc("Unable to remove recruit entry file from wrong directory!")


		# Get appropriate path:
		if p_entry.bIsRecruit:
			vFilePath = UserLibrary.GetRecruitEntryPath(p_entry.discordID)
		else:
			vFilePath = UserLibrary.GetEntryPath(p_entry.discordID)


		vLockFile = FilesAndFolders.GetLockPathGeneric(vFilePath)
		FilesAndFolders.GetLock(vLockFile)

		try:
			with open(vFilePath, "wb") as vFile:
				pickle.dump(p_entry, vFile)

			FilesAndFolders.ReleaseLock(vLockFile)
		except pickle.PickleError as vError:
			BUPrint.LogErrorExc("Unable to load user entry", vError)
			FilesAndFolders.ReleaseLock(vLockFile)
			return

		
		if p_entry.specialAbout == "":
			return

		vSpecialPath = vFilePath.replace(".bin", ".txt")
		try:
			with open(vSpecialPath, "wt") as vSpecialFile:
				vSpecialFile.write(p_entry.specialAbout)
		except OSError as vError:
			BUPrint.LogErrorExc("Unable to load special entry", vError)



	def LoadEntry(p_userID:int):
		"""
		# LOAD LIBRARY ENTRY
		If an entry exists, it is loaded and returned.

		### RETURNS:
		`User` library entry, or `None` if not found.
		"""

		BUPrint.Debug(f"Loading Library Entry: {p_userID}")
		if not UserLibrary.HasEntry(p_userID):
			BUPrint.Debug(f"User with id {p_userID} has no library entry")
			return None

		bIsRecruit = UserLibrary.IsRecruitEntry(p_userID)
		vFilePath = ""

		if bIsRecruit:
			vFilePath = UserLibrary.GetRecruitEntryPath(p_userID)
		else:
			vFilePath = UserLibrary.GetEntryPath(p_userID)

		vLockFile = FilesAndFolders.GetLockPathGeneric(vFilePath)
		FilesAndFolders.GetLock(vLockFile)
		vLibEntry:User = None

		try:
			with open(vFilePath, "rb") as vFile:
				vLibEntry = pickle.load(vFile)

			FilesAndFolders.ReleaseLock(vLockFile)

		except pickle.PickleError as vError:
			BUPrint.LogErrorExc("Unable to load user entry", vError)
			FilesAndFolders.ReleaseLock(vLockFile)
			return None

		vSpecialPath = vFilePath.replace(".bin", ".txt")
		if os.path.exists(vSpecialPath):
			try:
				with open(vSpecialPath, "rt") as vSpecialFile:
					vLibEntry.specialAbout = vSpecialFile.read()
			except OSError as vError:
				BUPrint.LogErrorExc("Unable to load special entry", vError)


		return vLibEntry


	def GetAllEntries():
		"""
		# GET ALL ENTRIES
		Loads all entries and returns them in a list.
		"""
		vEntryList = []
		files = FilesAndFolders.GetFiles(settings.Directories.userLibrary, ".bin")

		file:str
		for file in files:
			vEntryList.append( UserLibrary.LoadEntry(file.replace(".bin", "")) )

		return vEntryList



	async def PropogatePS2Info(p_entry:User):
		"""
		# PROPGATE PS2 INFO
		Uses the AuraxClient to check valid PS2 name and set the PS2 details accordingly.

		### RETURN
		False on failure to find a character.

		True if character is found.
		"""
		if p_entry.ps2Name == "":
			BUPrint.Debug("Invalid PS2 name given, shouldn't have been able to get here!")
			return False
		
		vAuraxClient = AuraxClient(service_id=settings.BotSettings.ps2ServiceID)

		vPlayerChar = await vAuraxClient.get_by_name(AuraxPS2.Character, p_entry.ps2Name)

		if vPlayerChar == None:
			BUPrint.Debug("Provided character name not found! Resetting ps2name in entry.")
			p_entry.ps2Name = ""
			UserLibrary.SaveEntry(p_entry)
			await vAuraxClient.close()
			return False

		vOutfitChar = await vPlayerChar.outfit_member()

		if vOutfitChar == None:
			BUPrint.Debug("Player not part of outfit.")
			UserLibrary.SaveEntry(p_entry)
			await vAuraxClient.close()
			return True

		vOutfit = await vOutfitChar.outfit()

		p_entry.ps2Outfit = f"{vOutfit.name} {vOutfit.alias}"
		p_entry.ps2OutfitJoinDate = datetime.fromtimestamp(vOutfitChar.member_since, tz=timezone.utc)
		p_entry.ps2OutfitRank = vOutfitChar.rank

		UserLibrary.SaveEntry(p_entry)
		await vAuraxClient.close()
		return True


	def RemoveEntry(p_userID:int, p_removeSpecial:bool = False):
		"""
		# REMOVE ENTRY
		Removes a user entry file from disk.
		If removeSpecial is true, the special file is also removed if present.
		"""
		BUPrint.Info(f"Removing user library entry for user with ID: {p_userID}")
		vPath = UserLibrary.GetEntryPath(p_userID)
	
		try:
			os.remove(vPath)
		except OSError as error:
			BUPrint.LogErrorExc(f"Unable to remove file: {vPath}", error)

		if not p_removeSpecial:
			return

		try:
			vPath = vPath.replace(".bin", ".txt")
			os.remove(vPath)
		except OSError as error:
			BUPrint.LogErrorExc(f"Unable to remove file: {vPath}", error)


	def GetRecruitRequirements(p_entry:User):
		"""
		# GET RECRUIT REQUIREMENTS
		Almost functionally equivilant to QueryRecruit, except returns a string of the user requrements and doesn't do any modification.

		### RETURN 
		# `string` of the requirements; for human reading.
		"""
		if not p_entry.bIsRecruit:
			return "User is not a recruit."

		vRequirementsMsg = ""
		vGuild = UserLibrary.botRef.get_guild(int(settings.BotSettings.discordGuild))
		if vGuild == None:
			BUPrint.Debug("Unable to get guild?")
			return "*ERROR: Unable to get guild.*"
		vDiscordUser = vGuild.get_member(p_entry.discordID)

		if vDiscordUser == None:
			BUPrint.Debug("User entry is for an invalid user.")
			UserLibrary.RemoveEntry(p_entry)
			return

		bPromote = True
		vPromoteRules = settings.UserLib.autoPromoteRules

		if vPromoteRules.bAttendedMinimumEvents:
			if p_entry.eventsAttended < vPromoteRules.minimumEvents:
				BUPrint.Debug("User failed events attended requirement.")
				vRequirementsMsg += f"Needs to attend {vPromoteRules.minimumEvents-p_entry.eventsAttended} more event(s).\n"
				bPromote = False
		
		vDateNow = datetime.now(tz=timezone.utc)
		if vPromoteRules.bInDiscordForDuration:
			requiredDate = vDiscordUser.joined_at + vPromoteRules.discordDuration

			if vDateNow < requiredDate:
				vDifference:timedelta = requiredDate - vDateNow
				vRequirementsMsg += f"Needs to be in the discord for {vDifference.days} more day(s)."
				bPromote = False

		if vPromoteRules.bInOutfitForDuration:
			if p_entry.ps2Outfit == "":
					vRequirementsMsg += f"Needs to join the outfit!"
					bPromote = False
			else:
				requiredDate = p_entry.ps2OutfitJoinDate + vPromoteRules.discordDuration
				if vDateNow < requiredDate:
					vDifference:timedelta = requiredDate - vDateNow
					vRequirementsMsg += f"Needs to be in the outfit for {vDifference.days} more day(s)."
					bPromote = False


		if not bPromote:
			BUPrint.Debug("Not promoting user.")
			return vRequirementsMsg
		
		return "Awaiting promotion!"



	async def QueryRecruit(p_entry:User):
		"""
		# QUERY RECRUIT
		Checks a recruits user entry.
		If the user fulfils all the required criteria, they are promoted.

		If validation is enabled, a request is sent to the admin chanel.

		Returns a string to be used for administrative checking.
		"""
		if not settings.UserLib.bAutoPromoteEnabled:
			BUPrint.Debug("Auto promotion is disabled.")
			return ""

		if not p_entry.bIsRecruit:
			BUPrint.Debug("User is not a recruit.")
			return

		vGuild = UserLibrary.botRef.get_guild(int(settings.BotSettings.discordGuild))
		vDiscordUser = vGuild.get_member(p_entry.discordID)

		if vDiscordUser == None:
			BUPrint.Debug("User entry is for an invalid user.")
			UserLibrary.RemoveEntry(p_entry)
			return

		bPromote = True
		vPromoteRules = settings.UserLib.autoPromoteRules

		if vPromoteRules.bAttendedMinimumEvents:
			if p_entry.eventsAttended < vPromoteRules.minimumEvents:
				BUPrint.Debug("User failed events attended requirement.")
				bPromote = False
		
		vDateNow = datetime.now(tz=timezone.utc)
		if vPromoteRules.bInDiscordForDuration:
			requiredDate = vDiscordUser.joined_at + vPromoteRules.discordDuration

			if vDateNow < requiredDate:
				BUPrint.Debug("User failed discord date requirement.")
				bPromote = False

		if vPromoteRules.bInOutfitForDuration:
			if p_entry.ps2Outfit == "":
				BUPrint.Debug("User failed Outfit date requiremnt: They're not in an outfit!")
				bPromote = False
			else:
				requiredDate = p_entry.ps2OutfitJoinDate + vPromoteRules.discordDuration
				if vDateNow < requiredDate:
					BUPrint.Debug("User failed discord date requirement.")
					bPromote = False

		if not bPromote:
			BUPrint.Debug("Not promoting user.")
			return

		if settings.UserLib.bAutoPromoteEnabled:
			vRequest = UserLib_RecruitValidationRequest( p_entry )
			await vRequest.SendRequest()
		else:
			await UserLibrary.PromoteUser(vDiscordUser)


	async def QueryAllRecruits():
		allEntries = UserLibrary.GetAllEntries()

		entry: User
		for entry in allEntries:
			if entry.bIsRecruit:
				await UserLibrary.QueryRecruit(entry)


	async def PromoteUser(p_member:discord.Member):
		"""
		# PROMOTE USER
		Applies the specified promotion role and removes the recruit role.
		Quits
		"""

		vRecruitRole:discord.Role = None
		vPromotionRole:discord.Role = None
		vGuild = UserLibrary.botRef.get_guild(int(settings.BotSettings.discordGuild))
		
		for role in vGuild.roles:
			if vRecruitRole != None and vPromotionRole != None:
				break

			if role.id == settings.NewUsers.recruitRole:
				vRecruitRole = role
				continue

			if role.id == settings.UserLib.promotionRoleID:
				vPromotionRole = role
				continue


		await p_member.remove_roles(vRecruitRole, reason="Promotion of user from recruit!")
		await p_member.add_roles(vPromotionRole, reason="Promotion of user from recruit!")

		# Update Library Entry:
		userEntry = UserLibrary.LoadEntry(p_member.id)
		userEntry.bIsRecruit = False
		UserLibrary.SaveEntry(userEntry)

		# Notify Admin channel:
		vAdminChn = vGuild.get_channel( settings.BotSettings.adminChannel )
		if vAdminChn != None:
			vAdminChn.send(f"User {p_member.display_name} was promoted to {vPromotionRole.name} ({vRecruitRole.name} removed)")




class LibraryViewPage(Enum):
	"""
	# LIBRARY VIEW: PAGE
	Enum to mark the current page being viewed.
	"""
	general = 0
	ps2Info = 10
	sessions = 20
	individualSession = 25




class LibraryViewer():
	"""
	# LIBRARY VIEWER
	Class responsible for sending a viewer to see library information.

	## PARAMETERS
	`p_userID`: the user ID to view.

	`p_isViewingSelf`: Whether the calling viewer is viewing themself.
	"""
	def __init__(self, p_userID:int, p_isViewingSelf:bool):
		# Used to save a new entry.
		self.userID = p_userID
		# Used to determine if the configure button is shown.
		self.bIsViewingSelf = p_isViewingSelf
		# The User entry
		self.userEntry:User = UserLibrary.LoadEntry(p_userID)
		# Used to edit the viewer message.
		self.viewerMsg:discord.Message = None
		# Used to send the viewer controls
		self.vewerConrolsMsg:discord.Message = None

		# Stored to avoid unneeded repeated calls.
		self.recruitRequirements:str = ""

		self.page:LibraryViewPage = LibraryViewPage.general
		self.multiPageNum = 0 # The number of the current page viewed.
		self.listSelectMultiplier = 0 # When there's more than 25, this multiplier is used to offset the options.

		BUPrint.Debug(f"User is viewing self: {self.bIsViewingSelf}")



	async def UpdateViewer(self):
		"""
		# SEND VIEWER
		Updates the viewer message.
		"""
		if self.viewerMsg != None:
			await self.viewerMsg.edit(view=self.GenerateView(), embed=self.GenerateEmbed())
		


	async def SendViewer(self, p_interaction:discord.Interaction):
		"""
		# SEND VIEWER
		Send the intitial viewer from the interaction call.
		"""
		await p_interaction.response.send_message(view=self.GenerateView(), embed=self.GenerateEmbed(), ephemeral=True)
		self.viewerMsg = await p_interaction.original_response()



	def GenerateView(self):
		vView = LibViewer_view(self)
		btn_configure = LibViewerBtn_setup(self)
		btn_General = LibViewerBtn_general(self)
		btn_Ps2 = LibViewerBtn_planetside2(self)
		btn_sessions = LibViewerBtn_sessions(self)
		btn_sessionPrev = LibViewerBtn_session_previous(self)
		btn_sessionNext = LibViewerBtn_session_next(self)

		if self.bIsViewingSelf:
			vView.add_item(btn_configure)
		vView.add_item(btn_General)
		vView.add_item(btn_Ps2)
		vView.add_item(btn_sessions)
		vView.add_item(btn_sessionPrev)
		vView.add_item(btn_sessionNext)

		if self.page == LibraryViewPage.general:
			btn_General.disabled = True
			btn_sessionNext.disabled = True
			btn_sessionPrev.disabled = True

		elif self.page == LibraryViewPage.ps2Info:
			btn_Ps2.disabled = True
			btn_sessionNext.disabled = True
			btn_sessionPrev.disabled = True

		elif self.page == LibraryViewPage.sessions:
			btn_sessions.disabled = True
			btn_sessionNext.disabled = True
			btn_sessionPrev.disabled = True

		elif self.page == LibraryViewPage.individualSession:
			if self.multiPageNum == 0:
				btn_sessionPrev.disabled = True
			else:
				btn_sessionPrev.disabled = False

			if self.multiPageNum == len(self.userEntry.sessions):
				btn_sessionNext.disabled = True
			else:
				btn_sessionNext.disabled = False

		if len(self.userEntry.sessions) == 0:
			btn_sessions.disabled = True
			btn_sessionNext.disabled = True
			btn_sessionPrev.disabled = True

		return vView



	def GenerateEmbed(self):
		"""
		# GENERATE EMBED
		Creates an embed using the current page setting and returns it.
		"""
		if self.page == LibraryViewPage.general:
			return self.GenerateEmbed_General()

		if self.page == LibraryViewPage.ps2Info:
			return self.GenerateEmbed_ps2()

		if self.page == LibraryViewPage.individualSession:
			try:
				return self.GenerateEmbed_session(self.userEntry.sessions[self.multiPageNum])
			except IndexError:
				BUPrint.LogError("Invalid session index given!")
				return self.GenerateEmbed_General()



	def GenerateEmbed_General(self):
		vGuild = UserLibrary.botRef.get_guild(int(settings.BotSettings.discordGuild))
		discordUser = vGuild.get_member(self.userID)
		vEmbed = discord.Embed(
			title=f"General Info for {discordUser.display_name}",
			description=f"They joined the server {DateFormatter.GetDiscordTime(discordUser.joined_at, DateFormat.Dynamic)}!"
		)

		if self.userEntry.specialAbout != "":
			vEmbed.add_field(
				name="Special",
				value=self.userEntry.specialAbout,
				inline=False
			)

		if self.userEntry.aboutMe != "":
			vEmbed.add_field(
				name="About",
				value=self.userEntry.aboutMe,
				inline=False
			)

		if self.userEntry.birthday != None:
			vEmbed.add_field(
				name="Birthday",
				value=f"{self.userEntry.birthday.day } of {self.userEntry.birthday.month}",
				inline=True
			)

		if self.userEntry.bIsRecruit:
			if self.recruitRequirements == "":
				self.recruitRequirements = UserLibrary.GetRecruitRequirements(self.userEntry)

			vEmbed.add_field(
				name="Recruit!",
				value=self.recruitRequirements,
				inline=True
			)

		vEmbed.add_field(
			name="Events Attended",
			value=str(self.userEntry.eventsAttended),
			inline=False
			)

		return vEmbed



	def GenerateEmbed_ps2(self):
		vEmbed = discord.Embed(title="Planetside 2 Information")

		if self.userEntry.ps2Name != "":
			vEmbed.add_field(
				name="PS2 Character",
				value=self.userEntry.ps2Name,
				inline=False
			)

		if self.userEntry.ps2Outfit != "":
			vEmbed.add_field(
				name="PS2 Outfit",
				value=f"{self.userEntry.ps2Outfit}",
				inline=False
				)

			vEmbed.add_field(
				name="Outfit Rank",
				value=f"{self.userEntry.ps2OutfitRank}",
				inline=False
			)

		if len(self.userEntry.sessions) != 0:
			displayStr = ""
			session:UserSession
			vIteration = 0
			for session in self.userEntry.sessions:
				displayStr += f"{session.eventDate}|{session.eventDate}"
				vIteration += 1

				if vIteration >= settings.UserLib.sessionPreviewMax:
					break
			
			vEmbed.add_field(
				name="Tracked Sessions",
				value=displayStr,
				inline=False
			)

		return vEmbed


	def GenerateEmbed_sessionBrowser(self):
		"""
		# GENERTAE EMBED: SESSION BROWSER
		Generates an embed showing a browser like view of the users sessions.
		"""
		vEmbed = discord.Embed(
			title="Tracked Sessions",
			description=f"This user has attended {self.userEntry.eventsAttended}, missed {self.userEntry.eventsMissed}, and has {len(self.userEntry.sessions)} tracked sessions saved!"
		)



	def GenerateEmbed_session(self, p_session:UserSession):
		"""
		# GENERATE EMBED: Session
		Generates an embed showing the stats from a session.
		"""
		vEmbed = discord.Embed(
					title=f"{p_session.eventName}",
					description=f"{p_session.eventDate}"
					)

		vEmbed.add_field(
			name="Kills",
			value=str(p_session.kills)
		)

		vEmbed.add_field(
			name="Deaths",
			value=str(p_session.deaths)
		)

		vEmbed.add_field(
			name="Assists",
			value=str(p_session.assists)
		)

		vEmbed.add_field(
			name="Score",
			value=str(p_session.score)
		)




####### LIBRARY VIEWER BUTTONS & UI.VIEWER
class LibViewer_view(discord.ui.View):
	def __init__(self, p_viewer:LibraryViewer):
		self.vViewer = p_viewer
		super().__init__(timeout=180)

	async def on_timeout(self):
		BUPrint.Debug(f"Viewer for {self.vViewer.userID} removed.")
		try:
			await self.vViewer.viewerMsg.delete()
		except discord.errors.NotFound:
			BUPrint.Debug("Message not found, user most likely dismissed message.")


class LibViewerBtn_setup(discord.ui.Button):
	def __init__(self, p_viewer:LibraryViewer):
		self.vViewer = p_viewer
		super().__init__(label="Setup", row=0)

	async def callback (self, p_interaction:discord.Interaction):
		await p_interaction.response.send_modal( LibViewer_ConfigureModal(self.vViewer) )


class LibViewerBtn_general(discord.ui.Button):
	def __init__(self, p_viewer:LibraryViewer):
		self.vViewer = p_viewer
		super().__init__(label="General", row=1)

	async def callback (self, p_interaction:discord.Interaction):
		self.vViewer.page = LibraryViewPage.general
		await self.vViewer.UpdateViewer()
		await p_interaction.response.defer()


class LibViewerBtn_planetside2(discord.ui.Button):
	def __init__(self, p_viewer:LibraryViewer):
		self.vViewer = p_viewer
		super().__init__(label="Planetside2", row=1)

	async def callback (self, p_interaction:discord.Interaction):
		self.vViewer.page = LibraryViewPage.ps2Info
		await self.vViewer.UpdateViewer()
		await p_interaction.response.defer()


class LibViewerBtn_sessions(discord.ui.Button):
	def __init__(self, p_viewer:LibraryViewer):
		self.vViewer = p_viewer
		super().__init__(label="Sessions", row=1)

	async def callback (self, p_interaction:discord.Interaction):
		self.vViewer.page = LibraryViewPage.individualSession
		await self.vViewer.UpdateViewer()
		await p_interaction.response.defer()


class LibViewerBtn_session_next(discord.ui.Button):
	def __init__(self, p_viewer:LibraryViewer):
		self.vViewer = p_viewer
		super().__init__(label=">", row=1)

	async def callback (self, p_interaction:discord.Interaction):
		self.vViewer.page = LibraryViewPage.individualSession
		self.vViewer.multiPageNum += 1
		await self.vViewer.UpdateViewer()
		await p_interaction.response.defer()


class LibViewerBtn_session_previous(discord.ui.Button):
	def __init__(self, p_viewer:LibraryViewer):
		self.vViewer = p_viewer
		super().__init__(label="<", row=1)

	async def callback (self, p_interaction:discord.Interaction):
		self.vViewer.page = LibraryViewPage.individualSession
		self.vViewer.multiPageNum -= 1
		await self.vViewer.UpdateViewer()
		await p_interaction.response.defer()




#### LIB VIEWER CONFIGURE MODAL

class LibViewer_ConfigureModal(discord.ui.Modal):
	"""
	# LIBRARY VIEWER: CONFIGURE MODAL
	Takes one of two parameters; if an entry is specified with p_adminEditEntry, 
	"""

	txt_ps2Char = discord.ui.TextInput(
		label="PS2 Character Name",
		placeholder="YourPS2CharName",
		required=False,
		style=discord.TextStyle.short
	)
	txt_about = discord.ui.TextInput(
		label="About You",
		placeholder="Space to tell people about you, or just put something funny!",
		required=False,
		max_length=1024,
		style=discord.TextStyle.paragraph
	)
	txt_birthday = discord.ui.TextInput(
		label="Birth Date (year is optional & never shown)",
		placeholder="DD/MM/YYYY (03/07/1991)",
		required=False,
		style=discord.TextStyle.short
	)

	txt_admin = discord.ui.TextInput(
		label="Admin Commands",
		placeholder="Enter commands here to change settings.",
		required=False
	)

	txt_adminSpecial = discord.ui.TextInput(
		label="Special",
		placeholder="Non-User Editable special info, saved to text file...",
		required=False,
		style=discord.TextStyle.paragraph,
		max_length=1024
	)

	def __init__(self, p_parentLibViewer:LibraryViewer = None, p_adminEditEntry:User = None):
		super().__init__(title="CONFIGURE YOUR LIBRARY ENTRY")
		self.parentViewer = p_parentLibViewer
		self.vUserEntry:User = None
		self.bIsAdminEdit = False

		if p_adminEditEntry != None:
			self.bIsAdminEdit = True
			self.vUserEntry = p_adminEditEntry
			self.parentViewer = None
		else:
			self.vUserEntry = p_parentLibViewer.userEntry
			self.remove_item(self.txt_admin)
			self.remove_item(self.txt_adminSpecial)

		if self.vUserEntry.ps2Name != "" and not self.vUserEntry.settings.bLockPS2Char:
			self.txt_ps2Char.placeholder = self.vUserEntry.ps2Name
		elif self.vUserEntry.settings.bLockPS2Char:
			self.remove_item(self.txt_ps2Char)
		
		if self.vUserEntry.aboutMe != "" and not self.vUserEntry.settings.bLockAbout:
			self.txt_about.default = self.vUserEntry.aboutMe
		elif self.vUserEntry.settings.bLockAbout:
			self.remove_item(self.txt_about)

		if self.vUserEntry.birthday != None:
			self.txt_birthday.default = f"{self.vUserEntry.birthday.day}/{self.vUserEntry.birthday.month}"

		if self.vUserEntry.specialAbout != "":
			self.txt_adminSpecial.default = self.vUserEntry.specialAbout


	async def on_submit(self, p_interaction:discord.Interaction):
		vSuccessMessage = "Entry has been updated!"

		if self.txt_adminSpecial.value != "":
			self.vUserEntry.specialAbout = self.txt_adminSpecial.value

		if self.txt_about.value != "":
			self.vUserEntry.aboutMe = self.txt_about.value

		if self.txt_birthday.value != "":
			vDateStr = ""
			vFormat = r"%d/%m/%Y"

			try:
				if self.txt_birthday.value.count("/") == 2:
					BUPrint.Debug("User provided full date.")
					vDate = datetime.strptime( self.txt_birthday.value , vFormat)
					vDateStr = self.txt_birthday.value
				else:
					BUPrint.Debug("User provided partial date.")
					vDateStr = f"{self.txt_birthday.value}/2000"
					vDate = datetime.strptime( f"{self.txt_birthday.value}/2000" , vFormat)
						
					
				BUPrint.Debug(f"Date Str: {vDateStr}")
				self.vUserEntry.birthday = vDate

			except ValueError:
				BUPrint.Debug("User provided invalid date format.")
				vSuccessMessage += f"\n\n{settings.Messages.invalidBirthdate}"


		if self.txt_ps2Char.value != "":
			if self.txt_ps2Char != self.vUserEntry.ps2Name:
				self.vUserEntry.ps2Name = self.txt_ps2Char.value
				await UserLibrary.PropogatePS2Info(self.vUserEntry)

		if self.bIsAdminEdit:
			self.ParseAdminCommands()
			vSuccessMessage += f"\n\n**Settings:**\n"
			vSuccessMessage += f"PS2 Character Locked: {self.vUserEntry.settings.bLockPS2Char}\n"
			vSuccessMessage += f"AboutMe Locked: {self.vUserEntry.settings.bLockAbout}\n"
			vSuccessMessage += f"Session History: {self.vUserEntry.settings.bTrackHistory}\n"
			vSuccessMessage += f"User is Recruit: {self.vUserEntry.bIsRecruit}\n"

			await p_interaction.response.send_message(vSuccessMessage, ephemeral=True)
		else:
			await self.parentViewer.UpdateViewer()
			await p_interaction.response.send_message(vSuccessMessage, ephemeral=True)

		UserLibrary.SaveEntry(self.vUserEntry)


	def ParseAdminCommands(self):
		"""
		# PARSE ADMIN COMMANDS
		Checks if any commands are found in the commands text field and sets their respective settings.
		"""
		adminCommands = self.txt_admin.value.lower()
		# Manually set recruit status
		if adminCommands.__contains__("isrecruit"):
			self.vUserEntry.bIsRecruit = True
		if adminCommands.__contains__("notrecruit"):
			self.vUserEntry.bIsRecruit = False

		# Set LockPS2 Character
		if adminCommands.__contains__("lockps2"):
			self.vUserEntry.settings.bLockPS2Char = True
		if adminCommands.__contains__("openps2"):
			self.vUserEntry.settings.bLockPS2Char = False
	
		# Set Lock About
		if adminCommands.__contains__("lockabout"):
			self.vUserEntry.settings.bLockAbout = True
		if adminCommands.__contains__("openabout"):
			self.vUserEntry.settings.bLockAbout = False
		
		# Set Tracking Sessions
		if adminCommands.__contains__("trackhistory"):
			self.vUserEntry.settings.bTrackHistory = True
		if adminCommands.__contains__("nohistory"):
			self.vUserEntry.settings.bTrackHistory = False
			self.vUserEntry.sessions.clear()
	
		BUPrint.Debug(f"Settings: \n{self.vUserEntry.settings}")



### RECRUIT ADMIN REQUEST

class UserLib_RecruitValidationRequest():
	"""
	# USER LIBRARY: RECRUIT VALIDATION
	A class that handles a validation request for a recruits promotion.
	"""
	botRef:commands.Bot

	def __init__(self, p_userEntry:User):
		self.userEntry = p_userEntry
		self.requestMsg:discord.Message = None


	async def SendRequest(self):
		"""
		# SEND REQUEST
		Sends the request to an admin channel.
		"""
		vAdminChn = self.botRef.get_channel(settings.BotSettings.adminChannel)

		if vAdminChn == None:
			BUPrint.Info("Unable to get admin channel for promotion request!")
			return

		vView = discord.ui.View(timeout=None)
		vView.add_item(RecruitValidationReq_btnAccept(self))

		vUser = self.botRef.get_user(self.userEntry.discordID)

		self.requestMsg = vAdminChn.send(f"User {vUser.mention} is ready to be promoted!", view=vView)


class RecruitValidationReq_btnAccept(discord.ui.Button):
	def __init__(self, p_parentRequest:UserLib_RecruitValidationRequest):
		self.parent = p_parentRequest
		super().__init__(label="Promote!", style=discord.ButtonStyle.green)

	async def callback(self, p_interaction:discord.Interaction):
		vUser = self.parent.botRef.get_user(self.parent.userEntry.discordID)
		
		await UserLibrary.PromoteUser( vUser )

		await self.parent.requestMsg.delete()

		await p_interaction.response.send_message(f"Done!", ephemeral=True)