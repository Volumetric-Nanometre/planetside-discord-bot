# OPS COMMANDER
# Provides a simple interface that allows those with permissions to:
# Alert -> Starts an alert coroutine, users signed up are pinged at 10 minute intervals.  Channels are created in prep.
# Start Ops -> Self explanitory, starts an op event.
# Debrief -> Begin a debrief process; after 5 minutes normal users are moved to 'planetside' channel, commanders are moved to 'command' channel, channels are cleaned up.
#			 Users are offered the ability to provide anonymised feedback via the bot regarding the event.  This is fed to the command channel.
# End Ops -> Removes the signup.

import discord
import discord.ext
from discord.ext import tasks, commands
import auraxium
from  OpCommander.events import OpsEventTracker

import enum
import sched

import botUtils
from botUtils import BotPrinter as BUPrint
import botData.settings as BotSettings
import botData.operations
from botData.operations import OperationData as OpsData
# from opsManager import OperationManager as OpsMan
from OpCommander.status import CommanderStatus


class Commander():
	"""
	# COMMANDER
	Class containing functions and members used during a live, running Operation
	"""
	vBotRef: commands.Bot
	def __init__(self, p_opData: OpsData) -> None:
		BUPrint.Info("Ops Commander created")
		self.vOpData : OpsData = p_opData # The OpData
		self.vCommanderStatus = CommanderStatus.Init

		# Auraxium client & Op event tracker
		self.vAuraxClient = auraxium.EventClient()
		self.vOpsEventTracker = OpsEventTracker(p_aurClient=self.vAuraxClient)


		#DiscordElements:
		self.vMessage : discord.Message = None # Message object used to edit. Set during first post.
		self.commanderChannel: discord.TextChannel = None # Channel for the Commander to be posted in.
		self.vCategory: discord.CategoryChannel = None # Category object to keep the Ops self contained. All channels are created within here, except non-soberdogs feedback


	async def GenerateCommander(self):
		"""
		# GENERATE COMMANDER

		Either creates, or updates an existing Commander view, using the current status.
		"""
		vMessageView = discord.ui.View(timeout=None)
		# add buttons here
		vEmbeds:list = []

		if self.vCommanderStatus.value < CommanderStatus.Started.value:
			vEmbeds.append( self.GenerateEmbed_OpInfo() )
			self.vMessage = await self.commanderChannel.send(view=vMessageView, embeds=vEmbeds)

	async def CommanderSetup(self):
		"""
		# COMMANDER SETUP
		Sets up the commander and operation, should only be called once.
		"""
		if(self.vCommanderStatus == CommanderStatus.Init):
			BUPrint.Info("Operation Commander first run setup...")
			# Perform first run actions.

			vGuild = await self.vBotRef.fetch_guild(BotSettings.BotSettings.discordGuild)
			serverRoles = await vGuild.fetch_roles()

			# Overwrite for general users, allowing them to see the ops category.			
			generalUserOverwrites:dict = {
				vGuild.default_role: discord.PermissionOverwrite(read_messages=False)
			}

			adminUserOverwrites:dict = {
				vGuild.default_role: discord.PermissionOverwrite(read_messages=False)
			}

			vAdminRoleList = BotSettings.BotSettings.roleRestrict_level_2 + BotSettings.BotSettings.roleRestrict_level_1 + BotSettings.BotSettings.roleRestrict_level_0
			
			vUserRoles = []
			vAdminRoles = []

			role: discord.Role
			for role in serverRoles:
				if role.id in BotSettings.BotSettings.roleRestrict_level_3 or role.name in BotSettings.BotSettings.roleRestrict_level_3:
					BUPrint.Debug(f"Adding USER role {role.name} to allowed.")
					vUserRoles.append(role)
					generalUserOverwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True, connect=True)
					adminUserOverwrites[role] = discord.PermissionOverwrite(read_messages=False, send_messages=False, connect=False)

				if role.id in vAdminRoleList or role.name in vAdminRoleList:
					BUPrint.Debug(f"Adding ADMIN role {role.name} to allowed")
					vAdminRoles.append(role)
					adminUserOverwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True, connect=True)



			if self.vCategory == None:
				BUPrint.Debug("	-> Create category.")
				try:
					self.vCategory = await vGuild.create_category(
						name=f"{self.vOpData.name}",
						reason=f"Creating category for {self.vOpData.fileName}",
						overwrites=generalUserOverwrites
					)
				except discord.Forbidden as error:
					BUPrint.LogErrorExc("	-> Unable to create category; invalid permissions!", error)
					return
				except discord.HTTPException as error:
					BUPrint.LogErrorExc("	-> Invalid form", error)
					return
				except TypeError as error:
					BUPrint.LogErrorExc("	-> Invalid permission overwrites", error)
					return

			# Add Commander text channel
			BUPrint.Debug("	-> Posting commander")
			self.commanderChannel = await self.vCategory.create_text_channel(name="OPS COMMANDER", overwrites=adminUserOverwrites)
			# await vCommanderChnl.send(f"**OPERATION COMMANDER** for {self.vOpData.name}", embed=self.GenerateEmbed_OpInfo(), view=vMessageView)

			# Create always present voice channels:
			BUPrint.Debug("	-> Creating default chanels")
			for newChannel in botData.operations.DefaultChannels.persistentVoice:
				channel:discord.VoiceChannel = await self.vCategory.create_voice_channel(name=newChannel)
				# for role in vUserRoles:
				# 	await channel.set_permissions(target=role, overwrite=generalUserOverwrites)

			# Create custom voice channels if present
			if len(self.vOpData.voiceChannels) != 0 and self.vOpData.voiceChannels[0] != "":
				BUPrint.Debug("	-> Voice channels specified...")
				for newChannel in self.vOpData.voiceChannels:
					BUPrint.Debug(f"	-> Adding channel: {newChannel}")
					channel = await self.vCategory.create_voice_channel(name=newChannel)
					# for role in vUserRoles:
					# 	await channel.set_permissions(target=role, overwrite=generalUserOverwrites)


			else: # No custom voice channels given, use default
				BUPrint.Debug("	-> No voice channels specified, using defaults...")
				for newChannel in botData.operations.DefaultChannels.voiceChannels:
					BUPrint.Debug(f"	-> Adding channel: {newChannel}")
					channel = await self.vCategory.create_voice_channel(name=newChannel)
					# for role in vUserRoles:
					# 	await channel.set_permissions(target=role, overwrite=generalUserOverwrites)


			# Set to standby and return.
			self.vCommanderStatus = CommanderStatus.Standby
			return

	async def RemoveChannels(self):
		"""
		# REMOVE CHANNELS
		Removes the channels and category related to the Ops.
		"""
		BUPrint.Debug("Removing Channels")

		# Remove Text channels
		for textChannel in self.vCategory.text_channels:
			BUPrint.Debug(f"	-> Removing {textChannel.name}")
			await textChannel.delete(reason="Op Commander removing channel.")

		# Get all connected users.
		userList = []
		voiceChannel: discord.VoiceChannel
		for voiceChannel in self.vCategory.voice_channels:
			userList += voiceChannel.members

		# Get fallback channel		
		user:discord.Member
		fallbackChannel = self.vBotRef.get_channel(BotSettings.BotSettings.fallbackVoiceChat)

		# Move connected users to fallback channel
		for user in userList:
			BUPrint.Debug(f"Attempting to move {user.display_name} to fallback channel.")
			await user.move_to(channel=fallbackChannel, reason="Moving user from Ops channel to fallback.")

		# Remove channels
		for voiceChannel in self.vCategory.voice_channels:
			await voiceChannel.delete(reason="Auto removal of channels after Operation end.")

		# Remove empty category
		await self.vCategory.delete(reason="Auto removal of category after Operation end.")

	def GenerateEmbed_OpInfo(self):
		"""
		# GENERATE EMBED : OpInfo

		Creates an Embed for Operation Info.
		"""
		vEmbed = discord.Embed(colour=botUtils.Colours.commander.value, title=f"**OPERATION INFO** | {self.vOpData.name}")

		# START | SIGNED UP
		vEmbed.add_field(
			name=f"START(ED) {botUtils.DateFormatter.GetDiscordTime(self.vOpData.date, botUtils.DateFormat.Dynamic)}", 
			value=f"{botUtils.DateFormatter.GetDiscordTime(self.vOpData.date, botUtils.DateFormat.DateTimeLong)}", 
			inline=True
		)
		
		vSignedUpCount = 0
		vLimitedRoleCount = 0
		vFilledLimitedRole = 0
		role: botData.operations.OpRoleData
		for role in self.vOpData.roles:
			vSignedUpCount += len(role.players)
			if role.maxPositions > 0:
				vLimitedRoleCount += vLimitedRoleCount
				vFilledLimitedRole += len(role.players)
		vEmbed.add_field(
			name="USERS | ROLES | RESERVES",
			value=f"{vSignedUpCount} | {len(self.vOpData.roles)}({vFilledLimitedRole}/{vLimitedRoleCount}) | {len(self.vOpData.reserves)}", 
			inline=True
		)

		# Only show verbose role info during the early stages.  Reduces clutter afterwards.
		if self.vCommanderStatus.value > CommanderStatus.Started.value:
			role: botData.operations.OpRoleData
			for role in self.vOpData.roles:
				vUsersInRole = ""
				for user in role.players:
					vUsersInRole += f"{self.vBotRef.get_user(int(user))}\n"
				vEmbed.add_field( name=f"{self.GetRoleName(role)}", value=vUsersInRole)

		return vEmbed

	def GenerateEmbed_Connections(self):
		"""
		# GENERATE EMBED : OpInfo

		Creates an Embed for player connections.
		"""
		pass

	def GenerateEmbed_Session(self):
		"""
		# GENERATE EMBED : Session

		Creates an Embed for displaying session stats.
		"""
		pass

	def GenerateEmbed_Feedback(self):
		"""
		# GENERATE EMBED : Feedback

		Creates an Embed for displaying player provided feedback, offering anonymity.
		"""
		pass

	def GetRoleName(self, p_role:botData.operations.OpRoleData):
		"""
		# GET ROLE NAME
		Convenience function to get a role name with icon prefix, if applicable.		
		"""
		vRoleName = ""
		if p_role.roleIcon != "-":
			vRoleName = f"{p_role.roleIcon}{p_role.roleName}"
		else:
			vRoleName = p_role.roleName

		return vRoleName

# EMBEDS:
# 1. OpInfo Embed: show if any options applied, signed up users
# 2. Connection Embed: Show status of signed up users (discord online|discord comms|Online Ingame)
# 3. SessionStats Embed: Start time, end time, user stats, link to Honu.
# 4. SessionFeedback: Place to store player feedback.

class Commander_btnStart(discord.ui.Button):
	def __init__(self, p_commanderParent:Commander):
		self.vCommander:Commander = p_commanderParent
		super().__init__(label="START", emoji="", row=0)

	def callback(self, p_interaction:discord.Interaction):
		pass