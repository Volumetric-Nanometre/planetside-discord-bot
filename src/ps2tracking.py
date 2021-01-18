import discord
from discord.ext import commands

import asyncio
import auraxium
from auraxium import ps2
from dotenv import load_dotenv
import os

from datetime import datetime

import settings
from tabulate import tabulate

class Ps2PersonalTrack(commands.Cog):
    
    def __init__(self,bot):
        self.membersBeingTracked_id = []
        self.trackingdata = {}
        self.eventTypesToTrack = {auraxium.EventType.filter_experience(1)  :'Kills', auraxium.EventType.VEHICLE_DESTROY :'Lost Vehicles', auraxium.EventType.filter_experience(7)  :'Revives', auraxium.EventType.filter_experience(4)  :'Heals', auraxium.EventType.filter_experience(2)  :'Assists', auraxium.EventType.filter_experience(34)  :'Resupply Player', auraxium.EventType.filter_experience(30)  :'Transport Assist'}
        self.bot = bot
    
    
    
    
    
    async def locate_player(self,ctx,client):
    
        for player in flat_list:
            print(player)
            print("Finding player")
            try:
                char = await client.get_by_name(ps2.Character, player)
            except:
                print("Player not found")
                await ctx.send('Player not found')
                continue
            else:
                print(f"{char.name()} found")

            if int(char.id) in self.membersBeingTracked_id:
                print("Player already tracking")
                await ctx.send("Player already tracking")
            else:
                print("Player tracking started")
                await ctx.send("Player tracking started")
                self.membersBeingTracked_id.append(int(char.id))
                
                
                
    async def start_event_client(self,triggerName):
        """
        Starts event client and sets it to the self.client variable
        """
        client = None
        
        try:
            print(f"{triggerName} client open attempt")
            client = auraxium.EventClient(service_id=settings.PS2_SVS_ID)
        except:
            print(f"{triggerName} client unable to be opened")
            return None
        else:
            print(f"{triggerName} client opened")
            return client
          
        
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
            
    
    @commands.command(name='ps2-channel-track-mk2')
    async def channel_track(self,ctx,category,channel):
        """
        Function to retrive all measured stats for all participents
        """  
        print(category)
        existing_category = discord.utils.get(ctx.guild.categories,
                                                      name=category)
        print(existing_category)
        if existing_category:
            existing_channel=discord.utils.get(existing_category.voice_channels,
                                       name=channel)
            print(existing_channel)
            if existing_channel:
                members = existing_channel.members
                nicknames = [member.nick for member in members]
                
                names = [member.name for member in members]
                for i in range(len(members)):
                    if not nicknames[i]:
                        nicknames[i]=names[i]
                
                await self.player_tracking_start(ctx,nicknames)
                
        print('Channel track complete')
        
    
    @commands.command(name='ps2-tracking-start')
    async def tracking_start(self,ctx):
        """
        Function to track the stats of players
        """       
        
        if not self.trackingdata:
            for event in self.eventTypesToTrack.items():
                
                print(event[0])
                newClient = await self.start_event_client(event[1])
                tracking = TrackingItem(event[0],event[1],newClient)
                self.trackingdata.update({event[1]:tracking})  
                        
        print('Tracking started. Add players to track')
        await ctx.send('Tracking started. Add players to track')
        
    @commands.command(name='ps2-tracking-end')
    async def tracking_end(self,ctx):
        """
        Function to track the stats of players
        """       
        print('Ending tracking')
        for key in self.trackingdata.keys():
            await self.trackingdata[key].eventTypeClient.close()
            print('Client closed')
        self.membersBeingTracked_id.clear() 
        self.trackingdata.clear()
        print('Tracking Finished.')
        await ctx.send('Tracking Finished.')

       
    
    @commands.command(name='ps2-track')
    async def player_tracking_start(self,ctx,*message):
        """
        Function to track the stats of players
        """       
        
        if not self.trackingdata:
            await ctx.send('Tracking not running. Use ps2-tracking-start to initialise tracking')
            return
        
        try:
            client = auraxium.Client(service_id=settings.PS2_SVS_ID)
        except: 
            print('Client not opened')
            return
            
        #
        # Check if player exist.
        # If exists, check if already being tracked
        # If not tracked, add to tracking, else return
        #
        if any(isinstance(x, list) for x in message):

            flat_list = [item for sublist in message for item in sublist]
            print(flat_list)
        else:
            flat_list = message
        for player in flat_list:
            print(f"Finding {player}")
            
            char = await client.get_by_name(ps2.Character, player)
            if char == None:
                print("Player not found")
                await ctx.send('Player not found')
                continue
            else:
                print(f"{char.name()} found")

            if int(char.id) in self.membersBeingTracked_id:
                print("Player already tracking")
                await ctx.send("Player already tracking")
            else:
                print("Player tracking started")
                await ctx.send("Player tracking started")
                self.membersBeingTracked_id.append(int(char.id))

                for trigger, trackingItem in self.trackingdata.items():
                    await trackingItem.add_player(char)
                
        await client.close()
        print('complete')
                   
                    
    @commands.command(name='ps2-untrack')
    async def player_tracking_end(self,ctx,*message):
        """
        Function to track the stats of players
        """       
        
        try:
            client = auraxium.Client(service_id=settings.PS2_SVS_ID)
        except: 
            print('Client not opened')
            return
        #
        # Check if player exist.
        # If exists, check if already being tracked
        # If not tracked, add to tracking, else return
        #
        if any(isinstance(x, list) for x in message):

            flat_list = [item for sublist in message for item in sublist]
            print(flat_list)
        else:
            flat_list = message
        for player in flat_list:
            print(player)
            print("Finding player")
            char = await client.get_by_name(ps2.Character, player)
            if char == None:
                print("Player not found")
                await ctx.send('Player not found')
                break
            else:
                print(f"{char.name()} found")

            if int(char.id) in self.membersBeingTracked_id:
                print("Player found in tracking")
                self.membersBeingTracked_id.remove(int(char.id))
                for trigger, trackingItem in self.trackingdata.items():
                    print('here')
                    await trackingItem.remove_player(char)

            else:
                print("Player not being tracked")
                await ctx.send("Player not being tracked")
        
        if not self.membersBeingTracked_id:
            await self.tracking_end(ctx)
        await client.close()
        print('complete')

    @commands.command(name='ps2-track-stats-mk2')
    async def player_stats(self,ctx):
        """
        Function to retrive all measured stats for all participents
        """
        print("Checking stats")
        aggregateData = {}
        isName = False
        
        for key in self.trackingdata.keys():
            print(key)
            
        for trigger, itemTracked in self.trackingdata.items():
            
            if isName == False:
                aggregateData.update({'Player':list(itemTracked.trackingdata.keys())})
                isName=True
            aggregateData.update({trigger:list(itemTracked.trackingdata.values())})  
        
        fullTable = tabulate(aggregateData,headers="keys",tablefmt="github")
         
        
        await ctx.send(f'Printing Backup to File')
        
        with open("recentOps.txt","w") as f:
            f.write(fullTable)
        
        message = '``` \n'
        tableCount = -1
        for index, row in enumerate(str(fullTable).split('\n')):
            if (index%12)==0 and index !=0:
                message = message + row + '```'
                await ctx.send(f'{message}')
                message = '``` \n'
            else:
                message= message + row +'\n'
        
        if message == '``` \n':
            pass
        else:
            message = message + '```'
            await ctx.send(f'{message}')
        
        
         
        print("Checking stats Complete")
                    
                

    
    
