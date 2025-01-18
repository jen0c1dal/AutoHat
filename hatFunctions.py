"""Backend logic for AutoHat app"""

# Built in libraries
import datetime as dt
from enum import Enum
import math
import os
import random as rd

# Third party libraries
import pandas as pd
import numpy as np


class SkillLevel:
    def __init__(self, level: int, text: str):
        self.level = level
        self.text = text


class Gender(Enum):
    MALE = 1
    FEMALE = 2


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
    def __init__(self, name: str, gender: Gender, throws: Throws, exp: Experience, athleticism: Athletics):
        self.name = name
        self.gender = gender
        self.throws = throws
        self.exp = exp
        self.athleticism = Athletics

    @property
    def rank(self):
        return self.throws + self.exp + self.athleticism


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


def calc_means(df_in):
    mean_throw = df_in['throws'].mean()
    mean_exp = df_in['experience'].mean()
    mean_athl = df_in['athleticism'].mean()
    mean_rank = df_in['rank'].mean()
    mean_vals = {'throw': [mean_throw], 'exp': [mean_exp], 'athl': [mean_athl], 'rank': [mean_rank]}
    return mean_vals


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


def pop_random_player(roster, low_index, high_index):
    idx = rd.randint(low_index, high_index)
    player = roster.iloc[idx]
    roster.drop(index=roster.index[idx], inplace=True)
    roster.reset_index(drop=True, inplace=True)
    return player


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
    raw_data.sort_values(by=['rank', 'experience', 'athleticism'], ascending=False, inplace=True)
    mean_vals = calc_means(raw_data)

    # Split the roster into rosters of men and women
    men = raw_data[raw_data['gender'] == 'male'].copy()
    men.drop(['gender'], axis=1, inplace=True)
    women = raw_data[raw_data['gender'] == 'female'].copy()
    women.drop(['gender'], axis=1, inplace=True)

    # Add a top-ranked player to each team from the men's roster
    for _ in range(num_teams):
        men.reset_index(drop=True, inplace=True)
        teams.append(men.iloc[0])
        men.drop(index=0, inplace=True)

    # Add a random player to each team from the men's roster
    for i in range(num_teams):
        player = pop_random_player(men, 0, men.shape[0] - 1)
        teams[i] = pd.concat([teams[i], player], axis=1)

    # Add male players to the teams based on how team rankings compare to the average rank
    team_index = assign_players(mean_vals['rank'], men, teams, num_teams)

    # Add female players to the teams based on how team rankings compare to the average rank
    team_index = assign_players(mean_vals['rank'], women, teams, num_teams, team_index)

    # Transpose the teams and add a row that averages all values to include in the output
    final_teams = []
    for team in teams:
        final_team = team.T
        averages = pd.DataFrame({'name': ['AVERAGE:'], 'throws': [final_team['throws'].mean()],
                                 'experience': [final_team['experience'].mean()],
                                 'athleticism': [final_team['athleticism'].mean()],
                                 'rank': [final_team['rank'].mean()]})
        final_teams.append(pd.concat([final_team, averages]))

    timestamp = dt.datetime.now().strftime('%m-%d-%Y_%H-%M-%S')
    save_path = os.path.join(save_directory, f'teams_{timestamp}.xlsx')

    # Write the excel file
    with pd.ExcelWriter(save_path, engine='xlsxwriter') as writer:
        offset = 0
        for team in final_teams:
            team.to_excel(writer, sheet_name='Sheet1', startrow=offset, index=False)
            offset += len(team) + 4
