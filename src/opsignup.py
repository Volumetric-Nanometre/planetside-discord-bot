import os
import asyncio
import discord

import settings

import traceback

from discord.ext import commands
from dotenv import load_dotenv

class OpSignUp(commands.Cog):
    """
    Class to generate automated signup sheets
    """
    def __init__(self,bot):
        self.signUpChannelName = {'soberdogs':['✍-soberdogs',SoberDogs],'armourdogs':['✍-armourdogs',ArmourDogs],
                                  'bastion':['📣-ps2-events',Bastion],'squadleaders':['✍-squadleaders',SquadLead],
                                  'dogfighters':['✍-dogfighters',DogFighters],'logidogs':['✍-logistics', Logidogs],
                                  'training':['✍-training',Training], 'jointops':['✍-joint-ops',JointOps],
                                  'raw':['✍-royal-air-woof', RoyalAirWoof],'ncaf':['✍-ncaf',NCAF],
                                  'cobaltclash':['✍-cobalt-clash',CobaltClash]}

        self.objDict = {}
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

        if payload.message_id in self.objDict:
            print('Remove react')
            obj = self.objDict[payload.message_id]
            await OpSignUp.generic_react_remove(obj,payload)
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
        if payload.message_id in self.objDict:
            print('Add react')
            obj = self.objDict[payload.message_id]
            await OpSignUp.generic_react_add(obj,payload)
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
        if payload.message_id in self.objDict:
            del self.objDict[payload.message_id]
            print('Message Deleted')
        else:
            pass

        print('Complete')


    @commands.command(name='ps2-signup')
    @commands.has_any_role('CO','Captain','Lieutenant','Sergeant')
    async def generic_signup(self,ctx,signup,date,*args):
        """
        Usage: !ps2-signup <squadtype> <date> <args>
        squadtype: squadleaders, soberdogs, armourdogs, dogfighters
                    bastion, training
        date: Type as a string within quotation marks, e.g "Monday 8:30"
        Notes: Only the 'CO', 'Captain', 'Lieutenant', 'Sergeant' roles
        will allow this command

        Functions to begin signup sheet operation.

        Creates the relevant squadtype object and stores in
        dictionary of form {message_id : squadObj}
        """

        channel = await OpSignUp.locate_sign_up(self,ctx,signup)

        if signup in self.signUpChannelName:
            print('Sign up found')
            try:
                obj=self.signUpChannelName[signup][1](channel,*args)
            except Exception:
                traceback.print_exc()
                print('Sign up failed')
            else:
                print(f'{signup} instantiated')
                await obj.send_message(ctx,date)
                print(f'{signup} message sent {obj.messageHandlerID}')
                self.objDict.update( {obj.messageHandlerID : obj})
                print(f'{signup} added to dictionary')

        elif signup == 'current-limits':
            try:
                obj = self.objDict[int(date)]
                print(obj)
                print(obj.messageHandlerID)
                await obj.get_reaction_details(ctx)

            except Exception:
                traceback.print_exc()
                print("Object does not exist")
                print(self.objDict)

        elif signup == 'set-limits':
            try:
                obj = self.objDict[int(date)]
                print(obj)
                print(obj.messageHandlerID)
                await obj.set_reaction_details(ctx,*args)

            except Exception:
                traceback.print_exc()
                print("Object does not exist")
                print(self.objDict)

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
            try:
                if self.signUpChannelName[signup][0] == channel.name:
                    print('Channel Found')
                    return channel
            except:
                print("No channel found")
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




class GenericSignup:

    def __init__(self):
        pass

    def get_message(messageLocation):
        with open(messageLocation,'r') as f:
            messageText = f.read()
            return messageText

    async def get_reaction_details(self,ctx):

        message = "Reaction : Max Number\n"
        for react in self.maxReact:

            if self.maxReact[react][0] == -1:
                message = message + f"{react} : (-1) Unlimited\n"
            else:
                message = message + f"{react} : {self.maxReact[react][0]}\n"

        await ctx.channel.send(message)

    async def set_reaction_details(self,ctx,*args):

        for index, value in enumerate(args):

            try:
                print(f"Changing {value}")
                if value in self.maxReact:
                    currentUsed = self.maxReact[value][1]
                    print(f"Current val {currentUsed}")

                    print(f"New val {args[index+1]}")
                    self.maxReact.update( {value: [int(args[index+1]),currentUsed]})
                    print(f"{self.maxReact[value]}")

                else:
                    print("React does not exist")
            except Exception:
                traceback.print_exc()

        await ctx.channel.send("New Values:")
        await self.get_reaction_details(ctx)