class TrackingItem():

    def __init__(self,auraxiumEventType,triggerName, eventTypeClient):
        self.membersBeingTracked_id = []
        self.trackingdata = {}
        self.eventTypeClient = eventTypeClient
        self.auraxiumEventType = auraxiumEventType
        self.triggerName = triggerName
        print('Initilaised')
    
    async def add_player(self,char):
        """
        Function to set trigger event when a player is added to tracking
        """ 
        
        self.membersBeingTracked_id.append(int(char.id))
        self.trackingdata.update({char.name():int(0)})
        await self.trigger_func()
        
            
    async def remove_player(self,char):
        """
        Function to set trigger event when player is removed from tracking
        """
        
        self.membersBeingTracked_id.remove(int(char.id))
        
        del self.trackingdata[char.name()]
        
        if self.membersBeingTracked_id == []:
            print("final player")
            self.remove_trigger(keep_websocket_alive=False)
            
            print('Trigger to be removed')            
        else:
            await self.trigger_func()
    
    def remove_trigger(self,keep_websocket_alive):
        print('shit')
        try:
            self.eventTypeClient.find_trigger(self.triggerName)
        except:
            print('Trigger not found')
            pass
        else:
            print('Trigger found')
            self.eventTypeClient.remove_trigger(self.triggerName, keep_websocket_alive=keep_websocket_alive)
            print('Trigger removed.')
    
    def stats_dictionary_insert(self,char,newitem):    
        try:
            dictVal = self.trackingdata[char.name()]
        except:
            return newitem
        else:
            dictVal.update(newitem)
            return dictVal
    
    
    async def trigger_func(self):
        self.remove_trigger(keep_websocket_alive=True)
        print(self.membersBeingTracked_id)
        @self.eventTypeClient.trigger(self.auraxiumEventType,characters=self.membersBeingTracked_id,name=self.triggerName)
        async def generic_trigger(event):
            char_id = int(event.payload['character_id'])
            char = await self.eventTypeClient.get_by_id(ps2.Character, char_id)
            
                
            try:
                total = self.trackingdata[char.name()] + 1
                self.trackingdata.update({char.name():total})
            except:
                print('ignored')
                
            else:
                print(f'{char.name()} has done {event}')

        print('Complete trigger')