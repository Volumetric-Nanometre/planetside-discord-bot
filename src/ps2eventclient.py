import discord
from discord.ext import commands

import asyncio
import auraxium
from auraxium import ps2
from dotenv import load_dotenv
import os

from datetime import datetime

from discordbasics import channelManipulation

import settings

class Ps2EventClient(commands.Cog):
    """
    Class to create the planetside 2 EventClient and set up a trigger
    environment
    """
    client = {}
    def __init__(self,bot):
        self.bot = bot
        
    async def start_event_client(triggerName):
        """
        Starts event client and sets it to the self.client variable
        """
        if triggerName not in Ps2EventClient.client:
            print(f'Starting event client for {triggerName}')
            if triggerName not in Ps2EventClient.client:
                try:
                    print(f"{triggerName} client open attempt")
                    Ps2EventClient.client.update({triggerName :auraxium.EventClient(service_id=settings.PS2_SVS_ID)})
                except:
                    print(f"{triggerName} client unable to be opened")
                    return None
                else:
                    print(f"{triggerName} client opened")
            else:
                print(f"{triggerName} client already open")
                
        return Ps2EventClient.client[triggerName]
        
    def remove_trigger(self,client,trigger):
        try:
            client.find_trigger(trigger)
        except:
            print('Trigger not found')
            pass
        else:
            print('Trigger found')
            client.remove_trigger(trigger,keep_websocket_alive=True)
            print('Trigger removed. Socket alive.')
            
"""        
class Ps2OpsEvents(Ps2EventClient,commands.Cog):
   
    def __init__(self):
        self.membersInOp = []
        super().__init__(self,bot)
        
    async def player_death(self,ctx):
        # NOTE: Depending on player activity, this script will likely exceed the
        # ~6 requests per minute and IP address limit for the default service ID.
        self.client.update({'ops-death':auraxium.EventClient(service_id='settings.PS2_SVS_ID')})

        start_event_client()
        client = auraxium.EventClient(service_id='settings.PS2_SVS_ID')
        @client.trigger(auraxium.EventType.DEATH,characters=self.members_id)
        async def print_levelup(event):
            char_id = int(event.payload['character_id'])
            char = await client.get_by_id(ps2.Character, char_id)

            # NOTE: This value is likely different from char.data.battle_rank as
            # the REST API tends to lag by a few minutes.

            print(f'{await char.name_long()} has died')
    """

    
