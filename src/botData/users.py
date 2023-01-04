from enum import Enum
from dataclasses import dataclass, field
import datetime


@dataclass
class UserSettings:
	"""
	# USER SETTINGS
	Settings pertaining to the User data object.
	"""
	bLockPS2Char = False
	bLockAbout = False
	bTrackHistory = True

	def __repr__(self) -> str:
		vStr = f"	> Lock PS2 Character:	{self.bLockPS2Char}\n"
		vStr += f"	> Lock About:		{self.bLockAbout}\n"
		vStr += f"	> Track History:	{self.bTrackHistory}\n"

		return vStr


@dataclass
class User:
	"""
	# USER (UserLibrary)
	Data object representing a user on the discord.  
	
	Contains their planetside2 character information, and tracked event sessions.
	"""
	discordID: int = -1

	# Users PS2 Character Name
	ps2Name: str = ""
	# Users PS2 Character Outfit
	ps2Outfit: str = ""
	# Users PS2 Char Outfit Rank, if applicable.
	ps2OutfitRank: str = ""

	# Used alongside auto-promote; this is set by newUser or manually.
	bIsRecruit = False

	# Tracked Sessions
	sessions :list = field(default_factory=list)
	
	# Number of events attended.
	eventsAttended = 0

	# Number of events the user signed up to, and wasn't present for.
	eventsMissed = 0
	
	# Users birthday.
	birthday:datetime.datetime = None

	# User provided "about" text.
	aboutMe = ""

	# About loaded from a seperate file, editable only by admins.
	specialAbout = ""

	# Settings object.
	settings: UserSettings = field(default_factory=UserSettings)

