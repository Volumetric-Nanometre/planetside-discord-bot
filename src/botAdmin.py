"""
BOT ADMIN
Functions and classes specifically for administrative tasks that don't really fit with other cogs.
"""

from discord.ext.commands import GroupCog, Bot
from discord import app_commands, Interaction, Role, TextChannel, CategoryChannel, Emoji
from botData.settings import BotSettings, Channels, Roles, Messages
from botUtils import BotPrinter as BUPrint
from botUtils import PrintSettings, SplitStrToSegments, GetGuildNF, ChannelPermOverwrites
from roleManager import UserAssignableRoleManager


class BotAdminCog(GroupCog, name="admin", description="Administrative commands and functionality relating to the bot itself"):

	def __init__(self, p_botRef:Bot):
		self.botRef = p_botRef
		self.shutdownFunction: function = None
		BUPrint.Info("Cog: ADMIN loaded!")


	def HasPermission(self, p_userID:int):
		"""
		# HAS PERMISSION
		Convenience function to check if calling user is in list of admin IDs.
		"""
		if p_userID in Roles.roleRestrict_ADMIN:
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
		vAdminChn = self.botRef.get_channel(Channels.botAdminID)

		if not self.HasPermission(p_interaction.user.id):
			if vAdminChn != None:
				await vAdminChn.send(f"**WARNING**: {p_interaction.user.mention} attempted to shut down the bot.")
				return

		await p_interaction.response.send_message("Shutting down the bot.", ephemeral=True)
		vMessage = f"{p_interaction.user.display_name} is shutting down the bot."
		if vAdminChn != None:
			await vAdminChn.send(vMessage)
		BUPrint.Info(vMessage)

		await self.shutdownFunction()



	@app_commands.command(name="config", description="Prints the bots settings")
	async def GetSettings(self, p_interaction:Interaction):
		"""
		# GET SETTINGS
		Command that prints the bots settings to messages.
		"""
		vAdminChn = self.botRef.get_channel(Channels.botAdminID)
	
		if not self.HasPermission(p_interaction.user.id):
			if vAdminChn != None:
				await vAdminChn.send(f"**WARNING**: {p_interaction.user.mention} tried to get the bot settings.")
				return

		if vAdminChn != None:
			await p_interaction.response.send_message("Posting settings...", ephemeral=True)
			
			
			settingSegments = SplitStrToSegments( p_string=PrintSettings(True), p_limit=1990 )

			for segment in settingSegments:
				await vAdminChn.send( f"```{segment}```")


		else:
			await p_interaction.response.send_message("Invalid ADMIN channel.", ephemeral=True)



	@app_commands.command(name="refresh_roles", description="Reloads user assignable roles from the saved files.")
	async def RefreshUserAssignableRoles(self, p_interaction:Interaction):
		if not self.HasPermission(p_interaction.user.id):
			p_interaction.response.send_message(Messages.invalidCommandPerms, ephemeral=True)
			return
		BUPrint.Info("Reloading user assignable roles")
		UserAssignableRoleManager().LoadRoles()

		await p_interaction.response.send_message("Roles reloaded!", ephemeral=True)



	@app_commands.command(name="new_role", description="Adds a new user assignable role. Do not use two of the same named params.")
	@app_commands.rename(
		p_role="role",
		p_channel="channel",
		p_roleName="role_name",
		p_channelName="chan_name",
		p_isOtherGame="is_other_game",
		p_emoji="emoji",
		p_description="description"
	)
	@app_commands.describe(
		p_role="An existing role.",
		p_roleName="Name for a new role.",
		p_channel="An existing text channel.",
		p_channelName="Name for a new text channel.",
		p_isOtherGame="Default:True | This role for another game. If False the role is added to the TDKD role selector.",
		p_emoji="Optional: The custom emoji string.",
		p_description="Description shown in the selector."
	)
	async def NewUserAssignableRole(self, 
				  p_interaction:Interaction,
				  p_role:Role = None,
				  p_roleName:str = "",
				  p_channel:TextChannel = None,
				  p_channelName:str = "",
				  p_isOtherGame:bool = True,
				  p_emoji:str = "",
				  p_description:str = ""
				  ):
		"""# New user Assignable Role:
		Command to add a new user assignable role.

		Takes multiple optional parameters:
		- p_role: A discord Role.
		- p_channel: a discord Channel.
		- p_roleName: a name for a new role.

		### USER ERROR
		When a user has specified multiple parameters for the same named property, the existing parameter takes priority.
		"""
		if not self.HasPermission(p_interaction.user.id):
			await p_interaction.response.send_message("You do not have permission to run this command!", ephemeral=True)
			return
		
		BUPrint.Info("Adding new user assignable role...")
		
		if p_channel == None and p_channelName == "":
			BUPrint.Debug("	-> No channel was specified.")


		if p_role == None and p_roleName == "":
			BUPrint.Debug("	-> No role was specified.  Exiting!")
			await p_interaction.response.send_message("No role was specified!\nThis command requires **one** of the role parameters to be used.")
			return

		assignableRole:Role = None
		linkedChannel:TextChannel = None

		# CHANNEL

		if p_channel != None:
			BUPrint.Debug("	-> Existing channel specified")
			linkedChannel = p_channel

		elif p_channelName != "":
			BUPrint.Debug("	-> Channel name specified, creating new channel.")
			gamesCategory:CategoryChannel = self.botRef.get_channel(Channels.otherGameCatID)

			linkedChannel = await GetGuildNF(self.botRef).create_text_channel(
				name=p_channelName,
				reason="Created for new role:channel",
				overwrites=ChannelPermOverwrites.invisible,
				category=gamesCategory)

		# ROLE
		
		if p_role != None:
			BUPrint.Debug("	-> Role specified")
			assignableRole = p_role

		elif p_roleName != "":
			BUPrint.Debug("	-> Role name specified, creating new role")
			assignableRole = await GetGuildNF(self.botRef).create_role(
				name=p_roleName,
				reason=f"{p_interaction.user.display_name} is adding a new user assignable role"
			)

		else:
			await p_interaction.response.send_message("Invalid arguments.  There must be a minimum of 1 role parameter.", ephemeral=True)
			return


		# Link Channel to Role:
		if assignableRole != None and linkedChannel != None:
			BUPrint.Debug("	-> Linking role to channel")
			# Set role/channel visibility.
			await linkedChannel.set_permissions(
				target=assignableRole,
				read_messages=True, send_messages=True
			)


		UserAssignableRoleManager().AddNewRole(p_isTDKDRole=not p_isOtherGame, p_roleName=assignableRole.name, p_roleID=assignableRole.id, p_emoji=p_emoji, p_desc=p_description)

		try:
			await p_interaction.response.send_message(f"Succesfully added a new role:channel!\n{assignableRole.mention}:{linkedChannel.mention}", ephemeral=True)
			await self.botRef.get_channel(Channels.botAdminID).send(f"Succesfully added a new role:channel!\n{assignableRole.mention}:{linkedChannel.mention}")
		except:
			BUPrint.Info("Unable to post notification to administration channel!")
		


	@app_commands.command(name="remove_role", description="Removes a custom role.  Does NOT remove the channel.")
	@app_commands.rename(p_role="role", p_deleteRole="delete")
	@app_commands.describe(p_role="The role to be removed from the selector.", p_deleteRole="Default: True | Delete the role.")
	async def RemoveCustomRole(self, p_interaction:Interaction, p_role:Role, p_deleteRole:bool=True):
		"""# Remove Custom Role

		Command that removes a role from being user assignable via the `/roles add/remove` command.
		"""
		if not self.HasPermission(p_interaction.user.id):
			await p_interaction.response.send_message("You do not have permission to run this command!", ephemeral=True)
			return		

		allRoles = UserAssignableRoleManager().tdkdRoles + UserAssignableRoleManager().gameRoles

		allRoleIDs = [int(role.value) for role in allRoles]

		if p_role.id not in allRoleIDs:
			await p_interaction.response.send_message("The specified role isn't set up to be user assignable.", ephemeral=True)
			return
		
		bRoleRemoved = False
		resultMsg = ""

		for option in UserAssignableRoleManager().tdkdRoles:
			if int(option.value) == p_role.id:
				UserAssignableRoleManager().tdkdRoles.remove(option)
				UserAssignableRoleManager().SaveRoles()
				bRoleRemoved = True
				resultMsg = f"Role {p_role.name} removed from TDKD role select menu."
				break
		
		if not bRoleRemoved:
			for option in UserAssignableRoleManager().gameRoles:
				if int(option.value) == p_role.id:
					UserAssignableRoleManager().gameRoles.remove(option)
					UserAssignableRoleManager().SaveRoles()
					bRoleRemoved = True
					resultMsg = f"Role {p_role.name} removed from game role select menu."
					break
				
		if bRoleRemoved:
			if p_deleteRole:
				await p_role.delete(reason=f"{p_interaction.user.display_name} removed role via command.")
				resultMsg += "\n>> Role deleted."

			await p_interaction.response.send_message(resultMsg, ephemeral=True)