import json
import time
import collections
import datetime
import matplotlib.pyplot as plt
from pathlib import Path
from enum import Enum
import re
Character = collections.namedtuple('character', 'player time')


class TeamColor(Enum):
    RED = "red"
    BLUE = "blue"


class TeamElements(Enum):
    TEAM_NAME = 0
    TEAM_ID = 1
    PLAYERS = 2
    CHARACTERS = 3
    PLAYTIME = 4


class AttackPhase(Enum):
    RED = "Attack - Red"
    BLUE = "Attack - Blue"


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
Initialize the blue and red teams and their players for go_through_match.
Players and Teams happen to have unique IDS.
'''


def initialize_data(datastore):
    player_list = collections.defaultdict(int)
    teams = collections.defaultdict(dict)
    colors = [TeamColor.RED, TeamColor.BLUE]
    for color in colors:
        teams[color][TeamElements.TEAM_NAME] = datastore[color.value]
        teams[color][TeamElements.TEAM_ID] = datastore["{0}TeamID".format(
            color.value)]
        player_names = datastore['{0}names'.format(color.value)]
        player_ids = datastore['{0}IDs'.format(color.value)]
        players = []
        for i in range(6):
            player_name = player_names[i]
            player_id = player_ids[i]
            players += [(player_name, player_id)]
        teams[color][TeamElements.PLAYERS] = players
        teams[color][TeamElements.CHARACTERS] = [None] * 6
        teams[color][TeamElements.PLAYTIME] = collections.defaultdict(int)
    return teams


def update_playtime(teams, color, player_id, current_time):
    old_character, old_time = teams[color][TeamElements.CHARACTERS][player_id]
    teams[color][TeamElements.PLAYTIME][old_character] += current_time - old_time


'''
Return the point captures for a specific map and round.
'''


def point_captures(json_file):
    return json_file["pointA"], json_file["pointB"], json_file["pointC"]


'''
Cycle through the match and define the teams, finding out pickrate, kills, and deaths.

'''


def go_through_match(teams, events):
    start = 0
    end = 0
    for event in events:
        time = event[0]
        event_type = event[1]
        if event_type == 'MATCH':
            start = event[0]
        elif event_type == 'END':
            end = event[0]
        elif event_type in ['UNPAUSE', 'PAUSE']:
            continue
        else:
            player_position = int(event[3]) - 1
            color = TeamColor(event[2].lower())
            if event_type == 'SWITCH':
                second_character = event[5]
                if teams[color][TeamElements.CHARACTERS][player_position] is not None:
                    update_playtime(teams, color, player_position, time)
                teams[color][TeamElements.CHARACTERS][player_position] = (
                    second_character, time)
    for color in teams:
        for player_position in range(0, 6):
            update_playtime(teams, color, player_position, end)
    return teams, end - start


def get_player_percentages_by_maps(game_stats):
    for teams, time, map_name, captures, phase in game_stats:
        values = [item.value for item in AttackPhase]
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
            for character in teams[color][TeamElements.PLAYTIME]:
                map_playtime[map_name][category][character] += teams[color][TeamElements.PLAYTIME][character]
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


if __name__ == "__main__":
    current_id = 2405
    max_id = 2417
    attack_phases = get_attack_phases()
    game_stats = []
    game_number = 1
    round_number = 1
    while current_id < max_id:
        json_file = get_json_file(current_id, game_number, round_number)
        if json_file is None:
            game_number += 1
            round_number = 1
            if game_number > 5:
                game_number = 1
                current_id += 1
            continue
        phase = attack_phases[str(current_id)][str(
            game_number)][round_number - 1]
        print(game_number, round_number, phase)
        teams = initialize_data(json_file)
        teams, time = go_through_match(teams, json_file["events"])
        map_name = json_file['mapPic']
        map_name = re.search(
            '\/pics\/maps\/(.*)_trans.(?:jpg|png)',
            map_name).group(1)
        captures = point_captures(json_file)
        phase = attack_phases[str(current_id)][str(
            game_number)][round_number - 1]
        game_stats.append((teams, time, map_name, captures, phase))
        round_number += 1
    map_playtime = {}
    get_player_percentages_by_maps(game_stats)
