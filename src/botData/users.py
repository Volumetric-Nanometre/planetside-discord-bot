from __future__ import annotations

from enum import Enum
from dataclasses import dataclass, field
import datetime
from dateutil.relativedelta import relativedelta


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




@dataclass(frozen=True)
class AutoPromoteRule():
	"""
	# AUTO PROMOTE RULE
	Contains values pertaining to the rules a user must meet before auto-promotion from recruit.

	This should be obtained from `botData.settings`!
	"""
	# Attended Minimum Events: the number of events a user must participate in
	bAttendedMinimumEvents: bool
	bEventsMustBePS2: bool
	minimumEvents: int

	# Length of time a user must be in the outfit.
	bInOutfitForDuration: bool
	outfitDuration: datetime.time

	# Length of time a user must have been in the discord server.
	bInDiscordForDuration: bool
	discordDuration: datetime.time


	def __repr__(self) -> str:
		vString = f"\n		> Attend Minimum Events: {self.bAttendedMinimumEvents} ({self.minimumEvents})\n"
		vString += f"		> Events must be Planetside 2: {self.bEventsMustBePS2}\n"
		vString += f"		> In Outfit for Duration: {self.bInOutfitForDuration} | {self.outfitDuration}\n"
		vString += f"		> In Discord for Duration: {self.bInDiscordForDuration} | {self.discordDuration}\n"

		return vString




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
	# Joindate of Ps2 outfit
	ps2OutfitJoinDate: datetime.datetime = None

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

