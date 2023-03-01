"""# PS2 Continent Tracker

Handles tracking and displaying information of continent changes for a specified world.


"""

from botData.settings import BotSettings, ContinentTrack, Channels, CommandLimit
from botUtils import BotPrinter as BUPrint
from botUtils import GetDiscordTime, UserHasCommandPerms
from botData.utilityData import PS2ZoneIDs
from discord.ext.commands import GroupCog, Bot
from discord.app_commands import command
from discord import Interaction
from auraxium.event import EventClient, ContinentLock, Trigger
from auraxium.ps2 import Zone
import time

class ContinentTracker(GroupCog):
	def __init__(self, p_bot:Bot):
		self.botRef = p_bot
		self.auraxClient = EventClient(service_id=BotSettings.ps2ServiceID)

		# Continent Locks
		self.lastOshurLock: ContinentLock = None
		self.lastIndarLock: ContinentLock = None
		self.lastEsamirLock: ContinentLock = None
		self.lastAmerishLock: ContinentLock = None
		self.lastHossinLock: ContinentLock = None

		super().__init__()
		BUPrint.Info("COG: ContinentTracker loaded.")


	@command(name="oldest", description="Posts the oldest locked continent lock.")
	async def GetOldestContinentLock(self, p_interaction:Interaction):
		# HARDCODED ROLE USEAGE:
		if not await UserHasCommandPerms(p_interaction.user, (CommandLimit.opManager), p_interaction):
			return

		await self.PostMessage_Oldest(p_interaction)


	@command(name="locks", description="Posts all continent lock timestamps.")
	async def GetAllContinentLocks(self, p_interaction:Interaction):
		# HARDCODED ROLE USEAGE:
		if not await UserHasCommandPerms(p_interaction.user, (CommandLimit.opManager), p_interaction):
			return

		await self.PostMessage_Oldest(p_interaction)



	def CreateTriggers(self):
		"""# Create Triggers
		Sets up the triggers to monitor """
		self.auraxClient.add_trigger( Trigger(
			Event=ContinentLock.event_name,
			worlds=ContinentTrack.worldID,
			action=self.NewContinentLock
			)
		)


	async def NewContinentLock(self, p_event:ContinentLock):
		"""# New Continent Lock
		Called when a continent has been locked.
		"""
		notifChannel = self.botRef.get_channel(Channels.ps2ContinentNotifID)

		p_event.timestamp
		pass


	def ReplaceOldLock(self, p_event:ContinentLock):
		"""# Replace Old Lock
		Where present, replaces the event data.
		"""
		continentID = p_event.zone_id

		if continentID == PS2ZoneIDs.amerishID:
			self.lastAmerishLock = p_event
		
		elif continentID == PS2ZoneIDs.esamirID:
			self.lastEsamirLock = p_event

		elif continentID == PS2ZoneIDs.hossinID:
			self.lastHossinLock = p_event
		
		elif continentID == PS2ZoneIDs.indarID:
			self.lastIndarLock = p_event

		elif continentID == PS2ZoneIDs.oshurID:
			self.lastOshurLock = p_event

		else:
			BUPrint.Info(f"Continent ID: {continentID} did not match existing settings.")
		


	def GetOldestLock(self) -> ContinentLock:
		"""# Get Oldest Lock:
		Returns the continentLock event data of the oldest locked continent.
		
		Returns NONE if continent data is invalid.
		"""
		continents = [
			self.lastAmerishLock, 
			self.lastEsamirLock, 
			self.lastHossinLock, 
			self.lastIndarLock, 
			self.lastOshurLock
			]
		
		timestamps = [continent.timestamp for continent in continents if continent != None]
		timestamps.sort()

		for continent in continents:
			if timestamps[0] == continent.timestamp:
				return continent
			
		return None


	async def PostMessage_Oldest(self, p_interaction:Interaction = None):
		"""Post Message: Basic
		Sends a simple message Containing the oldest continent.

		If p_interaction is None, message is sent to the settings specified channel.
		"""
		oldestLock = self.GetOldestLock()
		oldestContinent:Zone = await self.auraxClient.get_by_id(id_=oldestLock.zone_id, type_=Zone)
		
		vMessage = f"**Oldest continent lock:**\n{oldestContinent.name}, locked {GetDiscordTime(oldestLock.timestamp)}"

		if p_interaction != None:
			await p_interaction.response.send_message(content=vMessage)
			return

		else:
			await self.botRef.get_channel(Channels.ps2ContinentNotifID).send(vMessage)



	async def PostMessage_Sorted(self, p_interaction:Interaction = None):
		"""# Post Message: Sorted
		Sends a message with all continents, ordered from oldest to newest lock.

		if p_interaction is None, message is sent to the settings specified channel.
		"""
		continents = [
			self.lastAmerishLock, 
			self.lastEsamirLock, 
			self.lastHossinLock, 
			self.lastIndarLock, 
			self.lastOshurLock
			]

		continents.sort(key=lambda continent: continent.timestamp)

		vMessage = "***Continents Locked***\n"
		for continent in continents:
			zoneData:Zone = await self.auraxClient.get_by_id(Zone, continent.zone_id)
			vMessage += f"{zoneData.name} last locked {GetDiscordTime(continent.timestamp)}"


		if p_interaction != None:
			await p_interaction.response.send_message(content=vMessage)
			return

		else:
			await self.botRef.get_channel(Channels.ps2ContinentNotifID).send(vMessage)