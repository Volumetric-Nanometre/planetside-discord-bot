# USER MANAGER: Holds the content for the User Library classes.
from __future__ import annotations

import discord
import discord.ext
from discord.ext import commands, tasks

from discord import app_commands

from auraxium import Client as AuraxClient
import auraxium.ps2 as AuraxPS2

import os

import pickle

from datetime import datetime, timezone, timedelta

from enum import Enum

from botUtils import BotPrinter as BUPrint
from botUtils import FilesAndFolders, GetDiscordTime, UserHasCommandPerms

from botData.dataObjects import User, Session, OpsStatus, LibraryViewPage, UserInboxItem, EntryRetention

from botData.utilityData import DateFormat

import botData.settings as settings
import opsManager



class UserLibraryCog(commands.GroupCog, name="user_library"):
	"""
	# USER LIBRARY COG
	Commands related to the user library, for regular users.
	"""
	def __init__(self, p_botRef:commands.Bot):
		self.botRef = p_botRef
		BUPrint.Info("COG: User Library loaded!")
		if settings.UserLib.topQuoteReactions > 0 and settings.BotSettings.botFeatures.UserLibraryFun:
			self.botRef.add_listener(self.CheckReactions, "on_raw_reaction_add")
			self.botRef.add_listener(self.CheckReactions, "on_raw_reaction_remove")


	@app_commands.command(name="about", description="Show information about a user, or see your own!")
	@app_commands.describe(p_userToFind="The user you want to see information about;  Leave empty to see your own!")
	@app_commands.rename(p_userToFind="user")
	async def AboutUser(self, p_interaction:discord.Interaction, p_userToFind:discord.Member = None):
		# HARDCODED ROLE USEAGE:
		if not await UserHasCommandPerms(p_interaction.user, (settings.CommandLimit.userLibrary), p_interaction):
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

	
	@app_commands.command(name="my_events", description="List all the events you are signed up to.")
	async def GetMyEvents(self, p_interaction:discord.Interaction):
		""" # GET MY EVENTS
		App Command to get users signed up events.
		"""

		# HARDCODED ROLE USEAGE:
		if not await UserHasCommandPerms(p_interaction.user, (settings.CommandLimit.userLibrary), p_interaction):
			return

		if not settings.BotSettings.botFeatures.Operations:
			await p_interaction.response.send_message(settings.Messages.featureDisabled, ephemeral=True)
			return

		await p_interaction.response.defer(thinking=True, ephemeral=True)
		vMessage = ""


		vJumpBtns:list[discord.ui.Button] = []

		for liveEvent in opsManager.OperationManager.vLiveOps:
			signedUpRole = liveEvent.PlayerInOps(p_interaction.user.id)
			if signedUpRole != "":
				vMessage += f"- **{liveEvent.name}**, Starts {GetDiscordTime(liveEvent.date)}, signed up as: **{signedUpRole}**!\n"

			if liveEvent.status != OpsStatus.started and settings.UserLib.bShowJumpButtonsForGetEvents:
				plainDate = f"{liveEvent.date.day}/{liveEvent.date.month}/{liveEvent.date.year}"
				newBtn = discord.ui.Button(
					label=f"{liveEvent.name} {plainDate}",
					url=liveEvent.jumpURL,
				)
				vJumpBtns.append(newBtn)


		newView = discord.ui.View(timeout=180)
		if settings.UserLib.bShowJumpButtonsForGetEvents and len(vJumpBtns) != 0:
			for jumpBtn in vJumpBtns:
				newView.add_item(item=jumpBtn)		

		
		if vMessage != "":
			await p_interaction.edit_original_response(content=f"**Your Events:**\n{vMessage}", view=newView)
			return

		# user in no events.  If there are events, get the signup channels for them.  First check if there are any events.
		if len(opsManager.OperationManager.vLiveOps) == 0:
			await p_interaction.edit_original_response(content=settings.Messages.noEvents)
			return
		

		await p_interaction.edit_original_response(content=settings.Messages.noSignedUpEvents, view=newView)



	async def CheckReactions(self, p_data:discord.RawReactionActionEvent):
		if p_data.channel_id != settings.Channels.quoteID:
			# Not correct channel.
			return

		bQuoteExists = False
		quoteChanel = self.botRef.get_channel( p_data.channel_id )
		vMessage = await quoteChanel.fetch_message( p_data.message_id )

		if vMessage == None:
			BUPrint.LogError("Unable to get Quote Channel Message", "FETCH FAILED")
			return
		
		if len(vMessage.mentions) == 0:
			BUPrint.Debug("No mentions, unable to get quotee.")
			return
		
		vQuotedUser = vMessage.mentions[0]

		if not UserLibrary.HasEntry(vQuotedUser.id):
			BUPrint.Debug("User has no entry. Unable to update it.")
			return

		vUserLibEntry = UserLibrary.LoadEntry(vQuotedUser.id) 

		# Determine if quote exists already:
		existingQuote:str = str("")
		for quote in vUserLibEntry.topQuotes:
			if vMessage.content == quote:
				bQuoteExists = True
				existingQuote = quote


		# Get total reaction count.
		vTotalReactions = 0
		for reaction in vMessage.reactions:
			vTotalReactions += reaction.count


		if vTotalReactions < settings.UserLib.topQuoteReactions and bQuoteExists:
			BUPrint.Debug("Minimum quote threshold not reached, removing existing quote.")
			try:
				vUserLibEntry.topQuotes.remove(existingQuote)
				UserLibrary.SaveEntry(vUserLibEntry)
			except ValueError:
				BUPrint.LogError(p_titleStr="Unable to remove existing quote", p_string="Unable to remove matching entry from list.")
			return


		if vTotalReactions >= settings.UserLib.topQuoteReactions and not bQuoteExists:
			BUPrint.Debug("Quote threshold reached, adding quote!")
			if len(vUserLibEntry.topQuotes) == settings.UserLib.maxQuotes:
				BUPrint.Debug("Reached max quote count, removing oldest...")
				# Remove oldest top quote.
				vUserLibEntry.topQuotes.pop(-1)

			if not bQuoteExists:
				vUserLibEntry.topQuotes.append(vMessage.content)
			UserLibrary.SaveEntry(vUserLibEntry)
			return



