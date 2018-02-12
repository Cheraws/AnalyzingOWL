import json
import time
import collections
import datetime
import matplotlib.pyplot as plt
from pathlib import Path
from enum import Enum
import re
from Player import Player
import csv
import datetime
import pandas

Character = collections.namedtuple('character', 'player time')
Kill = collections.namedtuple('kill', 'killer_character killer_player killed_character killed_player color opposite_color time count')
Ult = collections.namedtuple('ult', 'time character user color count')
Teamfight = collections.namedtuple('teamfight', 'kills ults')
ult_durations = {
    "genji": (1,6),
    "zenyatta": (0,6),
    "mercy": (0,20)
}

class TeamColor(Enum):
    RED = "red"
    BLUE = "blue"
    
    def return_opposite_color(self):
        if self.name == "RED":
            return TeamColor["BLUE"]
        if self.name == "BLUE":
            return TeamColor["RED"]


class TeamElements(Enum):
    TEAM_NAME = 0
    TEAM_ID = 1
    PLAYERS = 2
    CHARACTERS = 3
    PLAYTIME = 4

class GameInfo(Enum):
    TIME = 0
    TEAMFIGHTS = 1
    KILLS = 2
    ULTS = 3
    MAP = 4
    PHASES = 5
    MATCH_NUMBER = 6
    MAP_NUMBER = 7
    ROUND_NUMBER = 8

class AttackPhase(Enum):
    RED = "Attack - Red"
    BLUE = "Attack - Blue"


def kill_action(event, game_info,time,count):
    color = TeamColor(event[2].lower())
    opposite_color = color.return_opposite_color()
    killer_position = int(event[3]) - 1
    killed_position = int(event[5]) - 1
    killer_character = event[4]
    killed_character = event[6]
    killer_player = game_info[color][TeamElements.PLAYERS][killer_position]
    killed_player = game_info[opposite_color][TeamElements.PLAYERS][killed_position]
    return Kill(killer_character,killer_player,killed_character,killed_player,color,opposite_color,time,count)

def time_converter(start, current_time):
    return str(datetime.timedelta(seconds=(current_time - start)))


def get_json_file(current_id, game_number, round_number):
    file_name = "game_data/{0}_{1}_{2}.json".format(
        current_id, game_number, round_number)
    f = Path(file_name)
    if not f.is_file():
        return None
    with open(file_name, 'r') as f:
        datastore = json.load(f)
        if len(datastore) == 0:
            return None
        return json.loads(datastore)


def get_attack_phases():
    file_name = "game_data/attack_phases.json"
    with open(file_name, 'r') as f:
        datastore = json.load(f)
        if len(datastore) == 0:
            return None
        return json.loads(datastore)


'''
Initialize the blue and red game_info and their players for go_through_match.
Players and Teams happen to have unique IDS.
'''


def initialize_data(datastore,player_info):
    player_list = collections.defaultdict(int)
    game_info = collections.defaultdict(dict)
    colors = [TeamColor.RED, TeamColor.BLUE]
    for color in colors:
        game_info[color][TeamElements.TEAM_NAME] = datastore[color.value]
        game_info[color][TeamElements.TEAM_ID] = datastore["{0}TeamID".format(
            color.value)]
        player_names = datastore['{0}names'.format(color.value)]
        player_ids = datastore['{0}IDs'.format(color.value)]
        players = []
        for i in range(6):
            player_name = player_names[i].lower()
            player_id = player_ids[i]
            players += [(player_name, player_id)]
        game_info[color][TeamElements.PLAYERS] = players
        game_info[color][TeamElements.CHARACTERS] = [None] * 6
        game_info[color][TeamElements.PLAYTIME] = collections.defaultdict(int)
    initialize_players(game_info,player_info)
    game_info[GameInfo.ULTS] = []
    return game_info, player_info


def update_playtime(game_info, color, player_id, current_time,player_info):
    old_character, old_time = game_info[color][TeamElements.CHARACTERS][player_id]
    player_id = game_info[color][TeamElements.PLAYERS][player_id][1]
    player_info[player_id].update_playtime(current_time - old_time,old_character)
    game_info[color][TeamElements.PLAYTIME][old_character] += current_time - old_time



'''
Return the point captures for a specific map and round.
'''


def point_captures(json_file):
    return json_file["pointA"], json_file["pointB"], json_file["pointC"]


'''
Cycle through the match and define the game_info, finding out pickrate, kills, and deaths.

'''

