import discord
from discord.ext import commands

import asyncio
import auraxium
from auraxium import ps2
from dotenv import load_dotenv
import os


from discordbasics import channelManipulation
 
class opschannels(channelManipulation,commands.Cog):
    """
    Class to create an ops channel object. This object in turn contains the
    creation and destructioin routines for voice channels in discord
    """
    def __init__(self,bot):
        self.category_names=['1st Platoon','2nd Platoon']
        self.channel_names=['Alpha','Bravo','Charlie','Delta']
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
                    print(f'Creating a new channel: {channel_name}')
                    await channelManipulation.create_voice_channel(
                        ctx,
                        channel_name,
                        existing_category) 

        print('Platoon creation complete')
        
    #@commands.command(name='start-ops')
    #async def create_plt(self,ctx):
    #    """
    #    Check if category exists. If it doesn't, create and fill with
    #    channels. 
    #    """
    #    guild = ctx.guild
    #    #
    #    # Create platoon categories
    #    #
    #    for category_name in self.category_names:
    #        existing_category = discord.utils.get(guild.categories, name=category_name)
    #        if not existing_category:
    #            print(f'Creating a new category: {category_name}')
    #            category = await guild.create_category(name=category_name)
    #            #
    #            # Fill categories with voice channels
    #            #
    #            for channel_name in self.channel_names:
    #                print(f'Creating a new channel: {channel_name}')
    #                await category.create_voice_channel(channel_name) 
    #
    #    print('Platoon creation complete')
        
        
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
                        tx,channels,
                        category=cat)
            await channelManipulation.delete_category(ctx,cat)
        print('Delete complete')
        
         # @commands.command(name='end-ops')
   # async def destroy_plt(self,ctx):
   #     """
   #     Check if category exists. If is does, delete all channels
   #     followed by the category
   #     """
   #     
   #     print('start')
   #     existing_categories = ctx.guild.categories
   #     print(existing_categories)
   #     for cat in existing_categories:
   #         print(cat.name)
   #         if cat.name in self.category_names :
   #             channels = cat.voice_channels
   #             print(channels)
   #             for channel in channels:
   #                 print(f'Deleting {channel}')
   #                 await channel.delete()
    #
    #            await cat.delete()
     #   print('Delete complete')


        
        
        
