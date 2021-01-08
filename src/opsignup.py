import os
import asyncio
import discord

import settings

from discord.ext import commands
from dotenv import load_dotenv


class OpSignUp(commands.Cog): 
    
    def __init__(self,bot):
        self.signUpChannelName ='✍-sign-up'
    
        self.soberObj = {}
        self.armourObj = {}
        self.bastionObj = {}
        self.bot = bot
        super().__init__()
        

    @commands.Cog.listener('on_raw_reaction_remove') 
    async def react_remove_sign_up_check(self,payload):
        print('remove reaction caught')   
           
        if payload.message_id in self.soberObj:
            print('Soberdogs remove react')
            sober = self.soberObj[payload.message_id]
            await OpSignUp.generic_react_remove(sober,payload)
        elif payload.message_id in self.armourObj:
            print('Armourdogs remove react')
            armour = self.armourObj[payload.message_id]
            await OpSignUp.generic_react_remove(armour,payload)
        elif payload.message_id in self.bastionObj:
            print('Bastion remove react')
            bastion = self.bastionObj[payload.message_id]
            await OpSignUp.generic_react_remove(bastion,payload)
        else:
            pass
        
        print('Complete')

        
        
    @commands.Cog.listener('on_raw_reaction_add') 
    async def react_sign_up_check(self,payload):
        
        print('reaction caught') 
        if payload.message_id in self.soberObj:
            print('Soberdogs remove react')
            sober = self.soberObj[payload.message_id]
            await OpSignUp.generic_react_add(sober,payload)
        elif payload.message_id in self.armourObj:
            print('Soberdogs remove react')
            armour = self.armourObj[payload.message_id]
            await OpSignUp.generic_react_add(armour,payload)
        elif payload.message_id in self.bastionObj:
            print('Soberdogs remove react')
            bastion = self.bastionObj[payload.message_id]
            await OpSignUp.generic_react_add(bastion,payload)
            
        else:
            pass
    
        print('Complete')
        
        
    @commands.Cog.listener('on_raw_message_delete') 
    async def generic_reset_check(self,payload):
        
        if payload.message_id in self.soberObj:
            del self.soberObj[payload.message_id]
        elif payload.message_id in self.armourObj:
            del self.armourObj[payload.message_id]
        elif payload.message_id in self.bastionObj:
            del self.bastionObj[payload.message_id]
            print(self.bastionObj)
        else:
            pass
    
        print('Complete')         
    
    
    @commands.command(name='ps2-signup')
    async def generic_signup(self,ctx,signup):
        
        channel = await OpSignUp.locate_sign_up(self,ctx)
        
        if signup == 'soberdogs':
            sober=SoberDogs(channel)
            print('Soberdogs instantiated')
            await sober.send_message()
            print(f'Soberdogs messgae sent {sober.messageHandlerID}')
            self.soberObj.update( {sober.messageHandlerID : sober})
            print('Soberdogs added to dictionary')
        elif signup == 'armourdogs':
            armour=ArmourDogs(channel)
            print('Armourdogs instantiated')
            await armour.send_message()
            print(f'Armourdogs messgae sent {armour.messageHandlerID}')
            self.armourObj.update( {armour.messageHandlerID : armour})
            print('Armourdogs added to dictionary')
        elif signup == 'bastion':
            bastion=Bastion(channel)
            print('Bastion instantiated')
            await bastion.send_message()
            print(f'Bastion messgae sent {bastion.messageHandlerID}')
            self.bastionObj.update( {bastion.messageHandlerID : bastion})
            print('Bastion added to dictionary')
        else:
            print('Sign up type does not exist')
            
        print('Complete')
    
    
    async def generic_react_add(self,payload):
        
        messageText  = self.messageText
        message = await self.signUpChannel.fetch_message(self.messageHandlerID)
        
        
        
        if  str(payload.emoji) in self.reactions.keys() and str(payload.user_id) not in self.members:
            
            self.members.append(str(payload.user_id))
            
            if payload.member.nick != None:
                self.memberText.update({str(payload.user_id):f'\n{self.reactions[str(payload.emoji)]} - @{str(payload.member.nick)}'})
            else:
                self.memberText.update({str(payload.user_id):f'\n{self.reactions[str(payload.emoji)]} - @{str(payload.member.name)}'})
                
            
            for player in self.memberText.values():
                messageText = messageText + str(player)


            print(messageText)

            await message.edit(content=messageText)

            print('Reaction accepted')
        else:
            self.ignoreRemove = True
            await message.remove_reaction(payload.emoji,payload.member)
            print('Reaction removed')
              
            
    async def generic_react_remove(self,payload):
            
        if self.ignoreRemove:
            self.ignoreRemove = False
            return

        if str(payload.emoji) in self.reactions.keys():
            message = await self.signUpChannel.fetch_message(self.messageHandlerID)
            messageText  = self.messageText
            del self.memberText[str(payload.user_id)]
            self.members.remove(str(payload.user_id))
            for player in self.memberText.values():
                messageText = messageText + str(player)
            await message.edit(content=messageText)
            
            
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
        
        
        
class SoberDogs:
    
    def __init__(self,channel):
        self.signUpChannel = channel
        self.messageText = SoberDogs.get_message()
        self.messageHandlerID = None
        self.members = []
        self.memberText = {}
        self.ignoreRemove = False
        self.reactions={'<:Icon_Heavy_Assault:795726910344003605>': 'Heavy','<:Icon_Combat_Medic:795726867960692806>' : 'Medic', '<:Icon_Infiltrator:795726922264215612>' : 'Infiltrator', '<:Icon_Light_Assault:795726936759468093>' : 'Light assault', '<:Icon_Engineer:795726888763916349>' : 'Engineer'}
   

    def get_message():
        with open('messages/soberdogs.txt','r') as f:
            messageText = f.read()
            return messageText
    
    async def send_message(self):
        messageHandler = await self.signUpChannel.send(self.messageText)
        self.messageHandlerID = messageHandler.id
        
        
        
class ArmourDogs:
    
    def __init__(self,channel):
        self.signUpChannel = channel
        self.messageText = ArmourDogs.get_message()
        self.messageHandlerID = None
        self.members = []
        self.memberText = {}
        self.ignoreRemove = False
        self.reactions={'<:Icon_Vanguard:795727955896565781>':'Vanguard','<:ps2flash:795726333455237121>': 'Flash','<:Icon_Sunderer:795727911549272104>': 'Sunderer','<:Icon_Lightning:795727852875677776>':'Lightning','<:Icon_ANT:795727784239824896>' : 'ANT','<:Icon_Harasser:795727814220840970>' : 'Harasser' }
   

    def get_message():
        with open('messages/armourdogs.txt','r') as f:
            messageText = f.read()
            return messageText
    
    async def send_message(self):
        messageHandler = await self.signUpChannel.send(self.messageText)
        self.messageHandlerID = messageHandler.id
        
        
class Bastion:
    
    def __init__(self,channel):
        self.signUpChannel = channel
        self.messageText = Bastion.get_message()
        self.messageHandlerID = None
        self.members = []
        self.memberText = {}
        self.ignoreRemove = False
        self.reactions={'<:NC:727306728470872075>':'NC'}
   

    def get_message():
        with open('messages/bastion.txt','r') as f:
            messageText = f.read()
            return messageText
    
    async def send_message(self):
        messageHandler = await self.signUpChannel.send(self.messageText)
        self.messageHandlerID = messageHandler.id