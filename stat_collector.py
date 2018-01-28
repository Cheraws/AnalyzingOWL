import json
import time
from collections import defaultdict
current = 2370
maxGame = 2426
import datetime
import matplotlib.pyplot as plt
MERCY_ULT_TIME = 20
from pathlib import Path

ult_timers = {
    'doomfist':4,
    'genji':6,
    'mccree': 6,
    'pharah': 3,
    'reaper': 3,
    'soldier':6,
    'mercy':6,
    'sombra':6,
    'tracer':3,
    'bastion':8,
    'hanzo':5,
    'junkrat':10,
    'mei':5,
    'torbjorn': 12,
    'widowmaker': 15.5,
    'orisa': 5,
    'reinhardt': 3,
    'roadhog': 6,
    'winston': 10,
    'zarya': 4,
    'ana': 8,
    'lucio': 6.25,
    'mercy':20,
    'moira':8
}


def update_mercy_lifespan(player,seconds,mercy_list):
    mercy_list[player][0] += seconds 
    mercy_list[player][1] += 1
    #means the player died.
    if seconds < 20:
        mercy_list[player][2] += 1


def time_converter(start, current_time):
    return str(datetime.timedelta(seconds=(current_time-start)))

def calculate_ults_in_teamfight(ult_time_dictionary,first_kill,last_kill):
    current_ults = defaultdict(list)
    future_ults = defaultdict(list)
    for color,ult_list in ult_time_dictionary.items():
        current_list = []
        new_list = []
        for ult in ult_list:
            character = ult[0]
            time = ult[1]
            advantage = ult[2]
            # if ult happened more than 12 seconds before, it doesn't count as part of the teamfight.
            if first_kill - time > 12:
                continue
            elif time - last_kill > 0:
                advantage = 0
                future_ults[color].append((character,time,advantage))
            else:
                current_ults[color].append((character,time,advantage))
    return current_ults, future_ults

                
                
