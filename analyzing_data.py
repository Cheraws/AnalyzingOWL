import json
import time
import collections
import datetime
import matplotlib.pyplot as plt
from pathlib import Path
from enum import Enum
import re
from Player import Player,UltimateData
import csv
import datetime
import pandas

Character = collections.namedtuple('character', 'player time')
Kill = collections.namedtuple('kill', 'killer_character killer_player killed_character killed_player color opposite_color time count')
Ult = collections.namedtuple('ult', 'time character user color count hold_time')
Teamfight = collections.namedtuple('teamfight', 'kills ults')
TeamComp = collections.namedtuple('teamcomp', 'character_list start end')
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
    TEAM_COMPS = 5

class GameInfo(Enum):
    TIME = 0
    TEAMFIGHTS = 1
    KILLS = 2
    ULTS = 3
    MAP = 4
    PHASES = 5
    MATCH_NUMBER = 6
    GAME_NUMBER = 7
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
        game_info[color][TeamElements.TEAM_COMPS] = []
        game_info[color][TeamElements.PLAYTIME] = collections.defaultdict(int)
    initialize_players(game_info,player_info)
    game_info[GameInfo.ULTS] = []
    return game_info, player_info


def update_playtime(game_info, color, player_id, current_time,player_info):
    comps = game_info[color][TeamElements.TEAM_COMPS]
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
    count = -1
    ult_number = 0
    ults_gained = dict()
    for event in events:
        time = event[0] - start
        event_type = event[1]
        count += 1
        if teamfight_now:
            if time - last_kill > 14:
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
            ult_user = game_info[color][TeamElements.PLAYERS][player_position]
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
                ult = Ult(time,first_character,ult_user, color,count,"")
                if ult_user in ults_gained:
                    if ults_gained[ult_user] != None:
                        charged_character, old_time = ults_gained[ult_user]
                        if charged_character == first_character:
                            hold_time = time - old_time
                            ult = Ult(time,first_character,ult_user, color,count,hold_time)
                        ults_gained[ult_user] = None
                ults.append(ult)
                ult_number += 1
            elif event[1] == "ULT_GAIN":
                ults_gained[ult_user] = (first_character,time)
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


'''
Pinpoint the exact place where the glitch happens to be reported.
'''
def get_map_info(game_info,time,events):
    game_number = game_info[GameInfo.GAME_NUMBER] 
    round_number = game_info[GameInfo.ROUND_NUMBER] 
    match_number = game_info[GameInfo.MATCH_NUMBER] 
    start = events[0][0]
    for ult in game_info[GameInfo.ULTS]:
        print(events[ult.count])
        print(events[ult.hold_time])
        print(events[ult.hold_time][0] - start)
    print("error occured at game {0} round {1} match {2} at {3}".format(
        game_number,round_number,match_number,time
        ))
   

'''
Record playtime on eachmap. First check map name then phase. Control
maps are split by stage, while other types are split by attack and
defense.
'''
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
    csv_categories = ["player_name","team", "character", "time_played"]
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

    gameInfo[GameInfo.GAME_NUMBER] = game_number
    gameInfo[GameInfo.ROUND_NUMBER] = round_number
    gameInfo[GameInfo.MATCH_NUMBER] = match_number


'''
Gather info about who won teamfights, etc.

'''
def teamfight_analysis(game):
    overall_ult_stats = collections.defaultdict(list)
    multi_ults = 0
    for game in games:
        prev_ults = []
        ults = game[GameInfo.ULTS]
        ult_count = 0
        for teamfight in game[GameInfo.TEAMFIGHTS]:
            ult_stats = collections.defaultdict(list)
            ults_by_color = {key: dict() for key in TeamColor}
            current_ults = {}
            ults_in_fight = 0
            kills_by_color = {key: 0 for key in TeamColor}
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
                    check_if_ult_finished(kills_by_color,current_ults,ult_stats,time,ults_by_color)
                    opposite_color = TeamColor.return_opposite_color(color)
                    ults_in_fight += 1
                    ults_by_color[color][character] = ult.user
                    ultimate_data = UltimateData(ult.user,
                            color,
                            character,
                            kills_by_color,
                            time,
                            game[GameInfo.GAME_NUMBER],
                            game[GameInfo.ROUND_NUMBER],
                            game[GameInfo.MATCH_NUMBER])
                    ultimate_data.ult_held = ult.hold_time
                    if ult.character in UltimateData.ult_times:
                        current_ults[ult.user] = ultimate_data
                        if ult.character == "zenyatta" :
                            if "genji" in  ults_by_color[opposite_color]:
                                genji_player = ults_by_color[opposite_color]["genji"]
                                current_ults[genji_player].other_ults.add(ult.character)                    
                        if ult.character == "genji":
                            for hero in ults_by_color[opposite_color]:
                                if hero == "zenyatta":
                                    #print("genji blades at {0}".format(time))
                                    zen = ults_by_color[opposite_color][hero]
                                    zen = current_ults[zen]
                                    #print("zen ults at {0}".format(zen.start_time))
                                    if time - zen.start_time <= 1:
                                        current_ults[ult.user].other_ults.add(hero)
                    ult_count += 1
                else:
                    time = kill.time
                    character = kill.killer_character
                    check_if_ult_finished(kills_by_color,current_ults,ult_stats,time,ults_by_color)
                    color = kill.color
                    kills_by_color[color] += 1
                    kill_in_fight += 1
                    if kill.killed_player in current_ults:
                        calculate_ult_stat(kill.killed_player,kills_by_color,current_ults,ult_stats,time,ults_by_color,killer_character = character)
                    if kill.killer_player in current_ults:
                        current_ults[kill.killer_player].kills += 1
            check_if_ult_finished(kills_by_color,current_ults,ult_stats,time,ults_by_color, finished= True)
            for player,ultimates in ult_stats.items():
                if len(ultimates) >= 2:
                    multi_ults += 1
                characters = set()
                for ultimate in ultimates:
                    if ultimate.character not in characters:
                        ultimate.teamfight_won = won_teamfight(kills_by_color,ultimate.color)
                        characters.add(ultimate.character)
                overall_ult_stats[player] += ultimates
            #print("ults in teamfight is {0}".format(ults_in_fight))

    print(len(overall_ult_stats))
    #print("Number of times a person ulted multiple times is {0}".format(multi_ults))
    create_ult_csv(overall_ult_stats)

