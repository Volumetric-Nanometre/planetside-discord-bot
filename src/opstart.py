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
 
class opschannels(channelManipulation,commands.Cog):
    """
    Class to create an ops channel object. This object in turn contains the
    creation and destructioin routines for voice channels in discord
    """
    def __init__(self,bot):
        self.category_names=['1st Platoon','2nd Platoon']
        self.channel_names=['Alpha','Bravo','Charlie','Delta']
        self.members = []
        self.isRecording = False
        self.starttime = None
        self.bot = bot
        super().__init__()
        
        
    @commands.command(name='start-ops')
    async def create_plt(self,ctx):
        """
        Check if category exists. If it doesn't, create and fill with
        channels. 
        """
        for category_name in self.category_names:
            await channelManipulation.create_category(ctx,category_name)
            existing_category = discord.utils.get(ctx.guild.categories,
                                                  name=category_name)
            
            if existing_category:
                #
                # Fill categories with voice channels
                #
                for channel_name in self.channel_names:
                    await channelManipulation.create_voice_channel(
                        ctx,
                        channel_name,
                        existing_category) 

        print('Platoon creation complete')
        
    @commands.command(name='end-ops')
    async def destroy_plt(self,ctx):
        """
        Check if category exists. If is does, delete all channels
        followed by the category
        """
        
        print('start')
        existing_categories = ctx.guild.categories
        for cat in existing_categories:
            if cat.name in self.category_names:
                channels = cat.voice_channels
                for channel in channels:
                    await channelManipulation.delete_voice_channel(
                        ctx,channel,
                        category=cat)
                await channelManipulation.delete_category(ctx,cat)
        print('Delete complete')

    
    @commands.command(name='start-rec')
    async def ops_data_record(self,ctx):
        
        if(not self.isRecording):
            print('Start Recording')
            for category_name in self.category_names:
                existing_category = discord.utils.get(ctx.guild.categories,
                                                      name=category_name)
                if existing_category:
                    print(category_name)
                    for channel_name in self.channel_names:
                        existing_channel=discord.utils.get(existing_category.voice_channels,
                                               name=channel_name)
                        if existing_channel:
                            print(existing_channel)
                            self.members.append(existing_channel.members)
                            print(existing_channel.members)
                            
            self.starttime = datetime.now()
            self.isRecording = True
            print(self.members)
            print('Recording started')
        else:
            print('Already Recording')
            print(f'Start time: {self.starttime}')


        

        
