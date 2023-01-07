# Similar to DataObjects, but specifically for Utility data objects.
from enum import Enum
import botUtils
from discord import Colour

class EmojiLibrary(Enum):
	# Infantry Classes
	ICON_LA  = "<:Icon_Light_Assault:795726936759468093>"
	ICON_HA  = "<:Icon_Heavy_Assault:795726910344003605>"
	ICON_ENG = "<:Icon_Engineer:795726888763916349>"
	ICON_MED = "<:Icon_Combat_Medic:795726867960692806>"
	ICON_INF = "<:Icon_Infiltrator:795726922264215612>"
	ICON_MAX = "<:Icon_MAX:795726948365631559>"
	# Ground Vehicles
	ICON_ANT  = "<:Icon_ANT:795727784239824896>"
	ICON_MBT  = "<:Icon_Vanguard:795727955896565781>"
	ICON_TANK = "<:Icon_Lightning:795727852875677776>"
	ICON_HAR  = "<:Icon_Harasser:795727814220840970>"
	ICON_SUN  = "<:Icon_Sunderer:795727911549272104>"
	# Air Vehicles
	ICON_VAL = "<:Icon_Valkyrie:795727937735098388>"
	ICON_GAL = "<:Icon_Galaxy:795727799591239760>"
	ICON_LIB = "<:Icon_Liberator:795727831605837874>"
	ICON_REA = "<:Icon_Reaver:795727893342846986>"
	ICON_DER = "<:Icon_Dervish:861303237062950942>"
	ICON_BAS = "<:Icon_Bastion:861304226957361162>"
	# OTHER
	ICON_GUNNER = "<:Icon_Infiltrator:795726922264215612>"

	def ParseStringToEmoji(p_str:str):
		"""
		# PARSE STRING TO EMOJI
		Returns the value of a given emoji name.
		"""
		for emote in EmojiLibrary:
			if emote.name == p_str.upper():
				botUtils.BotPrinter.Debug(f"Emoji {p_str} found in library!")
				return emote.value
		botUtils.BotPrinter.Debug(f"Name {p_str} does not match a emoji library entry.")
		return "-" # Return the default "blank" so nothing breaks!


class DateFormat(Enum):
	"""
	DATE FORMAT
	Used within discord timeformat string to change how a POSIX datetime is displayed.
	"""
	Dynamic = ":R" # Dyanmically changes to most appropriate smallest stamp (in X days, in X hours, in x seconds)
	DateShorthand = ":d" # dd/mm/year
	DateLonghand = ":D" # 00 Month Year
	TimeShorthand = ":t" # Hour:Minute
	TimeLonghand = ":T" # Hour:Minute:Seconds
	DateTimeShort = ":f" # Full date, no day.
	DateTimeLong = ":F" # Full date, includes Day
	Raw = "" # Raw POSIX.


class Colours(Enum):
	"""
	# COLOURS:
	Enum class of colours for use with discord objects.
	"""
	openSignup = Colour.from_rgb(0,244,0)
	opsStarting = Colour.from_rgb(150, 0, 0)
	opsStarted = Colour.from_rgb(255,0,0)
	editing = Colour.from_rgb(204, 102, 0)
	commander = Colour.from_rgb(0, 255, 360)
	userRequest = Colour.from_rgb(106, 77, 255)
	userWarnOkay = Colour.from_rgb(170, 255, 0)
	userWarning = Colour.from_rgb(255, 85, 0)



class ConsoleStyles:
	"""
	# CONSOLE STYLES
	Class specifically for holding values for setting console formatting & colours.
	"""
	reset = "\033[0m"
	bold = "\033[1m"
	dim = "\033[2m"
	colourWarn = "\033[31m"
	ColourInfo = "\033[37m"
	timeStyle = dim + ColourInfo