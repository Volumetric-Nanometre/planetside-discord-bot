"""# PS2 Continent Tracker

Handles tracking and displaying information of continent changes for a specified world.


"""

from botData.settings import BotSettings, ContinentTrack, Channels, CommandLimit
from botData.dataObjects import CommanderStatus, WarpgateCapture, ContinentStatus
from botUtils import BotPrinter as BUPrint
from botUtils import GetDiscordTime, UserHasCommandPerms
from botData.utilityData import PS2ZoneIDs, PS2WarpgateIDs
from discord.ext.commands import GroupCog, Bot
from discord.app_commands import command
from discord import Interaction
from auraxium.event import EventClient, ContinentLock, Trigger, FacilityControl
from auraxium.ps2 import Zone, World
from opsManager import OperationManager

class ContinentTrackerCog(GroupCog, name="continents"):
	def __init__(self, p_bot:Bot):
		self.botRef = p_bot
		self.auraxClient = EventClient(service_id=BotSettings.ps2ServiceID)

		self.warpgateCaptures:list[WarpgateCapture] = []
		"""Warpgate Captures
		List of warpgate capture objects.
		Should be cleared after determining continent un/lock."""

		# Continent Locks
		self.lastOshurLock: ContinentLock = None
		self.lastIndarLock: ContinentLock = None
		self.lastEsamirLock: ContinentLock = None
		self.lastAmerishLock: ContinentLock = None
		self.lastHossinLock: ContinentLock = None

		# Continent Statuses
		self.indarStatus = ContinentStatus("Indar)")
		self.oshurStatus = ContinentStatus("Oshur")
		self.esamirStatus = ContinentStatus("Esamir")
		self.amerishStatus = ContinentStatus("Amerish")
		self.hossinStatus = ContinentStatus("Hossin")

		super().__init__()
		BUPrint.Info("COG: ContinentTracker loaded.")


	@command(name="oldest", description="Posts the oldest locked continent lock.")
	async def GetOldestContinentLock(self, p_interaction:Interaction):
		# HARDCODED ROLE USEAGE:
		if not await UserHasCommandPerms(p_interaction.user, (CommandLimit.continentTracker), p_interaction):
			return

		await self.PostMessage_Oldest(p_interaction)


	@command(name="locks", description="Posts all continent lock timestamps.")
	async def GetAllContinentLocks(self, p_interaction:Interaction):
		# HARDCODED ROLE USEAGE:
		if not await UserHasCommandPerms(p_interaction.user, (CommandLimit.continentTracker), p_interaction):
			return

		await self.PostMessage_Sorted(p_interaction)



	def GetContLocksAsArray(self) -> list[ContinentStatus]:
		"""# Get Continent Locks as Array
		Returns all the continent locks as an array.  
		Does not include the cont lock if it's not yet set.
		"""
		allConts = [
			self.amerishStatus,
			self.indarStatus,
			self.oshurStatus,
			self.esamirStatus,
			self.hossinStatus
		]

		newArray = [status for status in allConts if status.lastLocked != None]
		
		return newArray



	async def CreateTriggers(self):
		"""# Create Triggers
		Sets up the triggers to monitor """
		worldToMonitor = await self.auraxClient.get_by_id(World, ContinentTrack.worldID)

		if worldToMonitor == None:
			BUPrint.LogError("Nop", "NO WORLD")

		self.auraxClient.add_trigger( 
			Trigger(
				event="ContinentLock",
				# worlds=[worldToMonitor],
				action=self.NewContinentLock
			)
		)


		self.auraxClient.add_trigger(
			Trigger(
				event="FacilityControl",
				# worlds=[worldToMonitor],
				action=self.FacilityControlChange
			)
		)


	async def NewContinentLock(self, p_event:ContinentLock):
		"""# New Continent Lock
		Called when a continent has been locked.
		"""
		continent:Zone = await self.auraxClient.get_by_id(Zone, p_event.zone_id)
		# chanToPostTo = self.botRef.get_channel(Channels.ps2ContinentNotifID)
		# For working out what continent ID is which.  Looking at you, Oshur.
		# await chanToPostTo.send(f"Continent: {continent.code} | ID: {continent.id}")
		# BUPrint.Debug(f"Debug: ContName: {continent.code}")
		
		if p_event.world_id != ContinentTrack.worldID:
			BUPrint.Debug("World doesn't match tracked setting. Ignoring.")
			return
		
		if continent == None:
			BUPrint.Debug("Dynamic zone. Ignoring.")
			return
		
		if p_event.zone_id in PS2ZoneIDs.allIDs.value:
			self.ReplaceOldLock(p_event)

			await self.PostMessage_Sorted()
		else:
			BUPrint.Debug(f"Ignoring continent lock. ({p_event.zone_id})")


	def ReplaceOldLock(self, p_event:ContinentLock):
		"""# Replace Old Lock
		Where present, replaces the event data.
		"""
		continentID = p_event.zone_id

		if continentID == PS2ZoneIDs.amerishID.value:
			self.lastAmerishLock = p_event
		
		elif continentID == PS2ZoneIDs.esamirID.value:
			self.lastEsamirLock = p_event

		elif continentID == PS2ZoneIDs.hossinID.value:
			self.lastHossinLock = p_event
		
		elif continentID == PS2ZoneIDs.indarID.value:
			self.lastIndarLock = p_event

		elif continentID == PS2ZoneIDs.oshurID.value:
			self.lastOshurLock = p_event

		else:
			BUPrint.Debug(f"Continent ID: {continentID} did not match existing settings.")
		


	def GetOldestLock(self) -> ContinentStatus:
		"""# Get Oldest Lock:
		Returns the continent status data of the oldest locked continent.
		
		Returns NONE if continent data is invalid.
		"""
		continents = self.GetContLocksAsArray()

		if continents.__len__() == 0:
			return None

		continents.sort(key=lambda continent: continent.lastLocked)

		for continentStatus in continents:
			if continentStatus.bIsLocked:
				return continentStatus
			
		return None


	async def PostMessage_Oldest(self, p_interaction:Interaction = None):
		"""Post Message: Basic
		Sends a simple message Containing the oldest continent.

		If p_interaction is None, message is sent to the settings specified channel.
		"""
		oldestLock = self.GetOldestLock()

		if oldestLock == None:
			if p_interaction != None:
				await p_interaction.response.send_message(content="Currently unable to fulfil this request. Sorry!", ephemeral=True)
				return
			else:
				BUPrint.Debug("No oldest lock available.")
				return

		
		vMessage = f"**Oldest continent lock:**\n{oldestLock.name}, locked {GetDiscordTime(oldestLock.lastLocked)}"

		if p_interaction != None:
			await p_interaction.response.send_message(content=vMessage, ephemeral=True)
			return

		else:
			await self.botRef.get_channel(Channels.ps2ContinentNotifID).send(vMessage)



	async def PostMessage_Sorted(self, p_interaction:Interaction = None):
		"""# Post Message: Sorted
		Sends a message with all continents, ordered from oldest to newest lock.

		if p_interaction is None, message is sent to the settings specified channel.
		"""
		continents = self.GetContLocksAsArray()

		if continents.__len__() == 0:
			if p_interaction != None:
				await p_interaction.response.send_message(content="Currently unable to fulfil this request. Sorry!", ephemeral=True)
				return
			else:
				BUPrint.Debug("Unable to post sorted message.")
				return
			

		continents.sort(key=lambda continent: continent.lastLocked)


		vMessage = "***Continents Locked:***"
		for continent in continents:

			if continent.bIsLocked:
				vMessage += f"\n\n**{continent.name}** last locked {GetDiscordTime(continent.name)}"
			else:
				vMessage += f"\n\n**{continent.name}** is currently **OPEN**!"


		if p_interaction != None:
			await p_interaction.response.send_message(content=vMessage, ephemeral=True)
			return

		else:
			# Prefix message with mentions of people managing live events that are in pre-start phase.
			if ContinentTrack.bAlertCommanders:
				commanders = OperationManager().vLiveCommanders

				if commanders.__len__() != 0:
					userMentions = ""
					for commander in commanders:
						if commander.vCommanderStatus.value < CommanderStatus.Started.value and commander.vOpData.managedBy != "":
							userMentions += self.botRef.get_user(int(commander.vOpData.managedBy)).mention
					
					vMessage = f"{userMentions}\n{vMessage}"


			await self.botRef.get_channel(Channels.ps2ContinentNotifID).send(vMessage)




	async def FacilityControlChange(self, p_event:FacilityControl):
		"""# Facility Control Change
		Function called by the auraxium client for facility control event.
		Current usage is just for determining if a continent has opened.
		"""
		if p_event.world_id != ContinentTrack.worldID:
			return
		
		if p_event.facility_id in PS2WarpgateIDs.allIDs.value:
			BUPrint.Info(f"Facility ID: {p_event.facility_id} matched warpgate!")
			await self.WarpgateFacilityCapture(p_event)
		else:
			# BUPrint.Debug(f"Facility ID: {p_event.facility_id} not in list of warpgates.")
			pass
		
			

	
	async def WarpgateFacilityCapture(self, p_event:FacilityControl):
		"""# Warpgate Facility Capture

		The facility provided MUST be a warpgate facility.

		Sets the continentStatus object for the continent and sends a message if the event is a continent opening.
		"""
		self.warpgateCaptures.append(
			WarpgateCapture(p_event.facility_id, p_event.zone_id, p_event.new_faction_id)
		)

		if self.warpgateCaptures.__len__() < 2:
			# Less than 2 warpgate changes thus far, skip.
			return
		
		if not self.GetIsLocked(p_event):
			await self.botRef.get_channel(Channels.ps2ContinentNotifID).send(
				f"{self.GetContinentNameFromWarpgate(p_event.facility_id)} is now **OPEN**!"
			)



	def GetIsLocked(self, p_event:FacilityControl) -> bool:
		"""# GET IS LOCKED
		## Returns 
		- True if the event passed is a lock event (or insufficient array length).
		- False if the event passed is part of a continent opening.

		Running the function also removes the associated entries from the warpgateCaptures array.
		"""


		bIsLocked = False
		firstFaction = -1 # 
		"""Used to check the faction in next iteration.  
		If it matches (more than one warpgate under a single faction), the continent is locked
		Uses -1 as unset, just incase there's some fuckery with factions.  Looking at you, NSO."""

		sanitisedList = [warpgate for warpgate in self.warpgateCaptures if warpgate.zoneID == p_event.zone_id]

		if sanitisedList.__len__() < 2:
			return True

		
		for warpgate in sanitisedList:
			if firstFaction == -1:
				firstFaction = warpgate.factionID

			else:
				if warpgate.factionID == firstFaction:
				# Matching faction IDs, continent is locked.
					bIsLocked = True
				else:
					# No matching faction ID, continent is open.
					bIsLocked = False
					
				self.SetContinentOpen( self.GetContinentNameFromWarpgate(warpgate.warpgateID), bIsLocked )
			
			# Cleanup warpgate capture list array.
			self.warpgateCaptures.remove(warpgate)


		return bIsLocked
	

	def SetContinentOpen(self, p_continentName:str, p_isOpen = True) -> None:
		"""# Set Continent Open
		Convenience function to set the appropriate continent bool values to true by default.
		Can be used to set open value to false."""
		if p_continentName.lower().__contains__("indar"):
			self.bIndarOpen = p_isOpen

		elif p_continentName.lower().__contains__("amerish"):
			self.bAmerishOpen = p_isOpen

		elif p_continentName.lower().__contains__("hossin"):
			self.bHossinOpen = p_isOpen

		elif p_continentName.lower().__contains__("esamir"):
			self.bEsamirOpen = p_isOpen

		elif p_continentName.lower().__contains__("oshur"):
			self.bOshurOpen	= p_isOpen



	def IsContinentLocked(self, p_continentName:str) -> bool:
		"""# Is Continent Locked
		Returns the value of the continent lock boolean based on the passed continent name."""

		if p_continentName.lower().__contains__("indar"):
			return self.bIndarOpen

		elif p_continentName.lower().__contains__("amerish"):
			return self.bAmerishOpen

		elif p_continentName.lower().__contains__("hossin"):
			return self.bHossinOpen

		elif p_continentName.lower().__contains__("esamir"):
			return self.bEsamirOpen

		elif p_continentName.lower().__contains__("oshur"):
			return self.bOshurOpen
		
		return False



	def GetContinentNameFromWarpgate(self, p_facilityID:int) -> str:
		"""# Get Continent Name from Warpgate (facility ID) 
		NOTE: WARPGATE IDs ONLY

		Returns a string of the continent name based on the facility ID.
		
		Name does not include whitespaces before or after.
		"""

		if p_facilityID in PS2WarpgateIDs.amerish.value:
			return str("Amerish")
		
		if p_facilityID in PS2WarpgateIDs.esamir.value:
			return str("Esamir")
		
		if p_facilityID in PS2WarpgateIDs.hossin.value:
			return str("Hossin")
		
		if p_facilityID in PS2WarpgateIDs.indar.value:
			return str("Indar")
		
		if p_facilityID in PS2WarpgateIDs.oshur.value:
			return str("Oshur")
		
		BUPrint.LogError(p_titleStr="Invalid warpgate ID", p_string=str(p_facilityID))
		return "" # Invalid ID