import discord
from discord.ext import commands
import auraxium

import dataclasses
import datetime, dateutil.relativedelta

import botData.settings
from botData.settings import NewUsers as NewUserSettings
from botData.settings import CommandLimit
from botUtils import BotPrinter, GetDiscordTime, UserHasCommandPerms, GetGuild
from botData.utilityData import Colours, DateFormat

from botData.dataObjects import User
from userManager import UserLibrary
from roleManager import RoleManager



@dataclasses.dataclass
class NewUserData:
	"""
	Minimal dataclass to hold data about a new user.
	"""
	bIsFirstLoop = True # MUST BE TRUE ON INITIALISATION! Used during loop to not enable button on first iteration.
	userObj : discord.Member = None
	joinMessage : discord.Message = None
	rulesMsg : discord.Message = None
	ps2CharObj: auraxium.ps2.Character = None
	ps2CharName : str = ""
	ps2OutfitName: str = ""
	ps2OutfitAlias: str = ""
	ps2OutfitCharObj: auraxium.ps2.OutfitMember = None
	bIsRecruit = False


class NewUser(commands.Cog):
	userDatas = []
	def __init__(self, pBot):
		self.botRef: commands.Bot = pBot
		self.newReq:NewUserRequest = NewUserRequest(p_userData=None)
		self.newReq.vBotRef = pBot

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


	@commands.Cog.listener("on_ready")
	async def startup(self):
		"""
		# STARTUP
		Clears the gate channel of all posts, and the join-req channel of all posts.
		This is here to keep start-up and shutdown clean:

		In the event the bot is shutdown while users are in the process of joining, the VIEWs cease to function.
		Given the low likelyhood of a user being affected by down-time, post a message afterwards instructing them to leave and re-join.
		"""
		BotPrinter.Info("Purging Join Posts and sent Requests...")

		gateChannel = self.botRef.get_channel(NewUserSettings.gateChannelID)
		await gateChannel.purge(reason="Start-up/Shutdown Purge.")
		BotPrinter.Debug("	-> Gate channel Purged.")

		adminRequestChannel = self.botRef.get_channel(botData.settings.BotSettings.adminChannel)
		await adminRequestChannel.purge(reason="Startup/Shutdown Purge")
		BotPrinter.Debug("	-> Request Channel Purged.")

		await gateChannel.send(botData.settings.Messages.gateChannelDefaultMsg)



	@commands.Cog.listener("on_member_join")
	async def promptUser(self, p_member: discord.Member):
		if NewUserRequest.vRequestChannel == None:
			NewUserRequest.vRequestChannel = self.botRef.get_channel(botData.settings.BotSettings.adminChannel)
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
				description=botData.settings.Messages.newUserInfo
			) # End - vEmbed

			vEmbed.add_field(name="ACCEPTANCE OF RULES", value=botData.settings.Messages.newUserRuleDeclaration, inline=True)

			vView = self.GenerateView(p_member.id)
			gateChannel = self.botRef.get_channel(NewUserSettings.gateChannelID)
			userData.joinMessage:discord.Message = await gateChannel.send(f"{p_member.mention}",  view=vView, embed=vEmbed)
		
		else:
			BotPrinter.Info("User already has an entry!")



	def GenerateView(self, p_memberID, bCanRequest: bool = False,):
		vView = discord.ui.View(timeout=None)
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
		super().__init__(label="Rules")

	async def callback(self, p_interaction:discord.Interaction):
		userData = NewUser.GetUserData(None, p_interaction.user.id)
		miniRules = NewUser_MiniRules(p_userID=p_interaction.user.id, p_guild=p_interaction.guild)

		await miniRules.Setup()
		if miniRules.bUseContent:
			await p_interaction.response.send_message(view=miniRules.view, content=miniRules.rulesMessage.content, ephemeral=True)
		else:
			await p_interaction.response.send_message(view=miniRules.view, embed=miniRules.rulesEmbed, ephemeral=True)
		userData.rulesMsg = await p_interaction.original_response()



class NewUser_btnRequest(discord.ui.Button):
	def __init__(self, p_userID: str):
		self.userID = p_userID
		super().__init__(label="REQUEST ACCESS", disabled=True, row=0, style=discord.ButtonStyle.blurple)

	async def callback(self, pInteraction: discord.Interaction):
		vUserData = NewUser.GetUserData(None, pInteraction.user.id)
		if pInteraction.user.id == self.userID:

			BotPrinter.Info(f"New user {vUserData.userObj.display_name}|{self.userID}, with ps2 character name {vUserData.ps2CharName} is requesting access!")
			vRequest = NewUserRequest(vUserData)
			await vRequest.SendRequest()
			await pInteraction.response.send_message("**Your request has been sent!**\n\nPlease wait, you will be notified if it has been accepted!", ephemeral=True)
			await vUserData.joinMessage.delete()

		else:
			vUserData = NewUser.GetUserData(None, pInteraction.user.id)
			
			vView:discord.ui.View = discord.ui.view()
			jumpBtn = discord.ui.Button(label="Jump to your join entry", url=vUserData.joinMessage.jump_url)
			vView.add_item(jumpBtn)

			await pInteraction.response.send_message("This is not your entry!", view=vView, ephemeral=True)



