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
def get_match_by_id(id: int, include_match_info=True)-> dict:
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
    if include_match_info:
        match_info: dict = {
            "link": BASE + str(id), 
            "id" : id, 
            "event" : RequestString(event).strip('\n').strip('\t').replace('\t', ''), 
            "teams" : teams, 
            "score": total_score.strip('\n').strip('\t').replace('\t', '').replace('\n', ''), 
            "date" : date.strip('\n').strip('\t'),
            "match_style": match_style.strip('\n').strip('\t'),
            "players_stats" : match_stats(match_soup)
        }
    elif not include_match_info:
        return match_stats(match_soup)
        
    return match_info


#gets stats from inside a match div of both teams
def match_stats(soup):
    match_stats = []
    stats_tab = soup.find(class_="vm-stats-container")
    game_id = stats_tab.find_all(class_="vm-stats-game")
    
    team_tab = soup.find(class_="match-header-vs")
    team_names = [RequestString(result.text).strip('\n').strip('\t') for result in soup.find_all(class_="wf-title-med")]
    team_ids = []
    for i in range(2):
        team_ids.append(int(team_tab.find("a", class_=f"match-header-link wf-link-hover mod-{i+1}").get('href').split('/')[2]))
    team_elos = []
    for result in team_tab.find_all(class_="match-header-link-name-elo"):
        if RequestString(result.text).strip('\n').strip('\t').strip('\n').strip('[').strip(']') == '':
            team_elos.append(-1)
            continue
        team_elos.append(int(RequestString(result.text).strip('\n').strip('\t').strip('\n').strip('[').strip(']')))
    
    for game in game_id:
        if game.get('data-game-id') == 'all':
            game_id.remove(game)
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
        players_kills = game.find_all(class_="mod-stat mod-vlr-kills")
        players_deaths = game.find_all(class_="mod-stat mod-vlr-deaths")
        players_assists = game.find_all(class_="mod-stat mod-vlr-assists")
        game_score = f"{game.find_all(class_='score')[0].text}: {game.find_all(class_='score')[1].text}"
        rounds_played = int(game.find_all(class_='score')[0].text) + int(game.find_all(class_='score')[1].text)
        
        players_adrs = game.find_all(class_="stats-sq mod-combat")
        for i in range(10):
            try: 
                player_name = RequestString(players_name[i].text).remove_newlines().remove_tabs()
                player_team = None
                if i <= 4:
                    player_team = team_names[0]
                    opponent_team = team_names[1]
                    player_team_id = team_ids[0]
                    opponent_team_id = team_ids[1]
                    player_team_elo = team_elos[0]
                    opponent_team_elo = team_elos[1]
                elif i > 5:
                    player_team = team_names[1]
                    opponent_team = team_names[0]
                    player_team_id = team_ids[1]
                    opponent_team_id = team_ids[0]
                    player_team_elo = team_elos[1]
                    opponent_team_elo = team_elos[0]
                    
                agent = players_agents[i]
                kills = RequestString(players_kills[i].text).strip().split("\n")[0]
                deaths =  RequestString(players_deaths[i].find(class_="stats-sq").text).replace('/', '').strip().split("\n")[0]
                assists = RequestString(players_assists[i].text).strip().split("\n")[0]
                adr = RequestString(players_adrs[i].text).strip().split("\n")[0]
                if adr == '':
                    adr = -1
                playerstats = {"name" :  player_name.strip().lower(), 
                            "link": (players_hrefs[i])['href'],
                            "team":player_team,
                            "team id": player_team_id,
                            "team elo": player_team_elo,
                            "opponent": opponent_team,
                            "opponent id": opponent_team_id,
                            "opponent elo": opponent_team_elo,
                            "agent": agent.lower(),
                            "map": map.lower(),
                            "kills" : int(kills),  
                            "deaths": int(deaths),
                            "assists": int(assists), 
                            "adr" : int(adr),
                            "kpr": round(float(int(kills) / rounds_played), 2),
                            "rounds_played:": rounds_played
                            }
            except IndexError:
                #This helps with issues of missing/incomplete information from vlr 
                continue
                

            match_stats.append(playerstats)
    return match_stats



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

def get_player_match_ids(id: int, amount: int = 1):
    match_ids = []
    for i in range(int(amount/50) + 1):
        player_matches_soup = get_soup(PLAYER + MATCHES + str(id) + '/?page=' + str(i+1))
        matches = player_matches_soup.find_all("a", class_="wf-card fc-flex m-item")
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


