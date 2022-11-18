# Ops Manager: Manages creating, editing and removing of Ops.

import os
import pickle

import discord
from discord.ext import commands
import enum

import OpSignup
import opsCommander

import settings
import botUtils
import botData

class OpsManager():
	def init(self):
		# List of ops (file names)
		self.vOpsList: list = self.GetOps()

	# Returns a list of full pathed strings for each 
	async def GetOps():
		botUtils.BotPrinter.Debug("Getting Ops list...")
		vOpsDir = f"{settings.botDir}/{settings.opsFolderName}/"
		vDataFiles: list = []
		
		for file in os.listdir(vOpsDir):
			if file.endswith(".json"):
				vDataFiles.append(file)
		botUtils.BotPrinter.Debug(f"Ops files found: {vDataFiles}")
		
		return vDataFiles


	# Returns an ENUM containing the names of saved default Operations.
	# Does not use SELF to make it callable without constructing an instance.
	# Does not use Async to allow it to be called in function parameters.
	# Mainly used to provide dynamic 
	def GetDefaultOpsAsEnum():
		botUtils.BotPrinter.Debug("Getting Ops list...")
		vOpsDir = f"{settings.botDir}/{settings.defaultOpsDir}/"
		OpsManager.createDefaultsFolder()

		vDataFiles: list = ["Custom"]
		
		for file in os.listdir(vOpsDir):
			if file.endswith(".json"):
				vDataFiles.append(file)

		if len(vDataFiles) > 1:
			botUtils.BotPrinter.Debug(f"Ops files found: {vDataFiles}")
			return enum.Enum("OpsType", vDataFiles)
		else:
			botUtils.BotPrinter.Debug("No ops files!")
			return enum.Enum("OpsType", ["Custom", "(noSavedDefaults)"])



	async def createOpsFolder():
		if (not os.path.exists(f"{settings.botDir}/{settings.opsFolderName}") ):
			try:
				os.makedirs(f"{settings.botDir}/{settings.opsFolderName}")
			except:
				botUtils.BotPrinter.LogError("Failed to create folder for Ops data!")


	def createDefaultsFolder():
		botUtils.BotPrinter.Debug("Creating default ops folder (if non existant)")
		if (not os.path.exists(f"{settings.botDir}/{settings.defaultOpsDir}") ):
			try:
				os.makedirs(f"{settings.botDir}/{settings.defaultOpsDir}")
			except:
				botUtils.BotPrinter.LogError("Failed to create folder for default Ops data!")


class OpsMessage(discord.ui.View):
	def init__(self, pOpsDataFile: str):
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

	# Returns a view using the data 
	async def GenerateEmbed(self):
		vEmbed = discord.Embed(colour=botUtils.Colours.editing, title=self.opsData.name, description=self.opsData.description, timestamp=self.opsData.date)

		# Generate lists for roles:
		role: botData.OpRoleData
		for role in self.opsData.roles:
			vSignedUpUsers: str
			for user in role.players:
				vSignedUpUsers += f"{user}\n"
			vEmbed.add_field(inline=True, 
			name=f"{role.roleName}({len(role.players)}/{role.maxPositions})",
			value=vSignedUpUsers)
	
	# async def UpdateView():
	# 	print("Teehee")

# Class responsible for displaying options, editing and checking.
class OpsEditor():
	def __init__(self, pBot: commands.Bot):
		self.welp = "nope"
		self.vBot = pBot

	# Used to post & create a new, empty ops.
	async def CreateNewCustomMessage():
		print("")