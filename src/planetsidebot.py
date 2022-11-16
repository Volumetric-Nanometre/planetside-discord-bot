"""
@author Michael O'Donnell
"""
import asyncio
import os
import enum

import discord
import dotenv
from discord import app_commands
from discord.ext import commands

import botUtils
import newUser
import roleManager
import opsManager
import settings
import botData

# internal modules
# import discordbasics
# import opstart
# import opsignup
# import chatlinker
# import fileManagement
# import bullybully
# import outfittracking

class Bot(commands.Bot):

    def __init__(self):
        super(Bot, self).__init__(command_prefix=['!'], intents=discord.Intents.all())

    async def setup_hook(self):
		# Needed for later functions, which want a discord object instead of a plain string.
        vGuildObj = await self.fetch_guild(settings.DISCORD_GUILD) # Make sure to use Fetch in case of outdated caching.

        botUtils.BotPrinter.Debug("Setting up hooks...")
        self.tree.copy_global_to(guild=vGuildObj)
        await self.tree.sync(guild=vGuildObj)

# Old:
		# await self.add_cog(opstart.opschannels(self))
        # await self.add_cog(opsignup.OpSignUp(self))
        # await self.add_cog(chatlinker.ChatLinker(self))

    async def on_ready(self):
        print(f'Logged in as {self.user.name} | {self.user.id} on Guild {settings.DISCORD_GUILD}')

bot = Bot()        

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.errors.CheckFailure):
        await ctx.send('You do not have the correct role for this command.', ephemeral=True)

@bot.event
async def on_member_join(pMember:discord.User):
	channel = bot.get_channel(358702477962379274)
	channel.send("Welcome!  To continue, use `/join`.")


# APP COMMANDS

@bot.tree.command(name="roles", description="Opens a menu to select both TDKD roles and other game roles, showing the respective channels.")
@app_commands.rename(isAddingRole="add_role")
@app_commands.describe(isAddingRole="TRUE if you want to add roles, FALSE if you want to remove them.")
async def userroles(pInteraction: discord.Interaction, isAddingRole: bool):
	vView = roleManager.RoleManager(bot, pInteraction.user, isAddingRole)
	vView.vInteraction = pInteraction
	vMessageTitle: str

	if isAddingRole:
		vMessageTitle = "**Select the roles you want to ADD**"
	else:
		vMessageTitle = "**Select the roles you want to REMOVE**"
	await pInteraction.response.send_message(vMessageTitle, view=vView, ephemeral=True)


@bot.tree.command(name="join", description="Show the join window if you have closed it.")
async def newuserjoin(pInteraction: discord.Interaction):
	await pInteraction.response.send_modal( newUser.NewUser())


@bot.tree.command(name="addops", description="Add a new Ops event")
@app_commands.describe(optype="Type of Ops to create.", edit="Open the Ops Editor after creating this event?")
# async def addopsevent (pInteraction: discord.Interaction, optype: botData.OpsTypes, edit: bool ):
async def addopsevent (pInteraction: discord.Interaction, optype: opsManager.OpsManager.GetDefaultOpsAsEnum(), edit: bool ):
	botUtils.BotPrinter.Debug(f"Adding new event ({optype}).  Edit after posting: {edit}")
	await pInteraction.response.send_message(f"Adding new event ({optype}).  Edit after posting: {edit}")

# START
botUtils.BotPrinter.Debug("Loop running...")
asyncio.run(bot.run(settings.DISCORD_TOKEN))