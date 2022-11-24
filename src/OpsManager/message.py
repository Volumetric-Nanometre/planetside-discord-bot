import pickle

import discord
from discord.ext import commands

import settings
import botUtils
import botData


class OpsMessage(discord.ui.View):
	def __init__(self, pOpsDataFile: str):
		self.opsDataFile = pOpsDataFile
		self.opsData: botData.OperationData
		botUtils.BotPrinter.Debug("OpsMessage created.  Don't forget to save or load data!")
		super().__init__(timeout=None)

	async def saveToFile(self):
		botUtils.BotPrinter.Debug(f"Attempting to save {self.opsData.name} to file: {self.opsDataFile}")
		try:
			with open(self.opsDataFile, 'wb') as vFile:
				pickle.dump(self.opsData, vFile)
				botUtils.BotPrinter.Debug("Saved data succesfully!")
		except:
			botUtils.BotPrinter.LogError(f"Failed to save {self.opsData.name} to file {self.opsDataFile}!")
		
	async def getDataFromFile(self):
		botUtils.BotPrinter.Debug(f"Attempting to load data from file: {self.opsDataFile}")
		try:
			with open(self.opsDataFile, 'rb') as vFile:
				self.opsData = pickle.load(vFile)
				botUtils.BotPrinter.Debug("Loaded data succesfully!")
		except:
			botUtils.BotPrinter.LogError(f"Failed to load Ops data from file: {self.opsDataFile}")

	# Sets this objects embed information from data.
	# Should be called prior to posting or updating the view this object is called from.
	async def GenerateEmbed(self):
		vEmbed = discord.Embed(colour=botUtils.Colours.editing, title=self.opsData.name, description=self.opsData.description, timestamp=self.opsData.date)

		if(self.opsData.customMessage != ""):
			vEmbed.add_field(inline=False, name="Additional Info:", value=self.opsData.customMessage)

		# Generate lists for roles:
		role: botData.OpRoleData
		for role in self.opsData.roles:
			vSignedUpUsers: str
			for user in role.players:
				vSignedUpUsers += f"{user}\n"
			vEmbed.add_field(inline=True, 
			name=f"{role.roleName}({len(role.players)}/{role.maxPositions})",
			value=vSignedUpUsers)

		return vEmbed
	
	# async def UpdateView():
	# 	print("Teehee")