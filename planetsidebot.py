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

print("Imports complete")

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')

print("Tokens loaded")


class Bot(commands.Bot):

    def __init__(self):
        super(Bot, self).__init__(command_prefix=['!'])

        self.add_cog(opstart.opschannels(self))

    async def on_ready(self):
        print(f'Logged in as {self.user.name} | {self.user.id}')
bot = Bot()        

@bot.command(name='add')
@commands.has_role('bot-wrangler')
async def add_user(ctx,message):
    
    users = message.split(",")
    await ctx.send(f'Adding {users}.')
    
    for user in users:
        if user in authedUsers:
            await ctx.send(f'{user} already given access.')
        else:
            authedUsers.append(user)
            await ctx.send(f'{user} given access.')
            
@bot.command(name='remove')
@commands.has_role('bot-wrangler')
async def remove_user(ctx,message):
    
    users = message.split(",")
    await ctx.send(f'Removing {users}.')
    
    for user in users:
        if user not in authedUsers:
            await ctx.send(f'{user} never had access.')
            
        else:
            authedUsers.remove(user)
            await ctx.send(f'{user} access removed.')
    
@bot.command(name='list')
async def list_users(ctx):
    for user in authedUsers:
        await ctx.send(f'{user} has access.')
    
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.errors.CheckFailure):
        await ctx.send('You do not have the correct role for this command.')
        
        
async def planetside_monitoring():
     async with auraxium.Client() as client:

        char = await client.get_by_name(ps2.Character, 'auroram')
        print(char.name())
        print(char.data.prestige_level)

        # NOTE: Any methods that might incur network traffic are asynchronous.
        # If the data type has been cached locally, no network communication
        # is required.

        # This will only generate a request once per faction, as the faction
        # data type is cached forever by default
        print(await char.faction())

        # The online status is never cached as it is bound to change at any
        # moment.
        print(await char.is_online())
        return
    
print("loop running")

bot.run(TOKEN)