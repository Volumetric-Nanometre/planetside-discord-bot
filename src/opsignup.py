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
        Usage 1: !ps2-signup <squadtype-1> <date>
        Usage 2: !ps2-signup <squadtype-2> <date> <op-type> <description>
        
        Usage 3: !ps2-signup <limit-type> <message ID> <react-1> <limit-1> ... <react-n> <limit-n>
        squadtype-1: squadleaders, soberdogs, armourdogs, dogfighters
                    bastion, raw
        squadtype-2: training, ncaf, cobaltclash
        limit-type: current-limits, set-limits 
                    
        date: Type as a string within quotation marks, e.g "Monday 8:30"
        
        op-type: A string describing the op type, e.g "Galaxy drop training"
        
        description: A string describing the op in detail. Can be multiline
                     so long as they remain within quotation marks 
        
        message ID: The message ID of the message you wish to change the react
                    limits on
        
        react-n: The reaction for the limit to be changed on
        
        limit-n: The new max limit for the reacts. -1 is unlimited. 0 is zero
                 limit>0 will enforce limit
        
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


class GenericMessage(GenericSignup):

    def __init__(self):
        super().__init__()
        pass

    async def send_message(self,ctx,date):
        
        try:
            self.messageText = f'\n**Activity Type: {self.opsType}**' + self.messageText
        except:
            print("opsType does not exist")
        
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
