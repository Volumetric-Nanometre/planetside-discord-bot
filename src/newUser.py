import discord
from discord.ext import commands, tasks
from discord import ui
import auraxium

import dataclasses
import asyncio
import datetime, dateutil.relativedelta

import botData.settings
from botUtils import BotPrinter
import botUtils

@dataclasses.dataclass
class NewUserData:
	"""
	Minimal dataclass to hold data about a new user.
	"""
	bIsFirstLoop = True # Used during loop to not enable button on first iteration.
	userObj : discord.Member = None
	joinMessage : discord.Message = None
	ps2CharObj: auraxium.ps2.Character = None
	ps2CharName : str = ""
	ps2OutfitName: str = ""
	ps2OutfitAlias: str = ""
	ps2OutfitCharObj: auraxium.ps2.OutfitMember = None


class NewUser(commands.Cog):
	userDatas = []
	def __init__(self, pBot):
		self.botRef: commands.Bot = pBot
		self.newReq:NewUserRequest = NewUserRequest(p_userData=None)
		self.newReq.vBotRef = pBot

	async def GetChannels(self):
		self.newReq.vRequestChannel = await self.botRef.fetch_channel(botData.settings.BotSettings.newUser_adminChannel)
		# self.newReq.vBotRef = self.botRef

		# self.nameModal = PS2NameModal(p_parent=self)
		# self.userData = NewUserData()

	def GetUserData(self, p_id: str):
		"""
		Returns the `NewUserData` with matching user ID.
		"""
		dataObj: NewUserData
		for dataObj in NewUser.userDatas:
			if dataObj.userObj.id == p_id:
				BotPrinter.Debug("Found matching temporary userData!")
				return dataObj
		BotPrinter.Info("No userdata matching the ID found!")
		return None

	@commands.Cog.listener("on_member_join")
	async def promptUser(self, p_member: discord.Member):
		if NewUserRequest.vRequestChannel == None:
			NewUserRequest.vRequestChannel = await self.botRef.fetch_channel(botData.settings.BotSettings.newUser_adminChannel)
			if(NewUserRequest.vRequestChannel == None):
				BotPrinter.Info("NEW USER REQUEST CHANNEL NOT FOUND!")
				return
	
		if( p_member not in self.userDatas):
			# self.botRef = p_bot
			userData = NewUserData()
			userData.userObj = p_member
			self.userDatas.append(userData)
			BotPrinter.Debug(f"New User Data objects: {NewUser.userDatas}")

			vEmbed = discord.Embed(colour=discord.Colour.from_rgb(0, 200, 50), 
				title=f"Welcome to The Drunken Dogs, {p_member.display_name}!", 
				description="To continue, use the buttons below to provide your Planetside 2 character name, and read the rules.\nThen you can request access, and wait for one of our admins to get you set up!"
			) # End - vEmbed

			vEmbed.add_field(name="ACCEPTANCE OF RULES", value="By pressing 'REQUEST ACCESS', you are confirming **you have read**, **understand**, and **agree to adhere** by the rules.", inline=True)

			vView = self.GenerateView(p_member.id)
			gateChannel = self.botRef.get_channel(botData.settings.BotSettings.newUser_gateChannelID)
			userData.joinMessage:discord.Message = await gateChannel.send(view=vView, embed=vEmbed)
			# BotPrinter.Debug(f"Join Message: {userData.joinMessage}")

			await self.enableRequestBtn.start(p_member.id)
		
		else:
			BotPrinter.Info("User already has an entry!")
	# Count must be set to 2.  1st loop is initial call, then 2nd loop is after timer.
	@tasks.loop(minutes=botData.settings.BotSettings.newUser_readTimer, count=2)
	async def enableRequestBtn(self, p_userID):
		BotPrinter.Debug(f"Enabling Join Request Button for user with ID {p_userID}")
		
		if (len(self.userDatas) == 0):
			BotPrinter.LogError("No user Data's in array!", 0)
			return

		vNewUserData : NewUserData = self.GetUserData(p_userID)
		if vNewUserData == None:
			BotPrinter.LogError("New User Data not found!")
			return

		if vNewUserData.bIsFirstLoop:
			BotPrinter.Debug("First iteration of loop.  Set bool to false, and not continuing!")
			vNewUserData.bIsFirstLoop = False
			return
		
		newView = self.GenerateView(p_userID, True)
		await vNewUserData.joinMessage.edit(view=newView)

	def GenerateView(self, p_memberID, bCanRequest: bool = False,):
		vView = discord.ui.View(timeout=300)
		btnName = NewUser_btnPs2Name(p_memberID, self)
		btnRules = NewUser_btnReadRules(self)
		btnRequest = NewUser_btnRequest(p_memberID)
		btnRequest.disabled = not bCanRequest

		vView.add_item(btnName)
		vView.add_item(btnRules)
		vView.add_item(btnRequest)

		return vView


