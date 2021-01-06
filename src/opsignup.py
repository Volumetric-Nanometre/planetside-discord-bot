import os
import asyncio
import discord

import settings

from discord.ext import commands
from dotenv import load_dotenv


class OpSignUp(commands.Cog): 
    
    def __init__(self,bot):
        self.soberdogsActive = False
        self.armourdogsActive = False
        self.soberdogMessageText = ""
        self.soberdogMessageID = None
        self.signUpChannelName ='✍-sign-up'
        self.signupPoll = False
        self.soberReactions={':Icon_Heavy_Assault:': 'Heavy',':Icon_Combat_Medic:' : 'Medic', ':Icon_Infiltrator:' : 'Infiltrator', ':Icon_Light_Assault:' : 'Light assault', ':Icon_Engineer:' : 'Engineer'}
        
        super().__init__()

        
        
    async def locate_sign_up(self,ctx):
        print('Lookup signup channel')
        try:
            channels = ctx.guild.text_channels
        except:
            print('fail')
            return None
        print('Got text channel list')
        for channel in channels:
            if self.signUpChannelName == channel.name:
                print('Channel Found')
                return channel
        print('Lookup complete')
    
    @commands.command(name='ps2-sober-signup')
    async def sober_dog_signup(self,ctx):
        channel = await OpSignUp.locate_sign_up(self,ctx)
        with open('messages/soberdogs.txt','r') as f:
            self.soberdogMessage = f.read()
        
        messageHandler = await channel.send(self.soberdogMessage)
        self.soberdogMessageHandlerID = messageHandler.id
        self.signupPoll = True
        while(self.signupPoll):
            print('Yay!')
            await asyncio.sleep(5)
            print(f'Yay- awake! {self.soberdogMessageHandlerID}')
            message = await ctx.fetch_message(self.soberdogMessageHandlerID)
            print('yes')
            reactions = message.reactions
            for reaction in reactions:
                print(reaction.emoji) 
            
                
            
            
            
            
            
            
        
        
        

        
        
        
        
    

