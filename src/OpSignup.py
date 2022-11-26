# Redundant? 

import traceback
import discord
import datetime

import botData
import botUtils
import settings

# New Generic class, configures defaults from passed external data rather than having subclasses.
class OpsSignup:

	# p_opsType: custom, armourdogs, soberdogs, etc...
	def __init__(self):
		self.opsData = botData.OpRoleData

	def setOpsData(self, p_typeToSet):
		botUtils.BotPrinter.Debug("Setting Ops data...")
		if p_typeToSet is "soberdogs": self.opsData = botData.DefaultOps_SoberDogs
		elif p_typeToSet is "armourDogs": self.opsData = botData.DefaultOps_ArmourDogs
		#continue...
		botUtils.BotPrinter.Debug("	> Ops data set!")

	async def GenerateEmbed(self):
		botUtils.BotPrinter.Debug("Generating Ops embed...")

		botUtils.BotPrinter.Debug("	> Ops Embed Generated!")

	# async def 