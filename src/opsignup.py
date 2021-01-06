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
        self.soberdogMessageHandlerID = None
        self.signUpChannelName ='✍-sign-up'
        self.signUpChannel = None
        self.soberMembers = []
        self.soberMemberText = {}
        self.ignoreRemove = False
        self.soberReactions={'<:Icon_Heavy_Assault:795726910344003605>': 'Heavy','<:Icon_Combat_Medic:795726867960692806>' : 'Medic', '<:Icon_Infiltrator:795726922264215612>' : 'Infiltrator', '<:Icon_Light_Assault:795726936759468093>' : 'Light assault', '<:Icon_Engineer:795726888763916349>' : 'Engineer'}
        self.bot = bot
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
        
        
    async def sober_dogs_add(self,payload):
        
        messageText  = self.soberdogMessageText
        message = await self.signUpChannel.fetch_message(self.soberdogMessageHandlerID)
        if  str(payload.emoji) in self.soberReactions.keys() and str(payload.user_id) not in self.soberMembers:

            self.soberMembers.append(str(payload.user_id))
            self.soberMemberText.update({str(payload.user_id):f'\n{self.soberReactions[str(payload.emoji)]} - @{str(payload.member.nick)}'})



            for player in self.soberMemberText.values():
                messageText = messageText + str(player)


            print(messageText)

            await message.edit(content=messageText)

            print('Reaction accepted')
        else:
            self.ignoreRemove = True
            await message.remove_reaction(payload.emoji,payload.member)
            print('Reaction removed')
       
    
    async def sober_dogs_remove(self,payload):
            
            if self.ignoreRemove:
                self.ignoreRemove = False
                return
            
            if str(payload.emoji) in self.soberReactions.keys():
                message = await self.signUpChannel.fetch_message(self.soberdogMessageHandlerID)
                messageText  = self.soberdogMessageText
                del self.soberMemberText[str(payload.user_id)]
                self.soberMembers.remove(str(payload.user_id))
                for player in self.soberMemberText.values():
                    messageText = messageText + str(player)
                await message.edit(content=messageText)
            
        
        
    
    @commands.command(name='ps2-sober-signup')
    async def sober_dog_signup(self,ctx):
        self.signUpChannel = await OpSignUp.locate_sign_up(self,ctx)
        with open('messages/soberdogs.txt','r') as f:
            self.soberdogMessageText = f.read()
        
        messageHandler = await self.signUpChannel.send(self.soberdogMessageText)
        self.soberdogMessageHandlerID = messageHandler.id
        print('Message sent')
    
    @commands.command(name='ps2-sober-signup-reset')
    async def sober_dog_signup_reset(self,ctx):
        await message.delete()
        
        self.soberdogsActive = False
        self.armourdogsActive = False
        self.soberdogMessageText = ""
        self.soberdogMessageHandlerID = None
        self.signUpChannelName ='✍-sign-up'
        self.signUpChannel = None
        self.soberMembers = []
        self.soberMemberText = {}
        self.ignoreRemove = False
    
 
    
    @commands.Cog.listener('on_raw_reaction_remove') 
    async def react_remove_sign_up_check(self,payload):
        print('remove reaction caught')       
    
        if not self.signUpChannel:
            return
        if payload.channel_id != self.signUpChannel.id:
            print('not in sign-up')
            return
        if payload.message_id == self.soberdogMessageHandlerID:
            print('Soberdogs remove react')
            await OpSignUp.sober_dogs_remove(self,payload)

            
        else:
            print('Not sober')
    
        print('removed in sign-up')
        
        
    @commands.Cog.listener('on_raw_reaction_add') 
    async def react_sign_up_check(self,payload):
        
        print('reaction caught') 
        if not self.signUpChannel:
            return
        if payload.channel_id != self.signUpChannel.id:
            print('not in sign-up')
            return
        if payload.message_id == self.soberdogMessageHandlerID:
            print('Soberdogs react')
            await OpSignUp.sober_dogs_add(self,payload)

            
        else:
            print('Not sober')
    
        print('in sign-up')
        
        
        
        
    
    
            
                
            
            
            
            
            
            
        
        
        

        
        
        
        
    

