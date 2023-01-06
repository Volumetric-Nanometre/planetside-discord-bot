from __future__ import annotations

from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime, time, timedelta
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
	WarmingUp = 10	# Warming Up: Updates the commander post with connections modal.
	Started = 20 	# Started: Ops has been started (either manually or by bot.)
	Debrief = 30	# Debrief: Pre-End stage, users are given a reactionary View to provide feedback
	Ended = 40		# Ended: User has ended Ops,  auto-cleanup.


@dataclass
class Session:
	"""
	# SESSION
	Dataclass that represents a single user session.
	"""
	bIsPS2Event: bool = True
	date: datetime = None
	duration: float = 0
	kills: int = 0
	deaths:int = 0
	assists:int = 0
	revives:int = 0
	heals:int = 0
	repairs:int = 0
	score: int = 0



@dataclass
class Participant:
	"""
	# PARTICIPANT
	Dataclass containing a reference to a `discord.Member`, and a `userLibrary.User` for a participant.
	"""
	# OBJECT REFERENCES
	discordUser : Member = None
	libraryEntry : User = None
	ps2Char : PS2Character = None
	userSession : Session = None

	# DATA
	discordID : int = 0
	bIsTracking : bool = False # Convenience bool, stays false if ps2Char is invalid/None.
	lastCheckedName : str = "" # Last Checked name: skips searching for a PS2 character if this is the same.

	def __repr__(self) -> str:
		vStr = f"PARTICIPANT: {self.discordID}\n"
		if self.ps2Char != None:
			vStr += f"	PS2 Character: {self.ps2Char}"
		if self.libraryEntry == None:
			vStr += f"	LIBRARY ENTRY NOT SET"
		else:
			vStr += f"	LIBRARY PS2 NAME: {self.libraryEntry.ps2Name}"
		if self.discordUser == None:
			vStr += f"	DISCORD USER UNSET"
		else:
			vStr += f"	DISCORD USER SET :{self.discordUser.display_name}"

		return vStr


	def LoadParticipant(self):
		"""
		# LOAD PARTICIPANT
		Loads and sets the `libraryEntry` data object representing the participant.
		"""
		dataFile = f"{Directories.userLibrary}{self.discordID}.bin"
		lockFile = BUFolders.GetLockPathGeneric(dataFile)

		
		if os.path.exists(f"{Directories.userLibrary}{self.discordID}.bin"):
			BUPrint.Debug(f"Found existing Library entry! \n{self.libraryEntry}")
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
		dataFile = f"{Directories.userLibrary}{self.discordID}.bin"
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
	userID:list[str] = field(default_factory=list) # Saved to allow users to edit their feedback.
	generic:list[str] = field(default_factory=list)
	forSquadmates:list[str] = field(default_factory=list)
	forSquadLead:list[str] = field(default_factory=list)
	forPlatLead:list[str] = field(default_factory=list)

	def SaveToFile(self, p_eventName:str):
		"""
		# SAVE TO FILE

		Saves the feedback to a file, using the event name provided.

		## Returns: 
		The filepath of the saved file.
		Or "" if saving failed.
		"""

		# Save feedback to file.
		filePath = f"{Directories.tempDir}{p_eventName}_feedback.txt"
		try:
			with open(filePath, "w") as vFile:
				vFile.write("GENERAL FEEDBACK\n")
				for line in self.generic:
					if line != "" or "\n":
						vFile.write(f"{line}\n\n")

				vFile.write("\n\nTO SQUADMATES\n")
				for line in self.forSquadmates:
					if line != "" or "\n":
						vFile.write(f"{line}\n\n")

				vFile.write("\n\nTO SQUAD LEAD\n")
				for line in self.forSquadLead:
					if line != "" or "\n":
						vFile.write(f"{line}\n\n")

				vFile.write("\n\nTO PLATOON LEAD\n")
				for line in self.forPlatLead:
					if line != "" or "\n":
						vFile.write(f"{line}\n\n")
			
			return filePath 

		except:
			BUPrint.LogError("Unable to save a the file!")
			return ""



@dataclass
class EventPoint():
	"""
	# EVENT POINT
	A singular point during an event
	"""
	timestamp: time = None
	users: list = field(default_factory=list)