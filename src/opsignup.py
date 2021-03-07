import os
import asyncio
import discord

import settings

from discord.ext import commands
from dotenv import load_dotenv


class OpSignUp(commands.Cog):
    """
    Class to generate automated signup sheets
    """
    def __init__(self,bot):
        self.signUpChannelName = {'soberdogs':'✍-soberdogs','armourdogs':'✍-armourdogs','bastion':'📣-ps2-events','squadleaders':'✍-squadleaders','dogfighters':'✍-dogfighters'}

        self.soberObj = {}
        self.armourObj = {}
        self.bastionObj = {}
        self.squadObj = {}
        self.airObj = {}
        self.bot = bot
        super().__init__()


    @commands.Cog.listener('on_raw_reaction_remove')
    async def react_remove_sign_up_check(self,payload):
        """
        Captures all remove reactions, then filters through to
        use only those that are pertinent to the
        signup functions
        """
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
        elif payload.message_id in self.squadObj:
            print('Squad remove react')
            squad = self.squadObj[payload.message_id]
            await OpSignUp.generic_react_remove(squad,payload)
        elif payload.message_id in self.airObj:
            print('Air remove react')
            air = self.airObj[payload.message_id]
            await OpSignUp.generic_react_remove(air,payload)
        else:
            pass

        print('Complete')



    @commands.Cog.listener('on_raw_reaction_add')
    async def react_sign_up_check(self,payload):
        """
        Captures all reactions, then filters through to
        use only those that are pertinent to the
        signup functions
        """
        print(f'reaction caught {str(payload.emoji)}')
        if payload.message_id in self.soberObj:
            print('Soberdogs add react')
            sober = self.soberObj[payload.message_id]
            await OpSignUp.generic_react_add(sober,payload)
        elif payload.message_id in self.armourObj:
            print('Armourdogs add react')
            armour = self.armourObj[payload.message_id]
            await OpSignUp.generic_react_add(armour,payload)
        elif payload.message_id in self.bastionObj:
            print('Bastion add react')
            bastion = self.bastionObj[payload.message_id]
            await OpSignUp.generic_react_add(bastion,payload)
        elif payload.message_id in self.squadObj:
            print('Squad add react')
            squad = self.squadObj[payload.message_id]
            await OpSignUp.generic_react_add(squad,payload)
        elif payload.message_id in self.airObj:
            print('Air add react')
            air = self.airObj[payload.message_id]
            await OpSignUp.generic_react_add(air,payload)

        else:
            pass

        print('Complete')


    @commands.Cog.listener('on_raw_message_delete')
    async def generic_reset_check(self,payload):
        """
        Captures all message deletes, then filters through to
        use only those that are pertinent to the
        signup functions.

        Function then cleans up the objects
        """
        if payload.message_id in self.soberObj:
            del self.soberObj[payload.message_id]
        elif payload.message_id in self.armourObj:
            del self.armourObj[payload.message_id]
        elif payload.message_id in self.bastionObj:
            del self.bastionObj[payload.message_id]
            print(self.bastionObj)
        elif payload.message_id in self.squadObj:
            del self.squadObj[payload.message_id]
            print(self.squadObj)
        elif payload.message_id in self.airObj:
            del self.airObj[payload.message_id]
            print(self.airObj)
        else:
            pass

        print('Complete')


    @commands.command(name='ps2-signup')
    @commands.has_any_role('CO','Captain','Lieutenant','Sergeant')
    async def generic_signup(self,ctx,signup,date):
        """
        Usage: !ps2-sign <squadtype> <date>
        Squadtypes: squadleaders, soberdogs, armourdogs, dogfighters
                    bastion
        Notes: Only the 'CO', 'Captain', 'Lieutenant', 'Sergeant' roles
        will allow this command

        Functions to begin signup sheet operation.

        Creates the relevant squadtype object and stores in
        dictionary of form {message_id : squadObj}
        """

        channel = await OpSignUp.locate_sign_up(self,ctx,signup)

        if signup == 'soberdogs':
            sober=SoberDogs(channel)
            print('Soberdogs instantiated')
            await sober.send_message(ctx,date)
            print(f'Soberdogs messgae sent {sober.messageHandlerID}')
            self.soberObj.update( {sober.messageHandlerID : sober})
            print('Soberdogs added to dictionary')
        elif signup == 'armourdogs':
            armour=ArmourDogs(channel)
            print('Armourdogs instantiated')
            await armour.send_message(ctx,date)
            print(f'Armourdogs messgae sent {armour.messageHandlerID}')
            self.armourObj.update( {armour.messageHandlerID : armour})
            print('Armourdogs added to dictionary')
        elif signup == 'bastion':
            bastion=Bastion(channel)
            print('Bastion instantiated')
            await bastion.send_message(ctx,date)
            print(f'Bastion messgae sent {bastion.messageHandlerID}')
            self.bastionObj.update( {bastion.messageHandlerID : bastion})
            print('Bastion added to dictionary')
        elif signup == 'squadleaders':
            squad=SquadLead(channel)
            print('squad instantiated')
            await squad.send_message(ctx,date)
            print(f'squad messgae sent {squad.messageHandlerID}')
            self.squadObj.update( {squad.messageHandlerID : squad})
            print('squad added to dictionary')
        elif signup == 'dogfighters':
            air=DogFighters(channel)
            print('air instantiated')
            await air.send_message(ctx,date)
            print(f'air messgae sent {air.messageHandlerID}')
            self.airObj.update( {air.messageHandlerID : air})
            print('air added to dictionary')
        else:
            print('Sign up type does not exist')

        print('Complete')


    async def generic_react_add(self,payload):

        messageText  = self.messageText
        message = await self.signUpChannel.fetch_message(self.messageHandlerID)



        if  str(payload.emoji) in self.reactions.keys() and str(payload.user_id) not in self.members and not OpSignUp.react_max(self,payload):




            OpSignUp.update_react_num(self,payload,'add')

            self.members.append(str(payload.user_id))

            self.memberText.update({str(payload.user_id):f'\n{self.reactions[str(payload.emoji)]} - {str(payload.member.mention)}'})

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
            OpSignUp.update_react_num(self,payload,'remove')
            for player in self.memberText.values():
                messageText = messageText + str(player)
            await message.edit(content=messageText)


    async def locate_sign_up(self,ctx,signup):
        print('Lookup signup channel')
        try:
            channels = ctx.guild.text_channels
        except:
            print('fail')
            return None
        print('Got text channel list')
        for channel in channels:
            if self.signUpChannelName[signup] == channel.name:
                print('Channel Found')
                return channel
        print('Lookup complete')

    def react_max(self,payload):

        if self.maxReact[str(payload.emoji)][0] < 0:
            return False
        elif self.maxReact[str(payload.emoji)][1] < self.maxReact[str(payload.emoji)][0]:
            return False
        else:
            return True

    def update_react_num(self,payload,operation=str):

        maxReact = self.maxReact[str(payload.emoji)][0]
        current = self.maxReact[str(payload.emoji)][1]
        if operation == 'add':
            current = current + 1
        elif operation == 'remove':
            current = current - 1

        self.maxReact.update({str(payload.emoji):[maxReact,current]})