class SimpleMessage(GenericSignup):

    def __init__(self):
        super(SimpleMessage,self).__init__()
        pass

    async def send_message(self,ctx,date):

        self.messageText = f'\n**Date of activity: {date}**\n' + self.messageText
        roles = await ctx.guild.fetch_roles()

        for role in roles:
            if role.name in self.mentionRoles:
                self.messageText = f'{role.mention} ' + self.messageText
            else:
                pass
            
        reactStr=str()
        for reaction in self.reactions.keys():
            reactStr = reactStr + f'{self.reactions[reaction]} {reaction}\n'

        self.messageText = self.messageText + f'\n\n**Use the following reacts:**\n{reactStr}'
        self.messageText = self.messageText + f'\n**If your name does not appear, your signup has not happened.**\n**To remove or change signup, unreact.**'
        
        messageHandler = await self.signUpChannel.send(self.messageText)
        self.messageHandlerID = messageHandler.id



class ComplexMessage(GenericSignup):

    def __init__(self):
        super(ComplexMessage,self).__init__()
        pass

    async def send_message(self,ctx,date):

        self.messageText = f'\n**Activity Type: {self.opsType}**' + self.messageText
        self.messageText = f'\n**Date of activity: {date}**\n' + self.messageText

        roles = await ctx.guild.fetch_roles()

        for role in roles:
            if role.name in self.mentionRoles:
                self.messageText = f'{role.mention} ' + self.messageText
            else:
                pass

        reactStr=str()
        for reaction in self.reactions.keys():
            reactStr = reactStr + f'{self.reactions[reaction]} {reaction}\n'

        self.messageText = self.messageText + f'\n\n**Use the following reacts:**\n{reactStr}'
        self.messageText = self.messageText + f'\n**If your name does not appear, your signup has not happened.**\n**To remove or change signup, unreact.**'

        messageHandler = await self.signUpChannel.send(self.messageText)
        self.messageHandlerID = messageHandler.id
        
        
class ArmourDogs(SimpleMessage):

    def __init__(self,channel):
        super(ArmourDogs,self).__init__()
        self.signUpChannel = channel
        self.messageText = ArmourDogs.get_message('messages/armourdogs.txt')
        self.messageHandlerID = None
        self.members = []
        self.memberText = {}
        self.ignoreRemove = False
        self.reactions={'<:Icon_Vanguard:795727955896565781>':'Vanguard','<:Icon_Sunderer:795727911549272104>': 'Sunderer'
                        ,'<:Icon_Lightning:795727852875677776>':'Lightning','<:Icon_Harasser:795727814220840970>' : 'Harasser'
                        ,'<:Icon_Spawn_Beacon_NC:795729269891530792>': 'Reserve/Maybe' }
        self.maxReact={'<:Icon_Vanguard:795727955896565781>':[-1,0],'<:Icon_Sunderer:795727911549272104>': [-1,0]
                       ,'<:Icon_Lightning:795727852875677776>':[-1,0], '<:Icon_Harasser:795727814220840970>' : [-1,0]
                       ,'<:Icon_Spawn_Beacon_NC:795729269891530792>':[-1,0] }
        self.mentionRoles =['ArmourDogs']

class Bastion(SimpleMessage):

    def __init__(self,channel):
        super(Bastion,self).__init__()
        self.signUpChannel = channel
        self.messageText = Bastion.get_message('messages/bastion.txt')
        self.messageHandlerID = None
        self.members = []
        self.memberText = {}
        self.ignoreRemove = False
        self.reactions={'<:tdkdsmall:803387734172762143>':'Woof'}
        self.maxReact={'<:tdkdsmall:803387734172762143>':[-1,0]}
        self.mentionRoles =['TDKD']

