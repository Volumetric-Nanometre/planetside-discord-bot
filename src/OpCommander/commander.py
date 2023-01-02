# OPS COMMANDER
# Provides a simple interface that allows those with permissions to:
# Alert -> Starts an alert coroutine, users signed up are pinged at 10 minute intervals.  Channels are created in prep.
# Start Ops -> Self explanitory, starts an op event.
# Debrief -> Begin a debrief process; after 5 minutes normal users are moved to 'planetside' channel, commanders are moved to 'command' channel, channels are cleaned up.
#			 Users are offered the ability to provide anonymised feedback via the bot regarding the event.  This is fed to the command channel.
# End Ops -> Removes the signup.


# EMBEDS:
# 1. OpInfo Embed: show if any options applied, signed up users
# 2. Connection Embed: Show status of signed up users (discord online|discord comms|Online Ingame)
# 3. SessionStats Embed: Start time, end time, user stats, link to Honu.
# 4. SessionFeedback: Place to store player feedback.

import discord
import discord.ext
from discord.ext import tasks, commands
import auraxium

import re
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import datetime, dateutil.relativedelta

from OpCommander.events import OpsEventTracker
from OpCommander.dataObjects import CommanderStatus
from OpCommander.dataObjects import Participant
import OpCommander.dataObjects

import botUtils
from botUtils import BotPrinter as BUPrint
from botUtils import ChannelPermOverwrites as ChanPermOverWrite

from botData.settings import BotSettings as botSettings
from botData.settings import Commander as commanderSettings
from botData.settings import PS2EventTrackOptions
from botData.settings import Messages as botMessages
from botData.settings import Directories

import botData.operations
from botData.operations import OperationData as OpsData
from botData.users import User as UserEntry

import opsManager

async def StartCommander(p_opData: OpsData):
	"""
	# START COMMANDER
	Self explanitory, calling this will start the commander for the given ops file.
	
	Starting a commander does NOT start an Ops.  That is a different event, handled by the commander itself (if bAutoStart is enabled in both op settings and botsettings).
	"""

	# CHECKS:
	if p_opData == None:
		BUPrint.Info("Invalid OpData given.  Not starting commander.")
		return

	if len(p_opData.GetParticipantIDs()) == 0:
		BUPrint.Info("Cannot start an event with 0 participants.  Not starting commander.")
		return


	BUPrint.Debug(f"Starting commander for {p_opData.fileName}!")
	vNewCommander = Commander(p_opData)
	await vNewCommander.CommanderSetup()
	opsManager.OperationManager.vLiveCommanders.append(vNewCommander)
	# Don't call `commander.GenerateCommander()` here! CommanderSetup handles this.



