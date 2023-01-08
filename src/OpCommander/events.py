"""
OP COMMANDER - EVENTS:
Deals with live ops tracking by use of events.
"""
from __future__ import annotations

from auraxium.event import EventClient, Trigger

from botUtils import BotPrinter as BUPrint
from botData.dataObjects import EventPoint

class OpsEventTracker():
	def __init__(self, p_aurClient: EventClient) -> None:
		self.auraxClient = p_aurClient
		self.triggerList:list[Trigger] = []
		eventPoints: list[EventPoint]
		BUPrint.Info("Ops Event Tracker initialised!")

	def Start(self):
		"""
		# START
		Starts the tracking.
		"""
		pass
		# self.auraxClient.add_trigger()


	def CreateTriggers(self):
		""" # CREATE TRIGGERS
		Creates and sets the triggers for the event.

		This does not add them.
		"""

		# 


	
	def AddAllTriggers(self):
		""" # ADD ALL TRIGGERS
		Adds all the triggers in the list to the event stream client.
		"""
		for triggerToAdd in self.triggerList:
			self.auraxClient.add_trigger(triggerToAdd)


	def ClearTriggers(self):
		"""# CLEAR TRIGGERS
		Removes the triggers from the client.  Unless a manually created trigger has been added elsewhere, this should close the client connection.
		"""
		BUPrint.Debug("Clearing all triggers...")
		for triggerToRemove in self.triggerList:
			self.auraxClient.remove_trigger(triggerToRemove)


	async def Stop(self):
		"""# STOP
		Stops the event tracker.
		"""
		self.ClearTriggers()
		await self.auraxClient.close()


