import json
import time
import collections
import datetime
import matplotlib.pyplot as plt
from pathlib import Path

Character = collections.namedtuple('character', 'player time')

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

def get_json_file(current_id,game_number,round_number):
    file_name = "game_data/"
    file_name += str(current_id) + "_" + str(game_number) + "_" +  str(round_number) + ".json"
    f = Path(file_name)
    if not f.is_file():
        return None
    with open(file_name,'r') as f:
        datastore = json.load(f)
        return json.loads(datastore)

def initialize_data(datastore):
    player_list = collections.defaultdict(int)
    teams = collections.defaultdict(dict)
    colors = ['red','blue']
    for color in colors:
        teams[color]['team_name'] = datastore[color]
        teams[color]['teamID'] = datastore[color+"TeamID"]
        player_names = datastore[color+'names']
        player_ids = datastore[color+'IDs']
        players = []
        for i in range(6):
            player_name = player_names[i]
            player_id = player_ids[i]
            players += [(player_name,player_id)]
        teams[color]['players'] = players
        teams[color]['characters'] = [None] * 6
        teams[color]['playtime'] = collections.defaultdict(int)
    return teams

def update_playtime(teams,color, player_id, current_time):
    old_character, old_time = teams[color]['characters'][player_id]
    teams[color]['playtime'][old_character] += current_time - old_time
    

def go_through_match(teams,events):
    start = 0
    end = 0
    for event in events:
        time = event[0]
        event_type = event[1]
        if event_type == 'MATCH':
            start = event[0]
        elif event_type == 'END':
            end = event[0]
        elif event_type == 'UNPAUSE' or event_type == 'PAUSE':
            continue
        else:
            player_position = int(event[3])  - 1
            color = event[2].lower()
            if event_type == 'SWITCH':
                second_character = event[5]
                print (teams[color]['characters'],color)
                if teams[color]['characters'][player_position] != None:
                    update_playtime(teams, color, player_position, time)
                teams[color]['characters'][player_position] = (second_character,time)
    print(teams['red']['characters'])
    for color in teams:
        for player_position in range(0,6):  
            update_playtime(teams,color, player_position, end)
        print(teams[color]['playtime'],teams[color]['team_name'])
    print(end - start)

                    

if __name__ == "__main__":
    current_id = 2405
    max_id = 2406
    game_number = 1
    round_number = 1
    json_file = get_json_file(current_id,game_number,round_number)
    teams = initialize_data(json_file)
    go_through_match(teams,json_file["events"])
    

    



