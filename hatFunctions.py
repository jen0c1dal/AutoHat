import datetime as dt
import math
import os
import pandas as pd
import random as rd
import xlsxwriter


def enumerate_throws(string_in):
    if string_in == "I've thrown a frisbee before.":
        return 1
    elif string_in == "I can throw a forehand and backhand, even if they're occasionally wobbly.":
        return 2
    elif string_in == "Accurate with standard throws; I know what IO and OI mean.":
        return 3
    elif string_in == "All the throws; I will destroy you with my full-field scoobers.":
        return 4
    
    return 0


def enumerate_exp(string_in):
    if string_in == "Rookie":
        return 1
    elif string_in == "Pickup player":
        return 2
    elif string_in == "Club (Sectionals) / Masters (Nationals) / High School (State / Nationals)":
        return 3
    elif string_in == "Club player (Regionals / Nationals)":
        return 4
    
    return 0


def enumerate_athletics(string_in):
    if string_in == "Out of shape; mostly I'm here to heckle.":
        return 1
    elif string_in == "Athletic; just don't make me play savage.":
        return 2
    elif string_in == "Very athletic; my two settings are Sprint and Horizontal.":
        return 3
    
    return 0


def import_roster(filepath):
    df = pd.read_csv(filepath)
    df['throws'] = df['throws'].apply(enumerate_throws)
    df['experience'] = df['experience'].apply(enumerate_exp)
    df['athleticism'] = df['athleticism'].apply(enumerate_athletics)
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
    assign_players(mean_vals['rank'], women, teams, num_teams, team_index)

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