def check_teamfight(game_info, kills,ults,time):
    return None

def time_converter(time):
    return str(datetime.timedelta(seconds=(time)))

def go_through_match(game_info, events):
    start = 0
    end = 0
    kills = []
    ults = []
    kills_and_ults = []
    teamfights = []
    teamfight_now = False
    last_kill = 0
    pause_time = 0
    count = 0
    ult_number = 0
    for event in events:
        time = event[0] - start
        event_type = event[1]
        count += 1
        if teamfight_now:
            if time - last_kill > 13:
                teamfight_now = False
                teamfight = Teamfight(kills,ults)
                teamfights.append(teamfight)
                game_info[GameInfo.ULTS] += (ults)
                kills,ults = [],[]
        if event_type == 'MATCH':
            start = event[0]
        elif event_type == 'END':
            end = event[0] - start
        elif event_type in 'UNPAUSE':
            pause_start = time
        elif event_type == 'PAUSE':
            start += (time - pause_time)
        else:
            player_position = int(event[3]) - 1
            color = TeamColor(event[2].lower())
            first_character = event[4]
            if event_type == 'SWITCH':
                second_character = event[5]
                if game_info[color][TeamElements.CHARACTERS][player_position] is not None:
                    update_playtime(game_info, color, player_position, time,player_info)
                game_info[color][TeamElements.CHARACTERS][player_position] = (
                    second_character, time)
            if event_type == 'KILL':
                teamfight_now = True
                last_kill = time
                kill = kill_action(event,game_info,time,count)
                kills.append(kill)
            elif event[1] == "ULT_USE":
                ult_user = game_info[color][TeamElements.PLAYERS][player_position]
                ult = Ult(time,first_character,ult_user, color,count)
                ults.append(ult)
                ult_number += 1
    #update times when game actually changes
    for color in TeamColor:
        for player_position in range(0, 6):
            update_playtime(game_info, color, player_position, end,player_info)
    if len(kills) > 0:
            teamfight = Teamfight(kills,ults)
            teamfights.append(teamfight)
            
    game_info[GameInfo.ULTS] += ults
    game_info[GameInfo.TIME] = end 
    game_info[GameInfo.TEAMFIGHTS] = teamfights
    return game_info


def get_player_percentages_by_maps(game_stats):
    for game in game_stats:
        print(game)
        phase = game[GameInfo.PHASES]
        values = [item.value for item in AttackPhase]
        map_name = game[GameInfo.MAP]
        time = game[GameInfo.TIME]
        print("time is {0}".format(time))
        attackingColor = None
        if phase in values:
            attackingColor = TeamColor[AttackPhase(phase).name]
        if map_name not in map_playtime:
            map_playtime[map_name] = collections.defaultdict(dict)
        for color in TeamColor:
            if attackingColor is not None:
                if color == attackingColor:
                    category = 'attack'
                else:
                    category = 'defense'
            else:
                category = phase
            if category not in map_playtime[map_name]:
                map_playtime[map_name][category] = collections.defaultdict(int)
            map_playtime[map_name][category]['total'] += time
            for character in game_info[color][TeamElements.PLAYTIME]:
                map_playtime[map_name][category][character] += game_info[color][TeamElements.PLAYTIME][character]
    for map_name in map_playtime:
        for category, playtimes in map_playtime[map_name].items():
            percentages = {}
            for key in sorted(playtimes):
                if key == "total":
                    continue
                else:
                    percentage = playtimes[key] / playtimes['total'] * 100
                    percentages[key] = percentage
            plot_play_percentage(percentages, map_name, category)

def show_kills_deaths(game_stats):
    players = {}
    for game_info, time, map_name, captures, phase,kills in game_stats:
        initialize_players(game_info,players)
        for kill in kills:
            killer_color = kill.color
            killed_color = kill.opposite_color
            killer_team = game_info[killer_color][TeamElements.TEAM_NAME]
            killed_team = game_info[killed_color][TeamElements.TEAM_NAME]
            killed_player, killed_id = kill.killed_player
            killer_player, killer_id = kill.killer_player
            killed_character = kill.killed_character
            killer_character = kill.killer_character
            players[killer_id].add_kill(killer_character,killed_character)
            players[killed_id].add_death(killer_character,killed_character)
    plot_kill_death_by_character(players, "tracer","tracer")



