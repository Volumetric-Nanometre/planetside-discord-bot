"""
OP COMMANDER - EVENTS:
Deals with live ops tracking by use of events.
"""
from __future__ import annotations

from auraxium.event import EventClient, Trigger, Event, PlayerLogin, PlayerLogout, GainExperience
from auraxium import event

from datetime import datetime, timezone

from botUtils import BotPrinter as BUPrint
from botData.dataObjects import EventPoint, Participant, EventID

class OpsEventTracker():
	"""
	# OPS EVENT TRACKER
	A class which handles the tracking of a planetside 2 track enabled event.

	Must be passed a participant list before starting.
	"""
	def __init__(self, p_aurClient: EventClient) -> None:
		self.auraxClient = p_aurClient
		self.updateParentFunction: function = None
		

		self.participants:list[Participant] = []
		self.triggerList:list[Trigger] = []
		self.loginTrigger : Trigger = None
		self.logOutTrigger : Trigger = None

		self.eventPoints: list[EventPoint] = []
		self.currentEventPoint:EventPoint = None
		BUPrint.Info("Ops Event Tracker initialised!")



	def Start(self):
		"""
		# START
		Starts the tracking.
		"""
		self.CreateTriggers()
		self.currentEventPoint = EventPoint( timestamp=datetime.now(timezone.utc).time(), activeParticipants=len(self.participants) )
		BUPrint.Info("Full event Tracking has started!")



	async def Stop(self):
		"""# STOP
		Stops the event tracker.
		"""
		self.ClearTriggers()
		await self.auraxClient.close()



	def CreateLoginTrigger(self):
		"""# CREATE LOGIN TRIGGER
		Seperate from `Create Triggers` in that this is specifically for login and logout events,
		and is added to the client immediately- intended to be called from the commander after the participant list has changed.
		"""

		BUPrint.Debug("Creating Login/Out Triggers")

		if self.loginTrigger != None:
			BUPrint.Debug("Removing old Login trigger...")
			self.auraxClient.remove_trigger(self.loginTrigger, keep_websocket_alive=True)
		
		if self.logOutTrigger != None:
			BUPrint.Debug("Removing old LogOut trigger...")
			self.auraxClient.remove_trigger(self.logOutTrigger, keep_websocket_alive=True)


		vCharList = []
		for participant in self.participants:
			if participant.ps2Char != None:
				BUPrint.Debug(f"	> {participant.ps2Char} added to trigger character list.")
				vCharList.append(participant.ps2Char)

		# Create new Login & Logout trigger
		self.loginTrigger = Trigger( event=PlayerLogin, characters=vCharList, action=self.UpdatePlayerLogin)
		self.logOutTrigger = Trigger( event=PlayerLogout, characters=vCharList, action=self.UpdatePlayerLogout)

		self.auraxClient.add_trigger( self.loginTrigger )

		self.auraxClient.add_trigger( self.logOutTrigger )



	async def UpdatePlayerLogin(self, p_loginEvent: PlayerLogin):
		await self.UpdatePlayerStatus(p_loginEvent.character_id, True)



	async def UpdatePlayerLogout(self, p_logoutEvent: PlayerLogout):
		await self.UpdatePlayerStatus(p_logoutEvent.character_id, False)




	async def UpdatePlayerStatus(self, p_charID:int, p_isLoggedIn:bool):
		"""# UPDATE PLAYER STATUS
		Since Login and Logout are individual events,
		this is a convenience function to be called from the respective individual functions.
		"""
		for participant in self.participants:
			if participant.ps2Char.id == p_charID:
				participant.bPS2Online = p_isLoggedIn
				BUPrint.Debug(f"Participant: {participant.discordUser.display_name} updated.  Online [{p_isLoggedIn}]")
				await self.updateParentFunction()
				return
		BUPrint.Debug("Player Status attempted update but participant not found")



	def NewEventPoint(self):
		"""# NEW EVENT POINT
		Moves the current event point into the point list, and sets a new one.
		"""
		self.eventPoints.append(self.currentEventPoint)
		stillOnline = 0
		for participant in self.participants:
			if participant.bPS2Online:
				stillOnline += 1
		self.currentEventPoint = EventPoint(timestamp=datetime.now(timezone.utc).time(), activeParticipants=len(self.participants))




	def CreateTriggers(self):
		""" # CREATE TRIGGERS
		Creates and sets the triggers for the event.

		This does not add them.
		"""
		playerCharacters = []
		triggerList = []
		eventIDs = EventID

		# eventIDs = [
		# 4, # Medic Squad Heal
		# 53, # Medic Squad Revive

		# 142, #eng_maxRepair

		# # Vehicle repairs:
		# 28, 129, 132, 133, 134, 138, 140, 141, 302, 505, 656,
		
		# 55 # Resupply
		# ]

		# Iterate through participants to get their PS2Char objects.
		for participant in self.participants:
			if participant.ps2Char != None:
				playerCharacters.append(participant.ps2Char)

		# User Logins
		triggerList.append(
			Trigger(action=self.updateParentFunction,
					characters=playerCharacters,
					event=event.PlayerLogin
			)
		)

		triggerList.append(
			Trigger(action=self.updateParentFunction,
					characters=playerCharacters,
					event=event.PlayerLogout
			)
		)



		# ENGINEER

		for eventID in eventIDs.eng_vehicleRepair:
			triggerList.append(
				Trigger(
					action=function,
					characters=playerCharacters,
					event=GainExperience.filter_experience(eventID)
				)
			)

		for triggerToAdd in triggerList:
			self.auraxClient.add_trigger(triggerToAdd)

	



	def ClearTriggers(self):
		"""# CLEAR TRIGGERS
		Removes the triggers from the client.  Unless a manually created trigger has been added elsewhere, this should close the client connection.
		"""
		BUPrint.Debug("Clearing all triggers...")
		for triggerToRemove in self.triggerList:
			self.auraxClient.remove_trigger(triggerToRemove)
		
		self.auraxClient.remove_trigger(self.loginTrigger)
		self.auraxClient.remove_trigger(self.logOutTrigger)




	def GetMatchingParticipant(self, p_playerCharID:int):
		"""
		# GET MATCHING PARTICIPANTS
		Gets the `Participant` object for the matching player character.
		
		None if not found, though this occurance shouldn't happen. 
		"""
		for participant in self.participants:
			if participant.ps2Char.id == p_playerCharID:
				return participant 
		return None

# # # # # EVENT FUNCTIONS

	# def PlayerDeath(self, )