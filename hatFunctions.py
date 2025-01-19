"""Backend logic for AutoHat app"""

# Built in libraries
import datetime as dt
from enum import Enum
import math
import os
import random as rd
from typing import List

# Third party libraries
import pandas as pd
import numpy as np


class SkillLevel:
    def __init__(self, level: int, text: str):
        self.level = level
        self.text = text


class Gender(Enum):
    MALE = 'male'
    FEMALE = 'female'


class Throws(Enum):
    NOOB = SkillLevel(1, "I've thrown a frisbee before.")
    COMPETENT = SkillLevel(2, "I can throw a forehand and backhand, even if they're occasionally wobbly.")
    PRO = SkillLevel(3, "Accurate with standard throws; I know what IO and OI mean.")
    SCOOBER_GOD = SkillLevel(4, "All the throws; I will destroy you with my full-field scoobers.")


class Experience(Enum):
    ROOKIE = SkillLevel(1, "Rookie")
    PICKUP = SkillLevel(2, "Pickup player")
    CLUB = SkillLevel(3, "Club (Sectionals) / Masters (Nationals) / High School (State / Nationals)")
    PRO = SkillLevel(4, "Club player (Regionals / Nationals)")


class Athletics(Enum):
    UNFIT = SkillLevel(1, "Out of shape; mostly I'm here to heckle.")
    FIT = SkillLevel(2, "Athletic; just don't make me play savage.")
    FAST = SkillLevel(3, "Very athletic; my two settings are Sprint and Horizontal.")


def skill_match(text: str, enum_type) -> Enum:
    for enum in enum_type:
        if enum.value.text == text:
            return enum.value.level
    
    return 0


class Player:
    def __init__(self, name: str, gender: Gender, rank: int):
        self.name = name
        self.gender = gender
        self.rank = rank

    def __lt__(self, other):
         return self.rank < other.rank

    def to_dict(self):
        return {
            'name': self.name,
            'gender': self.gender,
            'rank': self.rank,
        }


def import_roster(filepath):
    df = pd.read_csv(filepath)
    df['throws'] = df['throws'].apply(skill_match, args=(Throws,))
    df['experience'] = df['experience'].apply(skill_match, args=(Experience,))
    df['athleticism'] = df['athleticism'].apply(skill_match, args=(Athletics,))
    df['name'] = df['first_name'] + ' ' + df['last_name']
    df['rank'] = df['throws'] + df['experience'] + df['athleticism']
    product = df.columns[-3]
    df.drop(columns=['first_name', 'last_name', product], inplace=True)
    names = df.pop('name').str.title()
    df.insert(0, 'name', names)
    return df


def launch_checkin(data_in_path):
    raw_data = import_roster(data_in_path)
    raw_data.sort_values(by=['name'], ascending=True, inplace=True)
    raw_data.reset_index(drop=True, inplace=True)
    return raw_data


def calc_means(roster: List[Player]):
    return sum(p.rank for p in roster) / len(roster)


def assign_players(mean_rank, roster, teams, num_teams, team_index: int = 0) -> int:
    while roster.shape[0] > 0:
        if roster.shape[0] == 1:
            player = roster.iloc[0]
            roster.drop(index=roster.index[0], inplace=True)
            roster.reset_index(drop=True, inplace=True)
        else:
            if teams[team_index].loc['rank'].mean() < mean_rank:
                player = pop_random_player(roster, math.ceil(roster.shape[0] / 2), roster.shape[0] - 1)
            else:
                player = pop_random_player(roster, 0, math.floor(roster.shape[0] / 2))
        teams[team_index] = pd.concat([teams[team_index], player], axis=1)

        team_index = (team_index + 1) % num_teams
    
    return team_index


def pop_random_player(roster):
    if len(roster) == 1:
        return roster.pop(0)
    return roster.pop(rd.randint(0, len(roster) - 1))


# Add players one by one to build a dataframe of drop-in players. Only rank is enumerated,
# all other scores are given a value of NaN to indicate that the value isn't known
def add_drop_in(drop_in_df, name, gender, rank):
    drop_in_player = {'name': [name.title()], 'gender': [gender],
                      'throws': [np.nan], 'experience': [np.nan],
                       'athleticism': [np.nan], 'rank': [int(rank)]}
    if drop_in_df.empty:
        drop_in_df = pd.DataFrame(drop_in_player)
    else:
        drop_in_df = pd.concat([drop_in_df, pd.DataFrame(drop_in_player)], axis=0, ignore_index=True)
    return drop_in_df


def generate_teams(raw_data, save_directory, num_teams):
    teams = []
    players = [Player(name, Gender(gender), rank) for name, gender, rank in zip(raw_data['name'], raw_data['gender'], raw_data['rank'])]
    mean_rank = calc_means(players)

    # Split the roster into rosters of men and women
    men = [p for p in players if p.gender == Gender.MALE]
    women = [p for p in players if p.gender == Gender.FEMALE]

    men.sort(reverse=True)
    women.sort(reverse=True)

    # Add a top-ranked player to each team from the men's roster
    for _ in range(num_teams):
        teams.append([men.pop(0)])

    # Add a random player to each team from the men's roster
    for i in range(num_teams):
        teams[i].append(pop_random_player(men))

    # Add male players to the teams based on how team rankings compare to the average rank
    team_index = assign_players(mean_rank, men, teams, num_teams)

    # Add female players to the teams based on how team rankings compare to the average rank
    team_index = assign_players(mean_rank, women, teams, num_teams, team_index)

    # Transpose the teams and add a row that averages all values to include in the output
    final_teams = []
    for team in teams:
        team_df = pd.DataFrame.from_records(p.to_dict() for p in team)
        averages = pd.DataFrame({'name': ['AVERAGE:'], 'gender': [''], 'rank': [calc_means(team)]})
        final_teams.append(pd.concat([team_df, averages]))

    timestamp = dt.datetime.now().strftime('%m-%d-%Y_%H-%M-%S')
    save_path = os.path.join(save_directory, f'teams_{timestamp}.xlsx')

    # Write the excel file
    with pd.ExcelWriter(save_path, engine='xlsxwriter') as writer:
        offset = 0
        for team in final_teams:
            team.to_excel(writer, sheet_name='Sheet1', startrow=offset, index=False)
            offset += len(team) + 4