class NewUser_MiniRules():
	"""
	# NEW USER: MINI RULES
	Class containing a view for accepting & declining rules, and an embed that copies the rules post.
	"""
	def __init__(self, p_userID, p_guild:discord.Guild):
		BotPrinter.Debug(f"Showing mini rules for user with ID: {p_userID}")
		self.userID = p_userID
		self.guild = p_guild

		self.view = discord.ui.View(timeout=None)
		self.view.add_item(NewUser_MiniRules_btnAccept(self.userID))
		self.view.add_item(NewUser_MiniRules_btnDecline(self.userID))

		self.rulesMessage:discord.Message = None

		self.rulesEmbed = None
		self.bUseContent = False # Set to true if no embeds are found.



	async def Setup(self):
		"""
		# SETUP
		Grabs the rules message and sets the embed.
		"""
		ruleChannel:discord.TextChannel = self.guild.get_channel(NewUserSettings.ruleChnID)

		self.rulesMessage = await ruleChannel.fetch_message(NewUserSettings.ruleMsgID)
		
		if len(self.rulesMessage.embeds) != 0:
			try:
				self.rulesEmbed = self.rulesMessage.embeds[0]
			except IndexError:
				BotPrinter.Debug("NO RULES EMBED FOUND!  Falling back to message content")
				self.bUseContent = True
		else:
			BotPrinter.Debug("Using Rules Message content.")
			self.bUseContent = True

		



class NewUser_MiniRules_btnAccept(discord.ui.Button):
	def __init__(self, p_userID):
		self.userID = p_userID
		super().__init__(label="ACCEPT", style=discord.ButtonStyle.green)

	async def callback(self, p_interaction:discord.Interaction):
		newUsrObj = NewUser.GetUserData(None, self.userID)
		await newUsrObj.joinMessage.edit(view=NewUser.GenerateView(None, self.userID, True))

		await newUsrObj.rulesMsg.delete()

		await p_interaction.response.send_message(botData.settings.Messages.newUserAcceptedRules, ephemeral=True)



