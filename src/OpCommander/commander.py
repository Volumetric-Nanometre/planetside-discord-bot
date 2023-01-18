"""
COMMANDER:
	The major classes for the Operation Commander and its operation.
	Event tracking is handled seperately in events.py; and is only started/stopped by the commander.
"""

from __future__ import annotations # Backport of list hint typing.

import discord
import discord.ext
from discord.ext import commands
import auraxium
import re

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.schedulers import SchedulerNotRunningError
from datetime import timedelta, datetime, timezone
from dateutil.relativedelta import relativedelta

from OpCommander.events import OpsEventTracker
from botData.dataObjects import CommanderStatus, OpsStatus, Participant, Session, OpFeedback

from botUtils import GetGuild, GetDiscordTime
from botUtils import BotPrinter as BUPrint
from botUtils import ChannelPermOverwrites as ChanPermOverWrite
from botData.utilityData import DateFormat, Colours

from botData.settings import BotSettings as botSettings
from botData.settings import Commander as commanderSettings
from botData.settings import Messages as botMessages
from botData.settings import Directories, UserLib, NewUsers, Channels

from botData.dataObjects import OperationData, User, OpRoleData, PS2EventTrackOptions, ForFunData, ForFunVehicleDeath

import opsManager
# from userManager import UserLibrary, User
import userManager

async def StartCommander(p_opData: OperationData):
	"""
	# START COMMANDER
	Self explanitory, calling this will start the commander for the given ops file.
	
	Starting a commander does NOT start an Ops.  That is a different event, handled by the commander itself (if bAutoStart is enabled in both op settings and botsettings).

	## RETURNS: `int`
	`0` if commander has started.

	`1` Fail: Event already started

	`2` Fail: Invalid OpData given
	"""

	# CHECKS:
	if p_opData == None:
		BUPrint.Info("Invalid OpData given.  Not starting commander.")
		return 2

	# if len(p_opData.GetParticipantIDs()) == 0:
	# 	BUPrint.Info("Cannot start an event with 0 participants.  Not starting commander.")
	# 	return 2

	if p_opData.status.value >= OpsStatus.prestart.value:
		# Check to make sure there's no other commander, else calling command is taking over.
		for commander in opsManager.OperationManager.vLiveCommanders:
			if commander.vOpData.messageID == p_opData.messageID:
				BUPrint.Info("Trying to start a commander for an event that already has a commander!")
				return 1


	BUPrint.Debug(f"Starting commander for {p_opData.fileName}!")
	vNewCommander = Commander(p_opData)
	opsManager.OperationManager.vLiveCommanders.append(vNewCommander)
	await vNewCommander.SetupCommander()
	# Don't call functions to send/update commander info or commander messages, as setup calls these functions.
	
	return 0