class opstracking(commands.Cog):
    
    def __init__(self,bot):
        self.members = []
        self.members_id = [5428010917252961457,5428117870052769409,5429015528381958929]
        self.isRecording = False
        self.starttime = None
        self.bot = bot
        self.client = {}
        
    
        
    #@commands.command(name='start-rec')
    async def tracking_start(self,ctx):
        
        if(not self.isRecording):
            print('Start Recording')
            for category_name in self.category_names:
                existing_category = discord.utils.get(ctx.guild.categories,
                                                      name=category_name)
                if existing_category:
                    print(category_name)
                    for channel_name in self.channel_names:
                        existing_channel=discord.utils.get(existing_category.voice_channels,
                                               name=channel_name)
                        if existing_channel:
                            print(existing_channel)
                            self.members.append(existing_channel.members)
                            print(existing_channel.members)
                            
            self.starttime = datetime.now()
            self.isRecording = True
            print(self.members)
            print('Recording started')
        else:
            print('Already Recording')
            print(f'Start time: {self.starttime}')
            
    @commands.command(name='ps2-add-death')                        
    async def player_death(self,ctx):
        # NOTE: Depending on player activity, this script will likely exceed the
        # ~6 requests per minute and IP address limit for the default service ID.
        if('death' not in self.client):
            self.client.update({'death':auraxium.EventClient(service_id=settings.PS2_SVS_ID)})

            client = self.client['death']
            @client.trigger(auraxium.EventType.DEATH,characters=self.members_id)
            async def print_levelup(event):
                char_id = int(event.payload['character_id'])
                char = await client.get_by_id(ps2.Character, char_id)

                # NOTE: This value is likely different from char.data.battle_rank as
                # the REST API tends to lag by a few minutes.

                print(f'{await char.name_long()} has died')
                await ctx.send(f'{await char.name_long()} has died.')
                
            await ctx.send(f'Death tracking started')
    
    @commands.command(name='ps2-add-kill')                        
    async def player_kill(self,ctx):
        # NOTE: Depending on player activity, this script will likely exceed the
        # ~6 requests per minute and IP address limit for the default service ID.
        if('kill' not in self.client):
            self.client.update({'kill':auraxium.EventClient(service_id=settings.PS2_SVS_ID)})
            client = self.client['kill']

            @client.trigger(auraxium.EventType.KILL,characters=self.members_id)
            async def print_levelup(event):
                char_id = int(event.payload['character_id'])
                char = await client.get_by_id(ps2.Character, char_id)

                # NOTE: This value is likely different from char.data.battle_rank as
                # the REST API tends to lag by a few minutes.

                print(f'{await char.name_long()} has killed')
                
                
    @commands.command(name='ps2-add-faccap')                        
    async def player_faccap(self,ctx):
        # NOTE: Depending on player activity, this script will likely exceed the
        # ~6 requests per minute and IP address limit for the default service ID.
        if('faccap' not in self.client):
            self.client.update({'faccap':auraxium.EventClient(service_id=settings.PS2_SVS_ID)})
            client = self.client['faccap']

            @client.trigger(auraxium.EventType.PLAYER_FACILITY_CAPTURE ,characters=self.members_id)
            async def print_levelup(event):
                char_id = int(event.payload['character_id'])
                char = await client.get_by_id(ps2.Character, char_id)
                facility_id = int(event.payload['facility_id'])
                facility = await client.get_by_id(ps2.map_region, facility_id)

                # NOTE: This value is likely different from char.data.battle_rank as
                # the REST API tends to lag by a few minutes.

                print(f'{await char.name_long()} has captured facility {await facility.resolve()}')
                print(event.payload)

        
    @commands.command(name='ps2-add-facdef')                        
    async def player_facdef(self,ctx):
        # NOTE: Depending on player activity, this script will likely exceed the
        # ~6 requests per minute and IP address limit for the default service ID.
        if('facdef' not in self.client):
            self.client.update({'facdef':auraxium.EventClient(service_id=settings.PS2_SVS_ID)})
            client = self.client['facdef']

            @client.trigger(auraxium.EventType.PLAYER_FACILITY_DEFEND ,characters=self.members_id)
            async def print_levelup(event):
                char_id = int(event.payload['character_id'])
                char = await client.get_by_id(ps2.Character, char_id)
                facility_id = int(event.payload['facility_id'])
                facility = await client.get_by_id(ps2.map_region, facility_id)

                # NOTE: This value is likely different from char.data.battle_rank as
                # the REST API tends to lag by a few minutes.

                print(f'{await char.name_long()} has defended facility {await facility.resolve()}')
                print(event.payload)

            
    @commands.command(name='ps2-show-triggers') 
    async def show_trigger(self,ctx):
        print(self.client.keys())
        
