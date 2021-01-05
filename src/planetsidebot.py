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
import ps2eventclient
import settings

class Bot(commands.Bot):

    def __init__(self):
        super(Bot, self).__init__(command_prefix=['!'])

        self.add_cog(opstart.opschannels(self))
        self.add_cog(ps2eventclient.Ps2EventClient(self))
        self.add_cog(ps2eventclient.Ps2PersonalEvents(self))

    async def on_ready(self):
        print(f'Logged in as {self.user.name} | {self.user.id} on Guild {settings.DISCORD_GUILD}')
bot = Bot()        

@bot.command(name='ps2-add')
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
            
@bot.command(name='ps2-remove')
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
    
@bot.command(name='ps2-list')
async def list_users(ctx):
    for user in authedUsers:
        await ctx.send(f'{user} has access.')
    
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.errors.CheckFailure):
        await ctx.send('You do not have the correct role for this command.')
    
print("loop running")

bot.run(settings.DISCORD_TOKEN)