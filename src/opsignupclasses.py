import discord
import traceback
from datetime import datetime

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

        for reaction in self.reactions.values():

            if reaction.maxReact == -1:
                message = message + f"{reaction.symbol} : (-1) Unlimited\n"
            else:
                message = message + f"{reaction.symbol} : {reaction.maxReact}\n"

        await ctx.channel.send(message)

    async def set_reaction_details(self,ctx,*args):

        for index, value in enumerate(args):

            try:
                print(f"Changing {value}")
                if value in self.reactions.keys():

                    print(f"New val {args[index+1]}")
                    self.reactions[value].maxReact =int(args[index+1])
                    print(f"{self.reactions[value].maxReact}")

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
        for reaction in self.reactions.keys():
            reactStr = reactStr + f'{self.reactions[reaction].symbol} {self.reactions[reaction].name}\n'

        self.messageText = self.messageText + f'\n\n**Use the following reacts:**\n{reactStr}'
        self.messageText = self.messageText + f'\n**If your name does not appear, your signup has not happened.**\n**To remove or change signup, unreact.**'



        messageHandler = await ctx.guild.get_channel(self.signUpChannelID).send(roleText,embed=embed)
        self.messageHandlerID = messageHandler.id



class GenericEmbed(GenericSignup):
    """
    Class to generate a embed for the signups.

    """
    def __init__(self):
        super().__init__()
        pass

    def convert_date_to_unix(self,date):

        #message_date='Tuesday 27/09/21 16:00 bst' # Example
        date_string=date.replace('bst','+0100').replace('BST', '+0100').replace('gmt','+0000').replace('GMT','+0000')
        try:
            dtfloat=datetime.strptime(date_string,'%A %d/%m/%y %H:%M %z').timestamp()
            dtint=int(dtfloat) #the output is a float which doesn't work with <t:time:R>
        except:
            try:
                dtfloat=datetime.strptime(date_string,'%A %d/%m/%y %H:%M%z').timestamp()
                dtint=int(dtfloat) #the output is a float which doesn't work with <t:time:R>
            except:
                raise
        return dtint

    async def send_message(self,ctx,date):

        roles = await ctx.guild.fetch_roles()

        roleText = ""
        for role in roles:

            if role.name in self.mentionRoles:
                roleText = f'{role.mention} ' + roleText
            else:
                pass
        try:
            startTime = self.convert_date_to_unix(date)
            embed = discord.Embed(title = f'Local time: <t:{startTime}:F>', description =self.messageText ,color=0xff0000)
            embed.add_field( name = "Time till start", value = f'<t:{startTime}:R>', inline=False)


        except:
            embed = discord.Embed(title = f"UK time: {date}", description =self.messageText ,color=0xff0000)

        try:
            embed.add_field( name = "Op Type", value = self.opsType, inline=False)
        except:
            pass

        for reaction in self.reactions.keys():
            if self.reactions[reaction].maxReact > 0:
                embed.add_field( name = f'{self.reactions[reaction].symbol} {self.reactions[reaction].name}', value = f'LIMIT: 0 / {self.reactions[reaction].maxReact}\n{self.reactions[reaction].members["perm"]}', inline=True)
            else:
                embed.add_field( name = f'{self.reactions[reaction].symbol} {self.reactions[reaction].name}', value = f'{self.reactions[reaction].members["perm"]}', inline=True)

        embed.set_footer(text=f'\n**If your name does not appear, your signup has not happened.**\n**To remove or change signup, unreact.**')

        messageHandler = await ctx.guild.get_channel(self.signUpChannelID).send(roleText,embed=embed)
        self.messageHandlerID = messageHandler.id


        try:
            message = await ctx.guild.get_channel(self.signUpChannelID).fetch_message(self.messageHandlerID)
            for reaction in self.reactions.keys():
                await message.add_reaction(f"{reaction}")

            await message.add_reaction(f"💥")
        except:
            traceback.print_exc()



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
        self.members = {'perm':'\u200b'}

    def add_member(self, userID,userNameText):
        """
        Adds a user to the member dictionary as a dict
        of the form {userID : userNameText}
        """
        self.members.update({userID:userNameText})
        self.currentReact += 1

    def remove_member(self, userID):
        """
        Removes a user to the member dictionary
        """
        del self.members[userID]
        self.currentReact -= 1


    def check_member(self, userID):
        """
        Checks if the user is in the dict already
        """
        if userID in self.members.keys():
            return True
        else:
            return False


