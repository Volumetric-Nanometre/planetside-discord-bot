# Class/Module for managing role giving/removals.

import discord
import discord.ext
from discord.ext import commands
from discord import app_commands
import asyncio

import settings
import botData


class RoleManager(commands.Cog):
	def __init__(self, p_bot) -> None:
		self.bot = p_bot
		self.lock = asyncio.Lock()
		
		super().__init__()

	@commands.command()
	@app_commands.rename("Rolls")
	async def AssignRoles(p_interaction: discord.Interaction):
		print ("Stuff")
		await p_interaction.response.send_message("Embed will go here! :D")