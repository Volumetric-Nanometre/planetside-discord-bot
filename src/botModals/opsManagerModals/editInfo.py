import discord
import botData.operations as OpData
from botUtils import BotPrinter as BUPrint
import botModals.opsManagerModals.baseModal as baseModal
import botUtils

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

	txtVoiceChannels = discord.ui.TextInput(
		label="Voice Channels",
		placeholder="A list of voice channels (per line) to create for this Operation.",
		style=discord.TextStyle.paragraph,
		required=False
	)
	txtArguments = discord.ui.TextInput(
		label="Commands",
		placeholder="Optional commands (per line) to modify behaviour.",
		style=discord.TextStyle.paragraph,
		required=False
	)


	def __init__(self, *, p_OpData: OpData.OperationData):
		super().__init__(p_OpData, p_title="Edit Ops Info")

	# Where the fun happens!
	async def on_submit(self, pInteraction: discord.Interaction):
		botUtils.BotPrinter.Debug("Edit Info Modal submitted...")

		self.vOpData.name = self.txtName.value
		self.vOpData.description = self.txtDescription.value
		self.vOpData.customMessage = self.txtMessage.value

		self.txtVoiceChannels.value.split("\n")
		self.vOpData.voiceChannels = self.txtVoiceChannels.value.split("\n")
		self.vOpData.arguments = self.txtArguments.value.split("\n")

		await pInteraction.response.defer()

	def PresetFields(self):
		botUtils.BotPrinter.Debug("Auto-filling modal (INFO) with existing data.")
		self.txtName.default = self.vOpData.name
		self.txtMessage.default = self.vOpData.customMessage
		self.txtDescription.default = self.vOpData.description
		
		vTempStr: str = ""
		for channel in self.vOpData.voiceChannels:
			vTempStr += f"{channel}\n"		
		self.txtVoiceChannels.default = vTempStr.strip()
		
		vTempStr = ""
		for argument in self.vOpData.arguments:
			BUPrint.Debug(f"Adding Arg {argument} to modal.")
			vTempStr += f"{argument}\n"
		self.txtArguments.default = vTempStr.strip()