import discord
from discord.ext import commands
# from discord.ext.commands import Context
from discord import app_commands
from discord import SelectMenu, SelectOption

from auraxium import Client as AuraxClient
import auraxium.ps2 as AuraxPS2

import os

import pickle

import datetime

from enum import Enum

from botUtils import BotPrinter as BUPrint
from botUtils import UserHasCommandPerms
from botUtils import FilesAndFolders
from botUtils import DateFormatter, DateFormat

import botData.settings as settings
from botData.users import User
from botData.operations import UserSession

class UserLibraryCog(commands.GroupCog, name="user_library"):
	"""
	# USER LIBRARY COG
	Handles commands related to managing the user library.
	"""
	def __init__(self, p_botRef):
		self.botRef = p_botRef
		UserLibrary.botRef = p_botRef
		BUPrint.Info("COG: User Library loaded!")


	@app_commands.command(name="about", description="Show information about a user, or see your own!")
	@app_commands.describe(p_userToFind="The user you want to see information about;  Leave empty to see your own!")
	@app_commands.rename(p_userToFind="user")
	async def AboutUser(self, p_interaction:discord.Interaction, p_userToFind:discord.Member = None):
		# HARDCODED ROLE USEAGE:
		if not await UserHasCommandPerms(p_interaction.user, (settings.CommandRestrictionLevels.level3), p_interaction):
			return
		bViewingSelf = bool(p_userToFind == None)
		vLibViewer = LibraryViewer(p_interaction.user.id, bViewingSelf)

		await vLibViewer.SendViewer(p_interaction)

		# if p_userToFind == None:
		# 	await p_interaction.response.send_message("Viewing yourself!", ephemeral=True)

		# else:
		# 	await p_interaction.response.send_message(f"Viewing info for: {p_userToFind.name}", ephemeral=True)



class UserLibrary():
	"""
	# USER LIBRARY OBJECT
	Contains functions relating to the entries.
	Most functions will not require an instance.
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



	def HasEntry(p_UserID:int):
		"""
		# HAS LIBRARY ENTRY
		Checks if an entry for the user ID exists.

		### RETURNS
		`True` if an entry exists.

		`False` if no entry exists.
		"""
		if os.path.exists(f"{UserLibrary.GetEntryPath(p_UserID)}"):
			return True
		else:
			return False



	def SaveEntry(p_entry:User):
		"""
		# SAVE LIBRARY ENTRY
		Saves the passed entry to file.
		"""
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



	def LoadEntry(p_userID:int):
		"""
		# LOAD LIBRARY ENTRY
		If an entry exists, it is loaded and returned.

		### RETURNS:
		`User` library entry, or `None` if not found.
		"""
		if not UserLibrary.HasEntry(p_userID):
			BUPrint.Debug(f"User with id {p_userID} has no library entry")
			return None
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

		return vLibEntry


	async def PropogatePS2Info(p_entry:User):
		"""
		# PROPGATE PS2 INFO
		Uses the AuraxClient to check valid PS2 name and set the PS2 details accordingly.

		### RETURN
		False on failure to find a character.

		True if character is found.
		"""
		if p_entry.ps2Name == "":
			BUPrint.LogError("Invalid PS2 name given, shouldn't have been able to get here!")
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
		p_entry.ps2OutfitRank = vOutfitChar.rank

		UserLibrary.SaveEntry(p_entry)
		await vAuraxClient.close()
		return True
		



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
		vView = discord.ui.View()
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
			vEmbed.add_field(
				name="Recruit!",
				value=f"They need to attend {settings.UserLib.minAttendedEvents-self.userEntry.eventsAttended} more events.",
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




####### LIBRARY VIEWER BUTTONS

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
		label="Birth Date (year optional: it's never shown)",
		placeholder="DD/MM",
		required=False,
		style=discord.TextStyle.short
	)

	def __init__(self, p_parentLibViewer:LibraryViewer):
		self.parentViewer = p_parentLibViewer
		super().__init__(title="CONFIGURE YOUR LIBRARY ENTRY")
		if self.parentViewer.userEntry.ps2Name != "":
			self.txt_ps2Char.default = self.parentViewer.userEntry.ps2Name
		
		if self.parentViewer.userEntry.aboutMe != "":
			self.txt_about.default = self.parentViewer.userEntry.aboutMe

		if self.parentViewer.userEntry.birthday != None:
			self.txt_birthday.default = f"{self.parentViewer.userEntry.birthday.day}/{self.parentViewer.userEntry.birthday.month}"


	async def on_submit(self, p_interaction:discord.Interaction):
		await p_interaction.response.defer()

		self.parentViewer.userEntry.ps2Name = self.txt_ps2Char.value
		self.parentViewer.userEntry.aboutMe = self.txt_about.value

		if self.txt_birthday.value != "":
			if len(self.txt_birthday.value) > 5:
				# Provided full date- with year
				vDate = datetime.datetime.strptime(self.txt_birthday.value, r"%d/%m/%y")
			else:
				vDate = datetime.datetime.strptime(self.txt_birthday.value, r"%d/%m")
			
			self.parentViewer.userEntry.birthday = vDate

			UserLibrary.SaveEntry(self.parentViewer.userEntry)

		if self.txt_ps2Char.value != "":
			await UserLibrary.PropogatePS2Info(self.parentViewer.userEntry)