class UserLibraryAdminCog(commands.GroupCog, name="userlib_admin"):
	"""
	# USER LIBRARY ADMIN COG
	Administrative commands and listeners for managing the user library.
	"""
	def __init__(self, p_botRef):
		self.adminLevel = settings.CommandLimit.userLibraryAdmin
		self.botRef:commands.Bot = p_botRef
		self.UserLibRetentionTask = None

		if settings.BotSettings.botFeatures.UserLibrary:
			self.contextMenu_setAsRecruit = app_commands.ContextMenu(
				name="Set as Recruit",
				callback=self.SetUserAsRecruit
			)
			self.botRef.tree.add_command(self.contextMenu_setAsRecruit)

			if settings.BotSettings.botFeatures.userLibraryInboxSystem and settings.BotSettings.botFeatures.userLibraryInboxAdmin:
				self.contextMenu_warnMessage = app_commands.ContextMenu(
					name="Warn user about message",
					callback=self.SendUserMessageWarning
				)

				self.contextMenu_warnUser = app_commands.ContextMenu(
					name="Warn user",
					callback=self.SendUserWarning
				)
				self.botRef.tree.add_command(self.contextMenu_warnUser)
				self.botRef.tree.add_command(self.contextMenu_warnMessage)

			if settings.UserLib.entryRetention == EntryRetention.unloadAfter:

				self.UserLibRetentionTask = tasks.Loop(coro=self.CheckEntryRetention,
					time=None, seconds=None, hours=None,
					minutes=settings.UserLib.entryRetention_checkInterval
					)


		BUPrint.Info("COG: User Library Admin loaded!")



	async def cog_unload(self) -> None:
		self.botRef.tree.remove_command(self.contextMenu_setAsRecruit)
		self.botRef.tree.remove_command(self.contextMenu_warnMessage)
		self.botRef.tree.remove_command(self.contextMenu_warnUser)
		return await super().cog_unload()


	# CONTEXT MENU COMMANDS
	async def SetUserAsRecruit(self, p_interaction:discord.Interaction, p_User:discord.Member):
		"""
		# SET USER AS RECRUIT
		Context menu option that changes a user to a recruit.
		"""
		# HARDCODED ROLE USEAGE:
		if not await UserHasCommandPerms(p_interaction.user, self.adminLevel, p_interaction):
			return		
		
		vRecruitRole = p_interaction.guild.get_role(settings.Roles.recruit)
		vNormalRole = p_interaction.guild.get_role(settings.Roles.recruitPromotion)
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
			vUserEntry = User(discordID=p_User.id)
			vResultMessage += "User had no library entry! Entry was created.\n"
		
		vUserEntry.bRecruitRequestedPromotion = False
		vUserEntry.bIsRecruit = True
		vResultMessage += f"User library for {p_User.display_name} has been updated."

		UserLibrary.SaveEntry(vUserEntry)
		vAdminChn = p_interaction.guild.get_channel( settings.Channels.botAdminID )

		if vAdminChn != None:
			try:
				await vAdminChn.send(vResultMessage)
			except:
				BUPrint.Info(vResultMessage)
		else:
			BUPrint.Info(vResultMessage)

		await p_interaction.response.send_message("Sucessfully made user a recruit!", ephemeral=True)



	async def SendUserWarning(self, p_interaction:discord.Interaction, p_User:discord.Member):
		"""
		# SEND USER WARNING
		Context menu option that sends a warning message to the user via the library inbox.
		"""
		# HARDCODED ROLE USEAGE:
		if not await UserHasCommandPerms(p_interaction.user, self.adminLevel, p_interaction):
			return

		await p_interaction.response.send_modal(SendWarningModal(p_User.id, ""))
		

	async def SendUserMessageWarning(self, p_interaction:discord.Interaction, p_message:discord.Message):
		"""
		# SEND USER WARNING: MESSAGE
		Context menu option that sends a warning regarding a message to the user via the library inbox.
		"""
		# HARDCODED ROLE USEAGE:
		if not await UserHasCommandPerms(p_interaction.user, self.adminLevel, p_interaction):
			return

		await p_interaction.response.send_modal(SendWarningModal(p_message.author.id, p_message.content))


	async def CheckEntryRetention(self):
		vRemoveDate = datetime.now(tz=timezone.utc)
		for entry in UserLibrary.loadedEntries.values():
			if entry.lastAccessed + timedelta(minutes=settings.UserLib.entryRetention_unloadAfter) > vRemoveDate:
				BUPrint.Debug(f"User Entry: {entry.discordID} unloaded from library.")
				del UserLibrary.loadedEntries[entry.discordID]



