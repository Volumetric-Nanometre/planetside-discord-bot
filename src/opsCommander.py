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
import enum
import sched

import botUtils
from botUtils import BotPrinter as BUPrint

import botData.operations
from botData.operations import OperationData as OpsData
from opsManager import OperationManager as OpsMan

class CommanderStatus(enum.Enum):
	Init = -10		# Init: Commander has been created.
	Standby = 0 	# Standby: Commander has been posted and waiting.
	Prep = 10 		# Prep: Ops has started 30 minute prior Prep (either manually or by bot)
	Started = 20 	# Started: Ops has been started (either manually or by bot.)
	Debrief = 30	# Debrief: Pre-End stage, users are given a reactionary View to provide feedback
	Ended = 40		# Ended: User has ended Ops,  auto-cleanup.

class AutoCommander(commands.Cog):
	"""
	# AUTO COMMANDER

	A cog that sets up and automatically creates commanders for Operation events.
	"""
	def __init__(self) -> None:
		pass
		tasks.Loop()

	async def StartAutoCommander(self):
		# Use OpsManager to start an ops.
		# Create a Commander.
		# Lookit Sched
		pass

		#datetime - timedelta(minutes=0)
class AutoCommanderInstance():
	def __init__(self) -> None:
		pass


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

		#DiscordElements:
		self.vMessage : discord.Message = None # Message object used to edit. Set during first post.
		self.vCategory: discord.CategoryChannel # Category object to keep the Ops self contained. All channels are created within here, except non-soberdogs feedback

	async def GenerateCommander(self):
		"""
		# GENERATE COMMANDER

		Either creates, or updates an existing Commander view, using the current status.
		"""
		vMessageView = discord.ui.View(timeout=None)

		if(self.vCommanderStatus == CommanderStatus.Init):
			# Perform first run actions.

			# Set to standby and return.
			self.vCommanderStatus = CommanderStatus.Standby
			return


	async def GenerateEmbed_OpInfo(self):
		"""
		# GENERATE EMBED : OpInfo

		Creates an Embed for Operation Info.
		"""
		vEmbed = discord.Embed(colour=botUtils.Colours.commander, title=f"**OPERATION INFO** __{self.vOpData.name}__")

		# START | SIGNED UP
		vEmbed.add_field(name=f"START(ED) {botUtils.DateFormatter.GetDiscordTime(self.vOpData.date, botUtils.DateFormat.Dynamic)}", value=f"{botUtils.DateFormatter.GetDiscordTime(self.vOpData.date, botUtils.DateFormat.DateTimeLong)}", inline=True)
		
		vSignedUpCount = 0
		role: botData.operations.OpRoleData
		for role in self.vOpData.roles:
			vSignedUpCount += len(role.players)
		vEmbed.add_field(name="USERS | ROLES | RESERVES", value=f"{vSignedUpCount} | {len(self.vOpData.roles)} | {len(self.vOpData.reserves)}", inline=True)

		# Only show verbose role info during the early stages.  Reduces clutter afterwards.
		if self.vCommanderStatus.value > CommanderStatus.Started.value:
			vEmbed.add_field(name="", value="")
			role: botData.operations.OpRoleData
			for role in self.vOpData.roles:
				vUsersInRole = ""
				for user in role.players:
					vUsersInRole += f"{self.vBotRef.get_user(int(user))}\n"
				vEmbed.add_field( name=f"{self.GetRoleName(role)}")



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