class DogFighters(SimpleMessage):

    def __init__(self,channel):
        super(DogFighters,self).__init__()
        self.signUpChannel = channel
        self.messageText = DogFighters.get_message('messages/dogfighters.txt')
        self.messageHandlerID = None
        self.members = []
        self.memberText = {}
        self.ignoreRemove = False
        self.reactions={'<:Icon_Reaver:795727893342846986>': 'Reaver','<:Icon_Dervish:861303237062950942>':'Dervish','<:Icon_Spawn_Beacon_NC:795729269891530792>':'Reserve'}
        self.maxReact={'<:Icon_Reaver:795727893342846986>': [-1,0],'<:Icon_Dervish:861303237062950942>':[-1,0],'<:Icon_Spawn_Beacon_NC:795729269891530792>':[-1,0]}
        self.mentionRoles =['DogFighters']

class Logidogs(SimpleMessage):

    def __init__(self,channel):
        super(Logidogs,self).__init__()
        self.signUpChannel = channel
        self.messageText = Logidogs.get_message('messages/logidogs.txt')
        self.messageHandlerID = None
        self.members = []
        self.memberText = {}
        self.ignoreRemove = False
        self.reactions={'<:Icon_Infiltrator:795726922264215612>':'Hacker', '<:Icon_Engineer:795726888763916349>':'Router','<:Icon_Spawn_Beacon_NC:795729269891530792>': 'Reserve'}
        self.maxReact={ '<:Icon_Infiltrator:795726922264215612>' : [4,0], '<:Icon_Engineer:795726888763916349>' :[2,0],'<:Icon_Spawn_Beacon_NC:795729269891530792>': [-1,0]}
        self.mentionRoles =['LogiDogs']

class RoyalAirWoof(SimpleMessage):

    def __init__(self,channel):
        super(RoyalAirWoof,self).__init__()
        self.signUpChannel = channel
        self.messageText = RoyalAirWoof.get_message('messages/royalairwoof.txt')
        self.messageHandlerID = None
        self.members = []
        self.memberText = {}
        self.ignoreRemove = False
        self.reactions={'<:Icon_Galaxy:795727799591239760>': 'Gal-Pilot','<:Icon_Liberator:795727831605837874>':'Lib-Pilot'
                        ,'<:Icon_Engineer:795726888763916349>':'Gunner','<:Icon_Spawn_Beacon_NC:795729269891530792>':'Reserve'}
        self.maxReact={'<:Icon_Galaxy:795727799591239760>': [4,0],'<:Icon_Liberator:795727831605837874>':[0,0], '<:Icon_Engineer:795726888763916349>':[6,0] ,'<:Icon_Spawn_Beacon_NC:795729269891530792>':[-1,0]}
        self.mentionRoles =['RAW']

class SoberDogs(SimpleMessage):

    def __init__(self,channel):
        super(SoberDogs,self).__init__()
        self.signUpChannel = channel
        self.messageText = SoberDogs.get_message('messages/soberdogs.txt')
        self.messageHandlerID = None
        self.members = []
        self.memberText = {}
        self.ignoreRemove = False
        self.reactions={'<:Icon_MAX:795726948365631559>': 'MAX','<:Icon_Heavy_Assault:795726910344003605>': 'Heavy'
                        ,'<:Icon_Combat_Medic:795726867960692806>' : 'Medic', '<:Icon_Infiltrator:795726922264215612>' : 'Infiltrator'
                        , '<:Icon_Light_Assault:795726936759468093>' : 'Light assault', '<:Icon_Engineer:795726888763916349>' : 'Engineer'
                        ,'<:Icon_Spawn_Beacon_NC:795729269891530792>':'Reserve'}
        self.maxReact={'<:Icon_MAX:795726948365631559>': [0,0],'<:Icon_Heavy_Assault:795726910344003605>': [5,0]
                       ,'<:Icon_Combat_Medic:795726867960692806>' : [4,0], '<:Icon_Infiltrator:795726922264215612>' : [1,0]
                       , '<:Icon_Light_Assault:795726936759468093>' :[0,0], '<:Icon_Engineer:795726888763916349>' : [2,0]
                       ,'<:Icon_Spawn_Beacon_NC:795729269891530792>': [-1,0]}
        self.mentionRoles =['Soberdogs']