def initialize_players(game_info,player_list):
    for color in TeamColor:
        players = game_info[color][TeamElements.PLAYERS]
        player_team = game_info[color][TeamElements.TEAM_NAME]
        for player_name, player_id in players:
            if player_id not in player_list:
                player_list[player_id] = Player(player_name,player_id,player_team)


def plot_kill_death_by_character(players,own_character, opposing_character):
    x_axis = []
    y_axis = []
    graph_data = dict()
    for player_id, player in players.items():
        kills, deaths = 0 , 0
        played = False
        if own_character in player.kills:
            played = True
            kills = player.kills[own_character][opposing_character]
        if own_character in player.deaths:
            played = True
            deaths = player.deaths[own_character][opposing_character]
        if deaths == 0:
            deaths = 1
        if played == True:
            graph_data[player.player_name] = kills/deaths
    
    for w in sorted(graph_data, key=graph_data.get, reverse=True):
        x_axis += [w]
        y_axis += [graph_data[w]]
    print(x_axis)
    plt.bar(range(len(y_axis)), list(y_axis), align='center')
    plt.xticks(range(len(x_axis)), list(x_axis))
    plt.xticks(rotation=90)
    plt.title("KD ratio as {0} vs {1}".format(own_character, opposing_character))
    plt.ylabel("KD ratio")
    plt.tight_layout()
    plt.show()

            
'''
Gather what an ult accomplishes within the duration of a teamfight. 
The categories are Kills, kill plus/minus, lifespan, and opposing ults used.
'''
def create_ult_csv(character, d):
    return None


'''
Plot the graph for team comps or usage percentage
'''


def plot_play_percentage(d, map_name, category):
    x_axis = []
    y_axis = []
    error = []
    for w in sorted(d, key=d.get, reverse=True):
        x_axis += [w]
        y_axis += [d[w]]
    print(x_axis)
    plt.bar(range(len(y_axis)), list(y_axis), align='center')
    plt.xticks(range(len(x_axis)), list(x_axis))
    plt.xticks(rotation=90)
    plt.title("Play percentage on {0} at phase {1}".format(map_name, category))
    plt.ylabel("percentage")
    plt.tight_layout()
    plt.show()

def create_playtime_csv(player_info):
    csv_categories = ["player_name","team", "hero", "time_played"]
    myData = [csv_categories]
    for player_id, player in player_info.items():
        (player.playtime,player.player_name)
        for character,value in player.playtime.items():
            row = []
            row.append(player.player_name)
            row.append(player.team)
            row.append(character)
            row.append(value)
            myData += [row]
    myFile = open("data.csv","w")
    with myFile:
        writer = csv.writer(myFile)
        writer.writerows(myData)
    
'''
Adds info about map_name, captures, game_info
'''
def add_miscellaneous(gameInfo, json_file,game_number,round_number,match_number):
    map_name = json_file['mapPic']
    map_name = re.search(
        '\/pics\/maps\/(.*)_trans.(?:jpg|png)',
        map_name).group(1)
    captures = point_captures(json_file)
    phase = attack_phases[str(current_id)][str(
        game_number)][round_number - 1]
    gameInfo[GameInfo.MAP] = map_name
    gameInfo[GameInfo.PHASES] = phase
    gameInfo[GameInfo.ROUND_NUMBER] = round_number
    gameInfo[GameInfo.ROUND_NUMBER] = match_number