class ArmourDogs(GenericEmbed):

    def __init__(self,channel):
        super(ArmourDogs,self).__init__()
        self.signUpChannelID = channel.id
        self.messageText = ArmourDogs.get_message('messages/armourdogs.txt')
        self.messageHandlerID = None
        self.ignoreRemove = False
        self.reactions={'<:Icon_Vanguard:795727955896565781>' : ReactionData('Vanguard','<:Icon_Vanguard:795727955896565781>',-1),
                        '<:Icon_Sunderer:795727911549272104>' : ReactionData('Sunderer','<:Icon_Sunderer:795727911549272104>',-1),
                        '<:Icon_Lightning:795727852875677776>' : ReactionData('Lightning','<:Icon_Lightning:795727852875677776>',-1),
                        '<:Icon_Harasser:795727814220840970>' : ReactionData('Harasser','<:Icon_Harasser:795727814220840970>',-1),
                        '<:Icon_Spawn_Beacon_NC:795729269891530792>' : ReactionData('Reserve/Maybe','<:Icon_Spawn_Beacon_NC:795729269891530792>',-1)
                       }
        self.mentionRoles =['ArmourDogs']

class Bastion(GenericEmbed):

    def __init__(self,channel):
        super(Bastion,self).__init__()
        self.signUpChannelID = channel.id
        self.messageText = Bastion.get_message('messages/bastion.txt')
        self.messageHandlerID = None
        self.ignoreRemove = False
        self.reactions={'<:tdkdsmall:803387734172762143>' : ReactionData('Woof','<:tdkdsmall:803387734172762143>',-1)}
        self.mentionRoles =['TDKD']

class DogFighters(GenericEmbed):

    def __init__(self,channel):
        super(DogFighters,self).__init__()
        self.signUpChannelID = channel.id
        self.messageText = DogFighters.get_message('messages/dogfighters.txt')
        self.messageHandlerID = None
        self.ignoreRemove = False
        self.reactions={'<:Icon_Reaver:795727893342846986>' : ReactionData('Reaver','<:Icon_Reaver:795727893342846986>',-1),
                        '<:Icon_Dervish:861303237062950942>' : ReactionData('Dervish','<:Icon_Dervish:861303237062950942>',-1),
                        '<:Icon_Spawn_Beacon_NC:795729269891530792>' : ReactionData('Reserve/Maybe','<:Icon_Spawn_Beacon_NC:795729269891530792>',-1)
                       }
        self.mentionRoles =['DogFighters']

class Logidogs(GenericEmbed):

    def __init__(self,channel):
        super(Logidogs,self).__init__()
        self.signUpChannelID = channel.id
        self.messageText = Logidogs.get_message('messages/logidogs.txt')
        self.messageHandlerID = None
        self.ignoreRemove = False
        self.reactions={'<:Icon_Infiltrator:795726922264215612>' : ReactionData('Hacker','<:Icon_Infiltrator:795726922264215612>',4),
                        '<:Icon_Engineer:795726888763916349>' : ReactionData('Router','<:Icon_Engineer:795726888763916349>',2),
                        '<:Icon_Spawn_Beacon_NC:795729269891530792>' : ReactionData('Reserve/Maybe','<:Icon_Spawn_Beacon_NC:795729269891530792>',-1)
                       }
        self.mentionRoles =['LogiDogs']

