"""
@author Michael O'Donnell
"""
import asyncio
import os
import enum
import datetime

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
        botUtils.BotPrinter.Debug(f'Logged in as {self.user.name} | {self.user.id} on Guild {settings.DISCORD_GUILD}')

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


# ADD & REMOVE USER ROLES (/roles)

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



# NEW USER (/join)

@bot.tree.command(name="join", description="Show the join window if you have closed it.")
async def newuserjoin(pInteraction: discord.Interaction):
	await pInteraction.response.send_modal( newUser.NewUser())



# ADD OPS (/addops)

@bot.tree.command(name="addops", description="Add a new Ops event")
@app_commands.describe(optype="Type of Ops to create.",
						edit="Open the Ops Editor after creating this event?",
						pDay="The day this ops will run.",
						pMonth="The month this ops will run.",
						pHour="The HOUR (24) the ops will run in.",
						pMinute="The MINUTE within an hour the ops starts on",
						pYear="Optional.\nThe Year the ops should run.")
@app_commands.rename(pDay="day", pMonth="month", pHour="hour", pMinute="minute", pYear="year")
async def addopsevent (pInteraction: discord.Interaction, 
	optype: opsManager.OpsManager.GetDefaultOpsAsEnum(), 
	edit: bool, pDay:app_commands.Range[int, 0, 31], 
	pMonth:app_commands.Range[int, 1, 12], 
	pHour: app_commands.Range[int, 1, 23], 
	pMinute:app_commands.Range[int, 0, 59],
	pYear:int  = datetime.datetime.now().year
):

	botUtils.BotPrinter.Debug(f"Adding new event ({optype}).  Edit after posting: {edit}, Year: {pYear}")
	vTime = datetime.datetime(year=datetime.datetime.now().year, month=pMonth, day=pDay, minute=pMinute, hour=pHour )
	vUTCStamp = botUtils.DateFormatter.GetDiscordTime(vTime)
	vDate = datetime.datetime(
		year=pYear,
		month=pMonth,
		day=pDay,
		hour=pHour, minute=pMinute)

	# If OpType selected is not an actual saved optype, assumed custom (or the other notif to say no saved ops exist, was chosen.)
	if optype not in await opsManager.OpsManager.GetOps():
		# Make a new OpsData;
		newOpsData = botData.OperationData(date=vDate, status=botData.OpsStatus.editing)
		
		opsMessage = opsManager.OpsMessage()
		opsMessage.opsData = newOpsData

		await pInteraction.response.send_message("Adding a custom event.")
		return


	await pInteraction.response.send_message(f"Adding new event ({optype}).  Edit after posting: {edit}.\nThis ops will run{vUTCStamp}", ephemeral=True)




# START
botUtils.BotPrinter.Debug("Bot running...")
asyncio.run(bot.run(settings.DISCORD_TOKEN))