mercy_ult_win_ratio = [0,0]
kills = 0
ults = 0
#mercy lifespan contains three values. The first number is seconds alive, while the second number is times used, and third is times interrupted.
mercy_lifespan = defaultdict(list)
mercy_killers = defaultdict(int)
ults_used = defaultdict(int)
players_by_playtime = {}
mercy_ult_by_advantage = defaultdict(int)
time_to_charge_ult = defaultdict(dict)
#comp at team fight.
team_fight_comp = {}
while current < maxGame:
    fights = 0
    fight_happening = False
    game_number = 1
    round_number = 1
    blue_name = ""
    red_name = ""
    current_character_by_player = defaultdict(int)
    while game_number < 6:
        fight_happening = False
        current_ults = 0
        print(game_number, round_number)
        players = defaultdict(int)
        players_by_id = {'red':defaultdict(int),
                'blue':defaultdict(int)}
        file_name = "game_data/"
        file_name += str(current) + "_" + str(game_number) + "_" +  str(round_number) + ".json"
        f = Path(file_name)
        #game finished
        if not f.is_file():
            game_number += 1
            round_number = 1
            continue
        with open(file_name,'r') as f:
            datastore = json.load(f)
            datastore = json.loads(datastore)
        blue_playtime = defaultdict(int)
        red_playtime = defaultdict(int)
        start = 0
        end = 0
        #initializing players
        for key in datastore.keys():
            if key != 'events':
                if key == 'blue':
                    blue_name = datastore[key]
                if key == 'red':
                    red_name = datastore[key]
                if key == 'bluenames':
                    for index, player in enumerate(datastore[key]):
                        if player == "Nus":
                            player = "nus"
                        players_by_id['blue'][index+1] = player
                        if player not in players_by_playtime:
                            players_by_playtime[player] = defaultdict(int)
                if key == 'rednames':
                    for index, player in enumerate(datastore[key]):
                        if player == "Nus":
                            player = "nus"
                        players_by_id['red'][index+1] = player
                        if player not in players_by_playtime:
                            players_by_playtime[player] = defaultdict(int)
        current_character_by_player = defaultdict(int)
        '''
            Keep track of mercies ulting. If mercy ult > 20 seconds or death,
            set a negative number to end ult.
        '''
        mercy_ult_start = defaultdict(int)
        mercy_ult_start['red'] = -1000
        mercy_ult_start['blue'] = -1000
        opposite_color = {"blue":"red", "red":"blue"}
        last_ult_time = defaultdict(int)
        ults_used_by_color = defaultdict(list)
        player_advantage_in_ult = defaultdict(list)
        last_kill = 0
        first_kill = 0
        fight_kills = 0
        kills_by_color = {'red': 0, 'blue': 0}
        mercy = {}
        for event in datastore['events']:
            time = event[0]
            standard_time = str(datetime.timedelta(seconds=(time-start)))
            if(event[1] == 'PAUSE' or event[1] == 'UNPAUSE'):
                continue
            if fight_happening:
                #if fight has terminated
                if time - last_kill > 14 or event[1] == 'END':
                    fight_happening = False
                    #print("fight end is at " + str(datetime.timedelta(seconds=(last_kill-start)))) 
                    current_ults, future_ults = calculate_ults_in_teamfight(player_advantage_in_ult,first_kill, last_kill)
                    ult_first = None
                    mercy_color = None
                    both_mercies = False
                    for color in current_ults:
                        for ult in current_ults[color]:
                            character = ult[0]
                            ult_time = ult[1]
                            advantage = ult[2]
                            if character == 'mercy':
                                if not ult_first:
                                    ult_first = (ult_time,advantage)
                                else:
                                    if ult_time < ult_first[0]:
                                        ult_first = (ult_time,advantage)
                                if mercy_color == None:
                                    mercy_color = color
                                else:
                                    if mercy_color != color:
                                        both_mercies = True
                                mercy_ult_time = str(datetime.timedelta(seconds=(ult_time-start)))
                    if ult_first:            
                        mercy_ult_by_advantage[ult_first[1]] += 1  
                    player_advantage_in_ult = future_ults
                    winning_color = max(kills_by_color, key=kills_by_color.get)
                    if max(kills_by_color.values()) != min(kills_by_color.values()):
                        if (not both_mercies) and mercy_color != None:
                            print("There is only one mercy")
                            mercy_ult_win_ratio[1] += 1
                            if winning_color == mercy_color:
                                print("One mercy won!")
                                mercy_ult_win_ratio[0] += 1
                    kills_by_color = dict.fromkeys(kills_by_color, 0)
            #weird glitch involving player switches on Dragons vs Mayhem
            if time >= 11687 and time < 11699 and current == 2412:
                continue
            #Check if mercy lived through ult
            for color in mercy_ult_start:
                if mercy_ult_start[color] > 0 and time - mercy_ult_start[color] > 20:
                    mercy_player = mercy[color]
                    last_ult_time[mercy_player] = mercy_ult_start[color] + 20
                    update_mercy_lifespan(mercy_player,20, mercy_lifespan)
                    mercy_ult_start[color] = -1000
            if event[1] == 'END':
                end = time
            elif event[1] == 'MATCH':
                start = time
            else:
                color = event[2].lower()
                opposing_color = opposite_color[color]
                player_id = event[3]
                first_character = event[4]
                player = players_by_id[color][player_id]
                if event[1] == 'SWITCH':
                    second_character = event[5]
                    if player in current_character_by_player:
                        old_time,old_character = current_character_by_player[player]
                        play_time = time - old_time
                        players_by_playtime[player][old_character] += play_time
                        #since player switched, last ult time is now inaccurate.
                        if player in last_ult_time:
                            del last_ult_time[player]
                    if second_character == "mercy":
                        if player not in mercy_lifespan:
                            mercy_lifespan[player] = [0,0,0]
                        mercy[color] = player
                    current_character_by_player[player] = (time, second_character)
                elif event[1] == "ULT_USE":
                    ults_used_by_color[color] += [first_character]
                    ults_used[player] += 1
                    kills_differential = kills_by_color[color] - kills_by_color[opposing_color]
                    last_ult_time[player] = time
                    if current_character_by_player[player][1] == "mercy":
                        #print("{2} Mercy ulted at {0} with {1} advantage".format(standard_time,kills_differential,color))
                        #print(kills_by_color)
                        player_advantage_in_ult[color].append((first_character,time,kills_differential))
                        mercy_ult_by_advantage[kills_differential] += 1  
                        mercy_ult_start[color] = time
                elif event[1] == "KILL":
                    kills_by_color[color] += 1
                    last_kill = time
                    #the fight has started.
                    if not fight_happening:
                        first_kill = time
                        fights += 1
                    fight_happening = True
                    kills += 1
                    enemy_id = event[5]
                    dead_character = event[6]
                    killed_player = players_by_id[opposing_color][enemy_id]
                    if dead_character == "mercy":
                        #mercy died mid-ult
                        if mercy_ult_start[opposing_color] > 0:
                            last_ult_time[player] = time
                            mercy_killers[first_character] += 1
                            ult_time = time - mercy_ult_start[opposing_color]
                            update_mercy_lifespan(killed_player,ult_time, mercy_lifespan)
                            #mark ult as terminated
                            mercy_ult_start[opposing_color] = -1000
                elif event[1] == "REVIVE":
                    continue
                elif event[1] == "ULT_GAIN":
                    if first_character not in time_to_charge_ult[player]:
                        time_to_charge_ult[player][first_character] = []
                    initial_time, dummy = current_character_by_player[player]  
                    if player in last_ult_time:
                        initial_time = last_ult_time[player]
                    if first_character == "mercy":
                        print ("Ult gained for {0} mercy at".format(color),time_converter(start,initial_time), time_converter(start,time))
                    time_to_charge_ult[player][first_character].append(time - initial_time)
                    last_ult_time[player] = time
        for player in current_character_by_player:
            old_time,old_character = current_character_by_player[player]
            play_time = end - old_time
            players_by_playtime[player][old_character] += play_time
 
        #by playtime
        '''
        for player in players_by_playtime:
            for character in players_by_playtime[player]:
                playtime = players_by_playtime[player][character]
                print("{0} has been played by {1} for {2} seconds".format(character,player,playtime))
        '''

        print("fights are {0}".format(fights))
        print(str(datetime.timedelta(seconds=(end-start)))) 
        print(mercy_ult_win_ratio)
        round_number += 1
    current += 1

