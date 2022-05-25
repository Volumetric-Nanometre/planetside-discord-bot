import os
import asyncio
import discord
import random

import settings

import traceback
from discord.ext import commands
from dotenv import load_dotenv

from opsignupclasses import *


getFuckedGifRotation = ["https://tenor.com/view/sosiska-gif-23857394",
                        "https://tenor.com/view/twerk-chicken-gif-13392129",
                        "https://tenor.com/view/spinning-squirrel-silly-spin-gif-16499914",
                        "https://tenor.com/view/hilarious-fun-pet-pet-fun-fun-dog-dog-gif-23378410",
                        "https://tenor.com/view/vines-vine-hot-dog-vine-im-just-saying-im-just-sayin-gif-15617403",
                        "https://tenor.com/view/penguins-penguins-of-madagascar-madagascar-skipper-private-gif-22554041",
                        "https://tenor.com/view/most-certainly-i-deny-it-jean-luc-picard-patrick-stewart-star-trek-the-next-generation-gif-23358017",
                        "https://tenor.com/view/shrek-lord-farquaad-smug-walk-gif-4571303",
                        "https://tenor.com/view/simpsons-nelson-haha-gif-8845145"
                        ]

getFuckedTextRotation = ["you little shit",
                        "you require additional pylons",
                        "you have no power here",
                        "you ain't got rights to this shit",
                        "take a run and jump",
                        "how is there so much garbage in this village",
                        "you didn't say the magic word!",
                        "this has been reported to your local authorities. Please remain where you are.",
                        "you make me sick",
                        "I'm too old for this shit",
                        "you lack diplomatic immunity",
                        "the princess is in another castle",
                        "begone thot!",
                        "you are a sacrifice I am willing to make",
                        "you don't know the muffin man",
                        "our patience is wearing thin",
                        "do you understand how long this took to make?",
                        "I have the high ground!",
                        "418 - I'm a teapot"]





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
        elif payload.message_id in self.objDict:
            print('Remove react')
            async with self.lock:
                obj = self.objDict[payload.message_id]
                await OpSignUp.generic_react_remove(self,obj,payload)
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
                await OpSignUp.generic_react_add(self,obj,payload)
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


    async def generic_react_add(self,obj,payload):

        messageText  = obj.messageText

        message = await self.bot.get_channel(payload.channel_id).fetch_message(obj.messageHandlerID)
        #message = await self.signUpChannel.fetch_message(self.messageHandlerID)

        if  str(payload.emoji) == "💥":
            """
            Ping all names in list
            """

            if ('CO' in list([i.name for i in payload.member.roles])
                or  'Captain' in list([i.name for i in payload.member.roles])
                or 'Lieutenant'  in list([i.name for i in payload.member.roles])):
                try:
                    pingMessage=str()
                    for react in obj.reactions:
                        pingMessage+= ' '.join(list(obj.reactions[react].members.values()))

                        #pingMessage=pingMessage.replace('','')
                    pingMessage = f"Pinged by {payload.member.mention} for tonights Ops\n\n" + pingMessage

                    await self.bot.get_channel(payload.channel_id).send(pingMessage)

                except:
                    traceback.print_exc()
            else:

                nanites = [i for i in message.guild.channels if i.name == '💩-nanites-posting']

                randText =random.choice(getFuckedTextRotation)
                randGif = random.choice(getFuckedGifRotation)


                if randText == "you didn't say the magic word!":
                    randGif = "https://tenor.com/view/you-didnt-say-the-magic-word-ah-ah-nope-wagging-finger-gif-17646607"

                await self.bot.get_channel(nanites[0].id).send(f"Get fucked {payload.member.mention}, {randText}\n{randGif}")

            await message.remove_reaction(payload.emoji,payload.member)


        elif ( str(payload.emoji) in obj.reactions.keys()
        and not sum([obj.reactions[react].check_member(str(payload.user_id)) for react in obj.reactions])
        and not OpSignUp.react_max(obj,payload)):



            obj.reactions[str(payload.emoji)].add_member(str(payload.user_id),f'{str(payload.member.mention)}\n')

            print(obj.reactions[str(payload.emoji)].members.values())

            await OpSignUp.generic_update_embed(self,obj,message,payload)

            OpSignUp.update_data_entry(self,obj,obj.messageHandlerID)

        else:
            obj.ignoreRemove = True
            await message.remove_reaction(payload.emoji,payload.member)
            print('Reaction removed')


    async def generic_react_remove(self,obj,payload):

        if obj.ignoreRemove:
            obj.ignoreRemove = False
            return

        if str(payload.emoji) in obj.reactions.keys():
            message = await self.bot.get_channel(payload.channel_id).fetch_message(obj.messageHandlerID)

            #message = await obj.signUpChannel.fetch_message(obj.messageHandlerID)
            obj.reactions[str(payload.emoji)].remove_member(str(payload.user_id))
            await OpSignUp.generic_update_embed(self,obj,message,payload)


    async def generic_update_embed(self,obj, message,payload):


        embedOrig = message.embeds[0]

        embed_dict = embedOrig.to_dict()
        embed_fields = embed_dict['fields']

        for index,field in enumerate(embed_fields):
            if field['name'] == f'{obj.reactions[str(payload.emoji)].symbol} {obj.reactions[str(payload.emoji)].name}':
                print(obj.reactions[str(payload.emoji)].members.values())

                memberString = ""
                for member in obj.reactions[str(payload.emoji)].members.values():
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


    def update_data_entry(self,obj,messageID):

        # Attempt to write a data entry.
        #pickle.dump( self, open( "save.p", "wb" ) )

        #loaded_objects = pickle.load( open( "save.p", "rb" )

        print(obj.__dict__)
        #print(self.signUpChannel.__dict__)
        #def obj_dict(obj):
    #        return obj.__dict__

        #with open(f"{messageID}.pickle","w") as database:

        #    pickle.dump(obj,database, protocol=pickle.HIGHEST_PROTOCOL)

        #    testObj = pickle.load(database)
        #    print(testObj)
#
