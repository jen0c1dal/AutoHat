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
from pydantic import BaseModel, validator


class Gender(Enum):
    """Enum for player gender"""

    MALE = 'male'
    FEMALE = 'female'


class SkillLevel(Enum):
    """Class representing a skill level with level and text"""

    def __init__(self, level: int, text: str):
        """Initialize a skill level"""

        self.level = level
        self.text = text


class Throws(SkillLevel):
    """Enum for throwing skill levels"""

    NOOB = (1, "I've thrown a frisbee before.")
    COMPETENT = (2, "I can throw a forehand and backhand, even if they're occasionally wobbly.")
    PRO = (3, "Accurate with standard throws; I know what IO and OI mean.")
    SCOOBER_GOD = (4, "All the throws; I will destroy you with my full-field scoobers.")


class Experience(SkillLevel):
    """Enum for experience skill levels"""

    ROOKIE = (1, "Rookie")
    PICKUP = (2, "Pickup player")
    CLUB = (3, "Club (Sectionals) / Masters (Nationals) / High School (State / Nationals)")
    PRO = (4, "Club player (Regionals / Nationals)")


class Endurance(SkillLevel):
    """Enum for endurance skill levels"""

    BACKUP = (1, "I like to rest for a few points in between the points that I play.")
    LINE = (2, "I can play about every other point at full speed.")
    ANCHOR = (3, "I can play a few points in a row at full speed before I need a rest.")
    SAVAGE = (4, "I actually prefer to play savage.")


class Athletics(SkillLevel):
    """Enum for athleticism skill levels"""

    UNFIT = (1, "Out of shape; mostly I'm here to heckle.")
    FIT = (2, "Somewhat athletic; I can usually get open when I make a cut.")
    FAST = (3, "Quite athletic; I have no difficulty getting open when I make cuts.")
    ELITE = (4, "Very athletic; my two settings are Sprint and Horizontal.")


def skill_match(text: str, enum_type) -> Enum:
    """Match text to enum value"""
    for enum in enum_type:
        if enum.text == text:
            return enum.level

    return 0


class Player(BaseModel):
    """Class representing a player"""

    name: str
    gender: Gender
    rank: int

    def __lt__(self, other) -> bool:
        """Compare players by rank"""

        return self.rank < other.rank

    def to_dict(self) -> dict:
        """Convert player to dictionary"""

        return {
            'name': self.name,
            'gender': self.gender.value,
            'rank': self.rank,
        }


class PlayerGroup(BaseModel):
    """Class to baggage multiple players together"""

    players: list[Player] = []
    player_idxs: list[int] = []

    model_config = {'arbitrary_types_allowed': True}

    @validator('players')
    @classmethod
    def validate_players(cls, v):
        if not v:
            raise ValueError('PlayerGroup must have at least one player')
        return v

    @property
    def mean_rank(self) -> float:
        return calc_mean_rank(self.players)

    @property
    def num_fmp(self) -> int:
        return len([pp for pp in self.players if pp.gender == Gender.FEMALE])

    @property
    def num_players(self) -> int:
        return len(self.players)

    def __init__(self, players: list[Player] | list[str], roster: pd.DataFrame | None = None, **data):
        if isinstance(players[0], str):
            # From list[str] and roster
            p, idx = PlayerGroup.create_group(players, roster)
            super().__init__(
                players=p,
                player_idxs=idx,
                **data
            )
        else:
            # From list[Player]
            p = players
            super().__init__(
                players=p,
                player_idxs=[],
                **data
            )

    @staticmethod
    def create_group(players: list[str], roster: pd.DataFrame):
        """Create a group of players from names and roster"""
        group = []
        player_idxs = []
        for p in players:
            player = roster.loc[roster['name'] == p].iloc[0].copy()
            group.append(Player(name=player['name'], gender=Gender(player['gender']), rank=player['rank']))
            player_idxs.append(roster.index[roster['name'] == p][0])
        return group, player_idxs


    def add_players(self, players: Player | list[Player]):
        """Add players to the group"""
        if isinstance(players, Player):
            self.players.append(players)
        else:
            self.players.extend(players)

    def __lt__(self, other) -> bool:
        """Compare groups by mean rank"""

        return self.mean_rank < other.mean_rank


def import_roster(filepath: str) -> pd.DataFrame:
    """Import roster from CSV file"""
    df = pd.read_csv(filepath)
    df['throws'] = df['throws'].apply(skill_match, args=(Throws,))
    df['experience'] = df['experience'].apply(skill_match, args=(Experience,))
    df['endurance'] = df['endurance'].apply(skill_match, args=(Endurance,))
    df['athleticism'] = df['athleticism'].apply(skill_match, args=(Athletics,))
    df['name'] = df['first_name'] + ' ' + df['last_name']
    df['rank'] = df['throws'] + df['experience'] + df['endurance'] + df['athleticism']
    df.drop(columns=['first_name', 'last_name'], inplace=True)
    return df


