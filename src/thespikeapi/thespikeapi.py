from json import encoder
import bs4
import logging
import json
import requests
import requests.api




logging.basicConfig(level=logging.DEBUG)

BASE: str = "https://www.vlr.gg/"
MATCHES: str = "matches/"
RANKINGS: str= "rankings/"
TEAM: str= "team/"
NEWS: str = "news/"
FORUMS: str = "forum/"
PLAYER: str = "player/"

class RequestString(str):
    def __init__(self, string: str) -> None:
        self.string = string

    def remove_newlines(self):
        self.string = self.string.replace("\n", "")
        return self

    def remove_tabs(self):
        self.string = self.string.replace("\t", "")
        return self

    def __repr__(self) -> str:
        return self.string
    

#allows bs4 to parse the required address
def get_soup(address :str):
    request_link: str = BASE + address
    re = requests.get(request_link)
    logging.debug("requesting url: " + request_link + " : " + str(re))
    soup  = bs4.BeautifulSoup(re.content, 'lxml')
    if re.status_code == 404:
        return None
    else:
        return soup

#returns useful information on a match, given the id
#should work, but needs to add check if the matches are actually being played live
def get_match_by_id(id: int)-> dict:
    match_soup = get_soup(str(id))
    event = match_soup.find(class_="match-header-event").text
    match_style = RequestString(match_soup.find_all(class_="match-header-vs-note")[1].text)
    match_style.remove_newlines()
    match_style.remove_tabs()
    date = RequestString(match_soup.find(class_="moment-tz-convert").text)
    date.remove_newlines() 
    date.remove_tabs() 
    total_score = RequestString(match_soup.find(class_="js-spoiler").text)
    total_score.remove_tabs() 
    total_score.remove_newlines() 
    teams = [RequestString(result.text).strip('\n').strip('\t') for result in match_soup.find_all(class_="wf-title-med")]
    match_info: dict = {
        "link": BASE + str(id), 
        "id" : id, 
        "event" : RequestString(event).strip('\n').strip('\t').replace('\t', ''), 
        "teams" : teams, 
        "score": total_score.strip('\n').strip('\t').replace('\t', '').replace('\n', ''), 
        "date" : date.strip('\n').strip('\t'),
        "match_style": match_style.strip('\n').strip('\t'),
        "players_stats" : team_match_stats(match_soup)
    }
    return match_info

#gets stats from inside a match div
def team_match_stats(soup):
    match_stats = []
    stats_tab = soup.find(class_="vm-stats-container")
    game_id = stats_tab.find_all(class_="vm-stats-game")
    for game in game_id:
        if game.get('data-game-id') == 'all':
            game_id.remove(game)
    #print(game_id)
    for game in game_id:
        players_hrefs = game.find_all("a", href=True)
        players_name = game.find_all(class_="text-of")
        map_div = game.find(class_='map')
        map = map_div.find('span', style='position: relative;').text.replace("PICK", '').replace('\n', '').replace('\t', '')
        players_agents_images = game.find_all('img')
        players_agents = []
        for image in players_agents_images:
                if (image.get("title")):
                    players_agents.append(image.get("title"))
        #print(players_agents)
        players_kills = game.find_all(class_="mod-stat mod-vlr-kills")
        players_deaths = game.find_all(class_="mod-stat mod-vlr-deaths")
        players_assists = game.find_all(class_="mod-stat mod-vlr-assists")
        game_score = f"{game.find_all(class_='score')[0].text}: {game.find_all(class_='score')[1].text}"
        #print(game_score)
        rounds_played = int(game.find_all(class_='score')[0].text) + int(game.find_all(class_='score')[1].text)
        
        players_adrs = game.find_all(class_="stats-sq mod-combat")
        for i in range(10):
            try: 
                player_name = RequestString(players_name[i].text).remove_newlines().remove_tabs()
                agent = players_agents[i]
                #print(agent)
                #print(players_agents[i])
                kills = RequestString(players_kills[i].text).strip().split("\n")[0]
                deaths =  RequestString(players_deaths[i].find(class_="stats-sq").text).replace('/', '').strip().split("\n")[0]
                assists = RequestString(players_assists[i].text).strip().split("\n")[0]
                adr = RequestString(players_adrs[i].text).strip().split("\n")[0]
                #kpr = RequestString(players_kpr[i].text)
                playerstats = {"name" :  player_name.strip().lower(), 
                            "link": (players_hrefs[i])['href'],
                            "agent": agent.lower(),
                            "map": map.lower(),
                            "kills" : int(kills),  
                            "deaths": int(deaths),
                            "assists": int(assists), 
                            "adr" : int(adr),
                            "kpr": round(float(int(kills) / rounds_played), 2)
                            }
            except IndexError: 
                continue
                

            match_stats.append(playerstats)
    return match_stats

