"""
@author Michael O'Donnell
"""
import os

import discord
from discord.ext import commands
from dotenv import load_dotenv
import auraxium
from auraxium import ps2
import asyncio

import discordbasics
import opstart
import settings
import opsignup
import ps2tracking

class Bot(commands.Bot):

    def __init__(self):
        super(Bot, self).__init__(command_prefix=['!'])

        self.add_cog(opstart.opschannels(self))
        self.add_cog(opsignup.OpSignUp(self))
        self.add_cog(ps2tracking.Ps2PersonalTrack(self))

    async def on_ready(self):
        print(f'Logged in as {self.user.name} | {self.user.id} on Guild {settings.DISCORD_GUILD}')
bot = Bot()        

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.errors.CheckFailure):
        await ctx.send('You do not have the correct role for this command.')
    
print("loop running")

bot.run(settings.DISCORD_TOKEN)