import discord
from botData.dataObjects import OperationData
from botUtils import BotPrinter as BUPrint
import botModals.opsManagerModals.baseModal as baseModal
import os

class EditInfo(baseModal.BaseModal):
	txtName = discord.ui.TextInput(
		label="Ops Name",
		placeholder="Name of the Ops (used as the defaults name)",
		min_length=3, max_length=50,
		required=True
	)
	txtDescription = discord.ui.TextInput(
		label="Description",
		placeholder="Brief explanation of this Ops",
		style=discord.TextStyle.paragraph,
		max_length=400,
		required=True
	)
	txtMessage = discord.ui.TextInput(
		label="Details",
		placeholder="Optional detailed message about this ops.",
		style=discord.TextStyle.paragraph,
		max_length=800,
		required=False
	)
	txtRunner = discord.ui.TextInput(
		label="Managing User",
		placeholder="The user who will oversee this operation",
		style=discord.TextStyle.short,
		max_length=80,
		required=False
	)


	def __init__(self, *, p_OpData: OperationData):
		super().__init__(p_OpData, p_title="Edit Ops Info")

	# Where the fun happens!
	async def on_submit(self, pInteraction: discord.Interaction):
		BUPrint.Debug("Edit Info Modal submitted...")

		self.vOpData.name = self.txtName.value
		self.vOpData.description = self.txtDescription.value
		self.vOpData.customMessage = self.txtMessage.value
		self.vOpData.managedBy = self.txtRunner.value

		await pInteraction.response.defer()

	def PresetFields(self):
		BUPrint.Debug("Auto-filling modal (INFO) with existing data.")
		self.txtName.default = self.vOpData.name
		self.txtMessage.default = self.vOpData.customMessage
		self.txtDescription.default = self.vOpData.description
		self.txtRunner.default = self.vOpData.managedBy