class NewUser_btnPs2Name(discord.ui.Button):
	def __init__(self, p_userID:str, p_newUser: NewUser):
		self.newuserObj = p_newUser
		self.userID = p_userID
		super().__init__(label="PS2 Name", row=0)

	async def callback (self, pInteraction: discord.Interaction):
		if pInteraction.user.id == self.userID:
			await pInteraction.response.send_modal( PS2NameModal(p_userData=self.newuserObj.GetUserData(self.userID), p_parent=self) )
		else:
			vUserData:NewUserData = self.newuserObj.GetUserData(None, pInteraction.user.id)
			
			vView:discord.ui.View = discord.ui.view()
			jumpBtn = discord.ui.Button(label="Jump to your join entry", url=vUserData.joinMessage.jump_url)
			vView.add_item(jumpBtn)

			await pInteraction.response.send_message("This is not your entry!", view=vView, ephemeral=True)

class NewUser_btnReadRules(discord.ui.Button):
	def __init__(self, p_newUserRef: NewUser):
		self.newUserRef = p_newUserRef
		super().__init__(label="Rules", url=botData.settings.BotSettings.newUser_rulesURL )


class NewUser_btnRequest(discord.ui.Button):
	def __init__(self, p_userID: str):
		self.userID = p_userID
		super().__init__(label="REQUEST ACCESS", disabled=True, row=0, style=discord.ButtonStyle.blurple)

	async def callback(self, pInteraction: discord.Interaction):
		vUserData = NewUser.GetUserData(None, pInteraction.user.id)
		if pInteraction.user.id == self.userID:
			# Generate any other potential warnings, print info to console, then create a new entry for admins!	
			BotPrinter.Info(f"New user {vUserData.userObj.display_name}|{self.userID}, with ps2 character name {vUserData.ps2CharName} is requesting access!")
			# NEW ADMIN ENTRY HERE
			vRequest = NewUserRequest(vUserData)
			await vRequest.SendRequest()
			await pInteraction.response.send_message("Your request has been sent!  Please wait, you will be notified if it has been accepted!", ephemeral=True)
			await vUserData.joinMessage.delete()

		else:
			vUserData = NewUser.GetUserData(None, pInteraction.user.id)
			
			vView:discord.ui.View = discord.ui.view()
			jumpBtn = discord.ui.Button(label="Jump to your join entry", url=vUserData.joinMessage.jump_url)
			vView.add_item(jumpBtn)

			await pInteraction.response.send_message("This is not your entry!", view=vView, ephemeral=True)


class PS2NameModal(discord.ui.Modal, title="Enter your PS2 Character name"):
	vCharName = discord.ui.TextInput(label="PS2 Character Name:",
	style=discord.TextStyle.short,
	min_length=3, max_length=30,
	placeholder="myCharacterName",
	required=True
	) # End - vCharName
	"""
	#PS2 NAME MODAL
	
	Modal used to get the players PS2 character name.
	On succesful finding of the name, the user is renamed, with prefixed outfit tag if applicable.
	"""
	def __init__(self, p_userData: NewUserData, p_parent: NewUser):
		self.newUserRef: NewUser = p_parent
		self.userData : NewUserData = p_userData
		super().__init__(timeout=None, custom_id="NewUser_PS2NameModal")


	async def on_submit(self, pInteraction:discord.Interaction):
		# await pInteraction.response.defer()
		bIsValidChar = await self.CheckPlayer(self.vCharName.value, pInteraction.user)
		if bIsValidChar:
			await pInteraction.response.defer()
		else:
			await pInteraction.response.send_message(f"Could not find your in-game character name. \nPlease try again, or contact a CO for assistance.", ephemeral=True)

	async def on_eror(self, pInteraction: discord.Interaction, error: Exception):
		BotPrinter.LogError("Error occured on new user modal.", p_exception=error)

	async def on_timeout(self):
		await self.stop()

	# Main logic for checking player character name & guild.
	async def CheckPlayer(self, pIGN: str, pUser: discord.Member):
		"""
		Returns true if the provided IGN is a valid character.
		Function also fills the data object with items.
		"""
		BotPrinter.Debug(f"Checking player name for {pUser.name}: {pIGN}")

		async with auraxium.Client() as ps2Client:
			ps2Client.service_id = botData.settings.BotSettings.ps2ServiceID
			player: auraxium.ps2.Character = await ps2Client.get_by_name(auraxium.ps2.Character, f"{pIGN}")
			if player is not None:
				BotPrinter.Debug("	-> Found IGN!")
				self.userData.ps2CharObj = player
				self.userData.ps2CharName = pIGN
				vOutfit: auraxium.ps2.Outfit = await player.outfit()
				
				if vOutfit is None:
					BotPrinter.Debug("	-> Player is not part of any Outfit!")
					return True

				else: # USER IS PART OF OUTFIT
					# Check outfit rank
					outfitPlayer:auraxium.ps2.OutfitMember = await player.outfit_member()
					self.userData.ps2OutfitName = vOutfit.name
					self.userData.ps2OutfitAlias = vOutfit.alias
					self.userData.ps2OutfitCharObj = outfitPlayer
					return True

			else: 
				BotPrinter.Debug("User does not have a valid PS2 character name")
				return False



