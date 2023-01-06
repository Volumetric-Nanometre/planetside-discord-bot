import discord
from discord import app_commands
from discord.ext import commands
import botUtils
from botUtils import BotPrinter as BUPrint
from botUtils import ChannelPermOverwrites
import botData.settings as Settings

class ChatUtilityCog(commands.GroupCog, name="chatutils", description="Handles voice & text channel linking; and provides utility commands"):
	"""
	# CHAT UTILITY COG
	Handles auto-creation and deletion of channels when users join, and assigning overwrites.
	Provides utility commands for moving users 
	"""
	def __init__(self, p_botRef):
		self.botRef:commands.Bot = p_botRef
		self.adminLevel = Settings.CommandRestrictionLevels.level0
		BUPrint.Info("COG: Chat Monitor loaded!")

	@app_commands.command(name="move", description="Move all users from one channel to another.")
	@app_commands.rename(p_targetChannel="target", p_relocationChannel="new_channel")
	async def MoveUsers(self, p_interaction:discord.Interaction, p_targetChannel:discord.VoiceChannel, p_relocationChannel:discord.VoiceChannel):
		# HARDCODED ROLE USEAGE:
		if not await botUtils.UserHasCommandPerms(p_interaction.user, self.adminLevel, p_interaction):
			return

		stat_movedUSers = 0
		for member in p_targetChannel.members:
			try:
				await member.move_to(p_relocationChannel)
				stat_movedUSers += 1
			except discord.errors.Forbidden:
				BUPrint.Info(f"Invalid permission to move {member.display_name}")
			except discord.HTTPException:
				BUPrint.Info(f"Discord failed to move {member.display_name}.")

		await p_interaction.response.send_message(f"Succesfully relocated {stat_movedUSers} users to specified channel", ephemeral=True)



	@app_commands.command(name="remove_category", description="Removes a category and all its containing channels.")
	@app_commands.rename(p_category="category")
	@app_commands.describe(p_category="The category to remove.")
	async def RemoveCategory(self, p_interaction:discord.Interaction, p_category:discord.CategoryChannel):
		# HARDCODED ROLE USEAGE:
		if not await botUtils.UserHasCommandPerms(p_interaction.user, self.adminLevel, p_interaction):
			return

		p_interaction.response.defer()
		
		vMessage = f"{p_interaction.user.display_name} removed the Category: {p_category.name}\n\n"
		vAdminChannel = p_interaction.guild.get_channel( Settings.BotSettings.adminChannel )

		if p_category.id in Settings.BotSettings.protectedCategories:
			await p_interaction.response.send_message("That category is protected and cannot be removed with this command!", ephemeral=True)
			if vAdminChannel != None:
				await vAdminChannel.send(f"User {p_interaction.user.mention} attempted to delete protected category: {p_category.name}")
			return

		vReasonMsg = f"{p_interaction.user.display_name} used 'remove category' command."

		# Remove voice channels, moving any connected users to fallback (if found).
		# This is done first, since movin connected members should remove all the chat-linked text channels.
		fallbackVC = p_interaction.guild.get_channel( Settings.BotSettings.fallbackVoiceChat )
		vMessage += f"**Voice Channels: {len(p_category.voice_channels)}"
		for voiceChan in p_category.voice_channels:
			if fallbackVC != None:
				for member in voiceChan.members:
					try:
						await member.move_to(fallbackVC, reason=vReasonMsg)
						vMessage += f"{member.display_name} was moved to fallback.\n"
					except:
						vMessage += f"{member.display_name} was not moved to fallback.\n"
			else:
				vMessage += "Fallback Voice chat was not found.\n"

			try:
				await voiceChan.delete(reason=vReasonMsg)
				vMessage += f"Voice Channel: {voiceChan.name} was removed\n"
			except:
				vMessage += f"Voice Channel: {voiceChan.name} not removed\n"


		# Remove text channels second
		vMessage += f"**Text Channels: {len(p_category.text_channels)}"
		for textChan in p_category.text_channels:
			try:
				await textChan.delete(reason=vReasonMsg)
				vMessage += f"Text Channel: {textChan.name} removed\n"
			except:
				vMessage += f"Text Channel: {textChan.name} not removed\n"


		# Finally, delete category
		try:
			await p_category.delete(vReasonMsg)
		except:
			vMessage += f"Category {p_category.name} not removed! If empty, remove it manually.\n"

		try:
			await p_interaction.response.send_message("Category has been removed!", ephemeral=True)
		except discord.errors.NotFound:
			BUPrint.Info("Response not found.  Command likely used in channel that was removed (or the operation took longer than discords time-out.)")


		# Send administrative message if possible, else print to console
		if vAdminChannel != None:
			await vAdminChannel.send( vMessage )
		else:
			BUPrint.Info(vMessage)





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
			if vTextChan != None:
				try:
					await vTextChan.delete()
				except discord.errors.NotFound:
					BUPrint.Debug("Not found, presumably removed by Commander.")

		else:
			await vTextChan.set_permissions(p_member, read_messages=False, send_messages=False)