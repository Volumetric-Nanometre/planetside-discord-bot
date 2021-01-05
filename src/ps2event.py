    
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
        
  
    async def generic_event_trigger(self,ctx,char,client,trigger):
        """
        Function to set trigger event for when player dies
        """                            
        dictVal = Ps2PersonalEvents.stats_dictionary_insert(self,char,{trigger:int(0)})
        self.trackingdata.update({char.name():dictVal})
        
        Ps2EventClient.remove_trigger(self,client,trigger)

        @client.trigger(auraxium.EventType.DEATH,characters=self.membersBeingTracked_id,name=trigger)
        async def generic_payload (event):
            char_id = int(event.payload['character_id'])
            char = await client.get_by_id(ps2.Character, char_id)
            attacker_id = int(event.payload['attacker_character_id'])
            attack_char = await client.get_by_id(ps2.Character, attacker_id)
            char_fac=await char.faction().resolve()
            attack_fac=await attack_char.faction().resolve()
            
            print(char_fac)
            print(attack_fac)
            if char_id in self.membersBeingTracked_id:
                total = self.trackingdata[char.name()]['deaths'] + 1
                self.trackingdata.update({char.name(): Ps2PersonalEvents.stats_dictionary_insert(self,char,{'deaths':total})})
            elif char_fac == attack_fac and attacker_id in self.membersBeingTracked_id:
                total = self.trackingdata[attack_char.name()]['team-kills'] + 1
                self.trackingdata.update({attack_char.name(): Ps2PersonalEvents.stats_dictionary_insert(self,attack_char,{'team-kills':total})})
            else:
                total = self.trackingdata[attack_char.name()]['kills'] + 1
                self.trackingdata.update({attack_char.name(): Ps2PersonalEvents.stats_dictionary_insert(self,attack_char,{'kills':total})})

            print(f'{char.name()} has died to {attack_char.name()}')
            