class SoberDogs:

    def __init__(self,channel):
        self.signUpChannel = channel
        self.messageText = SoberDogs.get_message()
        self.messageHandlerID = None
        self.members = []
        self.memberText = {}
        self.ignoreRemove = False
        self.reactions={'<:Icon_Heavy_Assault:795726910344003605>': 'Heavy','<:Icon_Combat_Medic:795726867960692806>' : 'Medic', '<:Icon_Infiltrator:795726922264215612>' : 'Infiltrator', '<:Icon_Light_Assault:795726936759468093>' : 'Light assault', '<:Icon_Engineer:795726888763916349>' : 'Engineer','<:Icon_Spawn_Beacon_NC:795729269891530792>':'Reserve'}
        self.maxReact={'<:Icon_Heavy_Assault:795726910344003605>': [5,0],'<:Icon_Combat_Medic:795726867960692806>' : [4,0], '<:Icon_Infiltrator:795726922264215612>' : [1,0], '<:Icon_Light_Assault:795726936759468093>' :[0,0], '<:Icon_Engineer:795726888763916349>' : [2,0],'<:Icon_Spawn_Beacon_NC:795729269891530792>': [-1,0]}
        self.mentionRoles =['here','DrunkenDogs','Soberdogs']

    def get_message():
        with open('messages/soberdogs.txt','r') as f:
            messageText = f.read()
            return messageText

    async def send_message(self,ctx,date):

        self.messageText = f'\n**Date of activity: {date}**\n' + self.messageText
        roles = await ctx.guild.fetch_roles()

        for role in roles:
            if role.name in self.mentionRoles:
                self.messageText = f'{role.mention} ' + self.messageText
            else:
                pass
        messageHandler = await self.signUpChannel.send(self.messageText)
        self.messageHandlerID = messageHandler.id

    async def send_message(self,ctx,date):

        self.messageText = f'\n**Date of activity: {date}**\n' + self.messageText
        roles = await ctx.guild.fetch_roles()

        for role in roles:
            if role.name in self.mentionRoles:
                self.messageText = f'{role.mention} ' + self.messageText
            else:
                pass
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
        self.maxReact={'<:Icon_Vanguard:795727955896565781>':[-1,0],'<:ps2flash:795726333455237121>': [-1,0],'<:Icon_Sunderer:795727911549272104>': [-1,0],'<:Icon_Lightning:795727852875677776>':[-1,0],'<:Icon_ANT:795727784239824896>' : [-1,0],'<:Icon_Harasser:795727814220840970>' : [-1,0] }
        self.mentionRoles =['here','DrunkenDogs','ArmourDogs']

    def get_message():
        with open('messages/armourdogs.txt','r') as f:
            messageText = f.read()
            return messageText

    async def send_message(self,ctx,date):

        self.messageText = f'\n**Date of activity: {date}**\n' + self.messageText
        roles = await ctx.guild.fetch_roles()

        for role in roles:
            if role.name in self.mentionRoles:
                self.messageText = f'{role.mention} ' + self.messageText
            else:
                pass
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
        self.maxReact={'<:NC:727306728470872075>':[-1,0]}
        self.mentionRoles =['DrunkenDogs']


    def get_message():
        with open('messages/bastion.txt','r') as f:
            messageText = f.read()
            return messageText

    async def send_message(self,ctx,date):

        self.messageText = f'\n**Date of activity: {date}**\n' + self.messageText
        roles = await ctx.guild.fetch_roles()

        for role in roles:
            if role.name in self.mentionRoles:
                self.messageText = f'{role.mention} ' + self.messageText
            else:
                pass
        messageHandler = await self.signUpChannel.send(self.messageText)
        self.messageHandlerID = messageHandler.id