class Commander():
	"""
	# COMMANDER
	Class containing functions and members used during a live, running Operation.
	Instantiation requires an `OperationData` object, housing the information for the event.

	Creating a commander does not automatically run any setup.

	An Info Message must be created and set within the commander.
	"""
	vBotRef: commands.Bot
	def __init__(self, p_opData: OperationData) -> None:
		BUPrint.Info("Ops Commander created")
		self.vOpData : OperationData = p_opData
		self.vCommanderStatus = CommanderStatus.Init
		self.vFeedback = OpFeedback()
		self.bHasSoftEnded = False # Set to true if soft ended (debriefed.)
		self.bAttendanceChecked = False # When true and a participants attendance isn't already `True`, participant is marked late.
		self.trueStartTime: datetime = None # Set when the event is started.
		self.bIgnoreStateChange = False # Ignore State Change: should be used to check whether to perform discord actions based on state changes (eg, voice state change when moving users).

		# Auraxium client & Op event tracker
		self.vAuraxClient:auraxium.EventClient = None
		self.vOpsEventTracker:OpsEventTracker = None

		if p_opData.options.bIsPS2Event:
			BUPrint.Debug("Event is PS2 related, creating tracker & client...")
			self.vAuraxClient = auraxium.EventClient(service_id=botSettings.ps2ServiceID)
			self.vOpsEventTracker = OpsEventTracker(p_aurClient=self.vAuraxClient)
			self.vOpsEventTracker.updateParentFunction = self.UpdateCommanderLive

		# Alert & Autostart Scheduler
		self.scheduler = AsyncIOScheduler()
		self.alertTimes:list[datetime] = [] # Saved to be displayed in Info embed

		#DiscordElements:
		self.commanderInfoMsg : discord.Message = None # Message object for the Info embed.
		self.commanderMsg: discord.Message = None # Message object used to edit the commander. Set during first post.
		self.commanderChannel: discord.TextChannel = None # Channel for the Commander to be posted in.
		self.notifChn: discord.TextChannel = None # Channel used to display notifications
		self.vCategory: discord.CategoryChannel = None # Category object to keep the Ops self contained. All channels are created within here, except soberdogs feedback
		self.standbyChn: discord.VoiceChannel = None # Standby channel voice connected users are moved into during start.
		self.lastStartAlert: discord.Message = None # Last Start alert sent, used to store + remove a previous alert to not flood the channel.
		self.participants:list[Participant] = [] # List of Participant objects.
		self.notifFeedbackMsg: discord.Message = None # Message for non-soberdogs Feedback.
		
		# Soberdogs Discord Elements, saved here to avoid repeated fetching.
		self.soberdogFeedbackForum: discord.ForumChannel = None # Forum for soberdogs Debriefs.
		self.soberdogFeedbackThread : discord.Thread = None # Thread holding the feedback message. Also used to get a jump-link for the notif channel button.
		self.soberdogFeedbackMsg: discord.Message = None # Message for the soberdogs Feedback.


	async def SetupCommander(self):
		"""# SETUP COMMANDER:
		- Create the category and its channels.
		- send the initial info & commander messages.
		- Setup scheduler: auto alerts.
		- setup scheduler: auto start
		"""
		if self.vCommanderStatus.value >= CommanderStatus.Standby.value:
			BUPrint.LogError(p_titleStr="CANNOT SETUP COMMANDER | ", p_string="Commander has been set up already.")
			return

		await self.CreateChannels()
		self.CreateScheduleTasks_Prestart()
		await self.UpdateParticipants()

		# Update Signup Post:
		self.vOpData.status = OpsStatus.prestart
		self.vCommanderStatus = CommanderStatus.WarmingUp
		await opsManager.OperationManager().UpdateMessage(self.vOpData)
		await self.UpdateCommander()



	async def StartEvent(self):
		""" # START EVENT
		Officially starts the event; 
		- Updates the signup message
		- Moves users to standby (if enabled)
		"""
		if self.vCommanderStatus.value > CommanderStatus.WarmingUp.value:
			BUPrint.Info("Commander has started already, skipping!")
			return

		BUPrint.Info(f"Event: {self.vOpData.name} started!")
		self.scheduler.remove_all_jobs()

		self.vCommanderStatus = CommanderStatus.Started
		self.vOpData.status = OpsStatus.started
		await opsManager.OperationManager().UpdateMessage(self.vOpData)

		await self.MoveUsers(True)

		if commanderSettings.markedPresent != PS2EventTrackOptions.Disabled:
			self.scheduler.add_job(Commander.CheckAttendance, 'date', run_date=(datetime.now(tz=timezone.utc) + timedelta(minutes=commanderSettings.gracePeriod)), args=[self])

		await self.UpdateCommander()



	async def EndEventSoft(self):
		"""# END EVENT SOFT:
		Should be called when the event has stopped, but before closing the event entirely.
		"""
		await self.vAuraxClient.close()
		self.scheduler.shutdown()
		self.bHasSoftEnded = True
		self.vCommanderStatus = CommanderStatus.Debrief

		if botSettings.botFeatures.UserLibrary:
			for participant in self.participants:
				if participant.libraryEntry != None:
					if participant.bAttended:
						participant.libraryEntry.eventsAttended += 1
					else:
						participant.libraryEntry.eventsMissed += 1
					userManager.UserLibrary.SaveEntry(participant.libraryEntry)
			


	async def EndEvent(self):
		"""# END EVENT
		Officially ends the event, moving users back into the normal channel (either ps2 or fallback), and removes the operation from the OpManager."""
		if not self.bHasSoftEnded:
			await self.EndEventSoft()

		await self.MoveUsers(False)
		await self.DeleteChannels()

		# Only remove operation if event had actually started, else don't, in the event the bot has shutdown before event starts.
		if self.vCommanderStatus.value >= CommanderStatus.Debrief.value:
			await opsManager.OperationManager.RemoveOperation(p_opData=self.vOpData)

		BUPrint.Info(f"Commander for event {self.vOpData.name} has ended!")


	def CreateScheduleTasks_Prestart(self):
		"""# CREATE SCHEDULED TASKS: PRESTART
		
		Creates the scheuled task for pre-start commanders:
		- Auto Alerts
		- Auto Start
		"""
		if commanderSettings.bAutoAlertsEnabled:
			intervalTime = 0
			if commanderSettings.bAutoStartEnabled:
				intervalTime = commanderSettings.autoPrestart / commanderSettings.autoAlertCount
			else:
				# Event started manually, set interval from time now; if event isn't in the past.
				timeUntilOps:timedelta = datetime.now(tz=timezone.utc) - self.vOpData.date
				if timeUntilOps > 0:
					intervalTime = timeUntilOps.seconds * 60
			
			# Set last interval as op start datetime; so that first interval is subtracted from it
			lastInterval = self.vOpData.date
			setIntervals = 0
			if intervalTime != 0:
				while setIntervals < commanderSettings.autoAlertCount:
					lastInterval = lastInterval - relativedelta(minutes=intervalTime)
					self.alertTimes.append(lastInterval)
					BUPrint.Debug(f"AutoAlert Interval: {lastInterval}")
					self.scheduler.add_job( Commander.SendReminder, 'date', run_date=lastInterval, args=[self] )
					setIntervals += 1
		
		
		# Setup AutoStart
		if self.vOpData.options.bAutoStart and commanderSettings.bAutoStartEnabled:
			BUPrint.Debug(f"Commander set to Start Operation at {self.vOpData.date}")
			self.scheduler.add_job( Commander.StartEvent, 'date', run_date=self.vOpData.date, args=[self], id="CommanderAutoStart")

		self.scheduler.start()



	async def UpdateParticipants(self):
		"""# UPDATE PARTICIPANTS
		Updates the commander participants from the OpData.
		Will update the info and connections embed, and call to regenerate login.
		"""
		bRequiresUpdate = False # First check to make sure an update is required; times when it does not include a user just changing roles.
		vGuild:discord.Guild = await GetGuild(self.vBotRef)


		vOpDataPlayerIDs = self.vOpData.GetParticipantIDs() # Grab to avoid repetitious getting.
		vCommanderPlayerIDs = [participant.discordID for participant in self.participants]
		BUPrint.Debug(f"Commander Player IDs: {vCommanderPlayerIDs}")


		# First run		
		if self.participants.__len__() == 0:
			bRequiresUpdate = True

			for userID in vOpDataPlayerIDs:
				member = vGuild.get_member(userID)
				if member != None:
					self.participants.append( Participant(discordID=userID, discordUser=member) )
		else:

			# Check to see if Commander participants is outdated
			for participant in self.participants:
				if participant.discordID not in vOpDataPlayerIDs:
					self.participants.remove(participant)

					bRequiresUpdate = True

			# Check to see if new participants need to be added
			for newParticipantID in vOpDataPlayerIDs:
				if newParticipantID not in vCommanderPlayerIDs:
					member = vGuild.get_member(newParticipantID)
					if member != None:
						self.participants.append( Participant(discordID=newParticipantID, discordUser=member) )
					bRequiresUpdate = True
		
		if not bRequiresUpdate:
			BUPrint.Debug("Participants Updated: No Update required.")
			return


		# UPDATE PARTICIPANTS
		vLibrariesToLoad:list[Participant] = [participant for participant in self.participants if participant.libraryEntry == None ]
		if botSettings.botFeatures.UserLibrary:
			await self.UpdateParticipants_UserLibs(vLibrariesToLoad)
		
		if self.vOpData.options.bIsPS2Event:
		
			vPS2CharactersToLoad:list[Participant] = [participant 
				for participant in self.participants 
				if participant.libraryEntry == None or participant.ps2CharID == -1
			]
		
			await self.UpdateParticiants_PS2Chars(vPS2CharactersToLoad)
		
			await self.vOpsEventTracker.CreateLoginTriggers(vPS2CharactersToLoad)
		

		BUPrint.Debug("Participants Updated!")



	async def UpdateParticiants_PS2Chars(self, p_participantsToUpdate:list[Participant]):
		"""# UPDATE PARTICIPANTS: PS2 CHARS
		Attempts to load the ps2 character objects for the passed participants.

		Called from within `UpdateParticipants`.

		NOTE: `UpdateParticipants_UserLibs` should be called before this.
		"""
		BUPrint.Debug("	-> Getting PS2 Character IDs")

		for participant in p_participantsToUpdate:

			if participant.libraryEntry != None and participant.libraryEntry.ps2ID != -1:
				participant.ps2CharID = participant.libraryEntry.ps2ID
				BUPrint.Debug(f"Participant {participant.discordUser.display_name} has a set PS2 character ID. Using it...")
				continue

			charName = re.sub(r'\[\w\w\w\w\]', "", participant.discordUser.display_name )
			charName = charName.strip()
			
			if participant.libraryEntry == None and botSettings.botFeatures.UserLibrary:
				participant.libraryEntry = User(discordID=participant.discordID)

				if participant.libraryEntry.ps2ID == -1:
					if charName == participant.lastCheckedName:
						BUPrint.Debug("Participant name is same as last checked name.  Skipping...")
						continue

					vPlayerChar = await self.vAuraxClient.get_by_name(auraxium.ps2.Character, charName)
					
					if vPlayerChar == None:
						BUPrint.Debug(f"{participant.discordUser.display_name}'s name does not match a PS2 character!")
						continue
					participant.ps2CharID = vPlayerChar.id
					
					
					participant.libraryEntry.ps2ID = vPlayerChar.id
					participant.libraryEntry.ps2Name = charName

					if UserLib.bCommanderCanAutoCreate:
						userManager.UserLibrary.SaveEntry(participant.libraryEntry)

					participant.ps2CharID = vPlayerChar.id

			else:
				vPlayerChar = await self.vAuraxClient.get_by_name(auraxium.ps2.Character, charName)	
				
				if vPlayerChar == None:
					BUPrint.Debug(f"Participant {participant.discordUser.display_name} doesn't have a name that matches a PS2 character.")
					continue
				else:
					participant.ps2CharID = vPlayerChar.id
		
			participant.lastCheckedName = charName



	async def UpdateParticipants_UserLibs(self, p_participantsToUpdate:list[Participant]):
		"""# UPDATE PARTICIPANTS: USER LIBRARY

		Called from within `UpdateParticipants`.
	
		Attempts to load the library object for the passed participants.
		"""
		for participant in p_participantsToUpdate:
			participant.libraryEntry = userManager.UserLibrary.LoadEntry(participant.discordID)



	async def UpdateCommanderInfo(self):
		"""# UPDATE COMMANDER INFO:
		Updates the commaner's info message.

		If no message is present, this function creates one.
		"""
		if self.commanderInfoMsg == None:
			self.commanderInfoMsg = await self.commanderChannel.send(content=f"{self.vOpData.managedBy}", embed=self.CreateEmbed_Info())
		else:
			await self.commanderInfoMsg.edit(embed=self.CreateEmbed_Info())

	

	async def UpdateCommanderLive(self):
		"""# UPDATE COMMANDER: LIVE
		Updates the connections/sessions message.

		If no message is present, this function creates one.
		"""
		vEmbeds = [self.CreateEmbed_Connections()]

		if self.vOpData.options.bIsPS2Event:
			vEmbeds.append( self.CreateEmbed_Session() )

		if self.commanderMsg == None:
			self.commanderMsg = await self.commanderChannel.send(content="**OP COMMANDER**", embeds=vEmbeds, view=self.CreateCommanderView())
		else:
			await self.commanderMsg.edit(embeds=vEmbeds, view=self.CreateCommanderView())



	async def UpdateCommander(self):
		"""# UPDATE COMMANDER
		Convenience function that calls both update functions.
		"""
		BUPrint.Debug("Updating entire commander")
		await self.UpdateCommanderInfo()
		await self.UpdateCommanderLive()



	async def MoveUsers(self, p_isMovingToStandby: bool):
		"""# MOVE USERS
		Parameter: p_isMovingToStandby: when true, users are moved to the standby.
			When false, users are moved to the event end channel instead.

		Regardless of auto-vc move setting, when moving to event end channel users are always moved, since the channels will be removed.
		"""
		if p_isMovingToStandby and not commanderSettings.bAutoMoveVCEnabled:
			BUPrint.Debug("Automove is disabled for moving to standby channel.")
			return

		vUsersToMove:list[discord.Member] = []
		vParticipantIDs = self.vOpData.GetParticipantIDs()
		vGuild = await GetGuild(self.vBotRef)

		if p_isMovingToStandby:
			for voiceChannel in vGuild.voice_channels:
				for member in voiceChannel.members:
					if member.id in vParticipantIDs:
						vUsersToMove.append(member)
		else:
			for voiceChannel in self.vCategory.voice_channels:
				for member in voiceChannel.members:
					vUsersToMove.append(member)


		movebackChannel = None
		if self.vOpData.options.bIsPS2Event:
			movebackChannel = vGuild.get_channel(Channels.eventMovebackID)
		else:
			movebackChannel = vGuild.get_channel(Channels.voiceFallbackID)
		
		try:
			for member in vUsersToMove:
				if p_isMovingToStandby:
					await member.move_to(self.standbyChn)
				else:
					await member.move_to(movebackChannel)
		except discord.Forbidden as error:
			BUPrint.LogErrorExc("Invalid permission to move user.", error)
			return
		except discord.HTTPException as error:
			BUPrint.LogError("Discord encountered an error while attempting to move a user.", error)
			return
			


	def CheckAttendance(self):
		"""# CHECK ATTENDANCE
		Iterates through the current participants and sets their attended/late booleans.
		"""
		if not botSettings.botFeatures.UserLibrary or commanderSettings.markedPresent == PS2EventTrackOptions.Disabled:
			BUPrint.Debug("User Library (or attendance checking) disabled, skipping attendance")
			return

		for participant in  self.participants:
			# IN GAME ONLY:
			if commanderSettings.markedPresent == PS2EventTrackOptions.InGameOnly:
				if participant.bPS2Online:
					if self.bAttendanceChecked:
						participant.bAttended = True
						participant.bWasLate = True
					else:
						participant.bAttended = True
				continue


			if commanderSettings.markedPresent == PS2EventTrackOptions.InGameAndDiscordVoice:
				if participant.bPS2Online and participant.discordUser.voice != None:
					if participant.discordUser.voice.channel in self.vCategory.voice_channels:
						if self.bAttendanceChecked:
							participant.bAttended = True
							participant.bWasLate = True
						else:
							participant.bAttended = True
				
				continue



	async def CreateChannels(self):
		"""# CREATE CHANNELS:
		Creates the commander channels, including both voice and text channels.
		If existing category and channels are found, they are used instead.
		"""
		vGuild = await GetGuild(self.vBotRef)
		try:
			for category in vGuild.categories:
				if category.name.lower() == self.vOpData.name.lower():
					self.vCategory = category
			
			if self.vCategory == None:
				BUPrint.Debug("No existing category found, creating new one.")
				self.vCategory = await vGuild.create_category(
					name=self.vOpData.name,
					reason=f"Creating category for {self.vOpData.name} event",
					overwrites=ChanPermOverWrite.level3
				)

			vChannelsToCreate:list[str] = []

			# CREATE TEXT CHANNELS:
			for channel in self.vCategory.text_channels:
				if channel.name.lower() == commanderSettings.defaultChannels.notifChannel.lower():
					self.notifChn = channel
					BUPrint.Debug("Existing Notification Channel found.")

				elif channel.name.lower() == commanderSettings.defaultChannels.opCommander.lower():
					self.commanderChannel = channel
					BUPrint.Debug("Existing Commander Channel found.")

			# Commander Channel
			if self.commanderChannel == None:
				self.commanderChannel = await self.vCategory.create_text_channel(
					name=commanderSettings.defaultChannels.opCommander,
					overwrites=ChanPermOverWrite.level2
					)

			# Notifications channel
			if self.notifChn == None:
				self.notifChn = await self.vCategory.create_text_channel(
					name=commanderSettings.defaultChannels.notifChannel,
					overwrites=ChanPermOverWrite.level3_readOnly
					)
			

			# CREATE VOICE CHANNELS
			existingVoiceChannels = [voiceChan.name for voiceChan in self.vCategory.voice_channels]

			if self.vOpData.voiceChannels.__len__() == 0:
				vChannelsToCreate = commanderSettings.defaultChannels.voiceChannels + commanderSettings.defaultChannels.persistentVoice
				BUPrint.Debug(f"Voice Channels not specified, using default: {vChannelsToCreate}")
			else:
				vChannelsToCreate = self.vOpData.voiceChannels + commanderSettings.defaultChannels.persistentVoice
				BUPrint.Debug(f"Voice Channels specified, creating: {vChannelsToCreate}")

			# Create standby:
			for channel in self.vCategory.voice_channels:
				if channel.name == commanderSettings.defaultChannels.standByChannel:
					self.standbyChn = channel
					break

			if self.standbyChn == None:
				self.standbyChn = await self.vCategory.create_voice_channel(commanderSettings.defaultChannels.standByChannel)
				
			
			# Create normal channels:
			BUPrint.Debug(f"Chanels to create: {vChannelsToCreate}")
			for chanToCreate in vChannelsToCreate:
				if chanToCreate not in existingVoiceChannels and chanToCreate != "":
					await self.vCategory.create_voice_channel(name=chanToCreate)
		
		except discord.Forbidden as error:
			BUPrint.LogErrorExc("Invalid permission to create channels.", error)
			return
		except discord.HTTPException as error:
			BUPrint.LogErrorExc("Discord failed to create the channels.", error)
			return



	async def DeleteChannels(self):
		"""# DELETE CHANELS
		Should be called AFTER moveUsers.
		Deletes the voice channels, then the text channels before finally removing the category itself.
		"""
		BUPrint.Debug(f"Removing channels for {self.vCategory.name}")

		for voiceChan in self.vCategory.voice_channels:
			try:
				await voiceChan.delete()
			except discord.Forbidden as error:
				BUPrint.LogErrorExc("Invalid permissions to delete channels!", error)
				continue
			except discord.HTTPException as error:
				BUPrint.LogErrorExc(f"Discord failed to delete a channel {voiceChan.name}!", error)
				continue

		for textChan in self.vCategory.text_channels:
			try:
				await textChan.delete()
			except discord.Forbidden as error:
				BUPrint.LogErrorExc("Invalid permissions to delete channels!", error)
				continue
			except discord.HTTPException as error:
				BUPrint.LogErrorExc(f"Discord failed to delete a channel {textChan.name}!", error)
				continue

		if self.vCategory.text_channels.__len__() == 0 and self.vCategory.voice_channels.__len__() == 0:
			await self.vCategory.delete()



	def CreateEmbed_Info(self):
		"""# CREATE EMBED: INFO
		
		Creates and returns an embed containing op info.
		"""
		vEmbed = discord.Embed(colour=Colours.commander.value, title=f"**OPERATION INFO** | {self.vOpData.name}")

		# OPTIONS & DATA
		vTempStr = ""
		if self.vOpData.options.bAutoStart:
			vTempStr += "Autostart *Enabled*\n"
		else:
			vTempStr += "Autostart *Disbaled*\n"

		if self.vOpData.options.bUseReserve:
			vTempStr += "Reserve: *Enabled*\n"
		else:
			vTempStr += "Reserve: *Disabled*\n"

		if self.vOpData.options.bUseSoberdogsFeedback:
			vTempStr += "Feedback: *Soberdogs*\n"
		else:
			vTempStr += "Feedback: *Standard*\n"

		if commanderSettings.bAutoMoveVCEnabled:
			vTempStr += "AutoVC Move: *Enabled*\n"
		else:
			vTempStr += "AutoVC Move: *Disabled*\n"

		# START | SIGNED UP
		vEmbed.add_field(
			name=f"Start {GetDiscordTime(self.vOpData.date, DateFormat.Dynamic)}", 
			value=f"{GetDiscordTime(self.vOpData.date, DateFormat.DateTimeLong)}\n{vTempStr}", 
			inline=True
		)
		
		vTempStr = "Auto Alerts Disabled"
		if commanderSettings.bAutoAlertsEnabled:
			vTempStr = f"Auto Alerts Enabled\nSending: *{commanderSettings.autoAlertCount}*\n"

			self.alertTimes.reverse()
			alertTime: datetime
			iteration = 1
			for alertTime in self.alertTimes:
				vTempStr += f"**{iteration}**: {GetDiscordTime(alertTime, DateFormat.Dynamic )}\n"
				iteration += 1

		vEmbed.add_field(
			name="Alerts", 
			value=vTempStr
		)
		
		vSignedUpCount = 0
		vLimitedRoleCount = 0
		vFilledLimitedRole = 0
		vOpenRole = 0
		role: OpRoleData
		for role in self.vOpData.roles:
			vSignedUpCount += len(role.players)
			if role.maxPositions > 0:
				vLimitedRoleCount += role.maxPositions
				vFilledLimitedRole += len(role.players)
			elif role.maxPositions < 0:
				vOpenRole += 1

		vEmbed.add_field(
			name="ROLE OVERVIEW",
			value=f"Total Players: *{vSignedUpCount}*\nRoles: *{len(self.vOpData.roles)}*\nRole Spaces: *{vFilledLimitedRole}/{vLimitedRoleCount}*\nOpen Roles: *{vOpenRole}*",
			inline=True
			)
		
		usersInReserve = "*Disabled*"
		if self.vOpData.options.bUseReserve:
			if len(self.vOpData.reserves) != 0:
				usersInReserve = ""
				for user in self.vOpData.reserves:
					usersInReserve += f"{self.vBotRef.get_user(int(user)).mention}\n"
			else: usersInReserve = "*None*"


		vEmbed.add_field(
			name=f"RESERVES: {len(self.vOpData.reserves)}",
			value=usersInReserve,
			inline=True
			)


		bFirstRole = self.vOpData.options.bUseReserve
		role: OpRoleData
		for role in self.vOpData.roles:
			
			vUsersInRole = "*None*"
			if len(role.players) != 0:
				vUsersInRole = ""
				for user in role.players:
					vUsersInRole += f"{self.vBotRef.get_user(int(user)).mention}\n"
				
			vEmbed.add_field( 
				name=f"{role.GetRoleName()}", 
				value=vUsersInRole, 
				inline=bFirstRole
			)
			bFirstRole = True


		return vEmbed



	def CreateEmbed_Connections(self):
		"""# CREATE EMBED: CONNECTIONS
		
		Creates and returns an embed containing participant connection information.
		"""
		vEmbed = discord.Embed(colour=discord.Colour.from_rgb(200, 200, 255), title="CONNECTIONS", description="Discord and PS2 connection information for participants.")

		vPlayersStr = "\u200b\n"
		vStatusStr = f"{commanderSettings.connIcon_discord} | {commanderSettings.connIcon_voice} | {commanderSettings.connIcon_ps2}\n"

		for participant in self.participants:

			vPlayersStr += f"{participant.discordUser.display_name}\n"
			
			if participant.discordUser.status == discord.Status.offline:
				vStatusStr += f"{commanderSettings.connIcon_discordOffline} | "
			else:
				vStatusStr += f"{commanderSettings.connIcon_discordOnline} | "


			if participant.discordUser.voice == None:
				vStatusStr += f"{commanderSettings.connIcon_voiceDisconnected} | "
			elif participant.bInEventChannel:
				vStatusStr += f"{commanderSettings.connIcon_voiceConnected} | "
			else:
				vStatusStr += f"{commanderSettings.connIcon_voiceNotEventChan} | "


			if participant.libraryEntry != None and participant.libraryEntry.ps2ID != -1:
				if participant.bPS2Online == True:
					vStatusStr += f"{commanderSettings.connIcon_ps2Online}"
				else:
					vStatusStr += f"{commanderSettings.connIcon_ps2Offline}"

			else:
				vStatusStr += f"{commanderSettings.connIcon_ps2Invalid}"

			
			if botSettings.botFeatures.UserLibrary:
				if participant.libraryEntry != None and participant.libraryEntry.bIsRecruit:
					vStatusStr += f" | {commanderSettings.connIcon_ps2Recruit}"

			vStatusStr += "\n"

		vEmbed.add_field(name="PLAYERS", value=vPlayersStr)
		vEmbed.add_field(name=f"STATUS:", value=vStatusStr)

		vEmbed.set_footer(text=f"Last update: {datetime.now(tz=timezone.utc)}")

		return vEmbed



	def CreateEmbed_Session(self):
		"""# GENERATE EMBED: Session
		Creates and returns an embed containing session information.
		Only shows if the operation is for Planetside 2.
		"""
		vTempStr = ""
		vEmbed = discord.Embed(colour=discord.Colour.from_rgb(200, 200, 255), title="SESSION", 
		description=f"Status: {self.vCommanderStatus.name} | DataPoints: {str(self.vOpsEventTracker.eventPoints.__len__())}")

		vEmbed.add_field(
			name="Facilities...",
			value=f"Captured: {self.vOpsEventTracker.facilitiesCaptured}\nDefended: {self.vOpsEventTracker.faciltiiesDefended}",
			inline=True
		)

		if self.vOpsEventTracker.facilityFeed.__len__() != 0:
			for feedEntry in self.vOpsEventTracker.facilityFeed:
				vTempStr += f"{feedEntry}\n"
				vTempStr = vTempStr[:1024]
		
			vEmbed.add_field(
				name="Facility Feed",
				value=vTempStr,
				inline= True
			)

		vEmbed.set_footer(text=f"Last update: {datetime.now(tz=timezone.utc)}")
		return vEmbed



	async def SendReminder(self):
		"""# SEND REMINDER:
		Sends a reminder to the notification channel, only including nessecery pings.
		"""
		roleMentions = [f"{role.mention} " for role in self.vBotRef.get_guild(botSettings.discordGuild).roles if role.name in self.vOpData.pingables ]

		vParticipantMentions = self.GetParticipantMentions()
		spareSpaces = ""

		for role in self.vOpData.roles:
			if role.players.__len__() < role.maxPositions or role.maxPositions < 0:
				spareSpaces += f"**Role:** {role.roleName} has {role.maxPositions - role.players.__len__()} available spots!\n"

		# Compile message
		vMessage = f"**REMINDER** | {self.vOpData.name} starts in {GetDiscordTime(self.vOpData.date)}!"
		
		if vParticipantMentions != "":
			vMessage += f"\n\nPlease ensure you are online and ready to go, {vParticipantMentions}"

		if commanderSettings.bAutoMoveVCEnabled:
			vMessage += f"{botMessages.OpsAutoMoveWarn}\n"
		
		if spareSpaces != "":
			vMessage += "\n\n**ATTENTION** "
			for pingableRole in roleMentions:
				vMessage += f"{pingableRole}"

			vMessage += f"\nThe following roles still have open spaces!\n{spareSpaces}"


		vView = discord.ui.View(timeout=None)
		vView.add_item( discord.ui.Button(
				label="Go to signup",
				url=self.vOpData.jumpURL
			) 
		)

		if self.lastStartAlert != None:
			await self.lastStartAlert.delete()

		self.lastStartAlert = await self.notifChn.send(content=vMessage, view=vView)



	async def SendStartedAlert(self):
		"""# SEND STARTED ALERT
		Sends an alert notification only including 
		"""
		vParticipantMentions = self.GetParticipantMentions()

		if self.lastStartAlert != None:
			await self.lastStartAlert.delete()

		if vParticipantMentions.__len__() == 0:
			self.lastStartAlert = await self.notifChn.send(f"{self.vOpData.name} is starting!")
		else:
			self.lastStartAlert = await self.notifChn.send(f"**ATTENTION** {vParticipantMentions}, {self.vOpData.name} has *started!*")



	def AuraxClientUnavailableRetry(self):
		"""# AURAX CLIENT UNAVAILABLE: RETRY
		Called from the event tracker when adding triggers, if the service is unavailable.
		Creates a new task that recalls create triggers with a delay of x minutes.
		"""
		self.scheduler.add_job(
			OpsEventTracker.CreateTriggers,
			"date", run_date=datetime.now(timezone.utc) + timedelta(minutes=5),
			args=[self.vOpsEventTracker]
		)



	def GetParticipantMentions(self, p_getAll:bool = False):
		"""# GET PARTICIPANT MENTIONS
		Returns a string of participant mentions, matching the Commander settings.
		The list only includes mentions for users who are not matching the setting (or all, if disabled)

		### Parameters:
		- p_getAll: when true, gets all participant mentions.  Defaults to false.
		"""
		vParticipantMentions:list[str]

		if p_getAll or commanderSettings.markedPresent == PS2EventTrackOptions.Disabled:
			vParticipantMentions = [ f"{participant.discordUser.mention} " for participant in self.participants]

		elif commanderSettings.markedPresent == PS2EventTrackOptions.InGameOnly:
			vParticipantMentions = [ f"{participant.discordUser.mention} " for participant in self.participants if not participant.bPS2Online ]

		elif commanderSettings.markedPresent == PS2EventTrackOptions.InGameAndDiscordVoice:
			vParticipantMentions = [ f"{participant.discordUser.mention} " for participant in self.participants if not participant.bPS2Online or participant.discordUser.voice == None]


		returnStr = ""
		for mention in vParticipantMentions:
			returnStr += mention

		return returnStr



	def CreateCommanderView(self):
		"""
		# CREATE COMMANDER VIEW

		Creates a commander view.  Buttons status are updated depending on Op Status

		## RETURNS: `discord.ui.View`
		"""

		newView = discord.ui.View(timeout=None)
		# Button Objects
		btnStart = Commander_btnStart(self)
		btnEnd = Commander_btnEnd(self)
		btnDebrief = Commander_btnDebrief(self)
		btnDownloadDebrief = Commander_btnDownloadFeedback(self)
		btnNotify = Commander_btnNotify(self)

	
		# Before op Started:
		if self.vCommanderStatus.value < CommanderStatus.Started.value:
			btnEnd.disabled = True
			btnDebrief.disabled = True
			newView.add_item(btnStart)
			newView.add_item(btnNotify)

		# Ops Started:
		elif self.vCommanderStatus == CommanderStatus.Started:
			btnStart.disabled = True
			btnDebrief.disabled = False
			btnEnd.disabled = False
			newView.add_item(btnDebrief)
			newView.add_item(btnEnd)

		# Debrief:
		elif self.vCommanderStatus == CommanderStatus.Debrief:
			btnStart.disabled = True
			btnDebrief.disabled = True
			btnEnd.disabled = False
			newView.add_item(btnDownloadDebrief)
			newView.add_item(btnEnd)

		newView.add_item(discord.ui.Button(
							label="HELP",
							emoji="❓",
							url="https://github.com/LCWilliams/planetside-discord-bot/wiki/Op-Commander"
					)
		)

		return newView




	async def CreateFeedback(self):
		"""# CREATE FEEDBACK
		Takes the feedback provided and sends it to the appropriate channel, then updates the commander."""
		vFeedbackMsg = "**FEEDBACK:**\n"
		for feedback in self.vFeedback.generic:
			if feedback != "":
				vFeedbackMsg += f"{feedback}\n"

		if self.vOpData.options.bIsPS2Event:
			vFeedbackMsg += "**FOR SQUADMATES:**\n"
			for feedback in self.vFeedback.forSquadmates:
				if feedback != "":
					vFeedbackMsg += f"{feedback}\n"

			vFeedbackMsg += "**FOR SQUAD LEAD:**\n"
			for feedback in self.vFeedback.forSquadLead:
				if feedback != "":
					vFeedbackMsg += f"{feedback}\n"

			vFeedbackMsg += "**FOR PLATOON LEAD:**\n"
			for feedback in self.vFeedback.forPlatLead:
				if feedback != "":
					vFeedbackMsg += f"{feedback}\n"

		feedbackFile = discord.File( self.vFeedback.SaveToFile(f"{Directories.feedbackPrefix}{self.vOpData.fileName}") )

		if vFeedbackMsg.__len__() > 2000: # greater than discords max message limit
			vFeedbackMsg = vFeedbackMsg[:1900] + "\n\n**Feedback is too large!**\nDownload file to see entire message."


		if self.vOpData.options.bUseSoberdogsFeedback:
			if self.soberdogFeedbackMsg == None:
				self.soberdogFeedbackMsg = await self.soberdogFeedbackThread.send(content=vFeedbackMsg, file=feedbackFile)

			else:
				await self.soberdogFeedbackMsg.edit(content=vFeedbackMsg, attachments=[feedbackFile])

		# Guard catch; allows suberdogs feedback to be updated since its a persistent channel, but prevents errors when not soberfeedback
		if self.vCommanderStatus.Ended:
			BUPrint.Debug("User submitting feedback after event has ended, returning.")
			return

		else:
			if self.notifFeedbackMsg == None:
				self.notifFeedbackMsg = await self.notifChn.send(content=vFeedbackMsg, file=feedbackFile)
			
			else:
				await self.notifFeedbackMsg.edit(content=vFeedbackMsg, attachments=[feedbackFile])


		await self.UpdateCommanderLive()


