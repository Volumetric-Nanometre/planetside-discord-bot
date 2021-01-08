import os
import asyncio
import discord

import settings

from discord.ext import commands
from dotenv import load_dotenv


class OpSignUp(commands.Cog): 
    
    def __init__(self,bot):
        self.soberdogMessageText = ""
        self.soberdogMessageHandlerID = None
        self.signUpChannelName ='✍-sign-up'
        self.signUpChannel = None
        self.soberMembers = []
        self.soberMemberText = {}
        self.ignoreSoberRemove = False
        self.soberReactions={'<:Icon_Heavy_Assault:795726910344003605>': 'Heavy','<:Icon_Combat_Medic:795726867960692806>' : 'Medic', '<:Icon_Infiltrator:795726922264215612>' : 'Infiltrator', '<:Icon_Light_Assault:795726936759468093>' : 'Light assault', '<:Icon_Engineer:795726888763916349>' : 'Engineer'}
        
        self.armourdogMessageText = ""
        self.armourdogMessageHandlerID = None
        self.armourMembers = []
        self.armourMemberText = {}
        self.armourReactions={'<:Icon_Vanguard:795727955896565781>':'Vanguard','<:ps2flash:795726333455237121>': 'Flash','<:Icon_Sunderer:795727911549272104>': 'Sunderer','<:Icon_Lightning:795727852875677776>':'Lightning','<:Icon_ANT:795727784239824896>' : 'ANT','<:Icon_Harasser:795727814220840970>' : 'Harasser' }
        self.ignoreArmourRemove = False
        
        self.bastionMessageText = ""
        self.bastionMessageHandlerID = None
        self.bastionMembers = []
        self.bastionMemberText = {}
        self.bastionReactions={'<:NC:727306728470872075>':'NC'}
        self.ignoreBastionRemove = False
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
            
            if payload.member.nick != None:
                self.soberMemberText.update({str(payload.user_id):f'\n{self.soberReactions[str(payload.emoji)]} - @{str(payload.member.nick)}'})
            else:
                self.soberMemberText.update({str(payload.user_id):f'\n{self.soberReactions[str(payload.emoji)]} - @{str(payload.member.name)}'})
                
            
            for player in self.soberMemberText.values():
                messageText = messageText + str(player)


            print(messageText)

            await message.edit(content=messageText)

            print('Reaction accepted')
        else:
            self.ignoreSoberRemove = True
            await message.remove_reaction(payload.emoji,payload.member)
            print('Reaction removed')
       
    
    async def sober_dogs_remove(self,payload):
            
        if self.ignoreSoberRemove:
            self.ignoreSoberRemove = False
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
        message = await self.signUpChannel.fetch_message(self.soberdogMessageHandlerID)
        await message.delete()
        
        self.soberdogMessageText = ""
        self.soberdogMessageHandlerID = None
        self.soberMembers = []
        self.soberMemberText = {}
        self.ignoreSoberRemove = False
    
 
    
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
        if payload.message_id == self.bastionMessageHandlerID:
            print('Bastion remove react')
            await OpSignUp.bastion_remove(self,payload)

            
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
        if payload.message_id == self.armourdogMessageHandlerID:
            print('ArmourDogs react')
            await OpSignUp.armour_dogs_add(self,payload)
        if payload.message_id == self.bastionMessageHandlerID:
            print('Bastion react')
            await OpSignUp.bastion_add(self,payload)

            
        else:
            print('Not sober')
    
        print('in sign-up')
        

    @commands.command(name='ps2-armour-signup')
    async def armour_dog_signup(self,ctx):
        self.signUpChannel = await OpSignUp.locate_sign_up(self,ctx)
        with open('messages/armourdogs.txt','r') as f:
            self.armourdogMessageText = f.read()
        
        messageHandler = await self.signUpChannel.send(self.armourdogMessageText)
        self.armourdogMessageHandlerID = messageHandler.id
        print('Message sent')
    
    @commands.command(name='ps2-armour-signup-reset')
    async def armour_dog_signup_reset(self,ctx):
        message = await self.signUpChannel.fetch_message(self.armourdogMessageHandlerID)
        await message.delete()
        
        self.armourdogMessageText = ""
        self.armourdogMessageHandlerID = None
        self.armourMembers = []
        self.armourMemberText = {}
        self.ignoreArmourRemove = False
        
    
    async def armour_dogs_add(self,payload):
        
        messageText  = self.armourdogMessageText
        message = await self.signUpChannel.fetch_message(self.armourdogMessageHandlerID)
        
        if  str(payload.emoji) in self.armourReactions.keys() and str(payload.user_id) not in self.armourMembers:
            
            self.armourMembers.append(str(payload.user_id))
            
            if payload.member.nick != None:
                self.armourMemberText.update({str(payload.user_id):f'\n{self.armourReactions[str(payload.emoji)]} - @{str(payload.member.nick)}'})
            else:
                self.armourMemberText.update({str(payload.user_id):f'\n{self.armourReactions[str(payload.emoji)]} - @{str(payload.member.name)}'})
                
            
            for player in self.armourMemberText.values():
                messageText = messageText + str(player)


            print(messageText)

            await message.edit(content=messageText)

            print('Reaction accepted')
        else:
            self.ignoreArmourRemove = True
            await message.remove_reaction(payload.emoji,payload.member)
            print('Reaction removed')
            
            
    async def armour_dogs_remove(self,payload):
            
        if self.ignoreArmourRemove:
            self.ignoreArmourRemove = False
            return

        if str(payload.emoji) in self.armourReactions.keys():
            message = await self.signUpChannel.fetch_message(self.armourdogMessageHandlerID)
            messageText  = self.armourdogMessageText
            del self.armourMemberText[str(payload.user_id)]
            self.armourMembers.remove(str(payload.user_id))
            for player in self.armourMemberText.values():
                messageText = messageText + str(player)
            await message.edit(content=messageText)
            
    @commands.command(name='ps2-bastion-signup')
    async def bastion_signup(self,ctx):
        self.signUpChannel = await OpSignUp.locate_sign_up(self,ctx)
        with open('messages/bastion.txt','r') as f:
            self.bastionMessageText = f.read()
        
        messageHandler = await self.signUpChannel.send(self.bastionMessageText)
        self.bastionMessageHandlerID = messageHandler.id
        print('Message sent')
    
    @commands.command(name='ps2-bastion-signup-reset')
    async def bastion_signup_reset(self,ctx):
        message = await self.signUpChannel.fetch_message(self.bastionMessageHandlerID)
        await message.delete()
        
        self.bastionMessageText = ""
        self.bastionMessageHandlerID = None
        self.bastionMembers = []
        self.bastionMemberText = {}
        self.ignoreBastionRemove = False
        
        
    async def bastion_remove(self,payload):
            
        if self.ignoreBastionRemove:
            self.ignoreBastionRemove = False
            return

        if str(payload.emoji) in self.bastionReactions.keys():
            message = await self.signUpChannel.fetch_message(self.bastionMessageHandlerID)
            messageText  = self.bastionMessageText
            del self.bastionMemberText[str(payload.user_id)]
            self.bastionMembers.remove(str(payload.user_id))
            for player in self.bastionMemberText.values():
                messageText = messageText + str(player)
            await message.edit(content=messageText)
            
            
    async def bastion_add(self,payload):
        
        messageText  = self.bastionMessageText
        message = await self.signUpChannel.fetch_message(self.bastionMessageHandlerID)
        
        print(payload.emoji)
        
        if  str(payload.emoji) in self.bastionReactions.keys() and str(payload.user_id) not in self.bastionMembers:
            
            self.bastionMembers.append(str(payload.user_id))
            
            if payload.member.nick != None:
                self.bastionMemberText.update({str(payload.user_id):f'\n{self.bastionReactions[str(payload.emoji)]} - @{str(payload.member.nick)}'})
            else:
                self.bastionMemberText.update({str(payload.user_id):f'\n{self.bastionReactions[str(payload.emoji)]} - @{str(payload.member.name)}'})
                
            
            for player in self.bastionMemberText.values():
                messageText = messageText + str(player)


            print(messageText)
            
            await message.edit(content=messageText)

            print('Reaction accepted')
        else:
            self.ignoreBastionRemove = True
            await message.remove_reaction(payload.emoji,payload.member)
            print('Reaction removed')