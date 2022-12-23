"""
OP COMMANDER - EVENTS:
Deals with live ops tracking by use of events.
"""
import auraxium

from botUtils import BotPrinter as BUPrint
import OpCommander.dataObjects

class OpsEventTracker():
	def __init__(self, p_aurClient: auraxium.EventClient) -> None:
		self.auraxClient = p_aurClient
		BUPrint.Info("Ops Event Tracker initialised!")

	