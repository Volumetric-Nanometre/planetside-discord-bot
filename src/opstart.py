import discord
from discord.ext import commands

import asyncio
#import auraxium
#from auraxium import ps2
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
        self.platoon_setup ={'Headquarters':['Command'],'Standard':['Alpha','Bravo','Charlie','Delta'],'Specialist':['SoberDogs A','SoberDogs B','ArmourDogs','Royal Air Woof','DogFighters','LogiDogs']}    
        self.school={'School':['Headteachers Office']}
        self.members = []
        self.isRecording = False
        self.starttime = None
        self.bot = bot
        self.lock = asyncio.Lock()
        super().__init__()
        
        
    @commands.command(name='ps2-start-ops')
    async def create_plt(self,ctx,*args):
        """
        Create ops channels 
        """
        async with self.lock:
            for category_name in self.platoon_setup.keys():
                await channelManipulation.create_category(ctx,category_name)
                existing_category = discord.utils.get(ctx.guild.categories,
                                                      name=category_name)

                if existing_category:
                    #
                    # Fill categories with voice channels
                    #
                    for channel_name in self.platoon_setup[category_name]:
                        await channelManipulation.create_voice_channel(
                            ctx,
                            channel_name,
                            existing_category) 

        print('Platoon creation complete')
        
    @commands.command(name='ps2-end-ops')
    async def destroy_plt(self,ctx):
        """
        Destroy ops channels 
        """
        
        print('start')
        existing_categories = ctx.guild.categories
        for cat in existing_categories:
            if cat.name in self.platoon_setup.keys():
                channels = cat.voice_channels
                for channel in channels:
                    await channelManipulation.delete_voice_channel(
                        ctx,channel,
                        category=cat)
                await channelManipulation.delete_category(ctx,cat)
        print('Delete complete')
        
        
    @commands.command(name='ps2-start-school')
    async def start_school(self,ctx,arg):        
        """
        Usage: !ps2-start-school <numberOfClassrooms>
        Creates <numberOfClassrooms> channels, and one "headteacher" channel
        """
        async with self.lock:
            print('School Opening')
            self.schoolrooms = ['Headteachers Office']
            for classroom in range(int(arg)):
                self.schoolrooms.append(f'Classroom {classroom+1}')

            self.school = {'School':self.schoolrooms}

            for category_name in self.school.keys():
                await channelManipulation.create_category(ctx,category_name)
                existing_category = discord.utils.get(ctx.guild.categories,
                                                      name=category_name)

                if existing_category:
                    #
                    # Fill categories with voice channels
                    #
                    for channel_name in self.school[category_name]:
                        await channelManipulation.create_voice_channel(
                            ctx,
                            channel_name,
                            existing_category) 

        print('School Open')
    
    @commands.command(name='ps2-end-school')
    async def end_school(self,ctx):
        """
        Usage: !ps2-end-school
        Destroys all school channels
        """
        
        print('School Closing')
        existing_categories = ctx.guild.categories
        for cat in existing_categories:
            if cat.name in self.school.keys():
                channels = cat.voice_channels
                for channel in channels:
                    await channelManipulation.delete_voice_channel(
                        ctx,channel,
                        category=cat)
                await channelManipulation.delete_category(ctx,cat)
        print('School Closed')
        
        
    """
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
    """

        

        