# # # NORMAL COMMANDS
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
		

		vRecruitEntries = UserLibrary.GetRecruitEntries()

		if vRecruitEntries == None:
			await p_interaction.response.send_message("No user entries are saved.", ephemeral=True)
			return


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




class SendWarningModal(discord.ui.Modal):
	"""# SEND WARNING MODAL:
	A modal used by admins to send a warning to a users inbox.  Used for both member and message based menus.
	"""
	txt_messageTitle = discord.ui.TextInput(
		label="Title",
		style=discord.TextStyle.short,
		required=True,
		placeholder="Few word summary",
		max_length=50
	)

	txt_messageToSend = discord.ui.TextInput(
		label="Message",
		style=discord.TextStyle.long,
		placeholder="A message that should tell the user why they were warned",
		max_length=800
	)

	def __init__(self, p_userID:int, p_flaggedMessage:str):
		self.userID = p_userID
		self.flaggedMsg = p_flaggedMessage
		super().__init__(title="Send warning", custom_id=f"warningTo_{p_userID}")

	async def on_submit(self, p_interaction:discord.Interaction):
		userEntry:User = None
		if not UserLibrary.HasEntry(self.userID):
			userEntry = User(discordID=self.userID)
			UserLibrary.SaveEntry(userEntry)
		else:
			userEntry = UserLibrary.LoadEntry(self.userID)

		inboxItem = UserInboxItem(
			date=datetime.now(timezone.utc),
			adminContext=self.flaggedMsg[:150],
			title=self.txt_messageTitle.value,
			bIsWarning=True,
			message=self.txt_messageToSend.value
		)
		
		await UserLibrary.SendNewInboxMessage(userEntry, inboxItem)

		await p_interaction.response.send_message("Warning sent succesfully.", ephemeral=True)