class NewUserRequest():
	"""
	# NEW USER REQUEST
	Class containing functionality relating to the messages sent to the join request channel and their behaviour.
	"""
	vRequestChannel: discord.TextChannel = None
	vBotRef: commands.Bot = None

	def __init__(self, p_userData: NewUserData):
		self.userData = p_userData
		self.requestMessage: discord.Message # The admin request message.

	
	def GenerateReports(self):
		"""
		# GENERATE REPORTS

		Creates and returns a list of embeds detailing the user who requested to join.
		"""
	# USER INFO EMBED
		embed_userInfo = discord.Embed(colour=botUtils.Colours.userRequest.value, title=f"JOIN REQUEST: {self.userData.userObj.display_name}", description=f"User joined the server: {botUtils.DateFormatter.GetDiscordTime( pDate=self.userData.joinMessage.created_at, pFormat=botUtils.DateFormat.TimeShorthand)}")
		
		embed_userInfo.add_field(name="User ID", value=f"`{self.userData.userObj.id}`")
		embed_userInfo.add_field(name="User Name", value=f"{self.userData.userObj.name}")
		embed_userInfo.add_field(name="Display Name", value=f"{self.userData.userObj.display_name}", inline=True)
		embed_userInfo.add_field(name="Creation Date:", value=f"{ botUtils.DateFormatter.GetDiscordTime(self.userData.userObj.created_at, botUtils.DateFormat.DateTimeLong)}", inline=False)

	# PS2 EMBED
		if self.userData.ps2CharObj != None:
			embed_ps2 = discord.Embed(color=botUtils.Colours.userRequest.value, title=f"PS2 CHARACTER")
			embed_ps2.add_field(name="Character Name", value=f"{self.userData.ps2CharObj.data.name}")
			embed_ps2.add_field(name="Prestiege", value=f"{self.userData.ps2CharObj.data.prestige_level}", inline=True)
		if( self.userData.ps2OutfitCharObj != None ):
			embed_ps2.add_field(name="Outfit", value=f"{self.userData.ps2OutfitName}", inline=True)
			embed_ps2.add_field(name="Rank", value=f"{self.userData.ps2OutfitCharObj.rank}", inline=True)
			joinDate = datetime.datetime.fromtimestamp(self.userData.ps2OutfitCharObj.member_since)
			embed_ps2.add_field(name="Member Since", value=f"{botUtils.DateFormatter.GetDiscordTime(joinDate,botUtils.DateFormat.DateTimeShort)}", inline=True)

	# WARNINGS EMBED
		embed_warnings = discord.Embed(colour=botUtils.Colours.userWarnOkay.value, title="WARNINGS", description="Detailed warning checks are listed below.\n\n")
		
		# New Discord Account
		vDateNow = datetime.datetime.now(tz=datetime.timezone.utc)
		vWarnDate = vDateNow - dateutil.relativedelta.relativedelta(months=-3)
		if self.userData.userObj.created_at < vWarnDate:
			embed_warnings.add_field(name="⚠️ DISCORD ACCOUNT AGE", value=f"This discord account was created within the last {botData.settings.BotSettings.newUser_newAccntWarn} months", inline=False)
			embed_warnings._colour = botUtils.Colours.userWarning.value
		else:
			embed_warnings.add_field(name="✅ DISCORD ACCOUNT AGE", value=f"This discord account is older than {botData.settings.BotSettings.newUser_newAccntWarn} months", inline=False)

		# PS2 Invalid Char Name
		if self.userData.ps2CharObj == None:
			embed_warnings.add_field(name="⚠️ PS2 CHARACTER", value="No valid PS2 Character name was provided.", inline=False)
			embed_warnings._colour = botUtils.Colours.userWarning.value
		else:
			embed_warnings.add_field(name="✅ PS2 CHARACTER", value="User has provided a valid PS2 Character name.", inline=False)

		# IMPERSONATION WARNING
		if self.userData.ps2OutfitCharObj != None and self.userData.ps2OutfitCharObj.rank_ordinal < botData.settings.BotSettings.newUser_outfitRankWarn:
			embed_warnings.add_field(name="⚠️ IMPERSONATION CHECK", value=f"This user is claiming to be a character with a high **({self.userData.ps2OutfitCharObj.rank_ordinal})** Outfit **({self.userData.ps2OutfitName})** Rank **({self.userData.ps2OutfitCharObj.rank})!**", inline=False)
			embed_warnings._colour = botUtils.Colours.userWarning.value
		else:
			embed_warnings.add_field(name="✅ IMPERSONATION CHECK", value=f"This users claimed character is not a high ranking outfit member.", inline=False)

		vreturnList: list = []
		vreturnList.append(embed_userInfo)
		if self.userData.ps2CharObj != None:
			vreturnList.append(embed_ps2)
		vreturnList.append(embed_warnings)
		return vreturnList


	async def SendRequest(self):
		"""
		# SEND REQUEST

		Sends the request to the specified bot admin channel.
		"""
		BotPrinter.Debug("Preparing Send Request...")
		vView = discord.ui.View(timeout=None)
		btn_roles = NewUserRequest_btnAssignRole(self.userData, self)
		vView.add_item(btn_roles)

		self.requestMessage = await self.vRequestChannel.send(view=vView, embeds=self.GenerateReports())
		BotPrinter.Debug("	-> New User Join Request sent!")