def launch_checkin(data_in_path):
    """Launch check-in by importing and sorting roster"""
    raw_data = import_roster(data_in_path)
    raw_data.sort_values(by=['name'], ascending=True, inplace=True)
    raw_data.reset_index(drop=True, inplace=True)
    return raw_data


def calc_mean_rank(roster: list[Player]) -> int:
    """Calculate mean rank of players"""
    return sum(p.rank for p in roster) / len(roster)


def assign_players(mean_rank: float, roster: list[Player], teams: list[PlayerGroup], num_teams: int, team_index: int = 0) -> int:
    """Assign players to teams based on rank"""
    while len(roster) > 0:
        if teams[team_index].mean_rank > mean_rank:
            player = pop_random_player(roster, math.ceil(len(roster) / 2), len(roster) - 1)
        else:
            player = pop_random_player(roster, 0, math.floor(len(roster) / 2))
        teams[team_index].add_players(player)
        team_index = (team_index + 1) % num_teams

    return team_index


def pop_random_player(roster: list[Player], begin: int, end: int) -> Player:
    """Pop a random player from roster within range"""
    if len(roster) == 1:
        return roster.pop(0)
    return roster.pop(rd.randint(begin, end))


def add_baggages_to_teams(teams: list[PlayerGroup], baggages: list[PlayerGroup], mean_rank:float):
    """Add baggages to teams"""
    while len(baggages) > 0:
        for t in teams:
            if len(baggages) > 0:
                baggage = baggages.pop() if t.mean_rank > mean_rank else baggages.pop(0)
                t.add_players(baggage.players)


def balance_attribute(teams: list[PlayerGroup], roster: list[Player], mean_rank: float, get_attr):
    """Helper function to balance teams based on a given attribute"""
    max_attr = max(get_attr(t) for t in teams)
    min_attr = min(get_attr(t) for t in teams)
    while min_attr < max_attr and len(roster) > 0:
        for t in teams:
            if get_attr(t) < max_attr:
                if t.mean_rank > mean_rank:
                    t.add_players(pop_random_player(roster, math.ceil(len(roster) / 2), len(roster) - 1))
                else:
                    t.add_players(pop_random_player(roster, 0, math.floor(len(roster) / 2)))
            min_attr = min(get_attr(t) for t in teams)


def balance_teams(teams: list[PlayerGroup], m_roster: list[Player], f_roster: list[Player], mean_rank: float):
    """Balance teams by gender and player count"""
    balance_attribute(teams, f_roster, mean_rank, lambda t: t.num_fmp)
    balance_attribute(teams, m_roster, mean_rank, lambda t: t.num_players)


# Add players one by one to build a dataframe of drop-in players. Only rank is enumerated,
# all other scores are given a value of NaN to indicate that the value isn't known
def add_drop_in(name: str, gender: str, rank: str) -> pd.DataFrame:
    """Add drop-in player to roster"""
    drop_in_player = {
        'name': [name.title()],
        'gender': [gender],
        'throws': [np.nan],
        'experience': [np.nan],
        'endurance': [np.nan],
        'athleticism': [np.nan],
        'rank': [int(rank)],
    }

    return pd.DataFrame(drop_in_player)


# Add a baggage object, grouping players internally. Returns both a PlayerGroup object and
# the associated list of indeces so that players can be dropped from the main roster when
# it comes time to generate teams
def create_baggage(players: list[str], roster: pd.DataFrame) -> tuple[PlayerGroup, list[int]]:
    baggage = PlayerGroup(players, roster)
    return baggage, baggage.player_idxs


def create_players(df: pd.DataFrame) -> list[Player]:
    """Create a list of Player objects from a dataframe"""
    return [Player(name=name, gender=Gender(gender), rank=rank) for name, gender, rank in zip(df['name'], df['gender'], df['rank'])]