#gets information about the top n, with default to global (as a region). Other regions can be specified and passed as a string
def get_top_n(number: int=30, region: str=""):
    rankings_soup = get_soup(RANKINGS + region)
    teams = rankings_soup.find_all(class_="rank-item wf-card fc-flex")
    teams_array = []
    for i in range(number):
        team_name = RequestString(teams[i].find(class_="ge-text").text).remove_newlines().remove_tabs().string
        team_country = RequestString(teams[i].find(class_="rank-item-team-country").text).remove_tabs().remove_newlines()
        team_name = team_name.replace(team_country, "") #removes the country from the team name
        team_ranking = RequestString(teams[i].find(class_="rank-item-rank").text).remove_tabs().remove_newlines().string
        ratings_arr = teams[i].find_all(class_="rank-item-rating")
        streak = RequestString(teams[i].find(class_="rank-item-streak mod-right").text).remove_newlines().remove_tabs()
        teams_array.append({"team": team_name,
                            "country": team_country,
                            "ranking": int(team_ranking), "rating": int(ratings_arr[0].text),
                            "form": int(ratings_arr[1].text), "ach": int(ratings_arr[2].text),
                            "streak": streak})
    return teams_array 
    #could add winnings and last played, but is functional

#gets basic info about news  such as title, comments and time passed.
def get_news(page=1):
    news_soup = get_soup(NEWS+ f"?page={page}")
    news_list = news_soup.find_all(class_="wf-module-item", href=True) 
    news_array = []
    for article in news_list:
        divs = article.find_all("div")
        title = RequestString(divs[1].text).remove_newlines().remove_tabs()
        description = RequestString(divs[2].text).remove_newlines().remove_tabs()
        bot_row = (article.find_next(class_="ge-text-light").text).split("\u2022") # splits the string using the escape for the bullet (u+2022) 
        news_array.append({"title": title, "description" : description, "link": article['href'],
                           "author" : RequestString(bot_row[2]).remove_tabs().remove_newlines(), "date" : bot_row[1]})
    return news_array

#gets player infos from personal page
def get_player_infos(id: int)->dict:
    player_soup = get_soup(PLAYER +  str(id))
    header = player_soup.find(class_="wf-card mod-header mod-full") 
    name = header.find(class_="wf-title").text
    real_name = header.find(class_="player-real-name").text
    twitter_link =  header.find("a", href=True)
    twitch_link =  header.find_next("a", href=True)
    country = header.find_all("div")
    return  {"name": RequestString(name).remove_newlines().remove_tabs(), "real_name" : real_name, 
                    "twitter" : twitter_link["href"], "twitch" : twitch_link["href"], 
                    "country": RequestString(country[6].text).remove_tabs().remove_newlines()}

#returns array of last 50 matches played by player given the id
def get_player_matches_by_id(id: int):
    player_matches_soup = get_soup(PLAYER + MATCHES + str(id))
    matches_stats  = []
    matches = player_matches_soup.find_all(class_="wf-card", href=True)
    for match in matches:
        divs = match.find_all("div")
        score = RequestString(match.find(class_="m-item-result").text).remove_newlines().remove_tabs()
        dateclass = match.find(class_="rm-item-datze")
        date = RequestString(dateclass.find("div").text).remove_tabs().remove_newlines()
        team1 = RequestString(divs[3].text).remove_tabs().remove_newlines()
        team2 = RequestString(divs[10].text).remove_tabs().remove_newlines
        matches_stats.append({"link": match["href"],"score" : score, "date" : date, "teams": [team1.split("#")[0] ,team2.split("#")[0]]})
    return matches_stats

def get_player_match_ids(id: int, amount: int = 1):
    match_ids = []
    for i in range(int(amount/50) + 1):
        player_matches_soup = get_soup(PLAYER + MATCHES + str(id) + '/?page=' + str(i+1))
        matches = player_matches_soup.find_all("a", class_="wf-card fc-flex m-item")
        #print(matches[0].get("href").split('/')[1])
        #print(len(matches))
        for match in matches:
            match_ids.append(match.get("href").split('/')[1]) 
    return match_ids[0:amount]

def get_team_match_ids(id: int, amount: int = 1):
    match_ids = []
    for i in range(int(amount/50) + 1):
        player_matches_soup = get_soup(TEAM + MATCHES + str(id) + '/?page=' + str(i+1))
        matches = player_matches_soup.find_all("a", class_="wf-card fc-flex m-item")
        for match in matches:
            match_ids.append(match.get("href").split('/')[1]) 
    return match_ids[0:amount]

def to_json(filename: str, data: dict, indent=4, append=False):
    with open(f"{filename}.json", "a") as f:
        json.dump(data, f, indent=indent)
        f.write('\n')  # Add a newline after each JSON object for readability