class RoyalAirWoof(GenericEmbed):

    def __init__(self,channel):
        super(RoyalAirWoof,self).__init__()
        self.signUpChannelID = channel.id
        self.messageText = RoyalAirWoof.get_message('messages/royalairwoof.txt')
        self.messageHandlerID = None
        self.ignoreRemove = False
        self.reactions={'<:Icon_Galaxy:795727799591239760>' : ReactionData('Gal-Pilot','<:Icon_Galaxy:795727799591239760>',-1),
                        '<:Icon_Liberator:795727831605837874>' : ReactionData('Lib-Pilot','<:Icon_Liberator:795727831605837874>',-1),
                        '<:Icon_Valkyrie:795727937735098388>' : ReactionData('Valk-Pilot','<:Icon_Valkyrie:795727937735098388>',-1),
                        '<:Icon_Engineer:795726888763916349>' : ReactionData('Gunner','<:Icon_Engineer:795726888763916349>',-1),
                        '<:Icon_Spawn_Beacon_NC:795729269891530792>' : ReactionData('Reserve/Maybe','<:Icon_Spawn_Beacon_NC:795729269891530792>',-1)
                       }
        self.mentionRoles =['RAW']

class SoberDogs(GenericEmbed):

    def __init__(self,channel):
        super(SoberDogs,self).__init__()
        self.signUpChannelID = channel.id
        self.messageText = SoberDogs.get_message('messages/soberdogs.txt')
        self.messageHandlerID = None
        self.ignoreRemove = False
        self.reactions={'<:Icon_Heavy_Assault:795726910344003605>' : ReactionData('Heavy','<:Icon_Heavy_Assault:795726910344003605>',5),
                        '<:Icon_Combat_Medic:795726867960692806>' : ReactionData('Medic','<:Icon_Combat_Medic:795726867960692806>',4),
                        '<:Icon_Engineer:795726888763916349>' : ReactionData('Engineer','<:Icon_Engineer:795726888763916349>',2),
                        '<:Icon_Infiltrator:795726922264215612>' : ReactionData('Infiltrator','<:Icon_Infiltrator:795726922264215612>',1),
                        '<:Icon_Light_Assault:795726936759468093>' : ReactionData('Light assault','<:Icon_Light_Assault:795726936759468093>',0),
                        '<:Icon_MAX:795726948365631559>' : ReactionData('MAX','<:Icon_MAX:795726948365631559>',0),
                        '<:Icon_Spawn_Beacon_NC:795729269891530792>' : ReactionData('Reserve/Maybe','<:Icon_Spawn_Beacon_NC:795729269891530792>',-1)
                       }
        self.mentionRoles =['Soberdogs']

class SquadLead(GenericEmbed):

    def __init__(self,channel):
        super(SquadLead,self).__init__()
        self.signUpChannelID = channel.id
        self.messageText = SquadLead.get_message('messages/opsnight.txt')
        self.messageHandlerID = None
        self.ignoreRemove = False

        self.reactions={'<:Icon_A:795729153072431104>' : ReactionData('PL','<:Icon_A:795729153072431104>',-1),
                        '<:Icon_B:795729164891062343>' : ReactionData('SL','<:Icon_B:795729164891062343>',-1),
                        '<:Icon_C:795729176363270205>' : ReactionData('FL','<:Icon_C:795729176363270205>',-1),
                        '<:Icon_D:795729189260754956>' : ReactionData('Specialist SL','<:Icon_D:795729189260754956>',-1),
                        '<:NC:727306728470872075>' : ReactionData('Guest SL','<:NC:727306728470872075>',2),
                        '<:Icon_Spawn_Beacon_NC:795729269891530792>' : ReactionData('Reserve','<:Icon_Spawn_Beacon_NC:795729269891530792>',-1)
                        #'<:Icon_Heavy_Assault:795726910344003605>' : ReactionData('Soberdog S/FL','<:Icon_Heavy_Assault:795726910344003605>',-1),
                        #'<:Icon_Galaxy:795727799591239760>' : ReactionData('RAW S/FL','<:Icon_Galaxy:795727799591239760>',-1),
                        #'<:Icon_Vanguard:795727955896565781>' : ReactionData('Armourdog S/FL','<:Icon_Vanguard:795727955896565781>',-1),
                        #'<:Icon_Reaver:795727893342846986>' : ReactionData('Dogfighter S/FL','<:Icon_Reaver:795727893342846986>',-1)
                       }
        self.mentionRoles =['CO','Captain','Lieutenant','Sergeant','Corporal','Guest SL']


