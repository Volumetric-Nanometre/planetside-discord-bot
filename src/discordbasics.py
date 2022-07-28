import discord
import settings
import traceback

class channelManipulation():
    
    def __init__(self):
        self.bot=None
    
    async def create_category(ctx,category_name,overwrites):
        """
        Check if category exists, then create
        """
        existing_category = discord.utils.get(ctx.guild.categories,
                                              name=category_name)
        
        if not existing_category:
            print(f'Creating a new category: {category_name}')
            try:
                await ctx.guild.create_category(name=category_name,overwrites=overwrites)
            except:
                traceback.print_exc()
                print(f'Creating {category_name} failed')
        else:
            print(f'{category_name} already exists')
    
    async def delete_category(ctx,category_name):
        """
        Check if category exists, then delete
        """
        #existing_category = discord.utils.get(ctx.guild.categories,
        #                                      name=category_name)
        #print(existing_category)
        #if not existing_category:
        #    print(f'{category_name} does not exist')
       # else:
        print(f'Deleting: {category_name}')
        try:
            await category_name.delete()
        except:
            print(f'Deleting {category_name} failed')

    async def create_voice_channel(ctx,channel_name, category=None):
        """
        Assume if called the category exists. 
        Check if chennel exists in the intended category, then create
        """
        existing_channel=discord.utils.get(category.voice_channels,
                                           name=channel_name)
        if not existing_channel:   
            try:
                print(f'Creating a new channel: {channel_name}')
                await ctx.guild.create_voice_channel(channel_name,
                                                     category=category)
            except:
                print(f'Creating {channel_name} failed')
            
    async def delete_voice_channel(ctx,channel_name, category=None):
        """
        Assume if called the category exists. 
        Check if chennel exists in the intended category, then create
        """
        print(f'Deleting: {channel_name}')
        try:
            await channel_name.delete()
        except:
            print(f'Deleting {category_name} failed')

            
        