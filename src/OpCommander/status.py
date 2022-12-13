from enum import Enum

class CommanderStatus(Enum):
	Init = -10		# Init: Commander has been created.
	Standby = 0 	# Standby: Commander has been posted and waiting.
	Prep = 10 		# Prep: Ops has started 30 minute prior Prep (either manually or by bot)
	Started = 20 	# Started: Ops has been started (either manually or by bot.)
	Debrief = 30	# Debrief: Pre-End stage, users are given a reactionary View to provide feedback
	Ended = 40		# Ended: User has ended Ops,  auto-cleanup.