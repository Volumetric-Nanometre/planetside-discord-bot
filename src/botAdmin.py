"""
BOT ADMIN
Functions and classes specifically for administrative tasks that don't really fit with other cogs.
"""

from discord.ext.commands import GroupCog, Bot
from discord import app_commands, Interaction
from botData.settings import BotSettings, CommandLimit
from botUtils import BotPrinter as BUPrint
from botUtils import PrintSettings


class BotAdminCog(GroupCog, name="admin", description="Administrative commands and functionality relating to the bot itself"):

	def __init__(self, p_botRef:Bot):
		self.botRef = p_botRef
		BUPrint.Info("Cog: ADMIN loaded!")

	def HasPermission(self, p_userID:int):
		"""
		# HAS PERMISSION
		Convenience function to check if calling user is in list of admin IDs.
		"""
		if p_userID in BotSettings.roleRestrict_ADMIN:
			return True
		else:
			BUPrint.LogError(p_titleStr="ADMIN COMMAND USE", p_string="User attempted to use an admin command.")
			return False

	

	@app_commands.command(name="shutdown", description="Shutdown the bot.")
	async def BotShutdown(self, p_interaction:Interaction):
		"""
		# BOT SHUTDOWN:
		Command to cleanly shutdown the bot.
		"""
		vAdminChn = self.botRef.get_channel(BotSettings.adminChannel)

		if not self.HasPermission(p_interaction.user.id):
			if vAdminChn != None:
				await vAdminChn.send(f"**WARNING**: {p_interaction.user.mention} attempted to shut down the bot.")
				return

		await p_interaction.response.send_message("Shutting down the bot.", ephemeral=True)
		vMessage = f"{p_interaction.user.display_name} is shutting down the bot."
		if vAdminChn != None:
			await vAdminChn.send(vMessage)
		BUPrint.Info(vMessage)

		await self.botRef.close()



	@app_commands.command(name="config", description="Prints the bots settings")
	async def GetSettings(self, p_interaction:Interaction):
		"""
		# GET SETTINGS
		Command that prints the bots settings to messages.
		"""
		vAdminChn = self.botRef.get_channel(BotSettings.adminChannel)
	
		if not self.HasPermission(p_interaction.user.id):
			if vAdminChn != None:
				await vAdminChn.send(f"**WARNING**: {p_interaction.user.mention} tried to get the bot settings.")
				return

		if vAdminChn != None:
			await p_interaction.response.send_message("Posting settings...", ephemeral=True)
			vSettingStr = PrintSettings(True)
			splitString = [(vSettingStr[index:index+1995]) for index in range(0, len(vSettingStr), 1995)]
			for segment in splitString:
				segment = segment.replace(">", "-")
				await vAdminChn.send( f"{segment}\n" )
		else:
			await p_interaction.response.send_message("Invalid ADMIN channel.", ephemeral=True)