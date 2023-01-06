import discord
from botData.dataObjects import OperationData
from botUtils import BotPrinter as BUPrint
import botModals.opsManagerModals.baseModal as baseModal
import botUtils

class EditChannels(baseModal.BaseModal):
	txtTargetChanel = discord.ui.TextInput(
		label="Signup Channel",
		placeholder="Name of channel to post signup to.",
		style=discord.TextStyle.short,
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


	def __init__(self, *, p_OpData: OperationData):
		super().__init__(p_OpData, p_title="Edit Channel Info")

	# Where the fun happens!
	async def on_submit(self, pInteraction: discord.Interaction):
		botUtils.BotPrinter.Debug("Edit Channel Modal submitted...")

		self.txtVoiceChannels.value.split("\n")
		self.vOpData.voiceChannels = self.txtVoiceChannels.value.split("\n")
		self.vOpData.arguments = self.vOpData.ArgStringToList(self.txtArguments.value, "\n")
		self.vOpData.targetChannel = self.txtTargetChanel.value


		# Check if reserves have been removed and inform.
		if not self.vOpData.options.bUseReserve:
			if len(self.vOpData.reserves):
				affectedUsers = ""

				for userID in self.vOpData.reserves:
					affectedUsers += f"{pInteraction.guild.get_member(userID).mention} "

				await pInteraction.response.send_message(f"**ATTENTION!** Disabling reserve will remove the following users from this event:\n{affectedUsers}\n\nUse `ReserveOn` to revert this change.", ephemeral=True)

		await pInteraction.response.defer()



	def PresetFields(self):
		botUtils.BotPrinter.Debug("Auto-filling modal (CHANNELS) with existing data.")
		vTempStr: str = ""
		for channel in self.vOpData.voiceChannels:
			vTempStr += f"{channel}\n"		
		self.txtVoiceChannels.default = vTempStr.strip()
		
		vTempStr = ""

		BUPrint.Debug(f"Arguments: {self.vOpData.arguments}")
		if self.vOpData.arguments != None:
			for argument in self.vOpData.arguments:
				BUPrint.Debug(f"Adding Arg {argument} to modal.")
				vTempStr += f"{argument}\n"
			self.txtArguments.default = vTempStr.strip()

		self.txtTargetChanel.default = self.vOpData.targetChannel