class NewUserRequest_btnAssignRole(discord.ui.Select):
	def __init__(self, p_userData:NewUserData, p_parent:NewUserRequest):
		self.userData = p_userData
		self.parentRequest = p_parent

		super().__init__(
			custom_id=f"{self.userData.userObj.id}_joinRole",
			placeholder="Assign a role...",
			options=botData.settings.BotSettings.newUser_roles
		) # END - Init

	async def callback(self, pInteraction: discord.Interaction):
		
		# Assign given role:
		BotPrinter.Debug(f"Assigning {self.values[0]} to {self.userData.userObj.display_name}")
		vGuild = await pInteraction.client.fetch_guild(botData.settings.BotSettings.discordGuild)
		BotPrinter.Debug(f"Guild Obj: {vGuild}")
		vAllRoles = await vGuild.fetch_roles()
		BotPrinter.Debug(f"Roles: {vAllRoles}")
		vRole: discord.Role = None
		roleIndex: discord.Role
		for roleIndex in vAllRoles:
			BotPrinter.Debug(f"Current role: {roleIndex.name}|{roleIndex.id}")
			if roleIndex.id == self.values[0]:
				vRole = roleIndex
				break
		BotPrinter.Debug(f"Role to Assign: {vRole}")
		await self.userData.userObj.add_roles(vRole, reason=f"Assigned role on join request. Accepted by {pInteraction.user.display_name}")

		# Rename
		if self.userData.ps2CharName != None:
			vNewNick = ""
			if self.userData.ps2OutfitCharObj != None:
				vNewNick += f"({self.userData.ps2OutfitAlias}) "
			vNewNick += f"{self.userData.ps2CharName}"

			await self.userData.userObj.edit(nick=vNewNick)

		# Cleanup Join Request Channel
		await pInteraction.response.send_message(f"{pInteraction.user.display_name} confirmed {self.userData.ps2CharName}'s request with role {vRole.name}.")
		await self.parentRequest.requestMessage.delete()

		# Alert User
		vGeneralChannel = vGuild.fetch_channel(botData.settings.BotSettings.generalChanelID)
		vGeneralChannel.send(f"Welcome, {self.userData.userObj.mention}!\nYou have been assigned the role: {vRole.name}.\n\nMake sure to use `/roles` to assign both PS2 and other game related roles (and access related channels)!")

		# TODO: Create server User Library entry for new user.

		# Remove userData item from list
		NewUser.userDatas.remove(self.userData)