'''
Gather info about who won teamfights, etc.

'''
def teamfight_analysis(game):
    ult_stats = collections.defaultdict(list)
    for game in games:
        prev_ults = []
        ults = game[GameInfo.ULTS]
        ult_count = 0
        ults_by_color = {key: dict() for key in TeamColor}
        for teamfight in game[GameInfo.TEAMFIGHTS]:
            current_ults = {}
            ults_in_fight = 0
            kills_by_color = collections.defaultdict(int)
            kills = teamfight.kills
            first_kill = kills[0]
            time = first_kill.time
            #process ults used before a fight.
            while ult_count < len(ults):
                ult = ults[ult_count]
                if ult.count < first_kill.count:
                    #ult in teamfight
                    if first_kill.time - ult.time <= 12:
                        break
                    else:
                        ult_count += 1
                else:
                    break
            #process ults until it's after fight
            kill_in_fight = 0
            while kill_in_fight < len(kills):
                if ult_count < len(ults):
                    ult = ults[ult_count]
                else:
                    ult = None
                kill = kills[kill_in_fight]
                if ult != None and ult.count < kill.count:
                    color = ult.color
                    time = ult.time
                    character = ult.character
                    opposite_color = TeamColor.return_opposite_color(color)
                    plus_minus = generate_plus_minus(color,kills_by_color)
                    check_if_ult_finished(kills_by_color,current_ults,ult_stats,time)
                    ults_in_fight += 1
                    ults_by_color[color][character] = ult.user
                    if ult.character == "genji":
                        current_ults[ult.user] = [0,0,plus_minus,time,color]
                    ult_count += 1
                else:
                    time = kill.time
                    check_if_ult_finished(kills_by_color,current_ults,ult_stats,time)
                    color = kill.color
                    kills_by_color[color] += 1
                    kill_in_fight += 1
                    #for now this means genji player died in ult
                    if kill.killed_player in current_ults:
                        calculate_ult_stat(kill.killed_player,kills_by_color,current_ults,ult_stats,time)
                    if kill.killer_player in current_ults:
                        current_ults[kill.killer_player][0] += 1
            check_if_ult_finished(kills_by_color,current_ults,ult_stats,time, finished= True)
            print(ults_by_color)
            #print (ult_stats)
            #print(kills_by_color)
            #print("ults in teamfight is {0}".format(ults_in_fight))
    print(len(ult_stats))
    create_ult_csv(ult_stats)

def create_ult_csv(ult_stats):
    csv_categories = ["player_name","kills","plus/minus"]
    myData = [csv_categories]
    for player_stat, ult_stats in ult_stats.items():
        player_name = player_stat[0]
        print(player_stat)
        for ult_stat in ult_stats:
            row = []
            kills = ult_stat[0]
            plus_minus = ult_stat[2]
            row.append(player_name)
            row.append(kills)
            row.append(plus_minus)
            myData += [row]
    myFile = open("ults.csv","w")
    with myFile:
        writer = csv.writer(myFile)
        writer.writerows(myData)
    myFile = open("ults.csv","r")
    df = pandas.read_csv(myFile)
   


def check_if_ult_finished(kills_by_color,current_ults,ult_stats,time,finished = False):
    iterating_ults = dict(current_ults)
    for player,stats in iterating_ults.items():
        old_time = stats[3]
        finish_time = time
        if time - old_time > 7 or finished:
            if not finished:
                finish_time = old_time + 7
            calculate_ult_stat(player,kills_by_color,current_ults,ult_stats,finish_time)

def calculate_ult_stat(player,kills_by_color,current_ults,ult_stats,time):
    old_plus_minus = current_ults[player][2]
    color = current_ults[player][4]
    ult_kills = current_ults[player][0]
    old_time = current_ults[player][3]
    plus_minus_difference = generate_plus_minus(color,kills_by_color) - old_plus_minus
    current_ults[player][1] = plus_minus_difference
    ult_stat = [ult_kills, old_plus_minus,plus_minus_difference, old_time,time]
    ult_stats[player].append(ult_stat)
    del current_ults[player]

    


def generate_plus_minus(color,kills_by_color):
    return kills_by_color[color] - kills_by_color[TeamColor.return_opposite_color(color)]

def generate_elims(current_kills_by_color,kills_by_color,color):
    return current_kills_by_color[color] - kills_by_color[color]
            


if __name__ == "__main__":
    current_id = 2375
    max_id = 2452
    attack_phases = get_attack_phases()
    games = []
    game_number = 1
    round_number = 1
    player_info = {}
    match_number = 1
    while current_id < max_id:
        json_file = get_json_file(current_id, game_number, round_number)
        if json_file is None:
            game_number += 1
            round_number = 1
            if game_number > 5:
                game_number = 1
                current_id += 1
            continue
        else:
            if game_number == 1 and round_number == 1:
                match_number += 1
        phase = attack_phases[str(current_id)][str(
            game_number)][round_number - 1]
        #print(game_number, round_number, phase)
        game_info,player_info = initialize_data(json_file,player_info)
        game_info = go_through_match(game_info, json_file["events"])
        add_miscellaneous(game_info, json_file, game_number,round_number,match_number)
        games.append(game_info)
        round_number += 1
    map_playtime = {}
    teamfight_analysis(games)
    print("match number is {0}".format(match_number))
    #show_kills_deaths(game_stats)
    #create_playtime_csv(player_info)
    #get_player_percentages_by_maps(game_stats)
