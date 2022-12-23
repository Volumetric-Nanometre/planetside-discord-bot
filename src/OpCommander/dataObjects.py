from enum import Enum
from dataclasses import dataclass, field
from datetime import time, timedelta


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
class OpFeedback:
	"""
	# OPS FEEDBACK
	Class containing variable lists which hold user submitted feedback
	"""
	generic:list = field(default_factory=list)
	forSquadmates:list = field(default_factory=list)
	



@dataclass
class EventPoint():
	"""
	# EVENT POINT
	A singular point during an event
	"""
	timestamp: time = None
	users: list = field(default_factory=list)