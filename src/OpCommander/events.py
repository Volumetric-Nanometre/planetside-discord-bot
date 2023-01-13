"""
OP COMMANDER - EVENTS:
Deals with live ops tracking by use of events.
"""
from __future__ import annotations

from auraxium.event import EventClient, Trigger, Event, PlayerLogin, PlayerLogout, GainExperience
from auraxium.ps2 import Character
from auraxium import event

from datetime import datetime, timezone

from botUtils import BotPrinter as BUPrint
from botData.dataObjects import EventPoint, Participant, EventID, PS2SessionKDA, PS2SessionEngineer, PS2SessionMedic

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
		Starts the tracking and locks in the participants.
		"""
		self.CreateTriggers()
		self.currentEventPoint = EventPoint( timestamp=datetime.now(timezone.utc).time(), activeParticipants=len(self.participants) )
		
		
		BUPrint.Info("Full event Tracking has started!")



	async def Stop(self):
		"""# STOP
		Stops the event tracker.
		"""
		await self.auraxClient.close()



	async def CreateLoginTriggers(self):
		"""# CREATE LOGIN TRIGGERS
		Seperate from `Create Triggers` in that this is specifically for login and logout events,
		and is added to the client immediately- intended to be called from the commander after the participant list has changed.
		"""

		BUPrint.Debug(f"Creating Login/Out Triggers, for :{self.participants}")

		if self.loginTrigger != None:
			BUPrint.Debug("Removing old Login trigger...")
			self.auraxClient.remove_trigger(self.loginTrigger, keep_websocket_alive=True)
		
		if self.logOutTrigger != None:
			BUPrint.Debug("Removing old LogOut trigger...")
			self.auraxClient.remove_trigger(self.logOutTrigger, keep_websocket_alive=True)

		if len(self.participants) == 0:
			BUPrint.Debug("Participant list is empty. Not creating login triggers.")
			return

		vCharList:list[int] = []
		for participant in self.participants:
			if participant.ps2Char != None:
				BUPrint.Debug(f"	> {participant.ps2Char} added to trigger character list.")
				vCharList.append(participant.ps2Char.id)

				# Check status if player, incase they were already online when causing an update.
				if not participant.bPS2Online:
					participant.bPS2Online = await participant.ps2Char.is_online()

		

		# Create new Login & Logout trigger
		self.loginTrigger = Trigger( event="PlayerLogin", characters=vCharList, action=self.UpdatePlayerLogin)
		self.logOutTrigger = Trigger( event="PlayerLogout", characters=vCharList, action=self.UpdatePlayerLogout)

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
		"""
		playerCharacters = []
		eventIDs = EventID

		if len(self.participants) == 0:
			BUPrint.Debug("Empty participant list. Not creating full triggers.")
			return

		# Iterate through participants to get their PS2Char objects.
		for participant in self.participants:
			if participant.ps2Char != None:
				playerCharacters.append(participant.ps2Char.id)



		# ENGINEER
		# Squad Vehicle repairs
		for eventID in eventIDs.eng_vehicleRepair:
			self.auraxClient.add_trigger(
				Trigger(
					action=self.EngSquadVehicleRepair,
					characters=playerCharacters,
					event=GainExperience.filter_experience(eventID)
				)
			)

		# Squad Resupply
		self.auraxClient.add_trigger(
			Trigger(
				action=self.EngSquadResupply,
				characters=playerCharacters,
				event=GainExperience.filter_experience(eventIDs.eng_resupply)
			)
		)


		# MEDIC
		# Squad heal
		self.auraxClient.add_trigger(
			Trigger(
				action=self.MedicSquadHeal,
				characters=playerCharacters,
				event=GainExperience.filter_experience(eventIDs.med_heal)
			)
		)

		# Squad Revive
		self.auraxClient.add_trigger(
			Trigger(
				action=self.MedicSquadRevive,
				characters=playerCharacters,
				event=GainExperience.filter_experience(eventIDs.med_revive)
			)
		)		






	def GetMatchingParticipant(self, p_playerCharID:int):
		"""
		# GET MATCHING PARTICIPANTS
		Gets the `Participant` object for the matching player character.
		
		None if not found, though this occurance shouldn't happen. 
		"""
		for participant in self.participants:
			if participant.ps2Char.id == p_playerCharID:
				return participant 
		
		BUPrint.LogError(p_titleStr="Invalid participant given")
		return None

# # # # # EVENT FUNCTIONS

	# def PlayerDeath(self, )

	def EngSquadVehicleRepair(self, p_event: event.GainExperience):
		""" # ENGINEER SQUAD VEHICLE REPAIR:
		Event function for when a player gains experience from repairing a squad vehicle.
		"""
		vParticipant = self.GetMatchingParticipant(p_event.character_id)
		
		if vParticipant == None:
			return

		if vParticipant.userSession.engineerData == None:
			vParticipant.userSession.engineerData = PS2SessionEngineer()

		# Set operatons Event Point:
		self.currentEventPoint.repairs += p_event.amount
		
		# Set participants data:
		vParticipant.userSession.engineerData.repairScore += p_event.amount

	

	def EngSquadResupply(self, p_event: event.GainExperience):
		""" # ENGINEER SQUAD RESUPPLY:
		Event function for when a player gains experience from repairing a squad vehicle.
		"""
		vParticipant = self.GetMatchingParticipant(p_event.character_id)
		
		if vParticipant == None:
			return

		if vParticipant.userSession.engineerData == None:
			vParticipant.userSession.engineerData = PS2SessionEngineer()

		# Set operatons Event Point:  (none)
		# self.currentEventPoint.resupply += p_event.amount
		
		# Set participants data:
		vParticipant.userSession.engineerData.resupplyScore += p_event.amount



	def MedicSquadHeal(self, p_event: event.GainExperience):
		"""# MEDIC SQUAD HEAL
		Event function for when a player gains experience from healing a squadmate.
		"""
		vParticipant = self.GetMatchingParticipant(p_event.character_id)
		
		if vParticipant == None:
			return

		if vParticipant.userSession.medicData == None:
			vParticipant.userSession.medicData = PS2SessionMedic()

		# Set operatons Event Point: (None)
		# self.currentEventPoint.revives += p_event.amount
		
		# Set participants data:
		vParticipant.userSession.medicData.heals += p_event.amount


	def MedicSquadRevive(self, p_event: event.GainExperience):
		"""# MEDIC SQUAD REVIVE
		Event function for when a player gains experience from reviving a squadmate.
		"""
		vParticipant = self.GetMatchingParticipant(p_event.character_id)
		
		if vParticipant == None:
			return

		if vParticipant.userSession.medicData == None:
			vParticipant.userSession.medicData = PS2SessionMedic()

		# Set operatons Event Point:
		self.currentEventPoint.revives += 1
		
		# Set participants data:
		vParticipant.userSession.medicData.revives += 1
		vParticipant.userSession.score += p_event.amount