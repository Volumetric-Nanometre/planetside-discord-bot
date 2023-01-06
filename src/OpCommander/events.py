"""
OP COMMANDER - EVENTS:
Deals with live ops tracking by use of events.
"""
import auraxium
from auraxium.event import EventClient, Trigger

from botUtils import BotPrinter as BUPrint
import OpCommander.dataObjects

class OpsEventTracker():
	def __init__(self, p_aurClient: auraxium.EventClient) -> None:
		self.auraxClient = p_aurClient
		BUPrint.Info("Ops Event Tracker initialised!")

	def Start(self):
		"""
		# START
		Starts the tracking.
		"""
		pass
		# self.auraxClient.add_trigger()