class SquadLead:

    def __init__(self,channel):
        self.signUpChannel = channel
        self.messageText = SquadLead.get_message()
        self.messageHandlerID = None
        self.members = []
        self.memberText = {}
        self.ignoreRemove = False
        self.reactions={'<:Icon_A:795729153072431104>':'PL','<:Icon_B:795729164891062343>':'SL','<:Icon_C:795729176363270205>':'FL','<:Icon_D:795729189260754956>':'Reserve'}
        self.maxReact={'<:Icon_A:795729153072431104>':[-1,0],'<:Icon_B:795729164891062343>':[-1,0],'<:Icon_C:795729176363270205>':[-1,0],'<:Icon_D:795729189260754956>':[-1,0]}
        self.mentionRoles =['CO','Captain','Lieutenant','Sergeant','Corporal','Lance-Corporal']


    def get_message():
        with open('messages/opsnight.txt','r') as f:
            messageText = f.read()
            return messageText

    async def send_message(self,ctx,date):

        self.messageText = f'\n**Date of activity: {date}**\n' + self.messageText
        roles = await ctx.guild.fetch_roles()

        for role in roles:
            if role.name in self.mentionRoles:
                self.messageText = f'{role.mention} ' + self.messageText
            else:
                pass
        messageHandler = await self.signUpChannel.send(self.messageText)
        self.messageHandlerID = messageHandler.id


class DogFighters:

    def __init__(self,channel):
        self.signUpChannel = channel
        self.messageText = DogFighters.get_message()
        self.messageHandlerID = None
        self.members = []
        self.memberText = {}
        self.ignoreRemove = False
        self.reactions={'<:Icon_Valkyrie:795727937735098388>':'Valkyrie','<:Icon_Reaver:795727893342846986>': 'Reaver','<:Icon_Galaxy:795727799591239760>': 'Galaxy','<:Icon_Liberator:795727831605837874>':'Liberator'}
        self.maxReact={'<:Icon_Valkyrie:795727937735098388>':[-1,0],'<:Icon_Reaver:795727893342846986>': [-1,0],'<:Icon_Galaxy:795727799591239760>': [-1,0],'<:Icon_Liberator:795727831605837874>':[-1,0]}
        self.mentionRoles =['DrunkenDogs','DogFighters']

    def get_message():
        with open('messages/dogfighters.txt','r') as f:
            messageText = f.read()
            return messageText

    async def send_message(self,ctx,date):

        self.messageText = f'\n**Date of activity: {date}**\n' + self.messageText
        roles = await ctx.guild.fetch_roles()

        for role in roles:
            if role.name in self.mentionRoles:
                self.messageText = f'{role.mention} ' + self.messageText
            else:
                pass
        messageHandler = await self.signUpChannel.send(self.messageText)
        self.messageHandlerID = messageHandler.id
