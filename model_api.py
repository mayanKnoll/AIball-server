from typing import Dict, List
import pandas as pd
from joblib import load
from math import sqrt
from anylze_and_cleaning import *
import data_base_connection as db


WINS = 0
LOSSES = 1
DIFFERENCE = 2
GAMES = 3
POINTS = 4
LAST = 5


class ModelApi:
    """class of model Api
    """
    # TODO do all

    def __init__(self) -> None:
        # X_test[X_test.columns] = scaler.transform(X_test)
        # X = X.round(decimals=3)
        #TODO take all that info from database
        self._scaler = load('scaler.joblib')
        self._model = load('ann_model.joblib')
        self._teams_df = self.get_teams_by_year(2021)
        self._place = {True: "home_group", False: "visitor_group"}
        self._short_place = {True:  'Hm', False: "Vis"}

        """
        game - dict of {date,home_group,visitor_group}
        extend
        """

    def get_game_score(self, game: Dict[str, object]) -> int:
        date_to_season_and_days(game)
        db.add_balance(True, game)
        db.add_balance(False, game)
        self.add_team_data(True, game)
        self.add_team_data(False, game)
        db.add_last_game(game)
        del game["Season"]
        del game['Hm_G']
        # del game['Vis_G']
        keyorder = ['Hm_MP', 'Hm_FG', 'Hm_FGA', 'Hm_FGP', 'Hm_TP', 'Hm_TPA', 'Hm_tPp',
                    'Hm_wP', 'Hm_wPA', 'Hm_wPp', 'Hm_FT', 'Hm_FTA', 'Hm_FTp', 'Hm_ORB',
                    'Hm_DRB', 'Hm_TRB', 'Hm_AST', 'Hm_STL', 'Hm_BLK', 'Hm_TOV', 'Hm_PF',
                    'Hm_PTS', 'Hm_W', 'Hm_L', 'Hm_PW', 'Hm_PL', 'Hm_MOV', 'Hm_SOS',
                    'Hm_SRS', 'Hm_ORtg', 'Hm_DRtg', 'Hm_Pace', 'Hm_FTr', 'Hm_3PAr',
                    'Hm_eFG%', 'Hm_TOV%', 'Hm_ORB%', 'Hm_FT/FGA', 'Hm_eFG%.1', 'Hm_TOV%.1',
                    'Hm_DRB%', 'Hm_FT/FGA.1', 'Hm_rating', 'Vis_G', 'Vis_MP', 'Vis_FG',
                    'Vis_FGA', 'Vis_FGP', 'Vis_TP', 'Vis_TPA', 'Vis_tPp', 'Vis_wP',
                    'Vis_wPA', 'Vis_wPp', 'Vis_FT', 'Vis_FTA', 'Vis_FTp', 'Vis_ORB',
                    'Vis_DRB', 'Vis_TRB', 'Vis_AST', 'Vis_STL', 'Vis_BLK', 'Vis_TOV',
                    'Vis_PF', 'Vis_PTS', 'Vis_W', 'Vis_L', 'Vis_PW', 'Vis_PL', 'Vis_MOV',
                    'Vis_SOS', 'Vis_SRS', 'Vis_ORtg', 'Vis_DRtg', 'Vis_Pace', 'Vis_FTr',
                    'Vis_3PAr', 'Vis_eFG%', 'Vis_TOV%', 'Vis_ORB%', 'Vis_FT/FGA',
                    'Vis_eFG%.1', 'Vis_TOV%.1', 'Vis_DRB%', 'Vis_FT/FGA.1', 'Vis_rating',
                    'Last_same_game', 'Vis_Last_game', 'Hm_Last_game', 'Vis_Average_Points',
                    'Hm_Average_Points', 'Vis_Difference', 'Hm_Difference', 'Vis_Losses',
                    'Hm_Losses', 'Vis_Wins', 'Hm_Wins', 'days_from_start']
        game = {x: y for x, y in sorted(
            game.items(), key=lambda i: keyorder.index(i[0]))}
        return self.get_score(pd.DataFrame([game]))


    def add_team_data(self, home: bool, game: dict):
        team_data = self._teams_df[self._teams_df["group"]
                                   == game[self._place[home]]]
        team_data.drop("group", axis=1, inplace=True)
        index = team_data.index[0]
        for fither in team_data.columns:
            game[self._short_place[home] + "_" +
                 fither] = team_data.loc[index, fither]
        del game[self._place[home]]

        """
        """

    def get_teams_by_year(self, year: int):
        self._teams_df = pd.read_csv("teams_results.csv")
        self._teams_df.insert(
            0, 'year',  self._teams_df["index"].map(lambda b: b[:4]))
        self._teams_df.rename(columns={'index': 'group'}, inplace=True)
        self._teams_df["group"] = self._teams_df["group"].map(lambda b: b[4:])
        self._teams_df = self._teams_df[self._teams_df["year"] == str(year)]
        return self._teams_df.drop('year', axis=1)

    def get_score(self, X: pd.DataFrame):
        X[X.columns] = self._scaler.transform(X)
        proba = self._model.predict_proba(X)
        return round((1 - proba[0][1]) * 100, 3)
