import os
import asyncio
import discord

import settings

import traceback
from discord.ext import commands
from dotenv import load_dotenv

from opsignupclasses import *

class OpSignUp(commands.Cog):
    """
    Class to generate automated signup sheets
    """
    def __init__(self,bot):
        self.signUpChannelName = {'soberdogs':['✍-soberdogs',SoberDogs],'armourdogs':['✍-armourdogs',ArmourDogs],
                                  'bastion':['✍-bastion',Bastion],'squadleaders':['✍-squadleaders',SquadLead],
                                  'dogfighters':['✍-dogfighters',DogFighters],'logidogs':['✍-logistics', Logidogs],
                                  'training':['✍-live-exercises',Training], 'jointops':['✍-joint-ops',JointOps],
                                  'raw':['✍-royal-air-woof', RoyalAirWoof],'ncaf':['✍-ncaf',NCAF],
                                  'cobaltclash':['✍-cobalt-clash',CobaltClash]}

        self.objDict = {}
        self.bot = bot
        self.lock = asyncio.Lock()
        super().__init__()


    @commands.Cog.listener('on_raw_reaction_remove')
    async def react_remove_sign_up_check(self,payload):
        """
        Captures all remove reactions, then filters through to
        use only those that are pertinent to the
        signup functions
        """
        print('remove reaction caught')
        if payload.user_id == 797809584604446740:
            print('Passing bot reacts')
            pass
        if payload.message_id in self.objDict:
            print('Remove react')
            async with self.lock:
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
        if payload.user_id == 797809584604446740:
            print('Passing bot reacts')
            pass
        elif payload.message_id in self.objDict:
            print('Add react')
            async with self.lock:
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
            async with self.lock:
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
        Usage 2: !ps2-signup <squadtype-2> <date> <op-type> <description> <additonal-roles>

        Usage 3: !ps2-signup <limit-type> <message ID> <react-1> <limit-1> ... <react-n> <limit-n>
        squadtype-1: squadleaders, soberdogs, armourdogs, dogfighters
                    bastion, raw
        squadtype-2: training, ncaf, cobaltclash
        limit-type: current-limits, set-limits

        date: Type as a string within quotation marks, e.g "Monday 8:30"

        op-type: A string describing the op type, e.g "Galaxy drop training"

        description: A string describing the op in detail. Can be multiline
                     so long as they remain within quotation marks

        additional-roles: The exact test string for additional roles.
                          e.g "TDKD Captain" will give @TDKD @Captain

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

        async with self.lock:
            if signup in self.signUpChannelName:
                channel = await OpSignUp.locate_sign_up(self,ctx,signup)
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

        if ( str(payload.emoji) in self.reactions.keys()
        and not sum([self.reactions[react].check_member(str(payload.user_id)) for react in self.reactions])
        and not OpSignUp.react_max(self,payload)):



            self.reactions[str(payload.emoji)].add_member(str(payload.user_id),f'{str(payload.member.mention)}\n')

            print(self.reactions[str(payload.emoji)].members.values())

            await OpSignUp.generic_update_embed(self,message,payload)

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
            self.reactions[str(payload.emoji)].remove_member(str(payload.user_id))
            await OpSignUp.generic_update_embed(self,message,payload)


    async def generic_update_embed(self, message,payload):


        embedOrig = message.embeds[0]

        embed_dict = embedOrig.to_dict()
        embed_fields = embed_dict['fields']

        for index,field in enumerate(embed_fields):
            if field['name'] == f'{self.reactions[str(payload.emoji)].symbol} {self.reactions[str(payload.emoji)].name}':
                print(self.reactions[str(payload.emoji)].members.values())

                memberString = ""
                for member in self.reactions[str(payload.emoji)].members.values():
                    memberString = memberString + f"{member}"
                embed_dict['fields'][index].update({'value': str(memberString)})

        embedNew = discord.Embed().from_dict(embed_dict)

        #for field in embed_dict.values():

        #    print(field)
        await message.edit(embed = embedNew)



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

        if self.reactions[str(payload.emoji)].maxReact < 0:
            return False
        elif self.reactions[str(payload.emoji)].currentReact < self.reactions[str(payload.emoji)].maxReact:
            return False
        else:
            return True
