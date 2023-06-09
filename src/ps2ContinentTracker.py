"""# PS2 Continent Tracker

Handles tracking and displaying information of continent changes for a specified world.

Booleans relating to a continent being open or closed should follow:
"IS LOCKED?"
FALSE - Open 	| TRUE - Closed
"""

from botData.settings import BotSettings, ContinentTrack, Channels, CommandLimit, Messages, Directories
from botData.dataObjects import CommanderStatus, WarpgateCapture, ContinentStatus
from botUtils import BotPrinter as BUPrint, GetDiscordTime, UserHasCommandPerms, FilesAndFolders
from botData.utilityData import PS2ZoneIDs, PS2WarpgateIDs, PS2ContMessageType
from discord.ext.commands import GroupCog, Bot
from discord.ext import tasks
from discord.app_commands import command, rename, Choice
from discord import Interaction, Embed
from auraxium.event import EventClient, ContinentLock, Trigger, FacilityControl
from auraxium.ps2 import Zone, MapRegion, World, Outfit
from opsManager import OperationManager
from datetime import datetime, timezone
import asyncio
import pickle

class ContinentTrackerCog(GroupCog, name="continents"):
	def __init__(self, p_bot:Bot):
		self.botRef = p_bot
		self.auraxClient = EventClient(service_id=BotSettings.ps2ServiceID)

		self.antiSpamUpdateCount = 0
		"""Anti Spam update count:  When this count reaches a specified value, no new messages will be sent."""

		self.warpgateCaptures: list[WarpgateCapture] = []
		"""List of `Warpgate Capture` objects."""


		self.oshurStatus = ContinentStatus(PS2ZoneIDs.Oshur, PS2WarpgateIDs.oshur.value)
		self.amerishStatus = ContinentStatus(PS2ZoneIDs.Amerish, PS2WarpgateIDs.amerish.value)
		self.esamirStatus = ContinentStatus(PS2ZoneIDs.Esamir, PS2WarpgateIDs.esamir.value)
		self.hossinStatus = ContinentStatus(PS2ZoneIDs.Hossin, PS2WarpgateIDs.hossin.value)
		self.indarStatus = ContinentStatus(PS2ZoneIDs.Indar, PS2WarpgateIDs.indar.value)

		super().__init__()
		BUPrint.Info("COG: ContinentTracker loaded.")

		if ContinentTrack.bSaveOnShutdown:
			BUPrint.Info("	> Loading saved continent data")
			self.LoadContinentData()

		BUPrint.Debug("	> Starting auto reconnect task")
		self.ReconnectClient.start()



	@command(name="details", description="Posts a message of all continent statuses.")
	async def GetOldestContinentLock(self, p_interaction:Interaction):
		# HARDCODED ROLE USEAGE:
		if not await UserHasCommandPerms(p_interaction.user, (CommandLimit.continentTracker), p_interaction):
			return

		await self.PostMessage_Long(p_interaction)



	@command(name="reconnect", description="Reconnect the continent tracker if it's stopped.")
	async def ReconnectTracker(self, p_interaction:Interaction):
		"""# Reconnect Tracker
		Command to reconnect the continent tracker.
		"""
		if not await UserHasCommandPerms(p_interaction.user, (CommandLimit.continentTrackerAdmin), p_interaction):
			return

		await p_interaction.response.defer(thinking=True, ephemeral=True)

		await self.ReconnectClient()

		await p_interaction.edit_original_response(content="Continent Tracker reconnected")



	@command(name="set", description="Manually sets the status of a continent.")
	@rename(p_continentName="continent", p_isLocked="locked", p_timestamp="timestamp")
	async def CommandSetContinentStatus(self, p_interaction:Interaction, p_continentName:str, p_isLocked:bool, p_timestamp:int):
		"""# Command: set Continent Status
		Command related fuction to set a continents status.

		Manually sets the continent status and its time stamp.

		Not to be confused with `SetLocked`.  
		This function is soley for slash command and will call SetLocked.
		"""
		if not await UserHasCommandPerms(p_interaction.user, (CommandLimit.continentTrackerAdmin), p_interaction):
			return


		if p_continentName not in [enumEntry.name for enumEntry in PS2ZoneIDs]:
			BUPrint.Debug(f"Valid names: {[enumEntry.name for enumEntry in PS2ZoneIDs]}")
			await p_interaction.response.send_message("Invalid continent name given!", ephemeral=True)
			return
		
		try:
			dateObj = datetime.fromtimestamp(p_timestamp, timezone.utc)
		except ValueError:
			await p_interaction.response.send_message("Invalid timestamp given!", ephemeral=True)
			return

		BUPrint.Info(f"Manually setting {p_continentName}...")

		for continent in self.GetContinentsAsArray(False):
			if continent.ps2Zone.name == p_continentName:
				continent.SetLocked(p_isLocked, dateObj)

				await p_interaction.response.send_message(f"{continent.ps2Zone.name} updated!", ephemeral=True)

		

	@CommandSetContinentStatus.autocomplete("p_continentName")
	async def AutoCompleteContinentName(self, p_interaction:Interaction, p_typedStr:str):
		"""# Auto Complete: Continent Name

		Autocomplete function for CommandSetContinentStatus.
		"""
		validOptions = [zoneEnum.name for zoneEnum in PS2ZoneIDs]
		returnOpts = []

		if p_typedStr == "":
			for contName in validOptions:
				if contName != PS2ZoneIDs.allIDs.name:
					returnOpts.append(Choice(name=contName, value=contName))

		else:
			for contName in validOptions:
				if contName.lower().__contains__(p_typedStr):
					returnOpts.append(Choice(name=contName, value=contName))

		return returnOpts




	@tasks.loop(time=ContinentTrack.reconnectionTime)
	async def ReconnectClient(self):
		"""# Reconnect Client
		
		Convenience function to reconnect the auraxium client;
		 - Closes the current client.
		 - Recreate client triggers (removes old ones if they exist).
		 - Create new main loop task for aurax client.

		
		This may be called by a command, or from other functions in the event a `RuntimeError` is raised.

		It is also a looped task, such that it gets called on a recurring basis and thus eliminate the disconnection issue.

		It should NOT be confused for `ReconnectTracker`:  which is a command function that calls THIS function.
		"""
		BUPrint.Info("Reconnecting Auraxium Client...")


		BUPrint.Info("	>> Clearing current capture data")
		self.warpgateCaptures.clear()
		self.antiSpamUpdateCount = 0

		BUPrint.Info("	>> Closing current continent tracker.")
		await self.auraxClient.close()

		mainLoop = asyncio.get_event_loop()

		BUPrint.Info("	>> Recreating triggers.")
		await self.CreateTriggers()

		BUPrint.Info("	>> Recreating task loop.")
		await mainLoop.create_task(self.auraxClient.connect())

		BUPrint.Info("	>> Reconnect complete.")



	async def CreateTriggers(self):
		"""# Create Triggers
		Adds the continent lock and facility control triggers used for continent tracking.

		Because Continent Unlock is not working on Daybreak's side, FacilityControl is also used for this purpose.
		"""
		BUPrint.Info("	>> Creating triggers for continent tracker.")

		try:
			self.auraxClient.remove_trigger(keep_websocket_alive=True, trigger="CONTTRACK_Lock")
		except (KeyError, ValueError):
			BUPrint.Debug("No trigger for Continent Lock setup/found.")

		try:
			self.auraxClient.remove_trigger(keep_websocket_alive=True, trigger="CONTTRACK_Facility")
		except (KeyError, ValueError):
			BUPrint.Debug("No trigger for facility control setup/found.")



		if ContinentTrack.contLockMessageType != PS2ContMessageType.NoMessage:
			self.auraxClient.add_trigger(
				Trigger(
					name="CONTTRACK_Lock",
					event="ContinentLock",
					worlds=[ContinentTrack.worldID],
					action=self.ContinentLockCallback
				)
			) # END: Add trigger- Continent Lock


		self.auraxClient.add_trigger(
			Trigger(
				name="CONTTRACK_Facility",
				event="FacilityControl",
				worlds=[ContinentTrack.worldID],
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
		
		# Must be set before the below function; as the function updates the timestamps used by antiSpamCanPost resulting in a loop.
		bCanPost = self.AntiSpamCanPost()

		self.SetContinentIsLocked(True, p_event.zone_id)

		# Spam guard	
		if not bCanPost:
			return		


		if ContinentTrack.contLockMessageType == PS2ContMessageType.Simple:
			await self.PostMessage_Short( self.GetContinentFromID(p_event.zone_id) )
	
		elif ContinentTrack.contLockMessageType == PS2ContMessageType.Detailed:
			await self.PostMessage_Long()



	async def FacilityControlCallback(self, p_event:FacilityControl):
		"""# Facility Control Callback
		Function called when a facility control event is sent.
		
		Is currently used for two purposes.
		- Warpgate Captures; for checking if a continent is open/closed.  
			Because the open event isn't working on Daybreak's side this is used instead.
		- Outfit Facility Monitor; for alerting when the specified outfit captures a facility.
		"""
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

			await self.CheckWarpgates(p_event.zone_id)
			return
		

		if ContinentTrack.bMonitorFacilities:
			if p_event.outfit_id == ContinentTrack.facilityMonitorOutfitID:
				BUPrint.Debug("Facility capture: Outfit ID matched")

				try:
					takenFacility:MapRegion = await MapRegion.get_by_facility_id(p_event.facility_id, self.auraxClient)

				except RuntimeError as error:
					# BUPrint.LogError(p_titleStr="Session closed.", p_string="Reconnecting client...")
					# await self.ReconnectClient()
					BUPrint.LogErrorExc("Error occured obtaining facility.", error)
					return
					
					# Retry obtaining map region
					# try:
					# 	takenFacility:MapRegion = await MapRegion.get_by_facility_id(p_event.facility_id, self.auraxClient)
					# except RuntimeError:
					# 	BUPrint.Info("Failed to obtain map region after reconnecting client, aborting.")
					# 	return

				if takenFacility == None:
					BUPrint.Debug("Invalid facility ID.")
					return
				
				if p_event.old_faction_id != p_event.new_faction_id:
					message = Messages.facilityOutfitCapture.replace("_DATA", f"{takenFacility.facility_name} | {takenFacility.facility_type} | {GetDiscordTime(p_event.timestamp)}")
					BUPrint.Info(message)
					try:
						await self.botRef.get_channel(Channels.ps2FacilityControlID).send(message)

					except: # Intentional catch all; too many possible causes.
						BUPrint.LogError("Unable to post continent status message.", "EXCEPTION OCCURED")
						
			




	
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
			validList = [contStatus for contStatus in allContenents if contStatus.lastEventTime != None]
			return validList
		else:
			return allContenents
		


	def SetContinentIsLocked(self, p_isLocked:bool, p_id:int):
		"""# Set Continent Is Locked
		Will take either a warpgate or continent ID.

		## PARMETERS
		- p_isLocked - The new locked status.
		- p_id - Either a WARPGATE ID, or a Continent ID.
		"""

		BUPrint.Debug(f"Setting continent(zone/WG ID {p_id}) locked status({p_isLocked})")

		if p_id in PS2WarpgateIDs.amerish.value or p_id == PS2ZoneIDs.Amerish.value:
			self.amerishStatus.SetLocked(p_isLocked)

		if p_id in PS2WarpgateIDs.esamir.value or p_id == PS2ZoneIDs.Esamir.value:
			self.esamirStatus.SetLocked(p_isLocked)

		if p_id in PS2WarpgateIDs.indar.value or p_id == PS2ZoneIDs.Indar.value:
			self.indarStatus.SetLocked(p_isLocked)

		if p_id in PS2WarpgateIDs.hossin.value or p_id == PS2ZoneIDs.Hossin.value:
			self.hossinStatus.SetLocked(p_isLocked)

		if p_id in PS2WarpgateIDs.oshur.value or p_id == PS2ZoneIDs.Oshur.value:
			self.oshurStatus.SetLocked(p_isLocked)
	


	def GetContinentFromID(self, p_id:int) -> ContinentStatus:
		"""# Get Continent from ID
		Returns the continent status object from a continent ID or Warpgate ID.
		
		Returns NONE if invalid ID given."""
		
		for continent in self.GetContinentsAsArray(False):
			if continent.ps2Zone.value == p_id or p_id in continent.warpgateIDs:
				BUPrint.Debug("	> Matched")
				return continent
			
		BUPrint.LogError(p_titleStr="Invalid continent or Warpgate ID", p_string=str(p_id))
		return None # Invalid ID
	


	async def PostMessage_Short(self, p_continent:ContinentStatus = None):
		"""# Post Message: Short
		Sends a message to the settings specified channel.

		Message only includes the updated continent status of the passed event. 
		"""
		notifChannel = self.botRef.get_channel(Channels.ps2ContinentNotifID)
		message = f"**{p_continent.ps2Zone.name}** "
		if p_continent.bIsLocked:
			message += f"has **LOCKED**!"
		else:
			message += f"has **OPENED**!"

		message += f" | {GetDiscordTime(p_continent.lastEventTime)}"

		try:
			await notifChannel.send(message)
		except: # Intentional catch all; too many possible causes.
			BUPrint.LogError("Unable to post continent status message.", "EXCEPTION OCCURED")


		if ContinentTrack.bAlertCommanders:
			await self.PostMessage_Commanders()
	


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
		


		if p_interaction != None:
			try:
				await p_interaction.response.send_message(embed=self.CreateEmbed_Detailed(), ephemeral=True)
			except: # Intentional catch all; too many possible causes.
				BUPrint.LogError("Unable to post continent status message.", "EXCEPTION OCCURED")

		else:
			try:
				await self.botRef.get_channel(Channels.ps2ContinentNotifID).send(embed=self.CreateEmbed_Detailed())
			except: # Intentional catch all; too many possible causes.
				BUPrint.LogError("Unable to post continent status message.", "EXCEPTION OCCURED")

		if ContinentTrack.bAlertCommanders:
			await self.PostMessage_Commanders()



	def CreateEmbed_Detailed(self) -> Embed:
		"""# Create Embed: Detailed
		Creates and returns an embed for a detailed breakdown of the continent statuses."""
		allContenents = self.GetContinentsAsArray()

		openConts = [continent for continent in allContenents if not continent.bIsLocked]
		lockedConts = [continent for continent in allContenents if continent.bIsLocked]

		BUPrint.Debug(f"Open Conts Length: {openConts.__len__()} | Locked Conts Length: {lockedConts.__len__()}")

		# Sort locked
		lockedConts.sort(key=lambda continent: continent.lastEventTime)

		newEmbed = Embed(title="CONTINENT STATUS")
		# Compose message
		if openConts.__len__() != 0:
			for contenent in openConts:
				newEmbed.add_field(
					name=contenent.ps2Zone.name,
					value=f"**OPEN** | {GetDiscordTime(contenent.lastEventTime)}"
				)

		if lockedConts.__len__() != 0:
			for contenent in lockedConts:
				newEmbed.add_field(
					name=contenent.ps2Zone.name,
					value=f"**LOCKED** | {GetDiscordTime(contenent.lastEventTime)}",
					inline=False
				)


		return newEmbed


	async def PostMessage_Commanders(self):
		"""# Post Message: Commander
		Sends a detailed embed of the continent statuses to any live commanders.
		"""
		for commander in OperationManager.vLiveCommanders:
			if commander.vCommanderStatus.value < CommanderStatus.Started.value:
				managingUser = self.botRef.get_user(commander.vOpData.managedBy)

				newMessage = "Continents updated\n"

				if managingUser != None:
					newMessage += f"{managingUser.mention}\n"
				

				if commander.continentAlert == None:
					try:
						commander.continentAlert = await commander.notifChn.send(content=newMessage, embed=self.CreateEmbed_Detailed())

					except: # Intentional catch all; too many possible causes.
						BUPrint.LogError("Unable to post continent status message.", "EXCEPTION OCCURED")

				else:
					await commander.continentAlert.edit(embed=self.CreateEmbed_Detailed())



	async def CheckWarpgates(self, p_zoneID:int):
		"""# Check Warpgates
		Checks the warpgate captures array, based on the passed Zone(continent) ID.
		
		When a continent is considered locked or opened, the associated entries are removed from the array, and a message is posted."""
		BUPrint.Debug("Checking Warpgates...")
		
		matchingGates = [gateCapture for gateCapture in self.warpgateCaptures if gateCapture.zoneID == p_zoneID]

		if matchingGates.__len__() < 2:
			BUPrint.Debug(f"	> Insufficient gate length: {matchingGates.__len__()}")
			return

		firstFaction = -1
		for gate in matchingGates:
			if firstFaction == -1:
				firstFaction = gate.factionID
			
			else:
				if gate.factionID == firstFaction:
					BUPrint.Debug("Matching factions, Continent has locked.")
					# Commented out, since the actual continent lock event works as intended.

					# continent.SetLocked(True)
					# continent.lastLocked = p_timeStamp
					pass

				else:
					BUPrint.Debug("Mismatched factions. Continent open!")
					
					# Must be set before SetContinents as that updates the timestamps (to current), resulting in a loop.
					bCanPost = self.AntiSpamCanPost()

					self.SetContinentIsLocked(False, gate.warpgateID)

					if not bCanPost:
						return

					if ContinentTrack.contUnlockMessageType == PS2ContMessageType.NoMessage:
						BUPrint.Debug("Unlock event occured, set to ignore.")
						pass

					elif ContinentTrack.contUnlockMessageType == PS2ContMessageType.Detailed:
						await self.PostMessage_Long()

					elif ContinentTrack.contUnlockMessageType == PS2ContMessageType.Simple:
						await self.PostMessage_Short( self.GetContinentFromID(gate.warpgateID) )


		# Check if more than 2 warpgate entries are saved.  In this event, clear the warpgate list.
		if matchingGates.__len__() > 2:
			BUPrint.Info("Acquired too many matching gates. Clearing WG captures to avoid future duplicates.")
			self.warpgateCaptures.clear()
			return
		
		# Rerun loop & remove entries.
		BUPrint.Debug(f"Removing: {len(matchingGates)}")
		
		for gate in matchingGates:
			try:
				self.warpgateCaptures.remove(gate)
				BUPrint.Debug("Warpgate entry removed")
			except ValueError:
				BUPrint.Info("Warpgate not in array. Clearing WGCaptures to avoid future duplicates. May miss a continent opening.")
				self.warpgateCaptures.clear()
				return
			

	
	def GetMostRecentTimestamp(self) -> datetime:
		"""# Get most recent timestamp:
		Returns the timestamp of the most recent continent update.
		
		Return NONE if array is empty.
		"""
		contArray = self.GetContinentsAsArray()

		if contArray.__len__() == 0:
			return None

		contArray.sort(key=lambda continent: continent.lastEventTime, reverse=True)

		return contArray[0].lastEventTime
	


	def AntiSpamCanPost(self) -> bool:
		"""# Anti Spam: Can Post
		Function to protect against spam events, checks the given timestamp against the most recent.

		Will always return true if no recent time exists.
		

		## RETURNS
		- `TRUE`: when a continent event may be posted.
		- `FALSE`: When too many continent event updates have been posted.
		"""
		BUPrint.Info("Continent Update Antispam check...")

		mostRecentTime = self.GetMostRecentTimestamp()

		if mostRecentTime == None:
			return True
		
		BUPrint.Debug(f"	>> Checking: {mostRecentTime + ContinentTrack.antiSpamMinimalTime} > {datetime.now(tz=timezone.utc)}")

		if mostRecentTime + ContinentTrack.antiSpamMinimalTime > datetime.now(tz=timezone.utc):
			self.antiSpamUpdateCount += 1
			BUPrint.Debug(f"	>> Event is occuring within spam minimal timeframe. (Antispam count: {self.antiSpamUpdateCount})")

			if self.antiSpamUpdateCount >= ContinentTrack.antiSpamAllowedPosts:
				BUPrint.Info(f"	>> Continent Tracker AntiSpam prevented a message from being sent. {self.antiSpamUpdateCount - ContinentTrack.antiSpamAllowedPosts} Messages blocked.")
				return False
		
		else:
			BUPrint.Debug("	>> Event occured past minimal timeframe.")
			self.antiSpamUpdateCount = 0
		
		return True


	def LoadContinentData(self):
		"""# Load Continent Data
		Sets the continent objects with saved data from file.
		"""
		BUPrint.Info("Loading continent data from file...")
		
		contFiles = FilesAndFolders.GetFiles(Directories.tempDir, ".cont")

		for continentDataFilepath in contFiles:
			try:
				BUPrint.Debug(f"	> Unpickling: {continentDataFilepath}")
				with open(f"{Directories.tempDir}{continentDataFilepath}", "rb") as continentDataFile:
					continentData:ContinentStatus = pickle.load(continentDataFile)
			

			except pickle.UnpicklingError as vError:
				BUPrint.LogErrorExc("Invalid object passed to load.", vError)
				break

			except pickle.PickleError:
				BUPrint.LogError("Unable to load continent data", "PICKLE ERROR")
				break
			

			for continent in self.GetContinentsAsArray(False):
				if continent.ps2Zone == continentData.ps2Zone:
					BUPrint.Info(f"	> Setting {continent.ps2Zone.name} status")
					continent.SetLocked(continentData.bIsLocked, continentData.lastEventTime)



	def SaveContinentData(self):
		"""# Save Continent Data
		Saves the continent objects data to file.
		"""
		BUPrint.Info("Saving continent data to file...")
		
		continents = self.GetContinentsAsArray()

		for continent in continents:
			try:
				BUPrint.Debug(f"	> Pickling: {continent.ps2Zone.name}")
				filePath = f"{Directories.tempDir}{continent.ps2Zone.name}.cont"
				with open(filePath, "wb") as vFile:
					pickle.dump(continent, vFile, BotSettings.pickleProtocol)

			except pickle.PicklingError as vError:
				BUPrint.LogErrorExc("Invalid object passed to dump.", vError)
				break

			except pickle.PickleError:
				BUPrint.LogError("Unable to save continent data", "PICKLE ERROR")
				break