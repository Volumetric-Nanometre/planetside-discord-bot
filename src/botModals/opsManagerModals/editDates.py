import discord
from botData.dataObjects import OperationData
from botUtils import BotPrinter as BUPrint
import botModals.opsManagerModals.baseModal as baseModal
import datetime

class EditDates(baseModal.BaseModal):
	txtYear = discord.ui.TextInput(
		label="Year",
		placeholder="Full year",
		min_length=4, max_length=4,
		required=False
	)
	txtDay = discord.ui.TextInput(
		label="Day",
		placeholder="Day of month",
		min_length=1, max_length=2,
		required=False
	)
	txtMonth = discord.ui.TextInput(
		label="Month",
		placeholder="What month?  Numerical value!",
		min_length=1, max_length=2,
		required=False
	)
	txtHour = discord.ui.TextInput(
		label="Hour",
		placeholder="Hour",
		min_length=1, max_length=2,
		required=False
	)
	txtMinute = discord.ui.TextInput(
		label="Minute",
		placeholder="Minute",
		min_length=1, max_length=2,
		required=False
	)
	def __init__(self, *, p_opData: OperationData, p_liveOps:list = None):
		self.vLiveOps:list[OperationData] = p_liveOps
		super().__init__(p_opData=p_opData, p_title="Edit Dates")

	# Where the fun happens!
	async def on_submit(self, pInteraction: discord.Interaction):
		BUPrint.Debug("Edit Dates Modal submitted, creating new date...")
		try:
			newDateTime = datetime.datetime(
				year=int(self.txtYear.value),
				month=int(self.txtMonth.value),
				day=int(self.txtDay.value),
				hour=int(self.txtHour.value),
				minute=int(self.txtMinute.value),
				tzinfo=datetime.timezone.utc
			)
		except ValueError:
			await pInteraction.response.send_message("Invalid date given!", ephemeral=True)
			return

		if newDateTime < datetime.datetime.now(datetime.timezone.utc):
			await pInteraction.response.send_message("Date cannot be in the past!", ephemeral=True)
			return


		for liveOps in self.vLiveOps:
			if liveOps.messageID == self.vOpData.messageID:
				continue

			if liveOps.date == newDateTime and liveOps.name == self.vOpData.name:
				await pInteraction.response.send_message("This edit matches an existing live event!  Re-Edit the date/time values.", ephemeral=True)
				return

		self.vOpData.date = newDateTime


		await pInteraction.response.send_message("New date set succesfully.", ephemeral=True)



	def PresetFields(self):
		BUPrint.Debug(f"Auto-filling modal (DATE) with existing data: {self.vOpData.date}")
		self.txtYear.default = str(self.vOpData.date.year)
		self.txtDay.default = str(self.vOpData.date.day)
		self.txtMonth.default = str(self.vOpData.date.month)
		self.txtHour.default = str(self.vOpData.date.hour)
		self.txtMinute.default = str(self.vOpData.date.minute)