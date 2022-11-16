# Ops Manager: Manages creating, editing and removing of Ops.

import os

import discord
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