class Commander():
	"""
	# COMMANDER
	Class containing functions and members used during a live, running Operation
	"""
	vBotRef: commands.Bot
	def __init__(self, p_opData: OpsData) -> None:
		BUPrint.Info("Ops Commander created")
		self.vOpData : OpsData = p_opData
		self.vCommanderStatus = CommanderStatus.Init
		self.vFeedback = OpCommander.dataObjects.OpFeedback()
		self.bFeedbackTooLarge = False # Set to true if feedback is too large for an embed.
		self.bHasSoftEnded = False # Set to true if soft ended (debriefed.)

		# Auraxium client & Op event tracker
		self.vAuraxClient = auraxium.EventClient()
		self.vOpsEventTracker = OpsEventTracker(p_aurClient=self.vAuraxClient)

		# Alert & Autostart Scheduler
		self.scheduler = AsyncIOScheduler()
		self.alertTimes = [] # Saved to be displayed in Info embed

		#DiscordElements:
		self.commanderInfoMsg : discord.Message = None # Message object for the Info embed.
		self.commanderMsg: discord.Message = None # Message object used to edit the commander. Set during first post.
		self.commanderChannel: discord.TextChannel = None # Channel for the Commander to be posted in.
		self.notifChn: discord.TextChannel = None # Channel used to display notifications
		self.vCategory: discord.CategoryChannel = None # Category object to keep the Ops self contained. All channels are created within here, except soberdogs feedback
		self.standbyChn: discord.VoiceChannel = None # Standby channel voice connected users are moved into during start.
		self.lastStartAlert: discord.Message = None # Last Start alert sent, used to store + remove a previous alert to not flood the channel.
		self.participants = [Participant] # List of Participant objects.
		self.notifFeedbackMsg: discord.Message = None # Message for non-soberdogs Feedback.
		
		# Soberdogs Discord Elements, saved here to avoid repeated fetching.
		self.soberdogFeedbackForum: discord.ForumChannel = None # Forum for soberdogs Debriefs.
		self.soberdogFeedbackThread : discord.Thread = None # Thread holding the feedback message. Also used to get a jump-link for the notif channel button.
		self.soberdogFeedbackMsg: discord.Message = None # Message for the soberdogs Feedback.



	async def GenerateCommander(self):
		"""
		# GENERATE COMMANDER

		Updates an existing Commander, using the current status.
		The commander does not include the INFO embed, since it does not need to be updated.

		`commanderMsg` must be a valid discord.Message before this is called.

		If the Ops has not started, no embeds are added.  
		"""
		vMessageView = self.GenerateView_Commander()
		vEmbeds:list = []
		vMessageContent = "**OP COMMANDER**\n\n"
		
		# Pre-Started display
		if self.vCommanderStatus.value == CommanderStatus.WarmingUp.value:
			vEmbeds.append (await self.GenerateEmbed_Connections())
			if commanderSettings.bAutoAlertsEnabled:
				vMessageContent += botMessages.commanderAutoStart

		elif self.vCommanderStatus == CommanderStatus.Started:
			vEmbeds.append( await self.GenerateEmbed_Connections())
			if commanderSettings.trackEvent != PS2EventTrackOptions.Disabled:
				vEmbeds.append( self.GenerateEmbed_Session() )
		
		elif self.vCommanderStatus == CommanderStatus.Debrief:
			# vEmbeds.append(self.GenerateEmbed_Session())
			vEmbeds.append(self.GenerateEmbed_Feedback())


		await self.commanderMsg.edit(content=vMessageContent, view=vMessageView, embeds=vEmbeds)


	async def CommanderSetup(self):
		"""
		# COMMANDER SETUP
		Sets up the commander for the operation (category & channels), should only be called once.
		"""
		if(self.vCommanderStatus == CommanderStatus.Init):
			BUPrint.Info("Operation Commander first run setup...")
			# Perform first run actions.
			
			# Get & set guild ref.
			vGuild = await botUtils.GetGuild(self.vBotRef)

			# Create category and channels.
			await self.CreateCategory()
			await self.CreateTextChannels()
			await self.CreateVoiceChannels()
			
			# Setup Alerts
			BUPrint.Debug("Configuring Scheduler...")

			if commanderSettings.bAutoAlertsEnabled:
				intervalTime = commanderSettings.autoPrestart / commanderSettings.autoAlertCount
				setIntervals = 0
				lastInterval = self.vOpData.date
			
				while setIntervals < commanderSettings.autoAlertCount:
					lastInterval = lastInterval - dateutil.relativedelta.relativedelta(minutes=intervalTime)

					self.alertTimes.append(lastInterval)
					BUPrint.Debug(f"AutoAlert Interval: {lastInterval}")
					self.scheduler.add_job( Commander.SendAlertMessage, 'date', run_date=lastInterval, args=[self] )
					setIntervals += 1
			
			
			# Setup AutoStart
			if self.vOpData.options.bAutoStart and commanderSettings.bAutoStartEnabled:
				BUPrint.Debug(f"Commander set to Start Operation at {self.vOpData.date}")
				self.scheduler.add_job( Commander.StartOperation, 'date', run_date=self.vOpData.date, args=[self])

			
			# Setup Connections Refresh
			if commanderSettings.connectionRefreshInterval != 0:
				self.scheduler.add_job( Commander.GenerateCommander, 
					"interval", 
					seconds=commanderSettings.connectionRefreshInterval,
					end_date=self.vOpData.date,
					args=[self], 
					id="ConnectionRefresh"
				)
	
			self.scheduler.start()


			# Update Signup Post with new Status.
			self.vOpData.status = OpsData.status.prestart
			vOpMan = opsManager.OperationManager()
			await vOpMan.UpdateMessage(self.vOpData)

			BUPrint.Debug("	-> Posting Ops Info")
			await self.GenerateInfo()

			#Post standby commander, to set commander messageID; all future calls should use GenerateCommander instead.
			BUPrint.Debug("	-> Posting Commander")
			vCommanderMsg = f"**COMMANDER ON STANDBY**\n"
			if commanderSettings.bAutoStartEnabled:
				vCommanderMsg += botMessages.commanderAutoStart
			self.commanderMsg =  await self.commanderChannel.send(vCommanderMsg, view=self.GenerateView_Commander())

			# Set to WarmingUp and return.
			self.vCommanderStatus = CommanderStatus.WarmingUp

		else:
			BUPrint.LogError("Commander has already been set up!")


	async def CreateCategory(self):
		"""
		# CREATE CATEGORY
		Creates a category to self-contain the Op.
		If an existing category with the same name exists, that is used instead.

		## RETURN: `bool` True if successful.
		"""
		vGuild:discord.Guild = await botUtils.GetGuild(self.vBotRef)
		
		for category in vGuild.categories:
			if category.name.lower() == self.vOpData.name.lower():
				self.vCategory = category
				BUPrint.Debug("Existing category with matching name found.  Using it instead.")
				return True

		# No existing category, create one.
		if self.vCategory == None:
			BUPrint.Debug("No existing category with matching name, creating as normal")

			if self.vCategory == None:
				BUPrint.Debug("	-> Create category.")
				try:
					self.vCategory = await vGuild.create_category(
						name=f"{self.vOpData.name}",
						reason=f"Creating category for {self.vOpData.fileName}",
						overwrites=ChanPermOverWrite.level3
					)
				except discord.Forbidden as error:
					BUPrint.LogErrorExc("	-> Unable to create category; invalid permissions!", error)
					return False
				except discord.HTTPException as error:
					BUPrint.LogErrorExc("	-> Invalid form", error)
					return False
				except TypeError as error:
					BUPrint.LogErrorExc("	-> Invalid permission overwrites", error)
					return False


	async def CreateTextChannels(self):
		"""
		# CREATE TEXT CHANNELS
		Creates text channels used for the Operation.
		If existing channels are found, they are used instead.
		"""
		bFoundCommander = False
		bFoundNotif = False
		# Find existing Commander & Notif channels
		for txtChannel in self.vCategory.text_channels:
			if txtChannel.name.lower() == botData.operations.DefaultChannels.opCommander.lower():
				BUPrint.Debug("Existing op commander channel found in category, using that instead.")
				self.commanderChannel = txtChannel
				await self.commanderChannel.purge()
				bFoundCommander = True

			if txtChannel.name.lower() == botData.operations.DefaultChannels.notifChannel.lower():
				BUPrint.Debug("Existing notification channel found in category, using that instead.")
				self.notifChn = txtChannel
				await self.notifChn.purge()
				bFoundNotif = True

			if bFoundNotif and bFoundCommander:
				BUPrint.Debug("Found Commander and Notification channels. Exiting loop.")
				break

		# Manually create Commander & Notif channel if not already present
		if self.commanderChannel == None:
			self.commanderChannel = await self.vCategory.create_text_channel(
				name=botData.operations.DefaultChannels.opCommander,
				overwrites=ChanPermOverWrite.level2
			)

		if self.notifChn == None:
			self.notifChn = await self.vCategory.create_text_channel(
				name=botData.operations.DefaultChannels.notifChannel,
				overwrites=ChanPermOverWrite.level3_readOnly
			)

		# Add non-existing channels for custom text channels
		txtChannelName:str
		for txtChannelName in botData.operations.DefaultChannels.textChannels:
			if txtChannelName.lower() not in self.vCategory.text_channels:
				await self.vCategory.create_text_channel(
					name=txtChannelName,
					overwrites=ChanPermOverWrite.level3
				)


	async def CreateVoiceChannels(self):
		"""
		# CRETE VOICE CHANNELS
		Creates voice channels used for the Ops.
		Voice channels include persistent and custom entries.
		"""
		# Create always present voice channels:
		bAlreadyExists = False
		for existingChannel in self.vCategory.voice_channels:
			if existingChannel.name.lower() == botData.operations.DefaultChannels.standByChannel.lower():
				bAlreadyExists = True
				BUPrint.Debug("Existing standby channel found.")
				self.standbyChn = existingChannel
				break

		if self.standbyChn == None:
			self.standbyChn = await self.vCategory.create_voice_channel(name=botData.operations.DefaultChannels.standByChannel)

		BUPrint.Debug("	-> Creating default chanels")
		if len(botData.operations.DefaultChannels.persistentVoice) != 0:
			for newChannel in botData.operations.DefaultChannels.persistentVoice:

				bAlreadyExists = False
				for existingChannel in self.vCategory.voice_channels:
					if existingChannel.name == newChannel:
						bAlreadyExists = True
						BUPrint.Debug(f"Existing channel for: {newChannel} found.")
						break

				if not bAlreadyExists:
					BUPrint.Debug(f"No existing channel for {newChannel} found.  Creating new voice channel!")
					channel:discord.VoiceChannel = await self.vCategory.create_voice_channel(name=newChannel)


		# Create custom voice channels if present
		if len(self.vOpData.voiceChannels) != 0 and self.vOpData.voiceChannels[0] != "":
			BUPrint.Debug("	-> Voice channels specified...")
			newChannel:str
			for newChannel in self.vOpData.voiceChannels:
				BUPrint.Debug(f"	-> Adding channel: {newChannel}")

				bAlreadyExists = False
				for existingChannel in self.vCategory.voice_channels:
					if existingChannel.name.lower() == newChannel.lower():
						bAlreadyExists = True
						BUPrint.Debug(f"Existing channel for: {newChannel} found.")
						break

				if not bAlreadyExists:
					BUPrint.Debug(f"No existing channel for {newChannel} found.  Creating new voice channel!")
					channel = await self.vCategory.create_voice_channel(name=newChannel)
		
		
		else: # No custom voice channels given, use default
		
			BUPrint.Debug("	-> No voice channels specified, using defaults...")
			for newChannel in botData.operations.DefaultChannels.voiceChannels:
				BUPrint.Debug(f"	-> Adding channel: {newChannel}")
	
				bAlreadyExists = False
				for existingChannel in self.vCategory.voice_channels:
					if existingChannel.name == newChannel:
						bAlreadyExists = True
						BUPrint.Debug(f"Existing channel for: {newChannel} found.")
						break

				if not bAlreadyExists:
					BUPrint.Debug(f"No existing channel for {newChannel} found.  Creating new voice channel!")
					channel = await self.vCategory.create_voice_channel(name=newChannel)
	
	
	async def RemoveChannels(self):
		"""
		# REMOVE CHANNELS
		Removes the channels and category related to the Ops.
		"""
		BUPrint.Debug("Removing Channels")

		# Remove Text channels
		for textChannel in self.vCategory.text_channels:
			BUPrint.Debug(f"	-> Removing {textChannel.name}")
			await textChannel.delete(reason="Op Commander ending & removing channels")

		# Get all connected users.
		userList = []
		voiceChannel: discord.VoiceChannel
		for voiceChannel in self.vCategory.voice_channels:
			userList += voiceChannel.members

		# Get fallback channel		
		user:discord.Member
		fallbackChannel = self.vBotRef.get_channel(botSettings.fallbackVoiceChat)

		# Move connected users to fallback channel
		for user in userList:
			BUPrint.Debug(f"Attempting to move {user.display_name} to fallback channel.")
			await user.move_to(channel=fallbackChannel, reason="Op Commander ending: moving user from Ops channel to fallback.")

		# Remove channels
		for voiceChannel in self.vCategory.voice_channels:
			await voiceChannel.delete(reason="Op Commander Ending: removing voice channels.")

		for textChannel in self.vCategory.text_channels:
			await textChannel.delete(reason="Op Commander ending: removing text channels.")

		# Remove empty category
		await self.vCategory.delete(reason="Op Commander ending: removing category.")

		#removethisinamoment
		await self.vAuraxClient.close()



	async def GenerateAlertMessage(self):
		"""
		# GENERATE ALERT MESSAGE
		Convenience function to generate a pre-formatted message string for pre-start alerts.
		"""
		vRoleMentionPing = ""
		if len(self.vOpData.pingables) != 0:
			vGuild:discord.Guild = await botUtils.GetGuild(self.vBotRef)

			rolePing:str
			for rolePing in self.vOpData.pingables:
				discordRole:discord.Role = discord.utils.find(lambda role: role.name.lower() == rolePing.lower(), vGuild.roles)
				if discordRole != None:
					vRoleMentionPing += f"{discordRole.mention} "

		vMessage = f"**REMINDER: {self.vOpData.name} STARTS {botUtils.DateFormatter.GetDiscordTime( self.vOpData.date, botUtils.DateFormat.Dynamic )}**\n"

		vMessage += f"{vRoleMentionPing}|{self.GetParticipantMentions()}"

		notTrackedParticipants = ""
		for participant in self.participants:
			if participant.libraryEntry == None or participant.ps2Char == None:
				notTrackedParticipants += f"{participant.discordUser.mention} "

		if notTrackedParticipants != "":
			vMessage += f"**ATTENTION**\n{notTrackedParticipants}\n{botMessages.noMatchingPS2Char}\n\n"

		if commanderSettings.bAutoMoveVCEnabled:
			vMessage += f"\n\n*{botMessages.OpsAutoMoveWarn}*\n\n"


		opRole: botData.operations.OpRoleData
		for opRole in self.vOpData.roles:
			if len(opRole.players) < opRole.maxPositions and opRole.maxPositions > 0:
				vMessage += f"**{opRole.roleName}** currently has **{opRole.maxPositions - len(opRole.players)}** available spaces!\n"
				continue
			
			if opRole.maxPositions < 0:
				vMessage += f"{opRole.roleName} is **open**!"


		return vMessage


	async def GenerateStartAlertMessage(self):
		"""
		# GENERATE START ALERT MESSAGE
		Convenience function to generate a pre-formatted message string for ops Started alert.
		"""
		vParticipantsStr = self.GetParticipantMentions()

		vMessage = f"**{self.vOpData.name} HAS STARTED!**\n\n{vParticipantsStr}\n"

		notTrackedParticipants = ""

		for participant in self.participants:
			if participant.libraryEntry == None or participant.ps2Char == None:
				notTrackedParticipants += f"{participant.discordUser.mention} "

		if notTrackedParticipants != "":
			vMessage += f"\n\n\n**ATTENTION**\n{notTrackedParticipants}\n{botMessages.noMatchingPS2Char}\n\n"

		
		return vMessage


	async def SendAlertMessage(self, p_opStart:bool = False):
		"""
		# SEND ALERT MESSAGE
		Set p_opStart to TRUE to send an Op Started alert instead.
		"""
		if self.lastStartAlert != None:
			BUPrint.Debug("Removing previous alert message.")
			await self.lastStartAlert.delete()

		await self.UpdateParticipants()
		
		BUPrint.Info(f"Sending Alert message for {self.vOpData.name}")
		if p_opStart: # Send START alert.
			self.lastStartAlert = await self.notifChn.send( await self.GenerateStartAlertMessage() )
		else: # Send REMINDER alert
			self.lastStartAlert = await self.notifChn.send(content=await self.GenerateAlertMessage(), view=self.GenerateView_Alerts() )



	def GetParticipantMentions(self):
		"""
		# GET PARTICIPANT MENTIONS

		Returns a string of `member.mention` for all participants.
		"""
		vMentionStr = ""

		for participantObj in self.participants:
			if participantObj.discordUser != None:
				vMentionStr += f"{participantObj.discordUser.mention} "

		return vMentionStr



	async def UpdateParticipants(self):
		"""
		# UPDATE PARTICIPANTS

		Updates `self.participants` to match with the users in the opData.
		"""
		vParticipantIDs = self.vOpData.GetParticipantIDs()
		BUPrint.Debug(f"Updating Participants : {vParticipantIDs}")

		# FIRST RUN:
		if len(self.participants) == 0:
			BUPrint.Debug("	-> Updating Participants: First Run")

			for userID in vParticipantIDs:
				newParticipant = Participant(discordID=userID)
				self.participants.append(newParticipant)

		else:
			BUPrint.Debug("	-> Checking resigned participants")
			# Check if current participant has resigned & remove.
			for vParticipantObj in self.participants:
				if vParticipantObj.discordID not in vParticipantIDs:
					BUPrint.Debug(f"Participant: {vParticipantObj.discordID} not in list of Participant IDs, removing from list.")
					self.participants.remove(vParticipantObj)

			BUPrint.Debug("	-> Checking for new participants")
			# Check if list of participant IDs is not in self.participants.
			for participantID in vParticipantIDs:
				if participantID not in vParticipantIDs:
					BUPrint.Debug(f"Participant {participantID} is being added")
					newParticipant = Participant(discordID=participantID)
					self.participants.append(newParticipant)


		await self.LoadParticipantData()



	async def UpdateParticipantTracking(self):
		"""
		# UPDATE PARTICIPANT TRACKING

		If enabled, recursively check participants and enable tracking depending on the setting.
		"""

		if not commanderSettings.trackEvent == PS2EventTrackOptions.Disabled and self.vOpData.options.bIsPS2Event:
			for participantObj in self.participants:
				participantObj: Participant

				if participantObj.ps2Char == None:
					participantObj.bIsTracking = False
					continue
				try:
					if commanderSettings.trackEvent == PS2EventTrackOptions.InGameOnly:
						
						if await participantObj.ps2Char.is_online():
							participantObj.bIsTracking = True

					elif commanderSettings.trackEvent == PS2EventTrackOptions.InGameAndDiscordVoice:
						if await participantObj.ps2Char.is_online() and participantObj.discordUser.voice != None:
							participantObj.bIsTracking = True
				except auraxium.errors.AuraxiumException as vError:
					BUPrint.LogErrorExc("Unable to determine if user is online.", vError)


	async def LoadParticipantData(self):
		"""
		# LOAD PARTICIPANT DATA

		Recursively checks all Participant objects and loads them if they're not already populated.
		"""
		vGuild = await botUtils.GetGuild(self.vBotRef)

		BUPrint.Debug("Loading participant data...")
		for participantObj in self.participants:
			BUPrint.Debug(f"User with ID: {participantObj.discordID}")

			if participantObj.discordUser == None:
				BUPrint.Debug("	-> Discord User not set, getting...")
				participantObj.discordUser = vGuild.get_member(participantObj.discordID)

			if participantObj.libraryEntry == None:
				BUPrint.Debug("	-> Library Entry not set. Loading...")
				participantObj.LoadParticipant()

			if participantObj.ps2Char == None:
				BUPrint.Debug("	-> PS2 Character not set, setting...")
				participantObj.ps2Char = await self.GetParticipantPS2Char(participantObj)

				# If still none, set tracking to false:
				if participantObj.ps2Char == None:
					participantObj.bIsTracking = False


	async def GetParticipantPS2Char(self, p_participant: Participant):
		"""
		# GET PARTICIPANT PLANETSIDE 2 CHARACTER
		If an existing library entry is present, it is used to get the character name.
		If no library entry is found, or the player name is blank, the participants display name is used instead.

		## RETURNS:
		`auraxium.ps2.Character` for the participant.
		"""


		bExistingLibraryEntry = True
		if p_participant.libraryEntry == None:
			bExistingLibraryEntry = False


		if not bExistingLibraryEntry or p_participant.libraryEntry.ps2Name == "":
			charName = re.sub(r'\[\w\w\w\w\]', "", p_participant.discordUser.display_name )
			charName = charName.strip()

			if charName == p_participant.lastCheckedName:
				BUPrint.Debug("User hasn't renamed since last check.")
				return None


			BUPrint.Debug(f"Searching for PS2 Character: {charName}")
			playerChar = await self.vAuraxClient.get_by_name(auraxium.ps2.Character, charName)				

			if playerChar == None:
				BUPrint.Debug("	-> No PS2 character found.")
				p_participant.bIsTracking = False
				p_participant.lastCheckedName = charName
				return

			else:
				BUPrint.Debug("	-> PS2 Character found!")
				p_participant.libraryEntry = UserEntry(discordID=p_participant.discordID, ps2Name=charName)
				
				if commanderSettings.bAutoCreateUserLibEntry:
					BUPrint.Debug("Saving new user Entry:")
					p_participant.SaveParticipant()

				return playerChar

		else: # Name already exists in userLibrary
			BUPrint.Debug(f"	-> Character name is already set: {p_participant.libraryEntry.ps2Name}")
			playerChar = await self.vAuraxClient.get_by_name(auraxium.ps2.Character, p_participant.libraryEntry.ps2Name)
			if playerChar != None:
				return playerChar

	
	
	async def GenerateInfo(self):
		"""
		# GENERATE INFO:
		Sends/Updates the Info embed.
		"""	
		if self.commanderInfoMsg == None:
			vGuild = await botUtils.GetGuild(self.vBotRef)

			opString = f"*OPERATION INFORMATION for {self.vOpData.name}*"
			managingUser = vGuild.get_member(self.vOpData.managedBy)

			if managingUser != None:
				opString = f"{managingUser.mention} {opString}"
	
			self.commanderInfoMsg = await self.commanderChannel.send(content=opString, embed=self.GenerateEmbed_OpInfo() )
		else:
			await self.commanderInfoMsg.edit(embed=self.GenerateEmbed_OpInfo())


	def GenerateEmbed_OpInfo(self):
		"""
		# GENERATE EMBED : OpInfo

		Creates an Embed for Operation Info.
		"""
		vEmbed = discord.Embed(colour=botUtils.Colours.commander.value, title=f"**OPERATION INFO** | {self.vOpData.name}")

		# START | SIGNED UP
		vEmbed.add_field(
			name=f"Start {botUtils.DateFormatter.GetDiscordTime(self.vOpData.date, botUtils.DateFormat.Dynamic)}", 
			value=f"{botUtils.DateFormatter.GetDiscordTime(self.vOpData.date, botUtils.DateFormat.DateTimeLong)}", 
			inline=True
		)

		# DISPLAY OPTIONS & DATA
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

		vEmbed.add_field(
			name="OPTIONS", 
			value=vTempStr
		)
		
		vTempStr = "Auto Alerts Disabled"
		if commanderSettings.bAutoAlertsEnabled:
			vTempStr = f"Auto Alerts Enabled\nSending: *{commanderSettings.autoAlertCount}*\n"

			self.alertTimes.reverse()
			alertTime: datetime
			iteration = 1
			for alertTime in self.alertTimes:
				vTempStr += f"**{iteration}**: {botUtils.DateFormatter.GetDiscordTime(alertTime, botUtils.DateFormat.Dynamic )}\n"
				iteration += 1

		vEmbed.add_field(
			name="Alerts", 
			value=vTempStr
		)
		
		vSignedUpCount = 0
		vLimitedRoleCount = 0
		vFilledLimitedRole = 0
		vOpenRole = 0
		role: botData.operations.OpRoleData
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
		role: botData.operations.OpRoleData
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



	async def GenerateEmbed_Connections(self):
		"""
		# GENERATE EMBED : OpInfo

		Creates an Embed for player connections.
		"""
		await self.UpdateParticipants()

		vEmbed = discord.Embed(colour=discord.Colour.from_rgb(200, 200, 255), title="CONNECTIONS", description="Discord and PS2 connection information for participants.")

		vPlayersStr = "\u200b\n"
		vStatusStr = f"{commanderSettings.connIcon_discord} | {commanderSettings.connIcon_voice} | {commanderSettings.connIcon_ps2}\n"

		for participant in self.participants:
			vPlayersStr += f"{participant.discordUser.display_name}\n"
			
			BUPrint.Debug(f"Status of {participant.discordUser.display_name}: {participant.discordUser.status}")
			if participant.discordUser.status.value == discord.Status.offline.value:
				vStatusStr += f"{commanderSettings.connIcon_discordOffline} | "
			else:
				vStatusStr += f"{commanderSettings.connIcon_discordOnline} | "


			if participant.discordUser.voice == None:
				vStatusStr += f"{commanderSettings.connIcon_voiceDisconnected} | "
			else:
				vStatusStr += f"{commanderSettings.connIcon_voiceConnected} | "


			if participant.ps2Char != None:
				try:
					isOnline = await participant.ps2Char.is_online()
					if isOnline:
						vStatusStr += f"{commanderSettings.connIcon_ps2Online}\n"
					else:
						vStatusStr += f"{commanderSettings.connIcon_ps2Offline}\n"
				except:
					vStatusStr += f"{commanderSettings.connIcon_ps2Invalid}\n"


			else:
				vStatusStr += f"{commanderSettings.connIcon_ps2Invalid}\n"



		vEmbed.add_field(name="PLAYERS", value=vPlayersStr)
		vEmbed.add_field(name=f"STATUS:", value=vStatusStr)

		vEmbed.set_footer(text=f"Last update: {datetime.datetime.now()}")

		return vEmbed



	def GenerateEmbed_Session(self):
		"""
		# GENERATE EMBED : Session

		Creates an Embed for displaying session stats.
		"""
		vEmbed = discord.Embed(colour=discord.Colour.from_rgb(200, 200, 255), title="SESSION", description="Displays session stats.")

		vEmbed.add_field(name="Empty field", value="empty field")


		vEmbed.set_footer(text=f"Last update: {datetime.datetime.now()}")
		return vEmbed



	def GenerateEmbed_Feedback(self):
		"""
		# GENERATE EMBED : Feedback

		Creates an Embed for displaying player provided feedback, offering anonymity.
		"""
		vEmbed = discord.Embed(title="FEEDBACK", description="Player provided feedback")

		tempStr = ""
		for entry in self.vFeedback.generic:
			if entry != "" and entry != "\n":
				tempStr += f"{entry}\n"
		
		if tempStr != "" and entry != "\n":
			if len(tempStr) > 1024:
				tempStr[:1024]
				self.bFeedbackTooLarge = True
			vEmbed.add_field(name="General", value=tempStr, inline=False)

		
		tempStr = ""
		for entry in self.vFeedback.forSquadmates:
			if entry != "" and entry != "\n":
				tempStr += f"{entry}\n"
		
		if tempStr != "" and entry != "\n":
			if len(tempStr) > 1024:
				tempStr[:1024]
				self.bFeedbackTooLarge = True
			vEmbed.add_field(name="To Squad Mates", value=tempStr, inline=False)


		tempStr = ""
		for entry in self.vFeedback.forSquadLead:
			if entry != "" and entry != "\n":
				tempStr += f"{entry}\n"
		
		if tempStr != "" and entry != "\n":
			if len(tempStr) > 1024:
				tempStr[:1024]
				self.bFeedbackTooLarge = True
			vEmbed.add_field(name="To Squad Lead", value=tempStr, inline=False)


		tempStr = ""
		for entry in self.vFeedback.forPlatLead:
			if entry != "" and entry != "\n":
				tempStr += f"{entry}\n"
		
		if tempStr != "" and entry != "\n":
			if len(tempStr) > 1024:
				tempStr[:1024]
				self.bFeedbackTooLarge = True
			vEmbed.add_field(name="To Platoon Lead", value=tempStr, inline=False)

		if self.bFeedbackTooLarge:
			vEmbed.add_field(name="OVERFLOW WARNING", value=botMessages.feedbackOverflow)

		return vEmbed



	def GenerateView_UserFeedback(self):
		"""
		GENERATE VIEW: User Feedback:

		Creates a view providing a button to users to send feedback.
		"""
		vView = discord.ui.View(timeout=None)
		vView.add_item( Commander_btnGiveFeedback(self) )

		return vView



	async def GenerateFeedback(self):
		"""
		# GENERATE FEEDBACK
		Sends/Updates the feedback message.
		"""

		vFeedbackEmbed = self.GenerateEmbed_Feedback()

		if self.vOpData.options.bUseSoberdogsFeedback:
			if self.soberdogFeedbackMsg == None:
				self.soberdogFeedbackMsg = await self.soberdogFeedbackThread.send(embed=vFeedbackEmbed)

			else:
				if self.vCommanderStatus == CommanderStatus.Ended and self.bFeedbackTooLarge:
					
					vFilePath = self.vFeedback.SaveToFile(self.vOpData.fileName)
					if vFilePath != "":
						await self.soberdogFeedbackMsg.edit(embed=vFeedbackEmbed, attachments=discord.File(vFilePath))

				else:
					await self.soberdogFeedbackMsg.edit(embed=vFeedbackEmbed)

		else:
			if self.notifFeedbackMsg == None:
				self.notifFeedbackMsg = await self.notifChn.send(embed=vFeedbackEmbed)
			
			else:
				await self.notifFeedbackMsg.edit(embed=vFeedbackEmbed)


		await self.GenerateCommander()




	async def SetupFeedback(self):
		"""
		# SETUP FEEDBACK
		Performs the initial set up required to post and send a debrief feedback message.

		This includes setting the forum variable via finding, and thread variable via creation.

		This does NOT post a message and thus, does not set soberdogsFeedbackMsg.
		It DOES however create the SoberDogs forum thread.

		If using soberdogs but it isn't found or postable, fallback to using the default (off).
		"""
		await self.EndOperationSoft()
		
		if not self.vOpData.options.bUseSoberdogsFeedback:
			BUPrint.Debug("Not using SoberDogs feedback.  No setup needed.")
			return
		
		if self.soberdogFeedbackForum == None:
			vAllForums = self.vBotRef.guilds[0].forums
			forum: discord.ForumChannel
			for forum in vAllForums:
				if forum.id == commanderSettings.soberFeedbackID:
					self.soberdogFeedbackForum = forum
					break
			
			if self.soberdogFeedbackForum == None:
				BUPrint.Info("Unable to find Soberdogs Feedback Forum, falling back to default.")
				self.vOpData.options.bUseSoberdogsFeedback = False
				return
			
			vManagingUser = ""
			if self.vOpData.managedBy != "":
				vManagingUser = self.vBotRef.get_user( self.vOpData.managedBy ).mention
	
			try:
				self.soberdogFeedbackThread = await self.soberdogFeedbackForum.create_thread(
														name=f"{self.vOpData.date.year}-{self.vOpData.date.month}-{self.vOpData.date.day} Soberdogs",
														auto_archive_duration=None,
														reason="Soberdogs Debrief post",
														content=f"Managed By: {vManagingUser}\n{self.GetParticipantMentions()}"
														)

			except discord.Forbidden:
				BUPrint.LogError("Invalid permissions for posting threads! Falling back to default")
				self.vOpData.options.bUseSoberdogsFeedback = False
				return

			except discord.HTTPException as vException:
				BUPrint.LogErrorExc("Failed to start a new thread; falling back to default.", vException)
				self.vOpData.options.bUseSoberdogsFeedback = False
				return



	def GenerateView_Commander(self):
		"""
		# GENERATE VIEW: COMMANDER

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
		elif self.vCommanderStatus.value == CommanderStatus.Started.value:
			btnStart.disabled = True
			btnDebrief.disabled = False
			btnEnd.disabled = False
			newView.add_item(btnDebrief)
			newView.add_item(btnEnd)

		# Debrief:
		elif self.vCommanderStatus.value == CommanderStatus.Debrief.value:
			btnStart.disabled = True
			btnDebrief.disabled = True
			btnEnd.disabled = False
			newView.add_item(btnDownloadDebrief)
			newView.add_item(btnEnd)


		return newView


	def GenerateView_Alerts(self):
		"""
		# GENERATE VIEW: Alerts
		Generates a view with a button to jump to the related signup post.
		"""
		vView = discord.ui.View()
		btnJump = discord.ui.Button(label="Jump to signup", url=self.vOpData.jumpURL, row=0)

		vView.add_item(btnJump)

		return vView


	async def StartOperation(self):
		"""
		# START OPERATION
		Modifies and updates op signup post.
		
		Modifies commander status, then updates commander.
		
		Starts tracking, if enabled.
		"""
		if self.vOpData.status.value >= OpsData.status.started.value:
			BUPrint.Debug("Operation has already been started. Skipping.")
			return

		# If early start; stop connection refresh
		vSchedJob = self.scheduler.get_job("ConnectionRefresh")
		if vSchedJob != None:
			BUPrint.Debug("Event started early; stopping `ConnectionRefresh` job.")
			self.scheduler.remove_job("ConnectionRefresh")

		await self.UpdateParticipants()

		if commanderSettings.trackEvent != PS2EventTrackOptions.Disabled:
			# TODO: start tracking here.
			await self.UpdateParticipantTracking()
			# self.vOpsEventTracker.start()

		if commanderSettings.bAutoMoveVCEnabled:
			BUPrint.Debug("Moving VC connected participants")
			await self.MoveUsers(p_moveToStandby=True)

		await self.SendAlertMessage(p_opStart=True)
		self.vOpData.status = OpsData.status.started
		vOpMan = opsManager.OperationManager()
		await vOpMan.UpdateMessage(self.vOpData)
		self.vCommanderStatus = CommanderStatus.Started
		await self.GenerateCommander()



	async def EndOperationSoft(self):
		"""
		# SOFT END OPERATION
		Performs minor cleanup, during debrief.
		"""
		await self.vAuraxClient.close()
		self.scheduler.shutdown()

		self.bHasSoftEnded = True
	

	async def EndOperation(self):
		"""
		# END OPERATION
		Removes the live Op from the Operations manager, 
		then cleans up the Op Commander.
		"""
		self.vCommanderStatus = CommanderStatus.Ended

		if not self.bHasSoftEnded:
			await self.EndOperationSoft()

		# Removes the operation posting.
		vOpMan = opsManager.OperationManager()
		await vOpMan.RemoveOperation(self.vOpData)

		# Move users before removing channels.
		await self.MoveUsers(p_moveToStandby=False)
		
		# Yeetus deleetus the category; as if it never happened!
		await self.RemoveChannels()

		BUPrint.Info(f"Operation {self.vOpData.name} has ended.")



	async def MoveUsers(self, p_moveToStandby:bool = True):
		"""
		# MOVE USERS
		Moves currently connected users to the standby channel.
		`p_moveToStandby` : If false, users are instead moved to the fallback channel.
		"""
		if not commanderSettings.bAutoMoveVCEnabled and p_moveToStandby:
			BUPrint.Debug("Auto move disabled.")
			return
		
		vGuild:discord.Guild = await botUtils.GetGuild(self.vBotRef)

		fallbackChannel = vGuild.get_channel(commanderSettings.autoMoveBackChannelID)

		if fallbackChannel == None:
			fallbackChannel = await vGuild.fetch_channel(commanderSettings.autoMoveBackChannelID)
			if fallbackChannel == None:
				BUPrint.Info("ATTENTION!  Invalid Auto Move-back Channel ID provided!")
				fallbackChannel = await vGuild.fetch_channel(botSettings.fallbackVoiceChat)
				if fallbackChannel == None:
					BUPrint.Info("ATTENTION! Invalid fallback channel ID provided!  Unable to automatically move users.")
					return

		vConnectedUsers = []

		if p_moveToStandby: # Moving signed up users to standby
			vParticipantIDs = self.vOpData.GetParticipantIDs()
			for voiceChannel in vGuild.voice_channels:
				for user in voiceChannel.members:
					if user.id in vParticipantIDs:
						vConnectedUsers.append(user)


		else: # Moving users in event channels to fallback.
			for voiceChannel in self.vCategory.voice_channels:
				vConnectedUsers += voiceChannel.members


		user: discord.Member
		for user in vConnectedUsers:
			try:
				if p_moveToStandby:
					BUPrint.Debug(f"Moving {[user.display_name]} to standby channel ({self.standbyChn.name})")
					await user.move_to(channel=self.standbyChn)
				else:
					BUPrint.Debug(f"Moving {[user.display_name]} to fallback channel ({fallbackChannel.name})")
					await user.move_to(channel=fallbackChannel)
			except discord.Forbidden as vError:
				BUPrint.LogErrorExc("Invalid access to move member!", vError)
				return
			except Exception as vError:
				BUPrint.LogErrorExc(f"Unable to move member {user.display_name} to Channel (Standby Chn: {p_moveToStandby}).", vError)
				return





############  COMMANDER BUTTON CLASSES

class Commander_btnStart(discord.ui.Button):
	def __init__(self, p_commanderParent:Commander):
		self.vCommander:Commander = p_commanderParent
		super().__init__(label="START", emoji="🔘", row=0, style=discord.ButtonStyle.green)

	async def callback(self, p_interaction:discord.Interaction):
		await p_interaction.response.defer()

		await self.vCommander.StartOperation()

		try:
			await p_interaction.response.send_message("Starting the event!", ephemeral=True)
		except discord.errors.NotFound:
			BUPrint.Info("Discord Error, response bugged out. Safe to Ignore.")



class Commander_btnDebrief(discord.ui.Button):
	def __init__(self, p_commanderParent:Commander):
		self.vCommander:Commander = p_commanderParent
		super().__init__(label="DEBRIEF", emoji="🗳️", row=0)

	async def callback(self, p_interaction:discord.Interaction):
		self.vCommander.vCommanderStatus = CommanderStatus.Debrief
		# Updates the commander view.
		# await p_interaction.response.send_message("Debrief Started...", ephemeral=True)
		await p_interaction.response.defer()

		await self.vCommander.GenerateCommander()


		await self.vCommander.SetupFeedback()
		await self.vCommander.GenerateFeedback()

		vView = self.vCommander.GenerateView_UserFeedback()
		await self.vCommander.notifChn.send(f"{self.vCommander.GetParticipantMentions()}\n\nUse this button to provide feedback!", view=vView)




class Commander_btnNotify(discord.ui.Button):
	def __init__(self, p_commanderParent:Commander):
		self.vCommander:Commander = p_commanderParent
		super().__init__(label="NOTIFY", emoji="📨", row=0)

	async def callback(self, p_interaction:discord.Interaction):
		await self.vCommander.SendAlertMessage()
		await p_interaction.response.defer()
	



class Commander_btnEnd(discord.ui.Button):
	def __init__(self, p_commanderParent:Commander):
		self.vCommander:Commander = p_commanderParent
		super().__init__(label="END", emoji="🛑", row=0)

	async def callback(self, p_interaction:discord.Interaction):
		# End the Ops:
		await p_interaction.response.send_message("Ending Operation...", ephemeral=True)
		
		# Remove commander from Live list:
		commanderRef = opsManager.OperationManager.FindCommander(self.vCommander.vOpData)
		if commanderRef != None:
			opsManager.OperationManager.vLiveCommanders.remove(commanderRef)
		
		await self.vCommander.EndOperation()




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
		vFilePath = self.vCommander.vFeedback.SaveToFile(self.vCommander.vOpData.fileName)
		if vFilePath != "":
			vMessage = ""

			if self.vCommander.vOpData.options.bUseSoberdogsFeedback and self.vCommander.bFeedbackTooLarge:
				vMessage = "**NOTE:** This file will also be uploaded to the matching thread when the event is ended."

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
		self.PropogateFields(p_callingUser.id)
		super().__init__(title="Feedback", timeout=None)

	async def on_submit(self, pInteraction:discord.Interaction):
		if self.foundUserID == -1:
			BUPrint.Debug("No user ID found; new feedback entry...")
			self.parentCommander.vFeedback.userID.append(pInteraction.user.id)
			self.parentCommander.vFeedback.generic.append(f"{self.txt_general.value}")
			self.parentCommander.vFeedback.forSquadmates.append(f"{self.txt_squadMates.value}")
			self.parentCommander.vFeedback.forSquadLead.append(f"{self.txt_squadLead.value}")
			self.parentCommander.vFeedback.forPlatLead.append(f"{self.txt_platLead.value}")

		else:
			BUPrint.Debug(f"Found user ID at position {self.foundUserID}, updating entry...")
			self.parentCommander.vFeedback.generic[self.foundUserID] = self.txt_general.value
			self.parentCommander.vFeedback.forSquadmates[self.foundUserID] = self.txt_squadMates.value
			self.parentCommander.vFeedback.forSquadLead[self.foundUserID] = self.txt_squadLead.value
			self.parentCommander.vFeedback.forPlatLead[self.foundUserID] = self.txt_platLead.value

		await self.parentCommander.GenerateFeedback()
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
			self.txt_squadMates.default = feedback.forSquadmates[index]
			self.txt_squadLead.default = feedback.forSquadLead[index]
			self.txt_platLead.default = feedback.forPlatLead[index]