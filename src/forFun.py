# COG FOR "FOR FUN" EVENTS NOT TIED TO OTHER FEATURES

from discord import Message, Member, app_commands
from discord.ext import commands
from datetime import datetime
from dateutil import relativedelta

from botData.settings import Channels, ForFun

from botUtils import BotPrinter as BUPrint

from random import choice, shuffle

class ForFunCog(commands.Cog, name="for fun", description="Isolated fun elements not tied to other features."):
	def __init__(self, p_botRef):
		self.botRef:commands.Bot = p_botRef
		self.options = ForFun

		# Set by morning greeting message.
		self.nextGreeting:datetime = datetime.now()
		self.greetingResponses = ForFun.morningGreetings
		if ForFun.bMorningGreetingRandomGif:
			self.greetingResponses = self.greetingResponses + ForFun.morningGreetingsGif
			shuffle(self.greetingResponses)

		if self.options.bMorningGreeting:
			self.botRef.add_listener(self.SendMorningGreeting, "on_message")

		BUPrint.Debug(f"List of responses: {self.greetingResponses}")

		BUPrint.Info("COG: For Fun loaded!")




	async def SendMorningGreeting(self, p_message:Message):
		if p_message.author == self.botRef.user:
			return

		if datetime.now() < self.nextGreeting:
			BUPrint.Debug("Too soon for next morning message!")
			return

		if not p_message.content.lower().__contains__("morning") or p_message.content.count(" ") > 3:
			BUPrint.Debug("Not a morning message, ignoring.")
			return

		self.nextGreeting = datetime.now() + ForFun.morningGreetingMinTime
		BUPrint.Debug(f"Next morning message can be sent at: {self.nextGreeting}")

		msgResponse = choice(self.greetingResponses)

		msgResponse = msgResponse.replace("_USER", f"{p_message.author.mention}")

		await p_message.channel.send(content=msgResponse)