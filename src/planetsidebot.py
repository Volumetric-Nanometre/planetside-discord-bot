"""
@author Michael O'Donnell
"""
import asyncio
import os

import discord
# from discord import app_commands  # Not needed (also doesn't work), pass name & descriptions into the @Bot.tree.command decorator
import dotenv
from discord.ext import commands

import botUtils
import settings

import roleManager

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
        # self.tree = discord.app_commands.CommandTree(self)

    async def setup_hook(self):
		# Needed for later functions, which want a discord object instead of a plain string.
        vGuildObj = await self.fetch_guild(settings.DISCORD_GUILD) # Make sure to use Fetch in case of outdated caching.


        botUtils.BotPrinter.Debug("Setting up hooks...")
        # await self.add_cog(roleManager.RoleManager(self))
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



# APP COMMANDS

@bot.tree.command(name="roles", description="Opens a menu to select both TDKD roles and other game roles, showing the respective channels.")
async def userroles(pInteraction: discord.Interaction):
	vView = roleManager.RoleManager(bot, pInteraction.user)
	await pInteraction.response.send_message("MODIFY USER ROLES...", view=vView, ephemeral=True)




# START
botUtils.BotPrinter.Debug("Loop running...")
asyncio.run(bot.run(settings.DISCORD_TOKEN))