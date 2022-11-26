import discord
from discord.ext import commands
from discord import ui
import auraxium

import settings
from botUtils import BotPrinter

class NewUser(discord.ui.Modal, title="Welcome!\nPlease enter your PS2 Character name"):
	vCharName = discord.ui.TextInput(label="PS2 Character Name:",
	style=discord.TextStyle.short,
	min_length=3, max_length=30,
	placeholder="myCharacterName",
	required=True  
	) # End - vCharName

	# TODO: Check if player is already on discord, or rank is above pleb.
	# In these circumstances, notify admins to manually allow, deny/kick
	# Potential idea- construct view with buttons and post to admin only channel.
	# TODO: Give player role
	async def on_submit(self, pInteraction:discord.Interaction):
		# await pInteraction.response.defer()
		vNewName = await self.CheckPlayer(self.vCharName, pInteraction.user)
		BotPrinter.Debug(f"New user name: {vNewName}")
		if vNewName != "":
			await pInteraction.user.edit(nick=f"{vNewName}")
		else:
			await pInteraction.response.send_message(f"Could not find your in-game character name. \nPlease try again (`/Join`), or contact a CO for assistance.", ephemeral=True)
		await pInteraction.response.send_message("Welcome to TDKD! \nUse `/roles` to add PS2 and other game related roles (and view their channels)!", ephemeral=True)


	async def on_eror(self, pInteraction: discord.Interaction, error: Exception):
		BotPrinter.LogError("Error occured on new user modal.", p_exception=error)

	async def on_timeout(self):
		await self.stop()

	# Main logic for checking players & role assigning.
	async def CheckPlayer(self, pIGN: str, pUser: discord.User):
		BotPrinter.Debug(f"Checking player name for {pUser.name}: {pIGN}")

		async with auraxium.Client() as ps2Client:
			ps2Client.service_id = settings.PS2_SVS_ID
			player = await ps2Client.get_by_name(auraxium.ps2.Character, f"{pIGN}")
			if player is not None:
				BotPrinter.Debug("Found IGN!  Compiling new nickname")
				vNewUserName: str
				vOutfit: auraxium.ps2.Outfit = await player.outfit()
				if vOutfit is None:
					BotPrinter.Debug("Player is not part of any Outfit!")
					vNewUserName = pIGN
				elif vOutfit.alias == "TDKD":
					BotPrinter.Debug("Player is part of TDKD!")
					vNewUserName = pIGN
				elif vOutfit is not None:
					BotPrinter.Debug(f"Player is NOT part of TDKD! Prepending Alias {vOutfit.alias}")
					vNewUserName = f"[{vOutfit.alias}] {pIGN}"
			else: return ""
			
			return vNewUserName