class CobaltClash(GenericEmbed):

    def __init__(self,channel,opsType, message,additionalRoles=[]):
        self.signUpChannelID = channel.id
        self.opsType=opsType
        self.messageText = message
        self.messageHandlerID = None
        self.ignoreRemove = False
        self.reactions={'<:NC:727306728470872075>' : ReactionData('Coming','<:NC:727306728470872075>',-1),
                        '<:Icon_Spawn_Beacon_NC:795729269891530792>' : ReactionData('Reserve/Maybe','<:Icon_Spawn_Beacon_NC:795729269891530792>',-1),
                       }

        self.mentionRoles = additionalRoles


class JointOps(GenericEmbed):

    def __init__(self,channel,opsType, message):
        self.signUpChannelID = channel.id
        self.opsType=opsType
        self.messageText = message
        self.messageHandlerID = None
        self.ignoreRemove = False
        self.reactions={'<:NC:727306728470872075>' : ReactionData('Coming','<:NC:727306728470872075>',-1),
                        '<:Icon_Spawn_Beacon_NC:795729269891530792>' : ReactionData('Reserve/Maybe','<:Icon_Spawn_Beacon_NC:795729269891530792>',-1),
                       }
        self.mentionRoles =['TDKD']

class NCAF(GenericEmbed):

    def __init__(self,channel,opsType, message,additionalRoles=[]):
        self.signUpChannelID = channel.id
        self.opsType=opsType
        self.messageText = message
        self.messageHandlerID = None
        self.ignoreRemove = False
        self.reactions={'<:NC:727306728470872075>' : ReactionData('Coming','<:NC:727306728470872075>',-1),
                        '<:Icon_Spawn_Beacon_NC:795729269891530792>' : ReactionData('Reserve/Maybe','<:Icon_Spawn_Beacon_NC:795729269891530792>',-1),
                       }
        self.mentionRoles = additionalRoles

class Training(GenericEmbed):

    def __init__(self,channel,opsType, message,additionalRoles=[]):
        self.signUpChannelID = channel.id
        self.opsType=opsType
        self.messageText = message
        self.messageHandlerID = None
        self.ignoreRemove = False
        self.reactions={'<:NC:727306728470872075>' : ReactionData('Coming','<:NC:727306728470872075>',-1),
                        '<:Icon_Spawn_Beacon_NC:795729269891530792>' : ReactionData('Reserve/Maybe','<:Icon_Spawn_Beacon_NC:795729269891530792>',-1),
                       }
        self.mentionRoles = additionalRoles

class OutfitWars(GenericEmbed):

    def __init__(self,channel,opsType, message,additionalRoles=[]):
        self.signUpChannelID = channel.id
        self.opsType=opsType
        self.messageText = message
        self.messageHandlerID = None
        self.ignoreRemove = False
        self.reactions={'<:NC:727306728470872075>' : ReactionData('Coming','<:NC:727306728470872075>',-1),
                        '<:Icon_Spawn_Beacon_NC:795729269891530792>' : ReactionData('Reserve/Maybe','<:Icon_Spawn_Beacon_NC:795729269891530792>',-1),
                       }

        self.mentionRoles = additionalRoles
