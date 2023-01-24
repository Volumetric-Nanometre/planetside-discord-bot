"""
OP COMMANDER - EVENTS:
Deals with live ops tracking by use of events.
"""
from __future__ import annotations

from auraxium.event import EventClient, Trigger, PlayerLogin, PlayerLogout, GainExperience, VehicleDestroy
from auraxium.ps2 import Character, Vehicle, MapRegion
from auraxium.errors import ServiceUnavailableError
from auraxium import event

from datetime import datetime, timezone

from botUtils import BotPrinter as BUPrint
from botUtils import GetDiscordTime
from botData.utilityData import DateFormat

from botData.settings import ForFun, BotSettings
from botData.dataObjects import EventPoint, Participant, EventID, PS2SessionKDA, PS2SessionEngineer, PS2SessionMedic, ForFunData, ForFunVehicleDeath, FacilityData, PS2EventTotals

from random import choice


class OpsEventTracker():
	"""
	# OPS EVENT TRACKER
	A class which handles the tracking of a planetside 2 track enabled event.

	Must be passed a participant list before starting!
	"""
	def __init__(self, p_aurClient: EventClient) -> None:
		self.auraxClient = p_aurClient
		self.updateParentFunction:callable = None
		self.parentSendForFunVehicleDeath:callable = None
		self.parentReupdateTriggers:callable = None

		self.participants:list[Participant] = []
		self.triggerList:list[Trigger] = []
		self.loginTrigger : Trigger = None
		self.logOutTrigger : Trigger = None

		# LAST FACILITY DEFENDED/CAPTURED
		self.lastFacilityCaptured: FacilityData = None
		self.lastFacilityDefended: FacilityData = None
		# Session Stats, encapsulates KDA & facility capture/defense into a single dataclass.
		self.sessionStats:PS2EventTotals = PS2EventTotals()
		self.sessionStats.eventKDA = PS2SessionKDA()

		self.forFunVehicleDeaths: list[ForFunVehicleDeath] = []

		# More detailed, time set data.
		self.eventPoints: list[EventPoint] = []
		self.currentEventPoint:EventPoint = EventPoint(timestamp=datetime.now(timezone.utc), activeParticipants=self.participants.__len__())
		BUPrint.Info("Ops Event Tracker initialised!")



	def Start(self):
		"""
		# START
		Starts the tracking and locks in the participants.
		"""
		# Redundancy, the event should be closed without ever calling start if there's no participants.
		if self.participants.__len__() == 0:
			BUPrint.LogError(p_titleStr="OPS EVENT TRACKER | ", p_string="Not starting tracker, no participants!")
			return
		
		self.CreateTriggers()

		# Create KDA object.  Since every participant is capable of obtaining this; it is created for everyone, unlike the role specific objects.
		for participant in self.participants:
			participant.userSession.kda = PS2SessionKDA()
		
		
		BUPrint.Info("Full event Tracking has started!")



	async def Stop(self):
		"""# STOP
		Stops the event tracker.
		"""
		await self.auraxClient.close()



	async def CreateLoginTriggers(self, p_newParticipantList:list[Participant]):
		"""# CREATE LOGIN TRIGGERS
		Seperate from `Create Triggers` in that this is specifically for login and logout events,
		and is added to the client immediately- intended to be called from the commander after the participant list has changed.
		"""
		self.participants = p_newParticipantList
		BUPrint.Debug(f"Creating Login/Out Triggers, for :{self.participants}")

		if len(p_newParticipantList) == 0:
			BUPrint.Debug("Participant list is empty. Not creating login triggers.")
			return

		if self.loginTrigger != None:
			BUPrint.Debug("Removing old Login trigger...")
			self.auraxClient.remove_trigger(self.loginTrigger, keep_websocket_alive=True)
		
		if self.logOutTrigger != None:
			BUPrint.Debug("Removing old LogOut trigger...")
			self.auraxClient.remove_trigger(self.logOutTrigger, keep_websocket_alive=True)



		vCharList:list[int] = [participant.ps2CharID for participant in self.participants if participant.ps2CharID != -1]
		BUPrint.Debug(f"	> Character Trigger List: {vCharList}")	

		if vCharList.__len__() == 0:
			BUPrint.Debug("No Characters, not creating triggers.")
			return
		
		
		# Check status if player, incase they were already online when causing an update.
		for participant in self.participants:
			if not participant.bPS2Online and participant.ps2CharID != -1:
				character = await self.auraxClient.get_by_id(Character, participant.libraryEntry.ps2ID)
				if character != None: participant.bPS2Online = await character.is_online()

		

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
			if participant.ps2CharID == p_charID:
				participant.bPS2Online = p_isLoggedIn
				BUPrint.Debug(f"Participant: {participant.discordUser.display_name} updated.  Online [{p_isLoggedIn}]")
				await self.updateParentFunction()
				return
		BUPrint.Debug("Player Status attempted update but participant not found")



	def NewEventPoint(self):
		"""# NEW EVENT POINT
		Moves the current event point into the point list, and sets a new one.
		"""
		if self.currentEventPoint != None:
			self.eventPoints.append(self.currentEventPoint)
		
		stillOnline = [participant for participant in self.participants if participant.bPS2Online].__len__()
	
		
		self.currentEventPoint = EventPoint(timestamp=datetime.now(timezone.utc), activeParticipants=stillOnline)
		# self.currentEventPoint.timestamp = datetime.now(timezone.utc)
		# self.currentEventPoint.activeParticipants = stillOnline

		BUPrint.Debug(f"New Event Point: TimeStamp:{datetime.now(timezone.utc).time()}, Active Participants: {stillOnline}")



	def CreateTriggers(self):
		""" # CREATE TRIGGERS
		Creates and sets the triggers for the event.

		This does NOT include the login/out triggers which have their own function.
		"""
		playerCharacters = [participant.ps2CharID for participant in self.participants if participant.ps2CharID != -1]

		if len(self.participants) == 0:
			BUPrint.Debug("Empty participant list. Not creating full triggers.")
			return

		try:

			# ENGINEER
			# Squad Vehicle repairs
			for eventID in EventID.eng_vehicleRepair:
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
					event=GainExperience.filter_experience(EventID.eng_resupply)
				)
			)


			# MEDIC
			# Squad heal
			self.auraxClient.add_trigger(
				Trigger(
					action=self.MedicSquadHeal,
					characters=playerCharacters,
					event=GainExperience.filter_experience(EventID.med_heal)
				)
			)

			# Squad Revive
			self.auraxClient.add_trigger(
				Trigger(
					action=self.MedicSquadRevive,
					characters=playerCharacters,
					event=GainExperience.filter_experience(EventID.med_revive)
				)
			)		


			# NON-SPECIFIC:

			# Kill
			self.auraxClient.add_trigger(
				Trigger(
					action=self.GotKill,
					characters=playerCharacters,
					event=GainExperience.filter_experience(EventID.kill)
				)
			)
			# Assists
			self.auraxClient.add_trigger(
				Trigger(
					action=self.GotAssist,
					characters=playerCharacters,
					event=GainExperience.filter_experience(EventID.killAssist)
				)
			)
						
			# Death
			self.auraxClient.add_trigger(
				Trigger(
					action=self.Died,
					characters=playerCharacters,
					event="Death"
				)
			)

			self.auraxClient.add_trigger(
				Trigger(
					action=self.FacilityCapture,
					characters=playerCharacters,
					event="PlayerFacilityCapture"
				)
			)

			self.auraxClient.add_trigger(
				Trigger(
					action=self.FacilityDefense,
					characters=playerCharacters,
					event="PlayerFacilityDefend"
				)
			)

		except ServiceUnavailableError:
			BUPrint.LogError(p_titleStr="AURAXIUM SERVICE UNAVAILABLE", p_string="Creating scheduled task to re-run create triggers.")
			self.parentReupdateTriggers()



	def GetMatchingParticipant(self, p_playerCharID:int):
		"""
		# GET MATCHING PARTICIPANTS
		Gets the `Participant` object for the matching player character.
		
		None if not found, though this occurance shouldn't happen for events related to participants, it will occur for Deaths; when the attacker ID is not another participant. 
		"""
		for participant in self.participants:
			if participant.ps2CharID == -1:
				BUPrint.Debug(f"No PS2Char ID set for: {participant.ps2CharID}: Likely enemy.")
				return None

			BUPrint.Debug(f"Checking ID: {participant.ps2CharID} to: {p_playerCharID}")
			if participant.ps2CharID == p_playerCharID:
				return participant 
		
		return None



	async def GetForFunVehicleEvent(self, p_killerID, p_vehicleID):
		"""# GET FOR FUN VEHICLE EVENT:
		Checks existing vehicle events for a matching event and returns it if present.

		Else, create a new event, call parent function to send (sets up scheduler on first call), then return new event.
		"""
		for vehicleEvent in self.forFunVehicleDeaths:
			if vehicleEvent.driverCharID == p_killerID and vehicleEvent.driverVehicleID == p_vehicleID:
				return vehicleEvent

		# No existing event, make new one and run parent command which will post it after a delay.
		newEvent = ForFunVehicleDeath(driverCharID=p_killerID, driverVehicleID=p_vehicleID)

		self.forFunVehicleDeaths.append(newEvent)
		await self.parentSendForFunVehicleDeath(newEvent)

		return newEvent



	def SetLatestFacilityUpdate(self):
		pass

