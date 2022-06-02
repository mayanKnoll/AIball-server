"""
does the scrappings we want
"""
import re
import bs4
import requests
from typing import List, Dict




def crate_soup(link: str) -> bs4.BeautifulSoup:
    # https://www.basketball-reference.com/teams/MIA/2021.html
    page = requests.get(link)
    return bs4.BeautifulSoup(page.content, "html.parser")


def get_team_data(name: str, year: int) -> List[List[str]]:
    url = f"https://www.basketball-reference.com/teams/{name}/{year}.html"
    page = requests.get(url)
    soup = page.content.decode().replace("\n", "")
    if soup is None:
        return
    soup = re.search(
        'id="team_and_opponent" data-cols-to-freeze=",1">(.*)</table>', soup)
    if soup is None:
        return
    soup = soup.group(0)
    soup = '<table class="suppress_all stats_table sticky_table eq1 re1 le1" id="team_and_opponent" data-cols-to-freeze=",1">' + soup + '</table>'
    soup = bs4.BeautifulSoup(soup, "html.parser")
    result = soup.find("table")
    rows = result.find_all('tr')
    row = rows[1]
    cols = row.find_all('td')
    data = [ele.text.strip() for ele in cols]
    return data


def get_team_misc(name: str, year: int) -> List[List[str]]:
    url = f"https://www.basketball-reference.com/teams/{name}/{year}.html"
    page = requests.get(url)
    soup = page.content.decode().replace("\n", "")
    if soup is None:
        return
    soup = re.search(
        'id="team_misc"(.*)</table>', soup)
    if soup is None:
        return
    soup = soup.group(0)
    soup = f'<table class="suppress_all stats_table" id="team_misc"{soup}</table>'
    soup = bs4.BeautifulSoup(soup, "html.parser")
    result = soup.find("table")
    rows = result.find_all('tr')
    row = rows[2]
    cols = row.find_all('td')
    data = [ele.text.strip() for ele in cols]
    return data[:-2]


def add_rating(rows, rating_dict, teams_names):
    for row in rows:
        cell = row.find('th')
        team_name = cell.text
        if "Division" in team_name:
            continue
        if team_name[-1] != '*':
            rating_dict[team_name] = 5
        else:
            team_name = team_name[:-1]
        teams_names[team_name] = cell.find('a')['href'].split('/')[2]


def get_rating(year: int) -> Dict[str, int]:
    soup = crate_soup(
        f"https://www.basketball-reference.com/playoffs/NBA_{year}.html")
    table = soup.find("table", id="all_playoffs")
    table = [a.text for a in table.find_all(
        'a') if "Series Stats" not in a.text and "Game" not in a.text]
    lst = list()
    for i in range(0, len(table), 2):
        lst.append((table[i], table[i+1]))
    rating_dict = dict()
    rating_dict[lst[0][0]] = 30
    rating_dict[lst[0][1]] = 25
    for team in lst[1:3]:
        rating_dict[team[1]] = 20
    for team in lst[3:8]:
        rating_dict[team[1]] = 15
    for team in lst[8:17]:
        rating_dict[team[1]] = 10
    soup = crate_soup(
        f"https://www.basketball-reference.com/leagues/NBA_{year}.html")
    teams_names = dict()
    if year > 1970:
        tableE = soup.find("table", id="divs_standings_E")
        tableW = soup.find("table", id="divs_standings_W")
        rowsE = tableE.find_all('tr')[1:]
        rowsW = tableW.find_all('tr')[1:]
        teams_names = dict()
        add_rating(rowsE, rating_dict, teams_names)
        add_rating(rowsW, rating_dict, teams_names)
    else:
        table = soup.find("table")
        rows = table.find_all('tr')[1:]
        add_rating(rows, rating_dict, teams_names)

    return teams_names, rating_dict



def get_teams_names(year: int):
    soup = crate_soup(
        f"https://www.basketball-reference.com/leagues/NBA_{year}.html")
    teams_names = dict()
    if year > 1970:
        tableE = soup.find("table", id="divs_standings_E")
        tableW = soup.find("table", id="divs_standings_W")
        rowsE = tableE.find_all('tr')[1:]
        rowsW = tableW.find_all('tr')[1:]
        teams_names = dict()
        add_rating(rowsE, {}, teams_names)
        add_rating(rowsW, {}, teams_names)

    return teams_names




def get_games(year: int, month: int) -> List[List[str]]:
    soup = crate_soup(
        f"https://www.basketball-reference.com/leagues/NBA_{year}_games-{month.lower()}.html")
    if not soup:
        raise Exception("empty month")
    result = soup.find("table")
    if not result:
        return
    rows = result.find_all('tr')
    row = rows[1]
    games = list()
    for row in rows:
        cols = row.find_all(['td', 'th'])
        cols = [ele.text.strip() for ele in cols]
        if cols[0] == "Date":
            continue
        games.append(cols[:6])
    return games



        



