"""
@author Michael O'Donnell
"""
import os

import discord
from discord.ext import commands
from discord import app_commands
import dotenv
import asyncio

import settings
import botUtils

# import roleManager

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
        botUtils.BotPrinter.Debug("Setting up hooks...")
        # await self.add_cog(roleManager.RoleManager(self))
        # await self.tree.copy_global_to(guild=settings.DISCORD_GUILD)
        # await self.tree.sync(guild=settings.DISCORD_GUILD)

# Old:
		# await self.add_cog(opstart.opschannels(self))
        # await self.add_cog(opsignup.OpSignUp(self))
        # await self.add_cog(chatlinker.ChatLinker(self))

        #self.add_cog(bullybully.Bully(self))
        #self.add_cog(outfittracking.PS2OutfitTracker(self))

    async def on_ready(self):
        print(f'Logged in as {self.user.name} | {self.user.id} on Guild {settings.DISCORD_GUILD}')

bot = Bot()        

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.errors.CheckFailure):
        await ctx.send('You do not have the correct role for this command.', ephemeral=True)
    
# print("loop running")
botUtils.BotPrinter.Debug("Loop running...")
asyncio.run(bot.run(settings.DISCORD_TOKEN))