#calculate average lifespan of mercies

print("Total fights is {0}".format(fights))
print("Total kills is {0}".format(kills))
total_mercy_ults = 0
total_mercy_deaths = 0
mercy_death_graph = {}

#gathering data on average mercy lifespan in valkyrie
for player in mercy_lifespan:
    lifetimes, ult_times,deaths = mercy_lifespan[player]
    total_mercy_ults += ult_times
    total_mercy_deaths += deaths
    if ult_times > 0:
        mercy_death_graph[player] = deaths/ult_times
        avg_ult_time = lifetimes/ult_times
        print("{1} lives for an average of {0} seconds and died {2} times out of {3}".format(avg_ult_time,player,deaths,ult_times))

avg_seconds_per_ult = defaultdict(dict)
std_deviation_by_player = defaultdict(dict)
for player,player_ults in time_to_charge_ult.items():
    for character in player_ults:
        playtime = sum(player_ults[character])
        ults = len(player_ults[character])
        avg = playtime/ults
        avg_seconds_per_ult[character][player] = avg
        summation = 0
        if player == "nus" and character == "mercy":
            print("ults are {0}".format(player_ults[character]))
        for ult in player_ults[character]:
            summation += pow(ult - avg,2)
        std_dev = pow(summation/ults,0.5)
        std_deviation_by_player[character][player] = std_dev/pow(avg,0.5)

print("Percentage of mercies that die in ult is {0}".format(total_mercy_deaths/(total_mercy_ults)))

print("Mercy win ratio when only ulting on one side is {0} out of {1}".format(mercy_ult_win_ratio[0]/(mercy_ult_win_ratio[1]),mercy_ult_win_ratio[1]))
analyzed_character = "mercy"
d = avg_seconds_per_ult[analyzed_character]
print(avg_seconds_per_ult[analyzed_character])
x_axis = []
y_axis = []
error = []
for w in sorted(d, key=d.get, reverse=True):
    x_axis += [w]
    y_axis += [d[w]]
    error += [std_deviation_by_player[analyzed_character][w]]

print(x_axis)
print(y_axis)
print(error)
plt.errorbar(list(range(0,len(x_axis))), y_axis,yerr=error,fmt='o')
#plt.bar(range(len(y_axis)), list(y_axis), align='center')
plt.xticks(range(len(x_axis)), list(x_axis))
plt.xticks(rotation=90)
plt.title("Seconds to generate ult as " + analyzed_character)
plt.ylabel("seconds")
plt.tight_layout()
plt.show()
quit()