class NewUser_MiniRules_btnDecline(discord.ui.Button):
	def __init__(self, p_userID):
		self.userID = p_userID
		super().__init__(label="DECLINE", style=discord.ButtonStyle.red)

	async def callback(self, p_interaction:discord.Interaction):
		dataToRemove = NewUser.GetUserData(None, self.userID)
		NewUser.userDatas.remove(dataToRemove)
		await p_interaction.user.kick(reason="User declined to accept rules.")



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
		embed_userInfo = discord.Embed(colour=Colours.userRequest.value, title=f"JOIN REQUEST: {self.userData.userObj.display_name}", description=f"User joined the server: {GetDiscordTime( pDate=self.userData.joinMessage.created_at, pFormat=DateFormat.Dynamic)}")
		
		embed_userInfo.add_field(name="User ID", value=f"`{self.userData.userObj.id}`")
		embed_userInfo.add_field(name="User Name", value=f"{self.userData.userObj.name}")
		embed_userInfo.add_field(name="Display Name", value=f"{self.userData.userObj.display_name}", inline=True)
		embed_userInfo.add_field(name="Creation Date:", value=f"{GetDiscordTime(self.userData.userObj.created_at, DateFormat.DateTimeLong)}", inline=False)

	# PS2 EMBED
		if self.userData.ps2CharObj != None:
			embed_ps2 = discord.Embed(color=Colours.userRequest.value, title=f"PS2 CHARACTER")
			embed_ps2.add_field(name="Character Name", value=f"{self.userData.ps2CharObj.data.name}")
			embed_ps2.add_field(name="BattleRank", value=f"{self.userData.ps2CharObj.data.battle_rank.value}", inline=True)
		if( self.userData.ps2OutfitCharObj != None ):
			embed_ps2.add_field(name="Outfit", value=f"{self.userData.ps2OutfitName}", inline=True)
			embed_ps2.add_field(name="Rank", value=f"{self.userData.ps2OutfitCharObj.rank}", inline=True)
			joinDate = datetime.datetime.fromtimestamp(self.userData.ps2OutfitCharObj.member_since)
			embed_ps2.add_field(name="Member Since", value=f"{GetDiscordTime(joinDate,DateFormat.DateTimeShort)}", inline=True)

	# WARNINGS EMBED
		embed_warnings = discord.Embed(colour=Colours.userWarnOkay.value, title="WARNINGS & CHECKS", description="Detailed warning checks are listed below.\n\n")

		# Compiled string of warnings.
		strWarnings: str = ""
		# Compiled strings of Okay/Infos.
		strOkay: str = ""

		# New Discord Account
		vDateNow = datetime.datetime.now(tz=datetime.timezone.utc)
		vWarnDate = vDateNow - dateutil.relativedelta.relativedelta(months=-3)
		if self.userData.userObj.created_at < vWarnDate:
			embed_warnings._colour = Colours.userWarning.value
			strWarnings += f"DISCORD ACCOUNT AGE:\n> Account was created within the last {NewUserSettings.newAccntWarn} months!\n\n"
		else:
			strOkay += f"> Discord Account is over {NewUserSettings.newAccntWarn} months old.\n\n"

		# PS2 Invalid Char Name
		if self.userData.ps2CharObj == None:
			embed_warnings._colour = Colours.userWarning.value
			strWarnings += "NO VALID PS2 CHARACTER:\n> User has not provided a valid ps2 character\n\n"
		else:
			strOkay += "- Valid PS2 character provided\n\n"

		# IMPERSONATION WARNING
		if self.userData.ps2OutfitCharObj != None and self.userData.ps2OutfitCharObj.rank_ordinal < NewUserSettings.outfitRankWarn:
			embed_warnings._colour = Colours.userWarning.value
			strWarnings += f"HIGH RANK USER:\n> Claiming a character with a high *({self.userData.ps2OutfitCharObj.rank_ordinal})* Outfit *({self.userData.ps2OutfitName})* Rank *({self.userData.ps2OutfitCharObj.rank})!*"
		elif self.userData.ps2CharObj != None:
			strOkay += "- Users claimed character is not a high ranking outfit member.\n"


		if UserLibrary.HasEntry(self.userData.userObj.id):
			strOkay += "- User has been in the server previously.\n"

		if strOkay == "":
			strOkay = "*None*"
		if strWarnings == "":
			strWarnings = "*None*"

		embed_warnings.add_field(name="⚠️ WARNINGS", value=strWarnings, inline=False)
		embed_warnings.add_field(name="✅ CHECKS", value=strOkay, inline=False)

		# RECRUIT SUGGESTION
		if self.userData.ps2OutfitCharObj != None and self.userData.ps2OutfitAlias == "TDKD" and self.userData.ps2OutfitCharObj.rank == "Recruit":
			embed_warnings.add_field(name="🆕 TDKD RECRUIT", value="This users ps2 character is a TDKD recruit.", inline=False)

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
		btn_reject = NewUserRequest_btnReject(self.userData, self)
		btn_ban = NewUserRequest_btnBan(self.userData, self)
		vView.add_item(btn_roles)
		vView.add_item(btn_reject)
		vView.add_item(btn_ban)

		self.requestMessage = await self.vRequestChannel.send(view=vView, embeds=self.GenerateReports())
		BotPrinter.Debug("	-> New User Join Request sent!")



class NewUserRequest_btnReject(discord.ui.Button):
	def __init__(self, p_userData:NewUserData, p_parent: NewUserRequest):
		self.userData = p_userData
		self.parentRequest = p_parent

		super().__init__(
			style=discord.ButtonStyle.red,
			label="Reject",
			custom_id=f"{self.parentRequest.userData.userObj.id}_NewUserReq_Reject",
			row=1
		)

	async def callback(self, pInteraction: discord.Interaction):
		# HARDCODED ROLE USEAGE:
		if not await UserHasCommandPerms(pInteraction.user, (CommandLimit.validateNewuser), pInteraction):
			return

		await self.userData.userObj.kick(reason=f"User join request denied by {pInteraction.user.display_name}")
		await pInteraction.response.send_message(f"{pInteraction.user.display_name} **denied** {self.userData.userObj.display_name}'s request.")
		await self.parentRequest.requestMessage.delete()



class NewUserRequest_btnBan(discord.ui.Button):
	def __init__(self, p_userData:NewUserData, p_parent):
		self.userData:NewUserData = p_userData
		self.parentRequest:NewUserRequest = p_parent

		super().__init__(
			style=discord.ButtonStyle.red,
			label="Ban",
			custom_id=f"{self.parentRequest.userData.userObj.id}_NewUserReq_Ban",
			row=1
		)

	async def callback(self, pInteraction: discord.Interaction):
		if not await UserHasCommandPerms(pInteraction.user, (CommandLimit.validateNewuser), pInteraction):
			return

		await self.userData.userObj.ban(reason=f"User join request denied by {pInteraction.user.display_name}")
		await pInteraction.response.send_message(f"{pInteraction.user.display_name} **denied** {self.userData.userObj.display_name}'s request and **banned** the user.")
		await self.parentRequest.requestMessage.delete()



