import traceback

class GenericSignup:
    """
    Overarching signup class.
    This class allows one to query the max reacts,
    and then change them.
    
    This class also grabs pregen messages when required
    """
    def __init__(self):
        pass

    def get_message(messageLocation):
        with open(messageLocation,'r') as f:
            messageText = f.read()
            return messageText

    async def get_reaction_details(self,ctx):

        message = "Reaction : Max Number\n"
        
        for reaction in self.reactions:
            
            if reaction.maxReact == -1:
                message = message + f"{reaction.symbol} : (-1) Unlimited\n"
            else:
                message = message + f"{reaction.symbol} : {reaction.maxReact}\n"

        await ctx.channel.send(message)

    async def set_reaction_details(self,ctx,*args):

        for index, value in enumerate(args):

            try:
                print(f"Changing {value}")
                if value in self.maxReact:
                    currentUsed = self.maxReact[value][1]
                    print(f"Current val {currentUsed}")

                    print(f"New val {args[index+1]}")
                    self.maxReact.update( {value: [int(args[index+1]),currentUsed]})
                    print(f"{self.maxReact[value]}")

                else:
                    print("React does not exist")
            except Exception:
                traceback.print_exc()

        await ctx.channel.send("New Values:")
        await self.get_reaction_details(ctx)


class GenericMessage(GenericSignup):
    """
    Class to generate a message for the signups.
    These messages can come from various sources,
    and so this class handles the main 2. 
    
    The first source is the premade messages.
    The second is user entered messages
    """
    def __init__(self):
        super().__init__()
        pass

    async def send_message(self,ctx,date):
        
        try:
            self.messageText = f'\n**Activity Type: {self.opsType}**' + self.messageText
        except:
            print("opsType does not exist")
        
        self.messageText = f'\n**Date of activity: {date}**\n' + self.messageText
        roles = await ctx.guild.fetch_roles()

        for role in roles:
            if role.name in self.mentionRoles:
                self.messageText = f'{role.mention} ' + self.messageText
            else:
                pass
            
        reactStr=str()
        for reaction in self.reactions:
            reactStr = reactStr + f'{reaction.symbol} {reaction.name}\n'

        self.messageText = self.messageText + f'\n\n**Use the following reacts:**\n{reactStr}'
        self.messageText = self.messageText + f'\n**If your name does not appear, your signup has not happened.**\n**To remove or change signup, unreact.**'
        
        messageHandler = await self.signUpChannel.send(self.messageText)
        self.messageHandlerID = messageHandler.id

        
class ReactionData():
    """
    Contains all the data for storing the reactions
    from a signup for a specific react.
    
    Also contains the functions to access and alter
    this data.
    """
    def __init__(self,name,emoji,maxReact):
        self.name = name
        self.symbol = emoji
        self.maxReact = maxReact
        self.currentReact = 0
        self.members = {}
        
    def add_member(self, userID,userNameText):
        """
        Adds a user to the member dictionary as a dict
        of the form {userID : userNameText}
        """
        self.member.update({userID:userNameText})
    
    def remove_member(self, userID):
        """
        Removes a user to the member dictionary 
        """
        del self.member[userID]
        
        
    def check_member(self, userID):
        """
        Checks if the user is in the dict already
        """
        if userID in self.member.keys():
            return True
        else:
            return False    
        
        
class ArmourDogs(GenericMessage):

    def __init__(self,channel):
        super(ArmourDogs,self).__init__()
        self.signUpChannel = channel
        self.messageText = ArmourDogs.get_message('messages/armourdogs.txt')
        self.messageHandlerID = None
        self.ignoreRemove = False
        self.reactions=[ReactionData('Vanguard','<:Icon_Vanguard:795727955896565781>',-1),
                        ReactionData('Sunderer','<:Icon_Sunderer:795727911549272104>',-1),
                        ReactionData('Lightning','<:Icon_Lightning:795727852875677776>',-1),
                        ReactionData('Harasser','<:Icon_Harasser:795727814220840970>',-1),
                        ReactionData('Reserve/Maybe','<:Icon_Spawn_Beacon_NC:795729269891530792>',-1)
                       ]
        self.mentionRoles =['ArmourDogs']

class Bastion(GenericMessage):

    def __init__(self,channel):
        super(Bastion,self).__init__()
        self.signUpChannel = channel
        self.messageText = Bastion.get_message('messages/bastion.txt')
        self.messageHandlerID = None
        self.ignoreRemove = False
        self.reactions=[ReactionData('Woof','<:tdkdsmall:803387734172762143>',-1)]
        self.mentionRoles =['TDKD']

class DogFighters(GenericMessage):

    def __init__(self,channel):
        super(DogFighters,self).__init__()
        self.signUpChannel = channel
        self.messageText = DogFighters.get_message('messages/dogfighters.txt')
        self.messageHandlerID = None
        self.ignoreRemove = False
        self.reactions=[ReactionData('Reaver','<:Icon_Reaver:795727893342846986>',-1),
                        ReactionData('Dervish','<:Icon_Dervish:861303237062950942>',-1),
                        ReactionData('Reserve/Maybe','<:Icon_Spawn_Beacon_NC:795729269891530792>',-1)
                       ]
        self.mentionRoles =['DogFighters']