class SquadLead(SimpleMessage):

    def __init__(self,channel):
        super(SquadLead,self).__init__()
        self.signUpChannel = channel
        self.messageText = SquadLead.get_message('messages/opsnight.txt')
        self.messageHandlerID = None
        self.members = []
        self.memberText = {}
        self.ignoreRemove = False
        self.reactions={'<:Icon_A:795729153072431104>':'PL','<:Icon_B:795729164891062343>':'SL','<:Icon_C:795729176363270205>':'FL'
                        ,'<:Icon_D:795729189260754956>':'Reserve','<:Icon_Heavy_Assault:795726910344003605>': 'Soberdog S/FL'
                       ,'<:Icon_Galaxy:795727799591239760>': 'RAW S/FL','<:Icon_Vanguard:795727955896565781>':'Armour S/FL'}
        self.maxReact={'<:Icon_A:795729153072431104>':[-1,0],'<:Icon_B:795729164891062343>':[-1,0],'<:Icon_C:795729176363270205>':[-1,0]
                       ,'<:Icon_D:795729189260754956>':[-1,0],'<:Icon_Heavy_Assault:795726910344003605>': [-1,0]
                       ,'<:Icon_Galaxy:795727799591239760>': [-1,0],'<:Icon_Vanguard:795727955896565781>':[-1,0]}
        self.mentionRoles =['CO','Captain','Lieutenant','Sergeant','Corporal']


class CobaltClash(ComplexMessage):

    def __init__(self,channel,opsType, message):
        self.signUpChannel = channel
        self.opsType=opsType
        self.messageText = message
        self.messageHandlerID = None
        self.members = []
        self.memberText = {}
        self.ignoreRemove = False
        self.reactions={'<:NC:727306728470872075>':'Coming','<:Icon_Spawn_Beacon_NC:795729269891530792>':'Reserve'}
        self.maxReact={'<:NC:727306728470872075>':[-1,0],'<:Icon_Spawn_Beacon_NC:795729269891530792>':[-1,0]}
        self.mentionRoles =['TDKD']


class JointOps(ComplexMessage):

    def __init__(self,channel,opsType, message):
        self.signUpChannel = channel
        self.opsType=opsType
        self.messageText = message
        self.messageHandlerID = None
        self.members = []
        self.memberText = {}
        self.ignoreRemove = False
        self.reactions={'<:NC:727306728470872075>':'Coming','<:Icon_Spawn_Beacon_NC:795729269891530792>':'Reserve'}
        self.maxReact={'<:NC:727306728470872075>':[-1,0],'<:Icon_Spawn_Beacon_NC:795729269891530792>':[-1,0]}
        self.mentionRoles =['TDKD']

class NCAF(ComplexMessage):

    def __init__(self,channel,opsType, message):
        self.signUpChannel = channel
        self.opsType=opsType
        self.messageText = message
        self.messageHandlerID = None
        self.members = []
        self.memberText = {}
        self.ignoreRemove = False
        self.reactions={'<:NC:727306728470872075>':'Coming','<:Icon_Spawn_Beacon_NC:795729269891530792>':'Reserve'}
        self.maxReact={'<:NC:727306728470872075>':[-1,0],'<:Icon_Spawn_Beacon_NC:795729269891530792>':[-1,0]}
        self.mentionRoles =['TDKD']

class Training(ComplexMessage):

    def __init__(self,channel,opsType, message):
        self.signUpChannel = channel
        self.opsType=opsType
        self.messageText = message
        self.messageHandlerID = None
        self.members = []
        self.memberText = {}
        self.ignoreRemove = False
        self.reactions={'<:tdkdsmall:803387734172762143>': 'TDKD','<:NC:727306728470872075>':'Guest','<:Icon_Spawn_Beacon_NC:795729269891530792>':'Reserve'}
        self.maxReact={'<:tdkdsmall:803387734172762143>':[-1,0],'<:NC:727306728470872075>':[-1,0],'<:Icon_Spawn_Beacon_NC:795729269891530792>':[-1,0]}
        self.mentionRoles =['TDKD','The Washed Masses']