# # # # # EVENT FUNCTIONS

	def EngSquadVehicleRepair(self, p_event: event.GainExperience):
		""" # ENGINEER SQUAD VEHICLE REPAIR:
		Event function for when a player gains experience from repairing a squad vehicle.
		"""
		BUPrint.Debug("Vehicle repair!")
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
		BUPrint.Debug("Squad resupply!")
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
		BUPrint.Debug("Squad Heals!")
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
		BUPrint.Debug("Squad revive!")
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



	def GotKill(self, p_event: event.GainExperience):
		"""# GOT KILL:
		Function to run when a player has gotten a kill.

		Due to limitations, does not check if victim was an enemy or ally.  
		Death event does this instead.
		"""
		BUPrint.Debug("Player got a kill! :o")
		self.currentEventPoint.kills += 1

		vParticipant = self.GetMatchingParticipant(p_event.character_id)

		vParticipant.userSession.score += p_event.amount
		vParticipant.userSession.kda.kills += 1

		self.sessionStats.eventKDA.kills += 1
		


	async def GotAssist(self, p_event: event.GainExperience):
		"""# GOT ASSIST
		Function to run when a player gets a kill assist.  
		Infantry assists only (fornow(tm)).
		"""
		self.sessionStats.eventKDA.assists += 1
		vParticipant = self.GetMatchingParticipant(p_event.character_id)

		vParticipant.userSession.score += p_event.amount
		vParticipant.userSession.kda.assists += 1



	async def Died(self, p_event: event.Death):
		"""# DIED
		Function to run when a player died."""

		BUPrint.Debug("Player died :(")
		self.currentEventPoint.deaths += 1

		vParticipant = self.GetMatchingParticipant(p_event.character_id)
		vAttacker = self.GetMatchingParticipant(p_event.attacker_character_id)

		if vParticipant == None:
			BUPrint.Debug(f"Participant with PS2 ID: {p_event.character_id} not found")
			return


		if vParticipant.ps2CharID == p_event.attacker_character_id:
			vParticipant.userSession.kda.deathBySuicide += 1
			self.sessionStats.eventKDA.deathBySuicide += 1
		else:
			# Increment death total, to account for non-player caused deaths (pain fields) and avoid needing to caclulate later.
			vParticipant.userSession.kda.deathTotal += 1
			self.sessionStats.eventKDA.deathTotal += 1

		# Attacker is squadmate (or self).
		if vAttacker != None:
			BUPrint.Debug(f"{vParticipant.discordUser.display_name} killed by squadmate: {vAttacker.discordUser.display_name}")
			# Only add to stats if not the same person; as the relative suicide stat is already added beforehand.
			if vParticipant.ps2CharID != vAttacker.ps2CharID:
				vParticipant.userSession.kda.deathBySquad += 1
				vAttacker.userSession.kda.killedSquad += 1

			self.sessionStats.eventKDA.deathBySquad += 1
			self.sessionStats.eventKDA.killedSquad += 1

			if ForFun.bBroadcastPS2VehicleDeath or ForFun.bPS2VehicleDeathFunEvent:
				BUPrint.Debug("FFVehicle Death enabled.  Checking if participant was flying/driving!")
				if p_event.attacker_vehicle_id != 0:
					BUPrint.Debug("They were! :O")

					vFunEvent = await self.GetForFunVehicleEvent(p_event.attacker_character_id, p_event.attacker_vehicle_id)

					bIsDriver = bool(vParticipant.ps2CharID == vAttacker.ps2CharID)
					if bIsDriver:
						vFunEvent.driverMention = vParticipant.discordUser.mention

					# GALAXY:
					if p_event.attacker_vehicle_id == 11:
						
						if not bIsDriver:
							vFunEvent.killedMentions += f"{vParticipant.discordUser.mention} "
							if BotSettings.botFeatures.UserLibrary and BotSettings.botFeatures.UserLibraryFun:
								vParticipant.userSession.funEvents.append( choice(ForFunData.flightDeath).replace("_USER", vAttacker.discordUser.mention).replace("_VEHICLE", "Galaxy") )

						
						if vFunEvent.message == "":
							vFunEvent.message = choice(ForFunData.flightDeathBy).replace("_VEHICLE", "Galaxy")


					# VAKJ:
					if p_event.attacker_vehicle_id == 14:
						
						if not bIsDriver:
							vFunEvent.killedMentions += f"{vParticipant.discordUser.mention} "
							if BotSettings.botFeatures.UserLibrary and BotSettings.botFeatures.UserLibraryFun:
								vParticipant.userSession.funEvents.append( choice(ForFunData.flightDeath).replace("_USER", vAttacker.discordUser.mention).replace("_VEHICLE", "Valkyrie") )

						
						if vFunEvent.message == "":
							vFunEvent.message = choice(ForFunData.flightDeathBy).replace("_VEHICLE", "Valkryrie")
						



					# SUNDERER
					elif p_event.attacker_vehicle_id == 2:
						if not bIsDriver:
							vFunEvent.killedMentions += f"{vParticipant.discordUser.mention} "
							if BotSettings.botFeatures.UserLibrary and BotSettings.botFeatures.UserLibraryFun:
								vParticipant.userSession.funEvents.append( choice(ForFunData.partyBusDeath).replace("_USER", vAttacker.discordUser.mention) )

						if vFunEvent.message == "":
							vFunEvent.message = choice(ForFunData.partyBusDeathBy)

					else:
						BUPrint.Debug(f"Vehicle ID was {p_event.attacker_vehicle_id}")

			# End of: Attacker != None
			return


		# Determine if killer character is allied or an enemy.
		vAttackerPS2Char = await self.auraxClient.get_by_id(type_=Character, id_=p_event.attacker_character_id)
		if vAttackerPS2Char.faction_id == 2: # NC
			vParticipant.userSession.kda.deathByAllies += 1
			self.sessionStats.eventKDA.deathByAllies += 1
		else:
			vParticipant.userSession.kda.deathByEnemies += 1
			self.sessionStats.eventKDA.deathByEnemies += 1

		# Potential to do enemy character death by name fun events here.



	async def FacilityCapture(self, p_event: event.PlayerFacilityCapture):
		"""# FACILITY CAPTURE
		Function to call when a player participates in a facility capture."""
		vFacility = await MapRegion.get_by_facility_id(facility_id=p_event.facility_id, client=self.auraxClient)
		# BUPrint.Debug(f"Facility ID: {p_event.facility_id} | Resulted MapRegion: {vFacility}")

		if vFacility == None:
			vFacility = await self.auraxClient.get_by_id(MapRegion, p_event.facility_id)

			# Account for when the client decides to give an empty object despite having a correct ID.
			if vFacility == None and self.lastFacilityCaptured.facilityID == -999:
				self.lastFacilityCaptured.participants += 1
			elif vFacility == None:
				self.lastFacilityCaptured.facilityID = -999
				self.lastFacilityCaptured.facilityObj = None
				self.lastFacilityCaptured.timestamp = datetime.utcnow()
				return


		# First facility capture.
		if self.lastFacilityCaptured == None:
			self.NewFacilityCapture(vFacility)
			return

				
		# Existing/Current facility capture.  Ensures repeated calls (from each character) don't inflate the stats.
		# Also ensures if the facility captured is the last one captured and is being recaptured it's still counted.
		if self.lastFacilityCaptured.facilityID == p_event.facility_id:
			timeDifference = self.lastFacilityCaptured.timestamp - datetime.now()
			if  timeDifference.total_seconds() > 900: # 15 minutes
				BUPrint.Debug("Time difference is greater than 15 minutes.  Recaptured last capture.")
				self.NewFacilityCapture(vFacility)
				await self.updateParentFunction()
				return

			else: # Not new facility capture; nth call from each character.
				BUPrint.Debug("Adding participant to facility capture.")
				self.lastFacilityCaptured.participants += 1
				return

		
		# If reached here, facility ID doesn't match last facility ID, thus is a new capture!
		BUPrint.Debug("New Facility Capture!")
		self.NewFacilityCapture(vFacility)
		await self.updateParentFunction()


	def NewFacilityCapture(self, p_facility:MapRegion):
		"""# NEW FACILITY CAPTURE
		Convenience function for new facility capture to avoid repetition.
		"""
		vNewFacilityData = None
		bFacilityNotFound = False

		if p_facility == None:
			BUPrint.Debug("Client failed to find matching facility.")
			bFacilityNotFound= True
			# Make fake data:
			vNewFacilityData = FacilityData(
				facilityID=-999,
				timestamp=datetime.utcnow(),
				participants=1
			)
		else:
			vNewFacilityData = FacilityData(
					facilityID=p_facility.id, 
					timestamp=datetime.now(tz=timezone.utc),
					facilityObj = p_facility,
					participants=1
				)
		self.lastFacilityCaptured = vNewFacilityData

		if bFacilityNotFound:
			self.sessionStats.facilityFeed.append( f" {GetDiscordTime(vNewFacilityData.timestamp, DateFormat.TimeShorthand)} | **CAPTURED** | *FacilityLookupFailed* | {p_facility.facility_type}" )
		else:
			self.sessionStats.facilityFeed.append( f" {GetDiscordTime(vNewFacilityData.timestamp, DateFormat.TimeShorthand)} | **CAPTURED** | {p_facility.facility_name} | {p_facility.facility_type}" )
		self.currentEventPoint.captured += 1
		self.sessionStats.facilitiesCaptured += 1


	async def FacilityDefense(self, p_event: event.PlayerFacilityDefend):
		"""# FACILITY DEFENSE
		Function to call when a player participates in a facility defense."""
		vFacility:MapRegion = await MapRegion.get_by_facility_id(facility_id=p_event.facility_id, client=self.auraxClient)

		if vFacility == None:
			vFacility = await self.auraxClient.get_by_id(FacilityData, p_event.facility_id)

		# First facility capture.
		if self.lastFacilityDefended == None:
			self.NewFacilityDefense(vFacility)
			return

				
		# Existing/Current facility Defense.  Ensures repeated calls (from each character) don't inflate the stats.
		# Also ensures if the facility defended is the last one captured and is being redefended it's still counted.
		if self.lastFacilityDefended.facilityID == p_event.facility_id:
			timeDifference = self.lastFacilityDefended.timestamp - datetime.now()
			if  timeDifference.total_seconds() > 900: # 15 minutes
				BUPrint.Debug("Time difference is greater than 15 minutes.  Recaptured last capture.")
				self.NewFacilityDefense(vFacility)
				await self.updateParentFunction()
				return

			else: # Not new facility defense; nth call from each character.
				BUPrint.Debug("Not new defense, adding participant to last facility defended.")
				self.lastFacilityDefended.participants += 1
				return

		
		# If reached here, facility ID doesn't match last facility ID, thus is a new defense!
		BUPrint.Debug("New Facility Defense!")
		self.NewFacilityDefense(vFacility)
		await self.updateParentFunction()


	def NewFacilityDefense(self, p_facility:MapRegion):
		"""# NEW FACILITY DEFENSE
		Convenience function for new facility capture to avoid repetition.
		"""
		vNewFacilityData = None
		bFacilityNotFound = False

		if p_facility == None:
			BUPrint.Debug("Client failed to find matching facility.")
			bFacilityNotFound = True
			# Make fake data:
			vNewFacilityData = FacilityData(
				facilityID=-999,
				timestamp=datetime.utcnow(),
				participants=1
			)
		else:
			vNewFacilityData = FacilityData(
					facilityID=p_facility.id, 
					timestamp=datetime.now(tz=timezone.utc),
					facilityObj = p_facility,
					participants=1
				)

		self.lastFacilityDefended = vNewFacilityData

		if bFacilityNotFound:
			self.sessionStats.facilityFeed.append( f" {GetDiscordTime(vNewFacilityData.timestamp, DateFormat.TimeShorthand)} | **DEFENDED** | *FacilityLookupFailed* | {p_facility.facility_type}" )
		else:
			self.sessionStats.facilityFeed.append( f" {GetDiscordTime(vNewFacilityData.timestamp, DateFormat.TimeShorthand)} | **DEFENDED** | {p_facility.facility_name} | {p_facility.facility_type}" )
		self.currentEventPoint.defended += 1
		self.sessionStats.facilitiesDefended += 1