class Ps2PersonalEvents(Ps2EventClient,commands.Cog):
    """
    Class to track personal events
    """
    def __init__(self,bot):
        self.membersBeingTracked_id = []
        self.trackingdata = {}
        self.bot = bot
        super().__init__(self)
        
    def stats_dictionary_insert(self,char,newitem):    
        try:
            dictVal = self.trackingdata[char.name()]
        except:
            return newitem
        else:
            dictVal.update(newitem)
            return dictVal
        
    @commands.command(name='ps2-personal-stats')
    async def player_stats(self,ctx):
        """
        Function to retrive all measured stats for all participents
        """
        print("Checking stats")
        TextOuput ='```'+'\n'
        for player in self.trackingdata.items():
            for stat in player:
                print(stat)
                TextOuput= TextOuput + str(stat) + '\n'
                await ctx.send(f'{stat}')
                
        TextOuput =TextOuput + '```'
        
        await ctx.send(f'{TextOuput}')
        print("Complete")
        
        
    
    @commands.command(name='ps2-track-start')
    async def player_tracking_start(self,ctx,message):
        """
        Function to track the stats of players
        """
        
        async with auraxium.Client(service_id=settings.PS2_SVS_ID) as client:
            
            #
            # Check if player exist.
            # If exists, check if already being tracked
            # If not tracked, add to tracking, else return
            #
            print("Finding player")
            try:
                char = await client.get_by_name(ps2.Character, message)
            except:
                print("Player not found")
                await ctx.send('Player not found')
                return
            else:
                print(f"{char.name()} found")

            if int(char.id) in self.membersBeingTracked_id:
                print("Player already tracking")
                await ctx.send("Player already tracking")
            else:
                print("Player tracking started")
                await ctx.send("Player tracking started")
                self.membersBeingTracked_id.append(int(char.id))
                
                #
                # add death tracking
                # add kill tracking
                # add res tracking
                # add facdef tracking
                # add faccap tracking
                #
                                #self.trackingdata.update({char.name(): {}})
                print("Loading stats")
                await Ps2PersonalEvents.player_death(self,ctx,char)
                print('Death loaded')
                await Ps2PersonalEvents.player_basecap(self,ctx,char)
                print('Basecap loaded')
                await Ps2PersonalEvents.player_basedef(self,ctx,char)
                print('Basedef loaded')
                
                print("Loading complete")
                #
                # Set up logoff trigger to remove stats if char logs off
                #
                
                
                
    async def player_death(self,ctx,char):
        """
        Function to set trigger event for when player dies
        """            
        client = await Ps2EventClient.start_event_client('personal-death')
        
        dictVal = Ps2PersonalEvents.stats_dictionary_insert(self,char,{'deaths':int(0)})
        self.trackingdata.update({char.name():dictVal})
        
        Ps2EventClient.remove_trigger(self,client,'personal-death')

        @client.trigger(auraxium.EventType.DEATH,characters=self.membersBeingTracked_id,name='personal-death')
        async def player_death_generic(event):
            char_id = int(event.payload['character_id'])
            char = await client.get_by_id(ps2.Character, char_id)
            attacker_id = int(event.payload['attacker_character_id'])
            attack_char = await client.get_by_id(ps2.Character, attacker_id)
            
            total = self.trackingdata[char.name()]['deaths'] + 1

            self.trackingdata.update({char.name(): Ps2PersonalEvents.stats_dictionary_insert(self,char,{'deaths':total})})

            print(f'{char.name()} has died to {attack_char.name()}')


    async def player_logoff(self,ctx,char):
        """
        Function to set trigger event for if a player logs off. this will then
        close out all data for the player
        """
            
        client = await Ps2EventClient.start_event_client('personal-logoff')

        try:
            client.find_trigger('personal-logoff')
        except:
            pass
        else:
            print(f'new trigger{self.membersBeingTracked_id}')
            client.remove_trigger('personal-logoff',keep_websocket_alive=True)

        @client.trigger(auraxium.EventType.PLAYER_LOGOUT ,characters=self.membersBeingTracked_id,name='personal-logoff')
        async def player_logoff_triggered(event):
            char_id = int(event.payload['character_id'])
            char = await client.get_by_id(ps2.Character, char_id)
            print(f'{char.name()} has logged off')
        
        
        
    async def player_kill(self,ctx,char):
        """
        Function to set trigger event for player kills
        """
        if 'kills' not in Ps2EventClient.client:
            print("Creating client")
            await Ps2EventClient.start_event_client('kills')
            
        client = Ps2EventClient.client['kills']
        
        
        
        
    
    async def player_basecap(self,ctx,char):
        """
        Function to set trigger event for if a player facility captures
        """            
        client = await Ps2EventClient.start_event_client('personal-basecap')
                
        dictVal = Ps2PersonalEvents.stats_dictionary_insert(self,char,{'basecap':int(0)})
        self.trackingdata.update({char.name():dictVal})
        
        Ps2EventClient.remove_trigger(self,client,'personal-basecap')
            
        @client.trigger(auraxium.EventType.PLAYER_FACILITY_CAPTURE ,characters=self.membersBeingTracked_id,name='personal-basecap')
        async def player_death_generic(event):
            char_id = int(event.payload['character_id'])
            char = await client.get_by_id(ps2.Character, char_id)

            total = self.trackingdata[char.name()]['basecap'] + 1

            self.trackingdata.update({char.name(): Ps2PersonalEvents.stats_dictionary_insert(self,char,{'basecap':total})})

            print(f'{char.name()} has captured a facility')
            
            
            
    
    async def player_basedef(self,ctx,char):
        """
        Function to set trigger event for if a player facility defends
        """
            
        client = await Ps2EventClient.start_event_client('personal-basedef')
        
        dictVal = Ps2PersonalEvents.stats_dictionary_insert(self,char,{'basedef':int(0)})
         
        self.trackingdata.update({char.name(): dictVal})
        
        Ps2EventClient.remove_trigger(self,client,'personal-basedef')
        
        @client.trigger(auraxium.EventType.PLAYER_FACILITY_DEFEND  ,characters=self.membersBeingTracked_id,name='personal-basedef')
        async def player_death_generic(event):
            char_id = int(event.payload['character_id'])
            char = await client.get_by_id(ps2.Character, char_id)

            total = self.trackingdata[char.name()]['basedef'] + 1

            self.trackingdata.update({char.name(): Ps2PersonalEvents.stats_dictionary_insert(self,char,{'basedef':total})})

            print(f'{char.name()} has defended a facility')
        
        
 
    
    
                    
            
