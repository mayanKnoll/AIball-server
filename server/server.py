from model_api import ModelApi
import data_base_connection
import sys
from typing import List
import socket
import threading
from datetime import datetime
from datetime import date
from datetime import timedelta
import copy
from anylze_and_cleaning import date_to_number
import data_base_connection
sys.path.append('../AIball/Scrapper')
# sys.path.insert(
#     0, r'..\AIball\Scrapper')
import scrapper


MONTHS = [date(2021, 9, 30), date(2021, 10, 31), date(2021, 11, 30), date(2021, 12, 31), date(2022, 1, 31),
          date(2022, 2, 28), date(2022, 3, 31), date(2022, 4, 30), date(2022, 5, 31), date(2022, 6, 30)]


def get_last_games() -> List[List[str]]:
    game_list = list()
    for month in MONTHS:
        games = scrapper.get_games(month.year, month.strftime("%B"))
        if date.today() < month:
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
            if date.today() >= month - timedelta(days=month.day - 1):
                continue
            games = scrapper.get_games(month.year, month.strftime("%B"))
            if games is None:
                continue
            for game in games:
                if len(game) < 6 or game[3]:
                    continue
                game_dict = {
                    "date": game[0], "home_group": game[4], "visitor_group": game[2]}
                game_list.append(game_dict)
    clean_played_game(game_list)


def clean_played_game(games):
    for index, game in enumerate(games):
        date_game = date_to_number(game["date"])
        if date(year=int(date_game[4:8]), month=int(date_game[0:2]), day=int(date_game[2:4])) < date.today():
            del games[index]
        else:
            return


def update_balance():
    for game in get_last_games():
        data_base_connection.update_balance(game)




def check_acc():
    api = ModelApi()
    last_game = None
    game_pred = list()
    game_score = list()
    data_base_connection.create_balance()
    for game in get_last_games():
        last_game = {"date": game["date"], "home_group": game["home_group"],
         "visitor_group": game["visitor_group"]}
        game_pred.append(api.get_game_score(last_game))
        if game["home_pts"] > game["vis_pts"]:
            game_score.append(100)
        else:
            game_score.append(0) 
                   
        data_base_connection.update_balance(game)
        games = [abs(score - pred) for score,pred in zip(game_score, game_pred)]
        print(sum(games) / len(games), game_score, game_pred)
    



        

    


def server():
    serverSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    api = ModelApi()
    try:
        serverSocket.bind(('localhost', 900))
        print("start Serv!")
        next_games = list()
        done = "First"
        while(True):
            if done is "First" or (datetime.now().hour == 0 and not done):
                done = True
                T_update_balance = threading.Thread(
                    target=update_balance, args=())
                next_games = list()
                T_next_game = threading.Thread(
                    target=get_next_games, args=(next_games, ))
                T_update_balance.start()
                T_next_game.start()
            else:
                done = False
            massage, address = serverSocket.recvfrom(1024)
            print(massage)
            try:
                code, content = massage.decode().split(":")
                if code != "200" and code != "300":
                     raise ValueError()
            except ValueError:
                serverSocket.sendto("{wrong massage}".encode(), address)
                continue
            games = list()
            if code == "200":
                games = next_games[:5]
            else:
                for game in next_games:
                    if len(games) > 5:
                        break
                    if content.lower() in game["home_group"].lower() or content.lower() in game["visitor_group"].lower():
                        games.append(game)
            data = list()
            for game in games:
                home_group = game["home_group"]
                date = game["date"]
                visitor_group = game["visitor_group"]
                score = api.get_game_score(copy.deepcopy(game))
                massage = '{' + f'"date":"{date}","home_group":"{home_group}","visitor_group":"{visitor_group}","score":"{score}"' +'}'
                data.append(massage)
            data = "[" + ",".join(data) + "]"
            serverSocket.sendto(data.encode(), address)

    except KeyboardInterrupt:
        print("\nShutting down...\n")
    except Exception as exc:
        print("Error:\n")
        print(exc)
    serverSocket.close()


print('Access http://localhost:900')


def main():
    server()


if __name__ == "__main__":
    main()
