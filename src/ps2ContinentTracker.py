"""# PS2 Continent Tracker

Handles tracking and displaying information of continent changes for a specified world.

Booleans relating to a continent being open or closed should follow:
"IS LOCKED?"
FALSE - Open 	| TRUE - Closed
"""

from botData.settings import BotSettings, ContinentTrack, Channels, CommandLimit, Messages
from botData.dataObjects import CommanderStatus, WarpgateCapture, ContinentStatus
from botUtils import BotPrinter as BUPrint
from botUtils import GetDiscordTime, UserHasCommandPerms
from botData.utilityData import PS2ZoneIDs, PS2WarpgateIDs
from discord.ext.commands import GroupCog, Bot
from discord.app_commands import command
from discord import Interaction, Embed
from auraxium.event import EventClient, ContinentLock, Trigger, FacilityControl
from auraxium.ps2 import Zone, MapRegion, World, Outfit
from opsManager import OperationManager
from datetime import datetime

class ContinentTrackerCog(GroupCog, name="continents"):
	def __init__(self, p_bot:Bot):
		self.botRef = p_bot
		self.auraxClient = EventClient(service_id=BotSettings.ps2ServiceID)


		self.warpgateCaptures: list[WarpgateCapture] = []
		"""List of `Warpgate Capture` objects."""

		self.oshurStatus = ContinentStatus(PS2ZoneIDs.OshurID, PS2WarpgateIDs.oshur.value)
		self.amerishStatus = ContinentStatus(PS2ZoneIDs.AmerishID, PS2WarpgateIDs.amerish.value)
		self.esamirStatus = ContinentStatus(PS2ZoneIDs.EsamirID, PS2WarpgateIDs.esamir.value)
		self.hossinStatus = ContinentStatus(PS2ZoneIDs.HossinID, PS2WarpgateIDs.hossin.value)
		self.indarStatus = ContinentStatus(PS2ZoneIDs.IndarID, PS2WarpgateIDs.indar.value)

		super().__init__()
		BUPrint.Info("COG: ContinentTracker loaded.")


	@command(name="details", description="Posts a message of all continent statuses.")
	async def GetOldestContinentLock(self, p_interaction:Interaction):
		# HARDCODED ROLE USEAGE:
		if not await UserHasCommandPerms(p_interaction.user, (CommandLimit.continentTracker), p_interaction):
			return

		await self.PostMessage_Long(p_interaction)

	

	async def CreateTriggers(self):

		# worldToMonitor = await self.auraxClient.get(World, ContinentTrack.worldID)
		# Currently unused.  Uncommenting will cause the bot to not run.

		self.auraxClient.add_trigger(
			Trigger(
				event="ContinentLock",
				# worlds=[worldToMonitor],
				action=self.ContinentLockCallback
			)
		) # END: Add trigger- Continent Lock


		self.auraxClient.add_trigger(
			Trigger(
				event="FacilityControl",
				# worlds=[worldToMonitor],
				action=self.FacilityControlCallback
			)
		) # END: Add Trigger: Facility Control



	async def ContinentLockCallback(self, p_event:ContinentLock):
		"""# Continent Lock Callback
		The function called when a Continent Lock event is sent."""
		if p_event.world_id != ContinentTrack.worldID:
			return
		
		if p_event.zone_id not in PS2ZoneIDs.allIDs.value:
			return

		continent = self.GetContinentFromID(p_event.zone_id)
		continent.bIsLocked = True
		continent.lastLocked = p_event.timestamp

		if ContinentTrack.bPostFullMsgOnLock:
			await self.PostMessage_Long()
		else:
			await self.PostMessage_Short(continent)




	async def FacilityControlCallback(self, p_event:FacilityControl):
		"""# Facility Control Callback
		Function called when a facility control event is sent."""
		if p_event.world_id != ContinentTrack.worldID:
			return
		
		if p_event.facility_id in PS2WarpgateIDs.allIDs.value:
			self.warpgateCaptures.append(
				WarpgateCapture(
					warpgateID=p_event.facility_id,
					zoneID=p_event.zone_id,
					factionID=p_event.new_faction_id
				) # END - Warpgate Capture
			) # END - Append wg capture.

			await self.CheckWarpgates(p_event.zone_id, p_event.timestamp)
			return
		
		if ContinentTrack.bMonitorFacilities:
			if p_event.outfit_id == ContinentTrack.facilityMonitorOutfitID:
				takenFacility:MapRegion = self.auraxClient.get(MapRegion, p_event.facility_id)

				if takenFacility == None:
					BUPrint.Debug("Invalid facility ID.")
					return

				message = Messages.facilityOutfitCapture.replace("_DATA", f"{takenFacility.facility_name} | {takenFacility.facility_type} | {GetDiscordTime(p_event.timestamp)}")

				await self.botRef.get_channel(Channels.ps2FacilityControlID).send(message)



		


	
	def GetContinentsAsArray(self, p_validOnly:bool = True) -> list[ContinentStatus]:
		"""# Get Continents as Array
		Returns an array containing all the continent status objects.
		
		## PARAMETER:
		- `p_validOnly`: When `True` (default), the resulting aray will only contain status objects that have been set.
			
			When `False`, returns all array items.  This is primarily for setter functions."""
		
		allContenents = [
			self.amerishStatus,
			self.esamirStatus,
			self.hossinStatus,
			self.indarStatus,
			self.oshurStatus
		]

		if p_validOnly:
			validList = [contStatus for contStatus in allContenents if contStatus.lastLocked != None]
			return validList
		else:
			return allContenents



	def GetContinentFromWG(self, p_warpgateID:int) -> ContinentStatus:
		"""# Get Continent From Warpgate
		Returns the continent status object from a warpgate `Facility ID`
		
		Returns NONE if invalid ID given."""

		for continent in self.GetContinentsAsArray(False):
			if p_warpgateID in continent.warpgateIDs:
				return continent
		
		BUPrint.LogError(p_titleStr="Invalid warpgate ID", p_string=str(p_warpgateID))
		return None # Invalid ID
	


	def GetContinentFromID(self, p_contID:int) -> ContinentStatus:
		"""# Get Continent from ID
		Returns the continent status object from a continent ID.
		
		Returns NONE if invalid ID given."""
		
		for continent in self.GetContinentsAsArray(False):
			BUPrint.Debug(f"Continent: {continent.ps2Zone.name}, ID: {continent.ps2Zone.value} | Checking against: {p_contID}")

			if continent.ps2Zone.value == p_contID:
				return continent
			
		BUPrint.LogError(p_titleStr="Invalid continent ID", p_string=str(p_contID))
		return None # Invalid ID
	


	async def PostMessage_Short(self, p_continent:ContinentStatus = None):
		"""# Post Message: Short
		Sends a message to the settings specified channel.

		Message only includes the updated continent status of the passed event. 
		"""
		notifChannel = self.botRef.get_channel(Channels.ps2ContinentNotifID)
		message = f"**UPDATED CONTINENT**\n**{p_continent.ps2Zone.name}** "
		if p_continent.bIsLocked:
			message += "has **LOCKED**!"
		else:
			message += "has **OPENED**!"

		await notifChannel.send(message)

		if ContinentTrack.bAlertCommanders:
			await self.PostMessage_Commanders(message)
	


	async def PostMessage_Long(self, p_interaction:Interaction = None):
		"""# Post Message: Long

		Message includes all continent statuses.

 
		## PARAMETRS:
		- `p_interaction`: An interaction reference.
		
		If interaction is included, the output is directed to the interaction.  
		Else it sends a message to the settings specified channel.
		"""

		allContenents = self.GetContinentsAsArray()

		if allContenents.__len__() == 0:
			if p_interaction != None:
				await p_interaction.response.send_message(content=Messages.noContinentData, ephemeral=True)
			BUPrint.Debug("No continent data.  Can't send message.")
			return
		
		openConts = [continent for continent in allContenents if not continent.bIsLocked]
		lockedConts = [continent for continent in allContenents if continent.bIsLocked]

		# Sort locked
		lockedConts.sort(key=lambda continent: continent.lastLocked)

		message = "Continent Status..."
		newEmbed = Embed(title="CONTINENT STATUS")
		# Compose message
		if openConts.__len__() != 0:
			# message += "\n\n**OPEN**"
			for contenent in openConts:
				newEmbed.add_field(
					name=contenent.ps2Zone.name,
					value="**OPEN**"
				)
				# message += f"\n- {contenent.ps2Zone.name}"

		if lockedConts.__len__() != 0:
			# message += "\n\n**LOCKED**"
			for contenent in lockedConts:
				# message += f"\n- {contenent.ps2Zone.name} | Locked: {GetDiscordTime(contenent.lastLocked)}"
				newEmbed.add_field(
					name=contenent.ps2Zone.name,
					value=f"**LOCKED** | {GetDiscordTime(contenent.lastLocked)}"
				)

		if p_interaction != None:
			await p_interaction.response.send_message(content=message, embed=newEmbed, ephemeral=True)
		else:
			await self.botRef.get_channel(Channels.ps2ContinentNotifID).send(message)

		if ContinentTrack.bAlertCommanders:
			await self.PostMessage_Commanders(message, newEmbed)



	async def PostMessage_Commanders(self, p_message:str = None, p_embed:Embed = None):
		"""# Post Message: Commander
		Sends a copy of a message to the commander channel.
		"""
		for commander in OperationManager.vLiveCommanders:
			if commander.vCommanderStatus.value < CommanderStatus.Started.value:
				if commander.continentAlert == None:
					commander.continentAlert = await commander.notifChn.send(content=p_message, embed=p_embed)

				else:
					await commander.continentAlert.edit(content=p_message, embed=p_embed)



	async def CheckWarpgates(self, p_zoneID:int, p_timeStamp:datetime):
		"""# Check Warpgates
		Checks the warpgate captures array, based on the passed Zone(continent) ID.
		
		When a continent is considered locked or opened, the associated entries are removed from the array, and a message is posted."""
		matchingGates = [gateCapture for gateCapture in self.warpgateCaptures if gateCapture.zoneID == p_zoneID]

		if matchingGates.__len__() < 2:
			return

		firstFaction = -1
		continent:ContinentStatus = None
		for gate in matchingGates:
			if firstFaction == -1:
				firstFaction = gate.factionID
			
			else:
				continent = self.GetContinentFromWG(gate.warpgateID)

				if gate.factionID == firstFaction:
					# Matching factions, continent has locked
					# Commented out, since the actual continent lock event works as intended.

					# continent.bIsLocked = True
					# continent.lastLocked = p_timeStamp
					pass

				else:
					# Mismatching factions, continent has opened:
					continent.bIsLocked = False

					if ContinentTrack.bPostFullMsgOnOpen:
						await self.PostMessage_Long()

					else:
						await self.PostMessage_Short(continent)

		# Rerun loop & remove entries.
		for gate in matchingGates:
			self.warpgateCaptures.remove(gate)
