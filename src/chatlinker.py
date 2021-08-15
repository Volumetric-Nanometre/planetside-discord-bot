import discord
from discord.ext import commands
import settings
import asyncio

class ChatLinker(commands.Cog):
    """
    Creates chat channels for each channel when occupied. 
    Deletes the channels when unoccupied
    """
    
    def __init__(self,bot):
        self.bot = bot
        
        self.lock = asyncio.Lock()
        
        self.charDict = {} # {channel_id : chat_channel_id }
        super().__init__()
        
    
    
    @commands.Cog.listener('on_voice_state_update')
    async def voice_status(self,member,previousState,newState):
        """
        Captures all voice channel leave/join/state-changes
        """
        async with self.lock:
            print('State Change caught')



            print(previousState)        
            print(newState)

            # Check if leaving all VC
            if newState.channel == None:

                print('Left all VC')
                await self.remove_member_from_chat(member,previousState)
                await self.destroy_old_chat(member,previousState,newState)
                print("Completed")
                return 


            # Check if first VC join

            if previousState.channel == None:

                print('First VC join')
                await self.create_new_chat(member,previousState,newState)
                await self.add_member_to_chat(member,newState)
                print("Completed")
                return

            if previousState.channel != newState.channel:

                await self.create_new_chat(member,previousState,newState)
                await self.add_member_to_chat(member,newState)
                await self.remove_member_from_chat(member,previousState)
                await self.destroy_old_chat(member,previousState,newState)
                print("Completed")
                return
            
        
        
        
    async def destroy_old_chat(self,member,previousState,newState):
        """
        Checks if we need to destroy the old chat. This only occurs
        when the old VC is empty.
        """
        print("Destroy?")
        
        try:
            if previousState.channel.id in self.charDict:


                print( previousState.channel.members)
                if not previousState.channel.members:


                    chatChannel = self.charDict.get(previousState.channel.id)

                    await chatChannel.delete()

                    del self.charDict[previousState.channel.id]
                    print("Chat channel deleted.")

                else:
                    print("Channel still occupied")

            else:
                print("Chat channel does not exist.")
        except discord.errors.NotFound:
            print("Channel entry exists, but not found. Removing entry")
            del self.charDict[previousState.channel.id]

        
        
        
        
    async def create_new_chat(self,member,previousState,newState):
        
        """
        Checks if we need to create a new chat. This only occurs
        if the new VC didn't have one.
        """
        print("Create?")
        
        try:
            if newState.channel.id in self.charDict:

                print("Chat channel already exists.")

            else:

                chatName = f'{newState.channel.name} chat'

                overwrites = {
                                newState.channel.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                                newState.channel.guild.me: discord.PermissionOverwrite(read_messages=True)
                             }
                chatChannel = await newState.channel.guild.create_text_channel(chatName,category=newState.channel.category, overwrites=overwrites)

                print(chatChannel.id)

                self.charDict.update({newState.channel.id : chatChannel})

                print("Chat channel does not exist.")
        except discord.errors.NotFound:
            print("Channel entry exists, but not found. Removing entry")
            del self.charDict[previousState.channel.id]   
            
            
            
            
            
            
    async def add_member_to_chat(self,member,newState):
        """
        Adds member to the chat channel
        """
        
        try:
            if newState.channel.id in self.charDict:

                chatChannel = self.charDict.get(newState.channel.id)

                await chatChannel.set_permissions(member,read_messages=True)

        except discord.errors.Forbidden:
            print("Changing this permission is forbiden")
        except discord.errors.NotFound:
            print("Channel entry exists, but not found. Removing entry")
            del self.charDict[newState.channel.id] 
            
            
    async def remove_member_from_chat(self,member,previousState):
        """
        Removes member from the chat channel
        """
        
        try:
            if previousState.channel.id in self.charDict:

                chatChannel = self.charDict.get(previousState.channel.id)

                await chatChannel.set_permissions(member,overwrite=None)
        except discord.errors.Forbidden:
            print("Changing this permission is forbiden")
        except discord.errors.NotFound:
            print("Channel entry exists, but not found. Removing entry")
            del self.charDict[previousState.channel.id] 
            