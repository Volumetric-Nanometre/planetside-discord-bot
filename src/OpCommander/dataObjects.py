from enum import Enum
from dataclasses import dataclass, field
from datetime import time, timedelta
from discord import Member
from botData.users import User
from botData.settings import Directories
from botUtils import BotPrinter as BUPrint
from botUtils import FilesAndFolders as BUFolders
from botData.settings import Commander as CmdrSettings
from auraxium.ps2 import Character as PS2Character
import os
import pickle

class CommanderStatus(Enum):
	"""
	# COMMANDER STATUS
	Enum to contain the status of a commander.  
	
	### Values are numerical.
	"""
	Init = -10		# Init: Commander has been created.
	Standby = 0 	# Standby: Commander has been set up and waiting.
	Alerts = 10 	# Alerts: Commander is posting periodic alerts if autoStart is enabled.
	WarmingUp = 15	# Warming Up: Starts 5 mins prior to start time.  Updates the commander post with connections modal.
	Started = 20 	# Started: Ops has been started (either manually or by bot.)
	Debrief = 30	# Debrief: Pre-End stage, users are given a reactionary View to provide feedback
	Ended = 40		# Ended: User has ended Ops,  auto-cleanup.


@dataclass
class Participant:
	"""
	# PARTICIPANT
	Dataclass containing a reference to a `discord.Member`, and a `userLibrary.User` for a participant.
	"""
	discordUser: Member = None
	libraryEntry: User = None
	ps2Char: PS2Character = None

	def LoadParticipant(self):
		"""
		# LOAD PARTICIPANT
		Loads and sets the `libraryEntry` data object representing the participant.
		"""
		dataFile = f"{Directories.userLibrary}{self.discordUser.id}.bin"
		lockFile = BUFolders.GetLockPathGeneric(dataFile)

		
		if os.path.exists(f"{Directories.userLibrary}{self.discordUser.id}.bin"):
			BUPrint.Debug("Found existing Library entry!")
			BUFolders.GetLock(lockFile)
			try:
				with open(dataFile, "rb") as vFile:
					self.libraryEntry = pickle.load(vFile)

				BUFolders.ReleaseLock(lockFile)
			except pickle.PickleError as vError:
				BUPrint.LogErrorExc("Failed to load user library entry.", vError)
				BUFolders.ReleaseLock(lockFile)				
			
		else:
			BUPrint.Debug("No existing entry found...")



	def SaveParticipant(self):
		"""
		# SAVE PARTICIPANT
		Saves the participant libEntry data to file.
		"""
		dataFile = f"{Directories.userLibrary}{self.discordUser.id}.bin"
		lockFile = BUFolders.GetLockPathGeneric(dataFile)

		BUFolders.GetLock(lockFile)
		try:
			with open(dataFile, "wb") as vFile:
				self.libraryEntry = pickle.dump(self.libraryEntry, vFile)
			BUFolders.ReleaseLock(lockFile)
		except pickle.PickleError as vError:
			BUPrint.LogErrorExc("Failed to save user library entry.", vError)
			BUFolders.ReleaseLock(lockFile)



@dataclass
class OpFeedback:
	"""
	# OPS FEEDBACK
	Class containing variable lists which hold user submitted feedback
	"""
	generic:list = field(default_factory=list)
	forSquadmates:list = field(default_factory=list)
	forSquadLead:list = field(default_factory=list)
	forPlatLead:list = field(default_factory=list)
	



@dataclass
class EventPoint():
	"""
	# EVENT POINT
	A singular point during an event
	"""
	timestamp: time = None
	users: list = field(default_factory=list)