import asyncio
import auraxium
import matplotlib.pyplot as plt
from auraxium import ps2
from collections.abc import Mapping
import settings

name = 'hecules55'

def dictresolve(item,key=None,maxlevel=None,level=None):
    if(level!=None):
        level = level + 1
    else:
        level = 1
    if isinstance(item, Mapping):
        for key, item in item.items():
            if(maxlevel==None or level<maxlevel):
                dictresolve(item,key,maxlevel,level)
            else:
                print(key,item)
    else:
         print(key,item)
            
            
def dict_resolve_plting(item,key=None,maxlevel=None,level=None):
    if(level!=None):
        level = level + 1
    else:
        level = 1
    if isinstance(item, Mapping):
        for key, item in item.items():
            if(maxlevel==None or level<maxlevel):
                dictresolve(item,key,maxlevel,level)
            else:
                try:
                    print(key,item)
                    fig = plt.figure()
                    x = item.keys()
                    y = item.values()
                    
                    plt.scatter(x , y, label='Advanced Plan')  # Plot some data on the (implicit) axes.
                    plt.xlabel('Core Count')
                    plt.ylabel('Time (s)')
                    plt.title("FFTW plan Comparison plot - " + filename)
                    plt.legend(loc='upper center', bbox_to_anchor=(0.5, -0.05),
                      fancybox=True, shadow=True, ncol=5)
                    
                    plt.savefig('test.png')
                except:
                    print("fail")
    else:
         print(key,item)
            
            

async def main(name):
    async with auraxium.Client(service_id = settings.PS2_SVS_ID) as client:

        char = await client.get_by_name(ps2.Character, name)
        help(char)
        print(char.name())
        print(char.data.prestige_level)

        # NOTE: Any methods that might incur network traffic are asynchronous.
        # If the data type has been cached locally, no network communication
        # is required.

        # This will only generate a request once per faction, as the faction
        # data type is cached forever by default.
        print(await char.faction())

        # The online status is never cached as it is bound to change at any
        # moment.
        print(await char.is_online())
        
        print(await char.stat_by_faction())



async def player_history_data(player):
    async with auraxium.Client(service_id = settings.PS2_SVS_ID) as client:

        char = await client.get_by_name(ps2.Character, player)
        
        print(char.id)
        name = char.name()
        outfit = char.outfit()
        faction = await char.faction().resolve()
        stat = await char.stat()
        facstat = await char.stat_by_faction()
        
        isOnline = await char.is_online()
        prestige = char.data.prestige_level
        currency = await char.currency()
        weaponstat = await char.weapon_stat()
        stathistory= await char.stat_history(5)
        
        outfit = await outfit.resolve()
        print(name)
        print(outfit)
        print(currency)
        print(faction)
        print(prestige)
        print(isOnline)
        print(stat)
        print(facstat)
        
        player_stats_extract(stathistory,name)
         
            
            
def player_stats_extract(stathistory, name=None):
    fig = plt.figure()
    
    for i, stat in enumerate(stathistory):
        
        if(i == 0 or i == 2):
            
            if(i==0):
                colour = 'r-o'
            else:
                colour = 'g-o'
            print(stat['stat_name'])
            print(stat['day'])
            print(stat['week'])
            print(stat['month'])

            sorted_dict = dict(reversed(stat['day'].items()))

            x = [i for i in range(len(sorted_dict),0,-1)]
            print(x)
            y = [float(value) for value in sorted_dict.values()]

            #plt.scatter(x , y, label='Advanced Plan')  # Plot some data on the (implicit) axes.
            plt.plot(x , y,colour, label = stat['stat_name'])  # Plot some data on the (implicit) axes.
            
            plt.xlabel('Days since today')
            plt.ylabel('Rate')
            #plt.axis([,min(x)+1,min(y),max(y)+1])
            plt.legend()
            plt.title(name)
    plt.gca().invert_xaxis()
    plt.savefig('kvsd' + '.png')
    plt.show()
    plt.close()
        
        
        
    
            
        
        
asyncio.get_event_loop().run_until_complete(player_history_data(name))