'''

'''
def won_teamfight(kills_by_color, color):
    opposite_color = TeamColor.return_opposite_color(color)
    return int(kills_by_color[color] > kills_by_color[opposite_color])

'''
If player didn't die here, make sure to mark ult as finished after time is up.
'''
def check_if_ult_finished(kills_by_color,current_ults,ult_stats,time,ults_by_color,finished = False):
    iterating_ults = dict(current_ults)
    for player,stat in iterating_ults.items():
        if stat.ult_over(time) or finished:
            end_time = stat.start_time + stat.full_ult_time()
            calculate_ult_stat(player,kills_by_color,current_ults,ult_stats,end_time,ults_by_color)

def calculate_ult_stat(player,kills_by_color,current_ults,ult_stats,time,ults_by_color,killer_character = ""):
    ultimate_data = current_ults[player]
    old_kills_by_color = ultimate_data.kills_by_color
    color = ultimate_data.color
    ult_kills = ultimate_data.kills
    old_time = ultimate_data.start_time
    character = ultimate_data.character
    plus_minus_difference = generate_plus_minus(color,kills_by_color) - generate_plus_minus(color,old_kills_by_color)
    ultimate_data.elims = generate_elims(kills_by_color,old_kills_by_color,color) 
    ultimate_data.end_time = time
    ultimate_data.killed_by = killer_character
    ult_stats[player].append(ultimate_data)
    del current_ults[player]
    del ults_by_color[color][character]

'''
Creates the csv that stores data about ults. Currently focusing on genji.
'''
def create_ult_csv(ult_stats):
    csv_categories = ["player_name",
            "character",
            "kills",
            "elims",
            "ult time", 
            "start_time" ,
            "zen ult",
            "mercy ult",
            "game_number",
            "round_number",
            "match_number",
            "ult_held",
            "killed_by",
            "teamfight_won"
            ]
    myData = [csv_categories]
    for player_stat, ult_stats in ult_stats.items():
        player_name = player_stat[0]
        #print(player_stat)
        for ult_stat in ult_stats:
            if ult_stat.character != "genji":
                continue
            row = []
            kills = ult_stat.kills
            elims = ult_stat.elims
            ult_time = ult_stat.ult_time()
            row.append(player_name)
            row.append(ult_stat.character)
            row.append(kills)
            row.append(elims)
            row.append(ult_time)
            row.append(ult_stat.start_time)
            if "zenyatta" in ult_stat.other_ults:
                row.append(True)
            else:
                row.append(False)
            if "mercy" in ult_stat.other_ults:
                row.append(True)
            else:
                row.append(False)
            row.append(ult_stat.game_number)
            row.append(ult_stat.round_number)
            row.append(ult_stat.match_number)
            row.append(ult_stat.ult_held)
            row.append(ult_stat.killed_by)
            row.append(ult_stat.teamfight_won)
            myData += [row]
    myFile = open("ults.csv","w")
    with myFile:
        writer = csv.writer(myFile)
        writer.writerows(myData)
    myFile = open("ults.csv","r")
    df = pandas.read_csv(myFile)
      


def generate_plus_minus(color,kills_by_color):
    return kills_by_color[color] - kills_by_color[TeamColor.return_opposite_color(color)]

def generate_elims(current_kills_by_color,kills_by_color,color):
    return current_kills_by_color[color] - kills_by_color[color]
            


if __name__ == "__main__":
    current_id = 2375
    max_id = 2453
    attack_phases = get_attack_phases()
    games = []
    game_number = 1
    round_number = 1
    player_info = {}
    match_number = 0
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
        game_info,player_info = initialize_data(json_file,player_info)
        if current_id == 2399 and game_number == 2:
            if round_number != 1:
                add_miscellaneous(game_info,json_file,game_number,round_number-1,match_number)
            else:
                print("round number has an issue")
                round_number += 1
                continue
            round_number += 1
        else:
            add_miscellaneous(game_info, json_file, game_number,round_number,match_number)
        game_info = go_through_match(game_info, json_file["events"])
        games.append(game_info)
        round_number += 1
    map_playtime = {}
    teamfight_analysis(games)
    print("match number is {0}".format(match_number))
    #show_kills_deaths(game_stats)
    create_playtime_csv(player_info)
    #get_player_percentages_by_maps(game_stats)