class Logidogs(GenericMessage):

    def __init__(self,channel):
        super(Logidogs,self).__init__()
        self.signUpChannel = channel
        self.messageText = Logidogs.get_message('messages/logidogs.txt')
        self.messageHandlerID = None
        self.ignoreRemove = False
        self.reactions=[ReactionData('Hacker','<:Icon_Infiltrator:795726922264215612>',4),
                        ReactionData('Router','<:Icon_Engineer:795726888763916349>',2),
                        ReactionData('Reserve/Maybe','<:Icon_Spawn_Beacon_NC:795729269891530792>',-1)
                       ]
        self.mentionRoles =['LogiDogs']

class RoyalAirWoof(GenericMessage):

    def __init__(self,channel):
        super(RoyalAirWoof,self).__init__()
        self.signUpChannel = channel
        self.messageText = RoyalAirWoof.get_message('messages/royalairwoof.txt')
        self.messageHandlerID = None
        self.ignoreRemove = False
        self.reactions=[ReactionData('Gal-Pilot','<:Icon_Galaxy:795727799591239760>',4),
                        ReactionData('Lib-Pilot','<:Icon_Liberator:795727831605837874>',0),
                        ReactionData('Gunner','<:Icon_Engineer:795726888763916349>',-1),
                        ReactionData('Reserve/Maybe','<:Icon_Spawn_Beacon_NC:795729269891530792>',-1)
                       ]
        self.mentionRoles =['RAW']

class SoberDogs(GenericMessage):

    def __init__(self,channel):
        super(SoberDogs,self).__init__()
        self.signUpChannel = channel
        self.messageText = SoberDogs.get_message('messages/soberdogs.txt')
        self.messageHandlerID = None
        self.ignoreRemove = False
        self.reactions=[ReactionData('Heavy','<:Icon_Heavy_Assault:795726910344003605>',5),
                        ReactionData('Medic','<:Icon_Combat_Medic:795726867960692806>',4),
                        ReactionData('Engineer','<:Icon_Engineer:795726888763916349>',2),
                        ReactionData('Infiltrator','<:Icon_Infiltrator:795726922264215612>',1),
                        ReactionData('Light assault','<:Icon_Light_Assault:795726936759468093>',0),
                        ReactionData('MAX','<:Icon_MAX:795726948365631559>',0),
                        ReactionData('Reserve/Maybe','<:Icon_Spawn_Beacon_NC:795729269891530792>',-1)
                        ]
        self.mentionRoles =['Soberdogs']

class SquadLead(GenericMessage):

    def __init__(self,channel):
        super(SquadLead,self).__init__()
        self.signUpChannel = channel
        self.messageText = SquadLead.get_message('messages/opsnight.txt')
        self.messageHandlerID = None
        self.ignoreRemove = False
        
        self.reactions=[ReactionData('PL','<:Icon_A:795729153072431104>',-1),
                        ReactionData('SL','<:Icon_B:795729164891062343>',-1),
                        ReactionData('FL','<:Icon_C:795729176363270205>',-1),
                        ReactionData('Reserve','<:Icon_D:795729189260754956>',-1),
                        ReactionData('Soberdog S/FL','<:Icon_Heavy_Assault:795726910344003605>',-1),
                        ReactionData('RAW S/FL','<:Icon_Galaxy:795727799591239760>',-1),
                        ReactionData('Armourdog S/FL','<:Icon_Vanguard:795727955896565781>',-1),
                        ReactionData('Dogfighter S/FL','<:Icon_Reaver:795727893342846986>',-1)
                        ]
        self.mentionRoles =['CO','Captain','Lieutenant','Sergeant','Corporal']


class CobaltClash(GenericMessage):

    def __init__(self,channel,opsType, message):
        self.signUpChannel = channel
        self.opsType=opsType
        self.messageText = message
        self.messageHandlerID = None
        self.ignoreRemove = False
        self.reactions=[ReactionData('Coming','<:NC:727306728470872075>',-1),
                        ReactionData('Reserve','<:Icon_Spawn_Beacon_NC:795729269891530792>',-1),
                        ]

        self.mentionRoles =['TDKD']


class JointOps(GenericMessage):

    def __init__(self,channel,opsType, message):
        self.signUpChannel = channel
        self.opsType=opsType
        self.messageText = message
        self.messageHandlerID = None
        self.ignoreRemove = False
        self.reactions=[ReactionData('Coming','<:NC:727306728470872075>',-1),
                        ReactionData('Reserve','<:Icon_Spawn_Beacon_NC:795729269891530792>',-1),
                        ]
        self.mentionRoles =['TDKD']

class NCAF(GenericMessage):

    def __init__(self,channel,opsType, message):
        self.signUpChannel = channel
        self.opsType=opsType
        self.messageText = message
        self.messageHandlerID = None
        self.ignoreRemove = False
        self.reactions=[ReactionData('Coming','<:NC:727306728470872075>',-1),
                        ReactionData('Reserve','<:Icon_Spawn_Beacon_NC:795729269891530792>',-1),
                        ]
        self.mentionRoles =['TDKD']

class Training(GenericMessage):

    def __init__(self,channel,opsType, message):
        self.signUpChannel = channel
        self.opsType=opsType
        self.messageText = message
        self.messageHandlerID = None
        self.ignoreRemove = False
        self.reactions=[ReactionData('Coming','<:NC:727306728470872075>',-1),
                        ReactionData('Reserve','<:Icon_Spawn_Beacon_NC:795729269891530792>',-1),
                        ]
        self.mentionRoles =[]
