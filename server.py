import copy
import socket
import sys
import threading
from datetime import date, datetime, timedelta
from typing import List
import data_base_connection
from anylze_and_cleaning import date_to_number
from model_api import ModelApi
sys.path.append('../AIball/Scrapper')
import scrapper


# sys.path.insert(
#     0, r'..\AIball\Scrapper')


MONTHS = [date(2021, 9, 30), date(2021, 10, 31), date(2021, 11, 30), date(2021, 12, 31), date(2022, 1, 31),
          date(2022, 2, 28), date(2022, 3, 31), date(2022, 4, 30), date(2022, 5, 31), date(2022, 6, 30)]


def get_last_games() -> List[List[str]]:
    game_list = list()
    for month in MONTHS:
        games = scrapper.get_games(month.year, month.strftime("%B"))
        if date.today() < date(month.year, month.month, 1):
            break
        if games is None:
            continue
        for game in games:
            if len(game) < 6 or game[3] is '':
                continue
            game_dict = {"date": game[0], "home_group": game[4], "home_pts": int(game[5]),
                         "visitor_group": game[2], "vis_pts": int(game[3])}
            game_list.append(game_dict)
    return game_list

# Prepare a sever socket


def get_next_games(game_list) -> List[List[str]]:
    if len(game_list) is 0:
        for month in MONTHS:
            # if date.today() >= month - timedelta(days=month.day - 1):
            # continue
            games = scrapper.get_games(month.year, month.strftime("%B"))
            if games is None:
                continue
            for game in games:
                if len(game) < 6 or game[3]:
                    continue
                game_dict = {
                    "date": game[0], "home_group": game[4], "visitor_group": game[2]}
                game_list.append(game_dict)
    # clean_played_game(game_list)
    print("end this")


def clean_played_game(games):
    for index, game in enumerate(games):
        date_game = date_to_number(game["date"])
        if date(year=int(date_game[4:8]), month=int(date_game[0:2]), day=int(date_game[2:4])) < date.today():
            del games[index]
        else:
            return


def update_balance(db_connection):
    for game in get_last_games():
        print(game["date"])
        db_connection.update_balance(game)


def server():
    serverSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    api = ModelApi()
    db_connection = data_base_connection.db_connection()
    # db_connection.upload_teams("tables/initial_files/teams_results.csv")

    try:
        # db_connection.create_balance()
        # update_balance()
        serverSocket.bind(('localhost', 3000))
        print("start Serv!")
        # next_games = list()
        day_update = False
        year_update = False
        while(True):
            if datetime.now().month == 8 and datetime.now().day == 1 and not year_update:
                year_update = True
            elif datetime.now().day != 1:
                year_update = False
            if (datetime.now().hour == 0 and not done):
                done = True
                # TODO update button and time
                # db_connection.update_next_games()
                # db_connection.create_balance()
                # T_update_balance = threading.Thread(
                # target=update_balance, args=())
                # T_next_game = threading.Thread(
                # target=get_next_games, args=(next_games, ))
                # T_update_balance.start()
                # T_next_game.start()
            elif datetime.now().hour != 0:
                done = False
            try:
                massage, address = serverSocket.recvfrom(1024)
            except ConnectionResetError:
                continue
            print(massage)
            # T_next_game.join()
            # T_update_balance.join()
            try:
                code, content = massage.decode().split(":")
                if code != "200" and code != "300" and code != "400":
                    raise ValueError()
            except ValueError:
                serverSocket.sendto("{wrong massage}".encode(), address)
                continue
            games = list()
            if code == "300":
                games = db_connection.get_next_games(content)
            elif code == "400":
                team_names = list(db_connection.get_teams_name())
                team_names = '["' + '", "'.join(team_names) + '"]'
                serverSocket.sendto(team_names.encode(), address)
                continue
            else:
                games = db_connection.get_next_games()
            data = list()
            for game in games:
                home_group = game["home_group"]
                date = game["date"]
                visitor_group = game["visitor_group"]
                score = api.get_game_score(db_connection, copy.deepcopy(game))
                massage = '{' + f'"head":"{content}", "date":"{date}","home_group":"{home_group}","visitor_group":"{visitor_group}","score":"{score}"' + '}'
                data.append(massage)
            data = '[' + ",".join(data) + "]"
            serverSocket.sendto(data.encode(), address)

    except KeyboardInterrupt:
        print("\nShutting down...\n")
    # except Exception as exc:
    #     print("Error:\n")
    #     print(exc)
    serverSocket.close()


print('Access http://localhost:900')


def main():
    server()


if __name__ == "__main__":
    main()