class UserLibrary():
	"""
	# USER LIBRARY OBJECT
	Contains functions relating to the entries.
	Functions will not require an instance.
	"""
	botRef:commands.Bot
	loadedEntries: dict[int, User] = {}
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
				vFilePath = UserLibrary.GetEntryPath(p_entry.discordID)
				os.remove(vFilePath)
			except OSError as vError:
				BUPrint.LogError(f"Unable to remove recruit entry file from wrong directory! \n{vError.strerror}",0)

			if os.path.exists(UserLibrary.GetEntryPath(p_entry.discordID).replace(".bin", ".txt")):
				vSpecialPath = vFilePath.replace(".bin", ".txt")
				try:
					os.remove(vSpecialPath)
				except OSError as vError:
					BUPrint.LogError(f"Unable to remove recruit special entry file from wrong directory! \n{vError.strerror}",0)

		# Get appropriate path:
		if p_entry.bIsRecruit:
			BUPrint.Debug("Saving recruit entry.")
			vFilePath = UserLibrary.GetRecruitEntryPath(p_entry.discordID)
		else:
			BUPrint.Debug("Saving normal entry.")
			vFilePath = UserLibrary.GetEntryPath(p_entry.discordID)


		vLockFile = FilesAndFolders.GetLockPathGeneric(vFilePath)
		FilesAndFolders.GetLock(vLockFile)

		# Set KeepLoaded bool to current value to be reset afterwards.
		bKeepLoaded = p_entry.bKeepLoaded
		p_entry.bKeepLoaded = False

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

		p_entry.bKeepLoaded = bKeepLoaded
		p_entry.lastAccessed = datetime.now(tz=timezone.utc)



	def LoadEntry(p_userID:int):
		"""
		# LOAD LIBRARY ENTRY
		If an entry exists, it is loaded and returned.

		### RETURNS:
		`User` library entry, or `None` if not found.
		"""
		vLibEntry:User = None

		BUPrint.Debug(f"Loading Library Entry: {p_userID}")
		if not UserLibrary.HasEntry(p_userID):
			BUPrint.Debug(f"User with id {p_userID} has no library entry")
			return None


		if p_userID in UserLibrary.loadedEntries:
			vLibEntry = UserLibrary.loadedEntries.get(p_userID)
			vLibEntry.lastAccessed = datetime.now(tz=timezone.utc)
			return vLibEntry


		bIsRecruit = UserLibrary.IsRecruitEntry(p_userID)
		vFilePath = ""

		if bIsRecruit:
			vFilePath = UserLibrary.GetRecruitEntryPath(p_userID)
		else:
			vFilePath = UserLibrary.GetEntryPath(p_userID)

		vLockFile = FilesAndFolders.GetLockPathGeneric(vFilePath)
		FilesAndFolders.GetLock(vLockFile)

		try:
			with open(vFilePath, "rb") as vFile:
				vLibEntry = pickle.load(vFile)

			FilesAndFolders.ReleaseLock(vLockFile)

		except pickle.PickleError as vError:
			BUPrint.LogErrorExc("Unable to load user entry", vError)
			FilesAndFolders.ReleaseLock(vLockFile)
			return None
		except ModuleNotFoundError as vError:
			BUPrint.LogErrorExc("Module Not Found! Most likely due to changing data structure.")
			FilesAndFolders.ReleaseLock(vLockFile)

		vSpecialPath = vFilePath.replace(".bin", ".txt")
		if os.path.exists(vSpecialPath):
			try:
				with open(vSpecialPath, "rt") as vSpecialFile:
					vLibEntry.specialAbout = vSpecialFile.read()
			except OSError as vError:
				BUPrint.LogErrorExc("Unable to load special entry", vError)


		if settings.UserLib.entryRetention != EntryRetention.whenNeeded:
			vLibEntry.lastAccessed = datetime.now(tz=timezone.utc)
			UserLibrary.loadedEntries[vLibEntry.discordID] = vLibEntry

		return vLibEntry


	def GetAllEntries():
		"""
		# GET ALL ENTRIES
		Loads all entries and returns them in a list.

		NOTE: Extension is stripped.

		NOTE: This does NOT load all entries into the library's dictionary.
		"""
		vEntryList = []
		files = FilesAndFolders.GetFiles(settings.Directories.userLibrary, ".bin")
		files += FilesAndFolders.GetFiles(settings.Directories.userLibraryRecruits, ".bin")

		file:str
		for file in files:
			vEntryList.append( UserLibrary.LoadEntry(file.replace(".bin", "")) )

		return vEntryList



	async def SendNewInboxMessage(p_entry:User, p_message:UserInboxItem):
		"""# SEND NEW INBOX MESSAGE
		Adds the inbox item to user entry, then sends a notification.
		"""

		vMember = UserLibrary.botRef.get_user(p_entry.discordID)
		vChannel = UserLibrary.botRef.get_channel(settings.Channels.generalID)

		p_entry.inbox.append(p_message)
		UserLibrary.SaveEntry(p_entry)

		newView = discord.ui.View()
		newView.add_item(LibViewer_btnViewInbox(p_entry.discordID))

		if vMember != None and vChannel != None:
			await vChannel.send(content=f"{vMember.mention}, you have a new message in your inbox!", view=newView)




	def GetRecruitEntries():
		"""
		# GET RECRUIT ENTRIES
		Similar to get all entries; returns a list of entries.  
		The returned list of this function only includes recruits.
		"""
		vEntryList:list[User] = []

		files = FilesAndFolders.GetFiles(settings.Directories.userLibraryRecruits, ".bin")

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

		p_entry.ps2ID = vPlayerChar.id
		p_entry.ps2Outfit = f"{vOutfit.name} {vOutfit.alias}"
		p_entry.ps2OutfitJoinDate = datetime.fromtimestamp(vOutfitChar.member_since, tz=timezone.utc)
		p_entry.ps2OutfitRank = vOutfitChar.rank

		await vAuraxClient.close()
		UserLibrary.SaveEntry(p_entry)	
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


	def GetRecruitRequirements(p_entry:User, p_asBool:bool = False):
		"""
		# GET RECRUIT REQUIREMENTS
		Almost functionally equivilant to QueryRecruit, except returns a string of the user requrements and doesn't do any modification.

		### RETURN 
		- `string` of the requirements; for human reading.
		- `bool` if p_asBool is true:  returns True if user meets requirements.
		"""
		if not p_entry.bIsRecruit:
			return "User is not a recruit."

		vRequirementsMsg = ""
		vGuild = UserLibrary.botRef.get_guild(int(settings.BotSettings.discordGuild))
		if vGuild == None:
			BUPrint.Debug("Unable to get guild?")
			return "*ERROR: Unable to get guild.*" if not p_asBool else False
		vDiscordUser = vGuild.get_member(p_entry.discordID)

		if vDiscordUser == None:
			BUPrint.Debug("User entry is for an invalid user.")
			UserLibrary.RemoveEntry(p_entry)
			return "INVALID USER!" if not p_asBool else False

		bPromote = True
		vPromoteRules = settings.UserLib.autoPromoteRules

		if vPromoteRules.bAttendedMinimumEvents:			
			if p_entry.eventsAttended < vPromoteRules.minimumEvents:
				BUPrint.Debug("User failed events attended requirement.")
				vRequirementsMsg += f"Needs to attend {vPromoteRules.minimumEvents-p_entry.eventsAttended} more event(s).\n"
				bPromote = False
			elif p_entry.eventsAttended >= vPromoteRules.minimumEvents and vPromoteRules.bEventsMustBePS2:
				ps2Events = 0

				session : Session
				for session in p_entry.sessions:
					if session.bIsPS2Event:
						ps2Events += 1
				if ps2Events < vPromoteRules.minimumEvents:
					vRequirementsMsg += f"Needs to attend {vPromoteRules.minimumEvents-ps2Events} more Planetside 2 event(s).\n"
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
		
		if p_asBool:
			return bPromote
		else:
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
			return

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
			elif p_entry.eventsAttended >= vPromoteRules.minimumEvents and vPromoteRules.bEventsMustBePS2:
				ps2Events = 0

				session : Session
				for session in p_entry.sessions:
					if session.bIsPS2Event:
						ps2Events += 1
				if ps2Events < vPromoteRules.minimumEvents:
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
		recruitEntries = UserLibrary.GetRecruitEntries()

		for entry in recruitEntries:
			await UserLibrary.QueryRecruit(entry)



	async def PromoteUser(p_member:discord.Member):
		"""
		# PROMOTE USER
		Applies the specified promotion role and removes the recruit role.
		"""

		vRecruitRole:discord.Role = None
		vPromotionRole:discord.Role = None
		vGuild = UserLibrary.botRef.get_guild(int(settings.BotSettings.discordGuild))
		
		for role in vGuild.roles:
			if vRecruitRole != None and vPromotionRole != None:
				break

			if role.id == settings.Roles.recruit:
				vRecruitRole = role
				continue

			if role.id == settings.Roles.recruitPromotion:
				vPromotionRole = role
				continue


		await p_member.remove_roles(vRecruitRole, reason="Promotion of user from recruit!")
		await p_member.add_roles(vPromotionRole, reason="Promotion of user from recruit!")

		# Update Library Entry:
		userEntry = UserLibrary.LoadEntry(p_member.id)
		userEntry.bIsRecruit = False
		UserLibrary.SaveEntry(userEntry)

		# Notify Admin channel:
		vAdminChn = vGuild.get_channel( settings.Channels.botAdminID )
		if vAdminChn != None:
			await vAdminChn.send(f"User {p_member.display_name} was promoted to {vPromotionRole.name} ({vRecruitRole.name} removed)")





