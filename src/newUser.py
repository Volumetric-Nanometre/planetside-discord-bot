import discord
from discord.ext import commands, tasks
from discord import ui
import auraxium
import dataclasses
import asyncio

import botData.settings
from botUtils import BotPrinter

@dataclasses.dataclass
class NewUserData:
	"""
	Minimal dataclass to hold data about a new user.
	"""
	userObj : discord.User = None
	joinMessage : discord.Message = None
	ps2Name : str = ""
	ps2Outfit: str = ""
	rank: int = 0
	joinDate: int = 0
	warnings = [] # List of warning strings.


class NewUser(commands.Cog):
	userDatas = []
	def __init__(self, pBot):
		self.botRef: commands.Bot = pBot
		# self.nameModal = PS2NameModal(p_parent=self)
		# self.userData = NewUserData()

	def GetUserData(p_id: str):
		"""
		Returns the `NewUserData` with matching user ID.
		"""
		dataObj: NewUserData
		for dataObj in NewUser.userDatas:
			if dataObj.userObj.id == p_id:
				return dataObj

	@commands.Cog.listener("on_member_join")
	async def promptUser(self, p_member: discord.Member):
		# self.botRef = p_bot
		userData = NewUserData()
		userData.userObj = p_member
		self.userDatas.append(userData)

		vEmbed = discord.Embed(colour=discord.Colour.from_rgb(0, 200, 50), 
			title=f"Welcome to The Drunken Dogs, {p_member.display_name}!", 
			description="To continue, use the buttons below to provide your Planetside 2 character name, and read the rules.\nThen you can request access, and wait for one of our admins to get you set up!"
		) # End - vEmbed

		vEmbed.add_field(name="ACCEPTANCE OF RULES", value="By pressing 'REQUEST ACCESS', you are confirming **you have read**, **understand**, and **agree to adhere** by the rules.", inline=True)

		vView = self.GenerateView(p_member.id)
		gateChannel = self.botRef.get_channel(botData.settings.BotSettings.newUser_gateChannelID)
		userData.joinMessage = await gateChannel.send(view=vView, embed=vEmbed, delete_after=300)

	@tasks.loop(minutes=botData.settings.BotSettings.newUser_readTimer, count=1)
	async def enableRequestBtn(self, p_userID):
		BotPrinter.Debug("Enabling Join Request Button")
		data: NewUserData
		for data in self.userDatas:
			if p_userID == data.userObj.id:
				newView = self.GenerateView(p_userID, True)
				data.joinMessage.edit(view=newView)

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

	async def callback (self, p_interaction: discord.Interaction):
		if p_interaction.user.id == self.userID:
			await p_interaction.response.send_modal( PS2NameModal(p_userData=NewUser.GetUserData(self.userID), p_parent=self) )


class NewUser_btnReadRules(discord.ui.Button):
	def __init__(self, p_newUserRef: NewUser):
		self.newUserRef = p_newUserRef
		super().__init__(label="Rules", url=botData.settings.BotSettings.newUser_rulesURL )

	# async def callback(self, pInteraction: discord.Interaction):
		# self.newUserRef.enableRequestBtn(kwargs=pInteraction.user.id)
		# self.newUserRef.enableRequestBtn.start(args=pInteraction.user.id)


class NewUser_btnRequest(discord.ui.Button):
	def __init__(self, p_userID: str):
		self.userID = p_userID
		super().__init__(label="REQUEST ACCESS", disabled=True, row=0, style=discord.ButtonStyle.blurple)

	async def callback(self, pInteraction: discord.Interaction):
		if pInteraction.user.id == self.userID:
			BotPrinter.Debug("User requesting access!")


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
		vNewName = await self.CheckPlayer(self.vCharName, pInteraction.user)
		BotPrinter.Debug(f"New user name: {vNewName}")
		if vNewName != "":
			await pInteraction.user.edit(nick=vNewName)
			await pInteraction.response.defer()
		else:
			await pInteraction.response.send_message(f"Could not find your in-game character name. \nPlease try again, or contact a CO for assistance.", ephemeral=True)
		# await pInteraction.response.send_message("Welcome to TDKD! \nUse `/roles` to add PS2 and other game related roles (and view their channels)!", ephemeral=True)
		# Since URL buttons do not use callback, start the button timer here.
		self.newUserRef.enableRequestBtn.start(args=pInteraction.user.id)

	async def on_eror(self, pInteraction: discord.Interaction, error: Exception):
		BotPrinter.LogError("Error occured on new user modal.", p_exception=error)

	async def on_timeout(self):
		await self.stop()

	# Main logic for checking players & role assigning.
	async def CheckPlayer(self, pIGN: str, pUser: discord.User):
		BotPrinter.Debug(f"Checking player name for {pUser.name}: {pIGN}")

		async with auraxium.Client() as ps2Client:
			ps2Client.service_id = botData.settings.BotSettings.ps2ServiceID
			player: auraxium.ps2.Character = await ps2Client.get_by_name(auraxium.ps2.Character, f"{pIGN}")
			if player is not None:
				BotPrinter.Debug("Found IGN!  Compiling new nickname")
				self.userData.ps2Name = pIGN
				vNewUserName: str
				vOutfit: auraxium.ps2.Outfit = await player.outfit()
				if vOutfit is None:
					BotPrinter.Debug("Player is not part of any Outfit!")
					self.userData.warnings.append("User hasn't joined an outfit.")
					vNewUserName = pIGN
				else: # USER IS PART OF OUTFIT
					self.userData.ps2Outfit = vOutfit.name
					# Check outfit rank
					outfitPlayer:auraxium.ps2.OutfitMember = player.outfit_member()


					if outfitPlayer.rank_ordinal <= botData.settings.BotSettings.newUser_outfitRankWarn:
						self.userData.warnings.append(f"User is claiming to be a high ranking ({outfitPlayer.rank}) member of {vOutfit.name}!")

					# Outfit Tag prepends
					if vOutfit.alias == "TDKD":
						BotPrinter.Debug("Player is part of TDKD!")
						self.userData.joinDate = outfitPlayer.member_since
						vNewUserName = pIGN
					elif vOutfit is not None:
						BotPrinter.Debug(f"Player is NOT part of TDKD! Prepending Alias {vOutfit.alias}")
						vNewUserName = f"[{vOutfit.alias}] {pIGN}"
			else: 
				self.userData.warnings.append("User does not have a valid PS2 character name")
				return ""
			
			return vNewUserName



class NewUserRequest():
	"""
	# NEW USER REQUEST
	Class containing functionality relating to the messages sent to the join request channel and their behaviour.
	"""
	pass