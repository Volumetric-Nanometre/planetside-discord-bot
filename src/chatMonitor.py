import discord
from discord import app_commands
from discord.ext import commands
import botUtils
from botUtils import BotPrinter as BUPrint
from botUtils import ChannelPermOverwrites
import botData.settings as Settings

class ChatMonitorCog(commands.GroupCog, name="voice_monitor", description="Handles automatic managing of voice & text channel linking."):
	"""
	# CHAT MONITOR COG
	Handles auto-creation and deletion of channels when users join, and assigning overwrites.
	"""
	def __init__(self, p_botRef):
		self.botRef:commands.Bot = p_botRef
		BUPrint.Info("COG: Chat Monitor loaded!")

	@commands.has_any_role(f"{botUtils.CommandRestrictionLevels.level1.value}")
	@app_commands.command(name="move", description="Move all users from one channel to another.")
	@app_commands.rename(p_targetChannel="target", p_relocationChannel="new_channel")
	async def MoveUsers(self, p_interaction:discord.Interaction, p_targetChannel:discord.VoiceChannel, p_relocationChannel:discord.VoiceChannel):
		# HARDCODED ROLE USEAGE:
		if not await botUtils.UserHasCommandPerms(p_interaction.user, botUtils.CommandRestrictionLevels.level1, p_interaction):
			return

		for member in p_targetChannel.members:
			await member.move_to(p_relocationChannel)

		await p_interaction.response.send_message("Succesfully relocated users to specified channel", ephemeral=True)


	@commands.Cog.listener("on_voice_state_update")
	async def VoiceStateChanged(self, p_member:discord.Member, p_before:discord.VoiceState, p_after:discord.VoiceState):
		"""
		# VOICE STATE CHANGED: Listener
		Handles creation & deletion of channels relating to voice chats.
		"""
		# First check if user is joining or leaving
		bUserJoined = bool( p_before.channel == None)
		bUserSwappedChannels:bool = False
		
		if not bUserJoined and p_before.channel != None and p_after.channel != None:
			bUserSwappedChannels = bool( p_before.channel != p_after.channel )

			if not bUserSwappedChannels:
				BUPrint.Debug("User just updated mute settings, ignoring...")
				return

		vGuild = await botUtils.GetGuild(self.botRef)
		vTextChn:discord.TextChannel = None
		vVoiceChn:discord.VoiceChannel = None

		# Get channel name
		if bUserJoined or bUserSwappedChannels:
			vVoiceChn = p_after.channel
		else:
			vVoiceChn = p_before.channel

		# Find existing channel
		vTextChn = self.GetTextChannel(vGuild, vVoiceChn)
		
		# First user to join?
		if (bUserJoined or bUserSwappedChannels) and vTextChn == None:
			try:
				vTextChn = await vGuild.create_text_channel(
					name=f"{vVoiceChn.name}-chat",
					category=vVoiceChn.category,
					overwrites=ChannelPermOverwrites.invisible
				)
				await vTextChn.set_permissions(p_member, read_messages=True, send_messages=True)


			except discord.errors.Forbidden as error:
				BUPrint.LogErrorExc("Invalid permissions to create channel!", error)
				return
			except discord.errors.HTTPException as error:
				BUPrint.LogErrorExc("Unable to create channel", error)
				return

		elif bUserJoined or bUserSwappedChannels:
			await vTextChn.set_permissions(p_member, read_messages=True,send_messages=True)

		# Apply userLeft to old channel.
		if bUserSwappedChannels:
			await self.UserLeftChannel(vGuild, p_member, p_before.channel)
			return
		elif not bUserSwappedChannels and bUserJoined:
			return


	# If code reaches here, user has left:		
		# Get channel, possibly redundant.
		vVoiceChn = vGuild.get_channel(vVoiceChn.id)
		await self.UserLeftChannel(vGuild, p_member, vVoiceChn)


	
	def GetTextChannel(self, p_guild:discord.Guild, p_voiceChn:discord.VoiceChannel):
		"""
		# GET TEXT CHANNEL
		Returns the discord.TextChannel with matching name.
		"""
		for textChan in p_guild.text_channels:
			if textChan.name.lower() == f"{p_voiceChn.name.lower()}-chat":
				if textChan.category == p_voiceChn.category:
					return textChan


	async def UserLeftChannel(self, p_guild:discord.Guild, p_member:discord.Member, p_channel:discord.VoiceChannel):
		"""
		# USER LEFT CHANNEL
		Removes text channel If associated voice channel is empty.
		If not empty, sets permissions.
		"""

		vTextChan = self.GetTextChannel(p_guild, p_channel)

		if len(p_channel.members) == 0:
			await vTextChan.delete()

		else:
			await vTextChan.set_permissions(p_member, read_messages=False, send_messages=False)