class LibraryViewer():
	"""
	# LIBRARY VIEWER
	Class responsible for sending a viewer to see library information.

	## PARAMETERS
	- `p_userID`: the user ID to view.
	- `p_isViewingSelf`: Whether the calling viewer is viewing themself.
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
		self.listSelectMultiplier = 0 # this multiplier is used to offset the options.

		BUPrint.Debug(f"User is viewing self: {self.bIsViewingSelf}")



	async def UpdateViewer(self):
		"""
		# SEND VIEWER
		Updates the viewer message.  
		
		This is the function to call when needing to refresh the embed/view.
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
		"""# GENERATE VIEW:
		Creates and returns a view with button assignment appropriate for the current page/userData.

		When needing to update the viewer, use `UpdateViewer`.
		"""
		vView = LibViewer_view(self)
		btn_configure = LibViewerBtn_setup(self)
		btn_inbox = LibViewerBtn_inbox(self)
		btn_promoteReq = LibViewerBtn_recruitRequestPromotion(self)
		btn_General = LibViewerBtn_general(self)
		btn_Ps2 = LibViewerBtn_planetside2(self)
		btn_sessions = LibViewerBtn_sessions(self)
		btn_sessionPrev = LibViewerBtn_session_previous(self)
		btn_sessionNext = LibViewerBtn_session_next(self)
		btn_sessionSelect = LibViewerBtn_sessionSelector(self)

		if self.bIsViewingSelf:
			vView.add_item(btn_configure)
			vView.add_item(btn_inbox)
			if self.userEntry.bIsRecruit and not self.userEntry.bRecruitRequestedPromotion:
				if UserLibrary.GetRecruitRequirements(self.userEntry, p_asBool=True):
					vView.add_item(btn_promoteReq)
		vView.add_item(btn_General)
		vView.add_item(btn_Ps2)
		vView.add_item(btn_sessions)

		if self.page == LibraryViewPage.general:
			btn_General.disabled = True
			btn_sessionNext.disabled = True
			btn_sessionPrev.disabled = True

		elif self.page == LibraryViewPage.ps2Info:
			btn_Ps2.disabled = True
			btn_sessionNext.disabled = True
			btn_sessionPrev.disabled = True

		elif self.page == LibraryViewPage.sessions:
			vView.add_item(btn_sessionPrev)
			vView.add_item(btn_sessionNext)
			vView.add_item(btn_sessionSelect)

			btn_sessionPrev.disabled = bool(self.listSelectMultiplier == 0)
			btn_sessionNext.disabled = bool( len(self.userEntry.sessions) < settings.UserLib.sessionMaxPerPage and ((1+self.listSelectMultiplier)*settings.UserLib.sessionMaxPerPage) < len(self.userEntry.sessions) + settings.UserLib.sessionMaxPerPage)

		elif self.page == LibraryViewPage.individualSession:
			vView.add_item(btn_sessionPrev)
			vView.add_item(btn_sessionNext)
			vView.add_item(btn_sessionSelect)
			btn_sessionPrev.disabled = bool( self.multiPageNum == 0 )
			# Remember to account for arrays starting at 0.
			btn_sessionNext.disabled = bool(self.multiPageNum == len(self.userEntry.sessions)-1)

		if len(self.userEntry.sessions) == 0:
			btn_sessions.disabled = True
			btn_sessionNext.disabled = True
			btn_sessionPrev.disabled = True
			btn_sessionSelect.disabled = True

		if self.userEntry.ps2Name == "" or self.userEntry.ps2Name == None:
			btn_Ps2.disabled = True


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

		if self.page == LibraryViewPage.sessions:
			return self.GenerateEmbed_sessionBrowser()

		if self.page == LibraryViewPage.individualSession:
			try:
				return self.GenerateEmbed_session(self.userEntry.sessions[self.multiPageNum])
			except IndexError:
				BUPrint.LogError("Invalid session index given!")
				return self.GenerateEmbed_General()

		if self.page == LibraryViewPage.inbox:
			return self.GenerateEmbed_inbox()



	def GenerateEmbed_General(self):
		vGuild = UserLibrary.botRef.get_guild(int(settings.BotSettings.discordGuild))
		discordUser = vGuild.get_member(self.userID)
		vEmbed = discord.Embed(
			title=f"General Info for {discordUser.display_name}",
			description=f"They joined the server {GetDiscordTime(discordUser.joined_at, DateFormat.Dynamic)}!"
		)

		if len(self.userEntry.topQuotes) != 0:
			vQuotes = ""
			for quote in self.userEntry.topQuotes:
				vQuotes += f"{quote}\n"
			vEmbed.add_field(
				name="Top Quotes",
				value=vQuotes,
				inline=False
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
				value=f"{self.userEntry.birthday.day } / {self.userEntry.birthday.month}",
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



	def GenerateEmbed_inbox(self):
		vEmbed = discord.Embed(title="Inbox", description=f"You have {len(self.userEntry.inbox)} messages")

		if len(self.userEntry.inbox) == 0:
			return vEmbed

		for message in self.userEntry.inbox:
			embedTitle = ""
			if message.bIsWarning:
				embedTitle = "WARNING: "
			embedTitle += f"{GetDiscordTime(message.date, DateFormat.DateTimeShort)} | {message.title}"
			
			vEmbed.add_field(name=embedTitle, value=f"{message.adminContext}\n{message.message}", inline=False)

		return vEmbed



	def GenerateEmbed_ps2(self):
		vEmbed = discord.Embed(title="Planetside 2 Information")

		if self.userEntry.ps2Name != "" or self.userEntry.ps2Name != None:
			BUPrint.Debug(f"PS2 Character Val: {self.userEntry.ps2Name}")
			vEmbed.add_field(
				name="PS2 Character",
				value=self.userEntry.ps2Name,
				inline=False
			)

			if self.userEntry.ps2Outfit != "" or self.userEntry.ps2Outfit != None:
				BUPrint.Debug(f"Outfit Val: {self.userEntry.ps2Outfit}")
				vEmbed.add_field(
					name="PS2 Outfit",
					value=self.userEntry.ps2Outfit,
					inline=False
					)
			
			if self.userEntry.ps2OutfitRank != "" or self.userEntry.ps2OutfitRank != None:
				BUPrint.Debug(f"Outfit Rank val: {self.userEntry.ps2OutfitRank}")
				vEmbed.add_field(
					name="Outfit Rank",
					value=self.userEntry.ps2OutfitRank,
					inline=False
				)

		if len(self.userEntry.sessions) != 0:
			displayStr = ""
			session:Session
			vIteration = 0
			for session in self.userEntry.sessions:
				if session.bIsPS2Event:
					displayStr += f"{session.date.day}/{session.date.month}/{session.date.year} | {session.eventName}\n"
				
				vIteration += 1

				if vIteration >= settings.UserLib.sessionPreviewMax:
					break
			
			if displayStr != "":
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

		vDisplayStr = ""
		vIteration = 0
		for session in self.userEntry.sessions[int(self.listSelectMultiplier * settings.UserLib.sessionMaxPerPage) : int((1+self.listSelectMultiplier)* settings.UserLib.sessionMaxPerPage)]:
			vDisplayStr += f"{vIteration+1} | {session.date.day}/{session.date.month}/{session.date.year} | {session.eventName}"
			if not session.bIsPS2Event:
				vDisplayStr += " (Not PS2)\n"
			else: vDisplayStr += "\n"
			vIteration += 1

		vEmbed.add_field(name="Tracked Sessions", value=vDisplayStr)

		return vEmbed


	def GenerateEmbed_session(self, p_session:Session):
		"""
		# GENERATE EMBED: Session
		Generates an embed showing the stats from a session.
		"""
		vEmbed = discord.Embed(
					title=f"{p_session.eventName}",
					description=f"{GetDiscordTime(p_session.date, DateFormat.DateLonghand)}\nEvent lasted for {p_session.duration:.2f} hours"
					)


		if not p_session.bIsPS2Event:
			vEmbed.add_field(name="NOTE:",value="This event is not for PS2, and thus has no statistics to show.")
			
			return vEmbed


		if p_session.kda != None:
			vEmbed.add_field(
				name="Kills, Deaths & Assists",
				value=f"""Kills:{p_session.kda.kills}
				Allies: {p_session.kda.killedAllies}
				Squadmates: {p_session.kda.killedSquad}

				Deaths: {p_session.kda.deathTotal}
				From enemies: {p_session.kda.deathByEnemies}
				From allies: {p_session.kda.deathByAllies}
				From Squad: {p_session.kda.deathBySquad}

				Assists: {p_session.kda.assists}

				Vehicle Takedowns: {p_session.kda.vehiclesDestroyed}
				"""
			)

		if p_session.medicData != None:
			vEmbed.add_field(
				name="Medic Stats",
				value=f"""Heals: {p_session.medicData.heals}
				Revives: {p_session.medicData.revives}
				"""
			)

		if p_session.engineerData != None:
			vEmbed.add_field(
				name="Engineer Stats",
				value=f"""Vehicle Repairs: {p_session.engineerData.repairScore}
				Resupplies: {p_session.engineerData.resupplyScore}
				"""
			)


		vEmbed.add_field(
			name="Score",
			value=str(p_session.score)
		)


		if len(p_session.funEvents) != 0:
			vEventString = ""
			for event in p_session.funEvents:
				vEventString += f"{event}\n"

			vEventString = vEventString[:1024]
			vEmbed.add_field(
				name="Fun Events",
				value=vEventString,
				inline=False
			)

		return vEmbed





####### LIBRARY VIEWER BUTTONS & UI.VIEWER
class LibViewer_btnViewInbox(discord.ui.Button):
	def __init__(self, p_userID):
		self.userID = p_userID
		super().__init__( label="View inbox")

	async def callback(self, p_interaction:discord.Interaction):
		vViewer = LibraryViewer(self.userID, True)
		vViewer.page = LibraryViewPage.inbox

		await vViewer.SendViewer(p_interaction)
			


class LibViewer_view(discord.ui.View):
	def __init__(self, p_viewer:LibraryViewer):
		self.vViewer = p_viewer
		super().__init__(timeout=180)

	async def on_timeout(self):
		try:
			await self.vViewer.viewerMsg.delete()
		except discord.errors.NotFound:
			pass


class LibViewerBtn_setup(discord.ui.Button):
	def __init__(self, p_viewer:LibraryViewer):
		self.vViewer = p_viewer
		super().__init__(label="Setup", row=0)

	async def callback (self, p_interaction:discord.Interaction):
		await p_interaction.response.send_modal( LibViewer_ConfigureModal(self.vViewer) )



class LibViewerBtn_recruitRequestPromotion(discord.ui.Button):
	def __init__(self, p_viewer: LibraryViewer):
		self.vViewer = p_viewer
		super().__init__(label="Request Promotion!", row=0, style=discord.ButtonStyle.green)

	async def callback(self, p_interaction:discord.Interaction):
		vRequest = UserLib_RecruitValidationRequest( self.vViewer.userEntry )
		await vRequest.SendRequest()

		self.vViewer.userEntry.bRecruitRequestedPromotion = True
		UserLibrary.SaveEntry(self.vViewer.userEntry)
		await self.vViewer.UpdateViewer()

		await p_interaction.response.send_message("Promotion request sent!", ephemeral=True)


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
		self.vViewer.page = LibraryViewPage.sessions
		self.vViewer.multiPageNum = 0
		await self.vViewer.UpdateViewer()
		await p_interaction.response.defer()


class LibViewerBtn_session_next(discord.ui.Button):
	def __init__(self, p_viewer:LibraryViewer):
		self.vViewer = p_viewer
		super().__init__(label=">", row=1)

	async def callback (self, p_interaction:discord.Interaction):
		# self.vViewer.page = LibraryViewPage.individualSession
		if self.vViewer.page == LibraryViewPage.sessions:
			self.vViewer.listSelectMultiplier += 1
		else:
			self.vViewer.multiPageNum += 1
		
		await self.vViewer.UpdateViewer()
		await p_interaction.response.defer()


class LibViewerBtn_session_previous(discord.ui.Button):
	def __init__(self, p_viewer:LibraryViewer):
		self.vViewer = p_viewer
		super().__init__(label="<", row=1)

	async def callback (self, p_interaction:discord.Interaction):
		# self.vViewer.page = LibraryViewPage.individualSession
		if self.vViewer.page == LibraryViewPage.sessions:
			self.vViewer.listSelectMultiplier -= 1
		else:
			self.vViewer.multiPageNum -= 1		
		
		await self.vViewer.UpdateViewer()
		await p_interaction.response.defer()


class LibViewerBtn_sessionSelector(discord.ui.Select):
	def __init__(self, p_viewer:LibraryViewer):
		self.vViewer = p_viewer
		super().__init__(placeholder="Jump to a session page...")
		vIteration = 0
		for session in self.vViewer.userEntry.sessions[int(self.vViewer.listSelectMultiplier * settings.UserLib.sessionMaxPerPage) : int((1+self.vViewer.listSelectMultiplier)* settings.UserLib.sessionMaxPerPage)]:
			self.add_option(
				label=f"{vIteration+1} | {session.date.day}/{session.date.month}/{session.date.year} | {session.eventName}",
				value=vIteration
			)
			vIteration += 1


	async def callback (self, p_interaction:discord.Interaction):
		self.vViewer.page = LibraryViewPage.individualSession
		self.vViewer.multiPageNum = int(self.values[0])
		await self.vViewer.UpdateViewer()
		await p_interaction.response.defer()



class LibViewerBtn_inbox(discord.ui.Button):
	def __init__(self, p_viewer:LibraryViewer):
		self.vViewer = p_viewer
		super().__init__(label="Inbox", row=0)


	async def callback (self, p_interaction:discord.Interaction):
		self.vViewer.page = LibraryViewPage.inbox
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
		vAdminChn = self.botRef.get_channel(settings.Channels.botAdminID)

		if vAdminChn == None:
			BUPrint.Info("Unable to get admin channel for promotion request!")
			return

		vView = discord.ui.View(timeout=None)
		vView.add_item(RecruitValidationReq_btnAccept(self))

		vUser = self.botRef.get_user(self.userEntry.discordID)

		self.requestMsg = await vAdminChn.send(f"**RECRUIT PROMOTION VALIDATION**\nUser {vUser.mention} has met the set criteria and is ready to be promoted!", view=vView)


class RecruitValidationReq_btnAccept(discord.ui.Button):
	def __init__(self, p_parentRequest:UserLib_RecruitValidationRequest):
		self.parent = p_parentRequest
		super().__init__(label="Promote!", style=discord.ButtonStyle.green)

	async def callback(self, p_interaction:discord.Interaction):
		vUser = p_interaction.guild.get_member(self.parent.userEntry.discordID)
		
		await UserLibrary.PromoteUser( vUser )

		await self.parent.requestMsg.delete()

		await p_interaction.response.send_message(f"Done!", ephemeral=True)