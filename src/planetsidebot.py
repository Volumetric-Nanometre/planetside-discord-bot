"""
@author Michael O'Donnell
"""
import asyncio
import os
import enum
import datetime
import traceback

import discord
from discord import app_commands
from discord.ext import commands

import botUtils
from botUtils import BotPrinter as BUPrint
import botData
import newUser
import settings
import roleManager


import opsManager

# import chatlinker


class Bot(commands.Bot):

    def __init__(self):
        super(Bot, self).__init__(command_prefix=['!'], intents=discord.Intents.all())
        self.vGuildObj: discord.Guild
        self.vOpsManager = opsManager.OperationManager()
        opsManager.OperationManager.SetBotRef(self)

    async def setup_hook(self):
		# Needed for later functions, which want a discord object instead of a plain string.
        vGuildObj = await botUtils.GetGuild(p_BotRef=self)

        botUtils.BotPrinter.Debug("Setting up hooks...")
        self.tree.copy_global_to(guild=vGuildObj)
        await self.tree.sync(guild=vGuildObj)

# Old:
        # await self.add_cog(chatlinker.ChatLinker(self))

    async def on_ready(self):
        botUtils.BotPrinter.Debug(f'Logged in as {self.user.name} | {self.user.id} on Guild {settings.DISCORD_GUILD}')
        await self.vOpsManager.RefreshOps()


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
@app_commands.describe(optype="Type of Ops to create. If this doesn't match an existing option, defaults to 'custom'!",
						edit="Open Ops Editor before posting this event (Always true if 'Custom')",
						pDay="The day this ops will run.",
						pMonth="The month this ops will run.",
						pHour="The HOUR (24) the ops will run in.",
						pMinute="The MINUTE within an hour the ops starts on",
						pYear="Optional.\nThe Year the ops should run.",
						pArguments="Optional.\nAdditional arguments to control the op behaviour.")
@app_commands.rename(pDay="day", pMonth="month", pHour="hour", pMinute="minute", pYear="year", pArguments="arguments")
@app_commands.checks.has_any_role('CO','Captain','Lieutenant','Sergeant')
async def addopsevent (pInteraction: discord.Interaction, 
	optype: str,
	edit: bool, 
	pDay: app_commands.Range[int, 0, 31], 
	pMonth: app_commands.Range[int, 1, 12], 
	pHour: app_commands.Range[int, 1, 23], 
	pMinute:app_commands.Range[int, 0, 59],
	pYear: int  = datetime.datetime.now().year,
	pArguments: str = ""
):

	botUtils.BotPrinter.Debug(f"Adding new event ({optype}).  Edit after posting: {edit}")
	vDate = datetime.datetime(
		year=pYear,
		month=pMonth,
		day=pDay,
		hour=pHour, minute=pMinute)

	vOpTypeStr = str(optype).replace("OpsType.", "")


	newOpsData :botData.OperationData = botData.OperationData()
	vOpManager = opsManager.OperationManager()
	newOpsData.date = vDate

	if vOpTypeStr not in opsManager.OperationManager.GetDefaults():
		newOpsData.status = botData.OpsStatus.editing

		vEditor: opsManager.OpsEditor = opsManager.OpsEditor(pBot=bot, pOpsData=newOpsData)

		botUtils.BotPrinter.Debug(f"Editor: {vEditor}, Type: {type(vEditor)}")

		await pInteraction.response.send_message("**OPS EDITOR**", view=vEditor, ephemeral=True)
		return

	else:
		# MAKE SURE TO SWAP OP DATA FILE LATER, ELSE YOU WILL OVERWRITE THE SAVED DEFAULT
		# vOpsMessage = opsManager.OpsMessage(pOpsDataFile=f"{settings.botDir}/{settings.defaultOpsDir}/{optype}", pOpsData=None, pBot=bot)
		# vOpsMessage.getDataFromFile()

		vFilePath = f"{settings.botDir}/{settings.defaultOpsDir}/{optype}"
		newOpsData = opsManager.OperationManager.LoadFromFile(vFilePath)


		# Update date & args to the one given by the command
		newOpsData.date = vDate
		newOpsData.arguments += pArguments

		if(edit):
			vEditor = opsManager.OpsEditor(pBot=bot, pOpsData=newOpsData)
			await pInteraction.response.send_message(f"*Editing OpData for {optype}*", view=vEditor, ephemeral=True)
			# vEditor.vMessage = await pInteraction.original_response()
			
		else:
			# TODO -  Add method of choosing which channel signup goes into, then grab said channel and send message there.
			# vOpsMessage.opsData.GenerateFileName()
			# vOpsMessage.opsDatafilePath = f"{settings.botDir}/{settings.opsFolderName}/{vOpsMessage.opsData.fileName}.bin"
			# await vOpsMessage.PostMessage()

			if await vOpManager.AddNewLiveOp(p_opData=newOpsData):
				await pInteraction.response.send_message("Ops posted!", ephemeral=True)
			else:
				await pInteraction.response.send_message("Op posting failed, check console for more information.", ephemeral=True)

	# End AddOpsEvent

@addopsevent.autocomplete('optype')
async def autocompleteOpTypes( pInteraction: discord.Interaction, pTypedStr: str):
	choices: list = []
	vDataFiles: list = ["Custom"]

	vDataFiles =  opsManager.OperationManager.GetDefaultOpsAsList()

	option: str
	for option in vDataFiles:
		if(pTypedStr.lower() in option.lower()):
			# Add options matching current typed response to a list.
			# Allows bypassing discords max 25 item limit on dropdown lists.
			choices.append(discord.app_commands.Choice(name=option.replace(".bin", ""), value=option))
	return choices


# EDIT OPS (/editop)
@bot.tree.command(name="editop", description="Edit the values of a current live operation.")
@app_commands.describe(pOpsToEdit="Select the current live Op data to edit.")
@app_commands.rename(pOpsToEdit="file")
async def editopsevent(pInteraction: discord.Interaction, pOpsToEdit: str):
	BUPrint.Info(f"Editing Ops data for {pOpsToEdit}")
	vLiveOpData:botData.OperationData = opsManager.OperationManager.LoadFromFile( botUtils.FilesAndFolders.GetOpFullPath(pOpsToEdit))

	vEditor = opsManager.OpsEditor(pBot=bot, pOpsData=vLiveOpData)
	await pInteraction.response.send_message(f"**Editing OpData for** *{vLiveOpData.fileName}*", view=vEditor, ephemeral=True)


@editopsevent.autocomplete("pOpsToEdit")
async def autocompleteFileList( pInteraction: discord.Interaction, pTypedStr: str):
	choices: list = []
	vDataFiles: list = opsManager.OperationManager.GetOps()


	option: str
	for option in vDataFiles:
		if(pTypedStr.lower() in option.lower()):
			# Add options matching current typed response to a list.
			# Allows bypassing discords max 25 item limit on dropdown lists.
			choices.append(discord.app_commands.Choice(name=option.replace(".bin", ""), value=option.replace(".bin", "")))
	return choices


# START
BUPrint.Debug("Bot running...")
asyncio.run(bot.run(settings.DISCORD_TOKEN))