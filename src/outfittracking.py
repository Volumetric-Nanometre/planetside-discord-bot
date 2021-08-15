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

import traceback

import logging
logger = logging.getLogger(__name__)
logging.basicConfig(handlers=[logging.FileHandler(filename="log_records.log", 
                                                 encoding='utf-8', mode='a+')],
                    format="%(asctime)s %(name)s:%(levelname)s:%(message)s", 
                    datefmt="%F %A %T", 
                    level=logging.INFO)


class PS2OutfitTracker(commands.Cog):
    """
    Class that contains the information needed to initilase and run
    outfit tracking for multiple outfits
    """
    def __init__(self,bot):
        self.outfitObj = []
        self.bot=bot

    
    def start_event_client(self,outfitTag):
        """
        Creates an event client and returns it
        """
        
        client = None

        try:
            logging.info(f'{outfitTag} client open attempt')
            client = auraxium.event.EventClient(service_id=settings.PS2_SVS_ID)
        except:
            logging.warning(f'{outfitTag} client unable to be opened')
            logging.error(f'{traceback.format_exc()}')
            return None
        else:
            logging.debug(f'{outfitTag} client opened')
            return client   
        
    @commands.command(name='ps2-track-outfit')
    async def add_outfit(self,ctx, outfitTag):
        """
        Creates outfit SingleOutfitTrack object, and adds it to self.outfitObj.
        The client is generated and assigned
        """
        logging.info(f'Attempting to track {outfitTag}')
        try:
            client = self.start_event_client(outfitTag)
        except Exception:
            logging.error(f'{traceback.format_exc()}')
            
        logging.debug(f'Client returned')
         
        
        if client is not None:
            self.outfitObj.append(SingleOutfitTrack(outfitTag,client, self.bot))
            logging.info(f'Tracking {outfitTag} added')
        else:
            logging.warning(f'Tracking {outfitTag} failed')
            
            
            

class SingleOutfitTrack():
    """
    Class that contains the information needed to track a single outfit XP events
    """
    def __init__(self,outfitTag,client,bot):
        self.outfitTag = None
        self.outfitTrackingID = None
        self.outfitClient = None
        self.bot=bot
        
        
        