############  COMMANDER BUTTON CLASSES

class Commander_btnStart(discord.ui.Button):
	def __init__(self, p_commanderParent:Commander):
		self.vCommander:Commander = p_commanderParent
		super().__init__(label="START", emoji="🔘", row=0, style=discord.ButtonStyle.green)

	async def callback(self, p_interaction:discord.Interaction):
		await p_interaction.response.defer(ephemeral=True, thinking=True)
		
		await self.vCommander.StartEvent()

		try:
			await p_interaction.edit_original_response(content="Event Started!")
		except discord.errors.NotFound:
			BUPrint.Info("Discord Error; took too long for a response. Safe to Ignore.")



class Commander_btnDebrief(discord.ui.Button):
	def __init__(self, p_commanderParent:Commander):
		self.vCommander:Commander = p_commanderParent
		super().__init__(label="DEBRIEF", emoji="🗳️", row=0)

	async def callback(self, p_interaction:discord.Interaction):
		self.vCommander.vCommanderStatus = CommanderStatus.Debrief
		# Updates the commander view.
		await p_interaction.response.send_message("Debrief Started...", ephemeral=True)
		# await p_interaction.response.defer()
		feedbackView = discord.ui.View(timeout=None)
		feedbackView.add_item(Commander_btnGiveFeedback(self.vCommander))
		await self.vCommander.notifChn.send(f"{self.vCommander.GetParticipantMentions(True)}\n\nUse this button to provide feedback!", view=feedbackView)




