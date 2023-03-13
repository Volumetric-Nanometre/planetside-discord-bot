# Similar to DataObjects, but specifically for Utility data objects.
from enum import Enum
import botUtils
from discord import Colour

class EmojiLibrary(Enum):
	# Infantry Classes
	ICON_LA  = "<:LA:1078709307337617438>"
	ICON_HA  = "<:ha:1078709302333808750>"
	ICON_ENG = "<:eng:1078709299834011658>"
	ICON_MED = "<:medic:1078709312223985695>"
	ICON_INF = "<:infil:1078709305324359780>"
	ICON_MAX = "<:max:1078709310890184756>"
	# Ground Vehicles
	ICON_ANT  = "<:ant:1078709244209139712>"
	ICON_MBT  = "<:vanguard:1078709313855557802>"
	ICON_TANK = "<:lightning:1078709308906287146>"
	ICON_HAR  = "<:harasser:1078709303906685018>"
	ICON_SUN  = "<:sunderer:1078711388194738297>"
	# Air Vehicles
	ICON_VAL = "<:valk:1078712140304744489>"
	ICON_GAL = "<:gal:1078712136559243315>"
	ICON_LIB = "<:lib:1078712393376477265>"
	ICON_REA = "<:reaver:1078712137830117436>"
	ICON_DER = "<:derv:1078712135061868554>"
	ICON_BAS = "<:bastion:1078712132499165264>"
	# OTHER
	ICON_GUNNER = "<:infil:1078709305324359780>"

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



class PS2ZoneIDs(Enum):
	""" PS2 Zone IDS
	Convenience Enum to hold zone (continent) IDs
	"""
	IndarID: int = 2
	HossinID: int = 4
	AmerishID: int = 6
	EsamirID: int = 8
	OshurID: int = 344

	allIDs = [
		IndarID,
		HossinID,
		AmerishID,
		EsamirID,
		OshurID
		]
	

class PS2WarpgateIDs(Enum):
	""" # PS2 Warpgate IDs
	Convenience class to hold the `FACILITY ID`s of each continents warpgates. """

	indar = [7801, 120000, 4801]
	hossin = [308000, 309000, 310000]
	amerish = [200000, 201000, 203000]
	esamir = [258000, 259000, 260000]
	oshur = [400369, 400370, 400371]
	allIDs = indar + hossin + amerish + esamir + oshur
