# Ops Manager: Manages creating, editing and removing of Ops.

import os
import datetime
import pickle

import discord
from discord.ext import commands
import enum

# import OpSignup
# import opsCommander

import settings
import botUtils
import botData

# SubModules:
import OpsManager.message
import OpsManager.editor

class OpsManager():
	def init(self):
		# List of ops (file names)
		self.vOpsList: list = self.GetOps()

	# Returns a list of full pathed strings for each 
	async def GetOps():
		botUtils.BotPrinter.Debug("Getting Ops list...")
		vOpsDir = f"{settings.botDir}/{settings.opsFolderName}/"
		return botUtils.FilesAndFolders.GetFiles(vOpsDir, ".bin")

	async def GetDefaults():
		botUtils.BotPrinter.Debug("Getting default Ops...")
		vDir = f"{settings.botDir}/{settings.defaultOpsDir}"
		return botUtils.FilesAndFolders.GetFiles(vDir, ".bin")
		


	# Returns an ENUM containing the names of saved default Operations.
	# Does not use SELF to make it callable without constructing an instance.
	# Does not use Async to allow it to be called in function parameters.
	def GetDefaultOpsAsList():
		botUtils.BotPrinter.Debug("Getting Ops list...")
		vOpsDir = f"{settings.botDir}/{settings.defaultOpsDir}/"
		vDataFiles: list = ["Custom"]
		
		for file in os.listdir(vOpsDir):
			if file.endswith(".bin"):
				vDataFiles.append(file)

		if len(vDataFiles) > 1:
			botUtils.BotPrinter.Debug(f"Ops files found: {vDataFiles}")
			return vDataFiles
		else:
			botUtils.BotPrinter.Debug("No ops files!")
			return vDataFiles



	async def createOpsFolder():
		if (not os.path.exists(f"{settings.botDir}/{settings.opsFolderName}") ):
			try:
				os.makedirs(f"{settings.botDir}/{settings.opsFolderName}")
			except:
				botUtils.BotPrinter.LogError("Failed to create folder for Ops data!")