class NewUserRequest_btnAssignRole(discord.ui.Select):
	def __init__(self, p_userData:NewUserData, p_parent:NewUserRequest):
		self.userData:NewUserData = p_userData
		self.parentRequest:NewUserRequest = p_parent

		super().__init__(
			custom_id=f"{self.userData.userObj.id}_joinRole",
			placeholder="Assign a role...",
			options=botData.settings.Roles.newUser_roles
		) # END - Init

	async def callback(self, pInteraction: discord.Interaction):
		if not await UserHasCommandPerms(pInteraction.user, (CommandLimit.validateNewuser), pInteraction):
			return

		vAssignedRoleName = ""

		# Assign given role:
		vGuild = await GetGuild(pInteraction.client)
		vAllRoles = vGuild.roles
		# vRole: discord.Role = None
		rolesToAssign = []

		for roleIndex in vAllRoles:
			if roleIndex.id == int(self.values[0]):
				BotPrinter.Debug("	-> ROLE MATCH")
				rolesToAssign.append(roleIndex)
				vAssignedRoleName = roleIndex.name
				continue

			if roleIndex.id in NewUserSettings.autoAssignRoles:
				rolesToAssign.append(roleIndex)
				continue

			if roleIndex.id == NewUserSettings.recruitRole:
				self.userData.bIsRecruit = True
				rolesToAssign.append(roleIndex)
				continue


		BotPrinter.Info(f"Assigning {rolesToAssign} to {self.userData.userObj.display_name}")
		await self.userData.userObj.add_roles(*rolesToAssign, reason=f"Assigned role {vAssignedRoleName} on join request. Accepted by {pInteraction.user.display_name}")

		# Rename
		if self.userData.ps2CharName != None:
			vNewNick = ""
			# Prepend any outfit tag if any and NOT TDKD
			if self.userData.ps2OutfitCharObj != None and self.userData.ps2OutfitAlias != "TDKD":
				vNewNick += f"[{self.userData.ps2OutfitAlias}] "
			vNewNick += f"{self.userData.ps2CharName}"

			await self.userData.userObj.edit(nick=vNewNick)

		# Cleanup Join Request Channel
		vConfirmName: str = ""
		if self.userData.ps2CharObj != None:
			vConfirmName = self.userData.ps2CharName
		else:
			vConfirmName = self.userData.userObj.display_name

		await pInteraction.response.send_message(f"{pInteraction.user.display_name} **confirmed** {vConfirmName}'s request with role {vAssignedRoleName}.")
		await self.parentRequest.requestMessage.delete()


		# Create library entry, if enabled and user doesn't already have one:
		if NewUserSettings.bCreateLibEntryOnAccept and not UserLibrary.HasEntry(self.userData.userObj.id):
			vUserLibEntry = User(
				discordID=self.userData.userObj.id,
				ps2Name=self.userData.ps2CharName,
				)

			if self.userData.ps2OutfitName != "":
				vUserLibEntry.ps2Outfit = f"{self.userData.ps2OutfitName} {self.userData.ps2OutfitAlias}"

			if self.userData.ps2OutfitCharObj != None:
				vUserLibEntry.ps2OutfitRank = self.userData.ps2OutfitCharObj.rank
				vUserLibEntry.ps2OutfitJoinDate = datetime.datetime.fromtimestamp(self.userData.ps2OutfitCharObj.member_since, datetime.timezone.utc)

			self.userData.bIsRecruit = vUserLibEntry.bIsRecruit

			UserLibrary.SaveEntry(vUserLibEntry)


		BotPrinter.Debug("Removing Userdata from list.")
		# Remove userData item from list
		NewUser.userDatas.remove(self.userData)

		# Alert User
		vGeneralChannel = vGuild.get_channel(NewUserSettings.generalChanelID)
		
		vView = discord.ui.View()
		if NewUserSettings.bShowAddRolesBtn:
			vView.add_item(ShowRolesBtn(label="Click me to add roles!"))

		await vGeneralChannel.send(f"Welcome, {self.userData.userObj.mention}!\nYou have been assigned the role: {vAssignedRoleName}.\n\n{botData.settings.Messages.newUserWelcome}", view=vView)




class ShowRolesBtn(discord.ui.Button):
	async def callback (self, p_interaction: discord.Interaction):
		roleView = RoleManager(p_interaction.client, p_interaction.user, True)
		roleView.vInteraction = p_interaction
		await p_interaction.response.send_message( botData.settings.Messages.userAddingRoles, view=roleView, ephemeral=True )