class personaltracking(commands.Cog):
    
    def __init__(self,bot):
        self.members = []
        self.tracking_id = [5428010917252961457,5428117870052769409,5429015528381958929]
        self.isRecording = False
        self.starttime = None
        self.bot = bot
        self.client = {}
        
    
        
    @commands.command(name='start-selftrack', )
    async def self_tracking_start(self,ctx,message):
        
        try:
            char = await client.get_by_name(message, player)
        except:
            print('Character not found')
            return
        
        if(char in self.members):
            print('Character already tracking')
            return
        else:
            self.members.append(char)
            
        
        
        
            
        if(not self.isRecording):
            print('Start Recording')
            for category_name in self.category_names:
                existing_category = discord.utils.get(ctx.guild.categories,
                                                      name=category_name)
                if existing_category:
                    print(category_name)
                    for channel_name in self.channel_names:
                        existing_channel=discord.utils.get(existing_category.voice_channels,
                                               name=channel_name)
                        if existing_channel:
                            print(existing_channel)
                            self.members.append(existing_channel.members)
                            print(existing_channel.members)
                            
            self.starttime = datetime.now()
            self.isRecording = True
            print(self.members)
            print('Recording started')
        else:
            print('Already Recording')
            print(f'Start time: {self.starttime}')
            
    @commands.command(name='add-death')                        
    async def player_death(self,ctx):
        # NOTE: Depending on player activity, this script will likely exceed the
        # ~6 requests per minute and IP address limit for the default service ID.
        self.client.update({'death':auraxium.EventClient(service_id=settings.PS2_SVS_ID)})

        client = auraxium.EventClient(service_id=settings.PS2_SVS_ID)
        @client.trigger(auraxium.EventType.DEATH,characters=self.members_id)
        async def print_levelup(event):
            char_id = int(event.payload['character_id'])
            char = await client.get_by_id(ps2.Character, char_id)

            # NOTE: This value is likely different from char.data.battle_rank as
            # the REST API tends to lag by a few minutes.

            print(f'{await char.name_long()} has died')
    
    @commands.command(name='add-kill')                        
    async def player_kill(self,ctx):
        # NOTE: Depending on player activity, this script will likely exceed the
        # ~6 requests per minute and IP address limit for the default service ID.
        if('kill' not in self.client):
            self.client.update({'kill':auraxium.EventClient(service_id=settings.PS2_SVS_ID)})
            client = self.client['kill']

            @client.trigger(auraxium.EventType.KILL,characters=self.members_id)
            async def print_levelup(event):
                char_id = int(event.payload['character_id'])
                char = await client.get_by_id(ps2.Character, char_id)

                # NOTE: This value is likely different from char.data.battle_rank as
                # the REST API tends to lag by a few minutes.

                print(f'{await char.name_long()} has killed')
                
                
    @commands.command(name='add-faccap')                        
    async def player_faccap(self,ctx):
        # NOTE: Depending on player activity, this script will likely exceed the
        # ~6 requests per minute and IP address limit for the default service ID.
        if('faccap' not in self.client):
            self.client.update({'faccap':auraxium.EventClient(service_id=settings.PS2_SVS_ID)})
            client = self.client['faccap']

            @client.trigger(auraxium.EventType.PLAYER_FACILITY_CAPTURE ,characters=self.members_id)
            async def print_levelup(event):
                char_id = int(event.payload['character_id'])
                char = await client.get_by_id(ps2.Character, char_id)
                facility_id = int(event.payload['facility_id'])
                facility = await client.get_by_id(ps2.map_region, facility_id)

                # NOTE: This value is likely different from char.data.battle_rank as
                # the REST API tends to lag by a few minutes.

                print(f'{await char.name_long()} has captured facility {await facility.resolve()}')
                print(event.payload)

        
    @commands.command(name='add-facdef')                        
    async def player_facdef(self,ctx):
        # NOTE: Depending on player activity, this script will likely exceed the
        # ~6 requests per minute and IP address limit for the default service ID.
        if('facdef' not in self.client):
            self.client.update({'facdef':auraxium.EventClient(service_id=settings.PS2_SVS_ID)})
            client = self.client['facdef']

            @client.trigger(auraxium.EventType.PLAYER_FACILITY_DEFEND ,characters=self.members_id)
            async def print_levelup(event):
                char_id = int(event.payload['character_id'])
                char = await client.get_by_id(ps2.Character, char_id)
                facility_id = int(event.payload['facility_id'])
                facility = await client.get_by_id(ps2.map_region, facility_id)

                # NOTE: This value is likely different from char.data.battle_rank as
                # the REST API tends to lag by a few minutes.

                print(f'{await char.name_long()} has defended facility {await facility.resolve()}')
                print(event.payload)

            
    @commands.command(name='show-triggers') 
    async def show_trigger(self,ctx):
        print(self.client.keys())