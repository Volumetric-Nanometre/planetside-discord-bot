# COG FOR "FOR FUN" EVENTS NOT TIED TO OTHER FEATURES

from discord import Message, Member, app_commands
from discord.ext import commands
from datetime import datetime
from dateutil import relativedelta

from botData.settings import Channels, ForFun

from botUtils import BotPrinter as BUPrint

from random import choice

class ForFunCog(commands.Cog, name="for fun", description="Isolated fun elements not tied to other features."):
	def __init__(self, p_botRef):
		self.botRef:commands.Bot = p_botRef
		self.options = ForFun

		# Set by morning greeting message.
		self.nextGreeting:datetime = datetime.now()

		if self.options.bMorningGreeting:
			self.botRef.add_listener(self.SendMorningGreeting, "on_message")


	async def SendMorningGreeting(self, p_message:Message):
		if datetime.now() < self.nextGreeting:
			BUPrint.Debug("Too soon for next morning message!")
			return

		self.nextGreeting = datetime.now() + ForFun.morningGreetingMinTime

		responseChoices = ForFun.morningGreetings
		if ForFun.bMorningGreetingRandomGif:
			responseChoices += ForFun.morningGreetingsGif

		msgResponse = choice(responseChoices)

		msgResponse.replace("_USER", f"{p_message.author.mention}")

		await p_message.channel.send(content=msgResponse)