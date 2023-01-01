from enum import Enum
from dataclasses import dataclass, field
import datetime


@dataclass
class User:
	"""
	# USER
	Data object representing a user on the discord.
	"""
	discordID: int = -1

	# Users PS2 Character Name
	ps2Name: str = ""
	# Users PS2 Character Outfit
	ps2Outfit: str = ""
	# Users PS2 Char Outfit Rank, if applicable.
	ps2OutfitRank: str = ""

	# Tracked Sessions
	sessions :list = field(default_factory=list)
	
	# Number of events attended.
	eventsAttended = 0

	# Number of events the user signed up to, and wasn't present for.
	eventsMissed = 0
	
	# Users birthday.
	birthday:datetime = None

	# User provided "about" text.
	aboutMe = ""