def generate_teams(players: list[Player], save_directory: str, num_teams: int, baggages: list[PlayerGroup]):
    """Main function to generate a given number of teams teams from the list of checked in players"""
    mean_rank = calc_mean_rank(players)

    # Split the roster into rosters of men and women
    men = [p for p in players if p.gender == Gender.MALE]
    women = [p for p in players if p.gender == Gender.FEMALE]

    men.sort(reverse=True)
    women.sort(reverse=True)

    if len(men) >= num_teams:
        # Assign top players to teams
        teams = [PlayerGroup([men.pop(0)]) for _ in range(num_teams)]
        # Add random players
        for i in range(num_teams):
            teams[i].add_players(pop_random_player(men, 0, len(men) - 1))
    else:
        # Assign top women to teams
        teams = [PlayerGroup([women.pop(0)]) for _ in range(num_teams)]
        # Add random players
        for i in range(num_teams):
            teams[i].add_players(pop_random_player(women, 0, len(women) - 1))

    # If there are baggages, add them to the teams and then balance the number of women and
    # total number of players
    if len(baggages) > 0:
        baggages.sort(reverse=True)
        mean_rank = sum(t.mean_rank for t in teams) / num_teams
        add_baggages_to_teams(teams, baggages, mean_rank)
        balance_teams(teams, men, women, mean_rank)

    # Add male players to the teams based on how team rankings compare to the average rank
    team_index = assign_players(mean_rank, men, teams, num_teams)

    # Add female players to the teams based on how team rankings compare to the average rank
    team_index = assign_players(mean_rank, women, teams, num_teams, team_index)

    # Add a row that averages the rank to include in the output
    final_teams = []
    for team in teams:
        team_df = pd.DataFrame.from_records(p.to_dict() for p in team.players)
        averages = pd.DataFrame({'Average': [team.mean_rank]})
        final_teams.append(pd.concat([team_df, averages]))

    timestamp = dt.datetime.now().strftime('%m-%d-%Y_%H-%M-%S')
    save_path = os.path.join(save_directory, f'teams_{timestamp}.xlsx')

    # Write the excel file
    with pd.ExcelWriter(save_path, engine='xlsxwriter') as writer:
        offset = 0
        for team in final_teams:
            team.to_excel(writer, startrow=offset, index=False)
            offset += len(team) + 4


def export_players(player_data: pd.DataFrame, save_directory: str):
    """Export player data to Excel"""
    timestamp = dt.datetime.now().strftime('%m-%d-%Y_%H-%M-%S')
    save_path = os.path.join(save_directory, f'players_{timestamp}.xlsx')
    with pd.ExcelWriter(save_path, engine='xlsxwriter') as writer:
        player_data.to_excel(writer, index=False)


def load_exported_players(filepath: str) -> pd.DataFrame:
    """Load a previously-exported players .xlsx file

    Normalizes the `name` column (stripping whitespace and title-casing) when present.
    """

    # Prefer openpyxl for modern xlsx files
    df = pd.read_excel(filepath, engine='openpyxl')

    # Normalize name column
    df['name'] = df['name'].astype(str).str.strip()

    # Apply consistent formatting for matching
    df['__match_name'] = df['name'].str.lower().str.replace(r"\s+", " ", regex=True).str.strip()

    return df


def get_attendance_indices(roster_df: pd.DataFrame, exported_df: pd.DataFrame, key: str = 'name') -> tuple[list[int], list[str]]:
    """Return a list of indices in `roster_df` that match any name in `exported_df`.

    Matching is case- and whitespace-insensitive and uses the `name` column by default.
    Returns (indices, unmatched_exported_names).
    """
    if roster_df is None or exported_df is None:
        return [], []

    # Prepare match keys
    roster_match = roster_df.copy()
    if key in roster_match.columns:
        roster_match['__match_name'] = roster_match[key].astype(str).str.lower().str.replace(r"\s+", " ", regex=True).str.strip()
    else:
        roster_match['__match_name'] = roster_match.index.map(lambda i: '')

    if '__match_name' not in exported_df.columns and key in exported_df.columns:
        exported_df['__match_name'] = exported_df[key].astype(str).str.lower().str.replace(r"\s+", " ", regex=True).str.strip()

    exported_set = set(exported_df['__match_name'].dropna().unique())

    indices = [int(i) for i, val in enumerate(roster_match['__match_name']) if val in exported_set]

    matched_names = set(roster_match.loc[i, '__match_name'] for i in indices)
    unmatched = [n for n in exported_set if n not in matched_names]

    # Return original dataframe indices (not positional) — map positional indexes to df.index
    original_indices = [int(roster_df.index[i]) for i in indices]

    return original_indices, [n for n in unmatched]


def apply_attendance_column(roster_df: pd.DataFrame, indices: list[int], column_name: str = 'attended') -> pd.DataFrame:
    """Add or update a boolean attendance column on `roster_df` marking provided indices True"""
    if column_name not in roster_df.columns:
        roster_df[column_name] = False
    roster_df.loc[indices, column_name] = True
    return roster_df
