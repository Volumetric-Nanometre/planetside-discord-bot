import discord
from botData.dataObjects import OperationData
from botUtils import BotPrinter as BUPrint

class BaseModal(discord.ui.Modal):
	def __init__(self, p_opData:OperationData, p_title:str):
		super().__init__(title=p_title)
		self.vOpData:OperationData = p_opData

		self.parentCallback:callable
		"Function that should update the editor.  Needs to be set."

		self.PresetFields()

	async def on_error(self, pInteraction:discord.Interaction, error: Exception):
		BUPrint.LogErrorExc("Error occured while submitting a modal.", error)
		await pInteraction.response.defer()

	async def on_timeout(self):
		return await super().on_timeout()

	async def on_submit(self, pInteraction: discord.Interaction):
		pass

	async def PresetFields(self):
		"""
		# PRESET FIELDS
		Must be overwritten; called during initialisation.
		"""
		pass