class Commander_btnNotify(discord.ui.Button):
	def __init__(self, p_commanderParent:Commander):
		self.vCommander:Commander = p_commanderParent
		super().__init__(label="NOTIFY", emoji="📨", row=0)

	async def callback(self, p_interaction:discord.Interaction):
		await self.vCommander.SendReminder()
		await p_interaction.response.send_message("Reminder sent!", ephemeral=True)
	



class Commander_btnEnd(discord.ui.Button):
	def __init__(self, p_commanderParent:Commander):
		self.vCommander:Commander = p_commanderParent
		super().__init__(label="END", emoji="🛑", row=0, style=discord.ButtonStyle.danger)

	async def callback(self, p_interaction:discord.Interaction):
		# End the Ops:
		await p_interaction.response.send_message("Ending Operation...", ephemeral=True)
		
		# Remove commander from Live list:
		commanderRef = opsManager.OperationManager.FindCommander(self.vCommander.vOpData)
		if commanderRef != None:
			opsManager.OperationManager.vLiveCommanders.remove(commanderRef)
		
		await self.vCommander.EndEvent()



class Commander_btnGiveFeedback(discord.ui.Button):
	def __init__(self, p_commanderParent:Commander):
		self.vCommander:Commander = p_commanderParent
		super().__init__(label="FEEDBACK", emoji="🗳️", row=0)

	async def callback(self, p_interaction:discord.Interaction):
		await p_interaction.response.send_modal( FeedbackModal(self.vCommander, p_interaction.user) )



class Commander_btnDownloadFeedback(discord.ui.Button):
	def __init__(self, p_commanderParent:Commander):
		self.vCommander:Commander = p_commanderParent
		super().__init__(label="DOWNLOAD FEEDBACK", emoji="💾", row=0)


	async def callback(self, p_interaction:discord.Interaction):
		if len(self.vCommander.vFeedback.userID) == 0:
			await p_interaction.response.send_message("No user feedback yet!", ephemeral=True)
			return


		vFilePath = self.vCommander.vFeedback.SaveToFile(self.vCommander.vOpData.fileName)
		if vFilePath != "":
			vMessage = ""

			await p_interaction.response.send_message(f"{vMessage}\nDownload feedback here:", file=discord.File(vFilePath))
		else:
			await p_interaction.response.send_message("Unable to save the feedback to file.", ephemeral=True)



# # # # # FEEDBACK MODAL

class FeedbackModal(discord.ui.Modal):
	# Text inputs
	txt_general = discord.ui.TextInput(
			label="General Feedback",
			style=discord.TextStyle.paragraph,
			required=False,
			placeholder="Feedback about the event as a whole."
	)

	txt_squadMates = discord.ui.TextInput(
			label="Squadmate Feedback",
			style=discord.TextStyle.paragraph,
			required=False,
			placeholder="Feedback for your fellow squadmates."
	)

	txt_squadLead = discord.ui.TextInput(
			label="Squad Lead Feedback",
			style=discord.TextStyle.paragraph,
			required=False,
			placeholder="Feedback for the squad lead."
	)

	txt_platLead = discord.ui.TextInput(
			label="Platoon Lead Feedback",
			style=discord.TextStyle.paragraph,
			required=False,
			placeholder="Feedback for the platoon lead."
	)

	def __init__(self, p_parentCommander:Commander , p_callingUser:discord.User):
		self.parentCommander = p_parentCommander
		self.foundUserID = -1
		self.bIsPS2Event = self.parentCommander.vOpData.options.bIsPS2Event
		self.PropogateFields(p_callingUser.id)

		if self.bIsPS2Event:
			self.remove_item(self.txt_squadLead)
			self.remove_item(self.txt_squadMates)
			self.remove_item(self.txt_platLead)

		super().__init__(title="Feedback", timeout=None)

	async def on_submit(self, pInteraction:discord.Interaction):
		if self.foundUserID == -1:
			BUPrint.Debug("No user ID found; new feedback entry...")
			self.parentCommander.vFeedback.userID.append(pInteraction.user.id)
			self.parentCommander.vFeedback.generic.append(f"{self.txt_general.value}")
			if self.bIsPS2Event:
				self.parentCommander.vFeedback.forSquadmates.append(f"{self.txt_squadMates.value}")
				self.parentCommander.vFeedback.forSquadLead.append(f"{self.txt_squadLead.value}")
				self.parentCommander.vFeedback.forPlatLead.append(f"{self.txt_platLead.value}")

		else:
			BUPrint.Debug(f"Found user ID at position {self.foundUserID}, updating entry...")
			self.parentCommander.vFeedback.generic[self.foundUserID] = self.txt_general.value
			if self.bIsPS2Event:
				self.parentCommander.vFeedback.forSquadmates[self.foundUserID] = self.txt_squadMates.value
				self.parentCommander.vFeedback.forSquadLead[self.foundUserID] = self.txt_squadLead.value
				self.parentCommander.vFeedback.forPlatLead[self.foundUserID] = self.txt_platLead.value


		await self.parentCommander.CreateFeedback()
		await pInteraction.response.send_message("Thank you, your feedback has been submited!", ephemeral=True)


	def PropogateFields(self, p_userID:int):
		"""
		# PROPOGATE FIELDS
		Finds the user ID and pre-sets the fields if present.
		"""
		feedback = self.parentCommander.vFeedback

		# Get position of user:

		index = 0
		for userID in self.parentCommander.vFeedback.userID:
			if userID == p_userID:
				self.foundUserID = index
				break
			index += 1

		if self.foundUserID != -1:
			self.txt_general.default = feedback.generic[index]
			if self.bIsPS2Event:
				self.txt_squadMates.default = feedback.forSquadmates[index]
				self.txt_squadLead.default = feedback.forSquadLead[index]
				self.txt_platLead.default = feedback.forPlatLead[index]