from json import encoder
import bs4
import logging
import json
import requests
import requests.api
import pandas as pd


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

# Retrieves a list of bs4 strings for each map, removes match summary
def get_game_soups(id=id, match_soup=None):
    if match_soup is None:
        match_soup = get_soup(str(id))
    stat_tab = match_soup.find(class_="vm-stats-container")
    game_soups = stat_tab.find_all(class_="vm-stats-game")
    i = 0
    while i < len(game_soups):
        if game_soups[i].get('data-game-id') == 'all' or get_game_map(game_soup=game_soups[i]) == 'TBD':
            del game_soups[i]
        else:
            i += 1
    return game_soups

def add_player_to_dataFrame(dataframe, player): 
    dataframe.append(player)

#returns match data for players specified, if all_players - returns all player data from matches
def get_match_player_data(match_ids : list, dataset=None, player_ids=None, all_players=True):
    # Defining the columns for the dataset
    columns = [
                'match_id',
                'match_date',
                'match_style',
                #'match_event': [],
                'match_score',
                'game_index',
                'map',
                'game_score',
                'player_agent',
                'rounds_played',
                'player_id',
                'player_name',
                'player_team_id',
                'player_team_name_long',
                'player_team_name_short',
                'player_team_vlr_rating',
                'player_adr',
                'player_kills',
                'player_deaths',
                'player_assists',
                'player_kpr',
                'opponent_id',
                'opponent_name_long',
                'opponent_name_short',
                'opponent_vlr_rating',
        ]
    data_frame = pd.DataFrame(columns=columns)

    used_match_ids = []
    if dataset is not None:
        used_match_ids = dataset['match_id'].drop_duplicates().to_list()
        used_match_ids = [str(elem) for elem in used_match_ids]
        match_ids = [match for match in match_ids if match not in used_match_ids]
        print(f'DATASET DETECTED APPPENDING {len(match_ids)} MATCHES')

    # Looping through each match in the match_id list
        # Sets the information that doesnt through map/players
    match_num = 1
    for match_id in match_ids:
        match_soup = get_soup(str(match_id))
        game_soups = get_game_soups(match_soup=match_soup)
        match_date = get_match_date(match_soup=match_soup)
        match_style = get_match_style(soup=match_soup)
        match_event = get_match_event(soup=match_soup)
        match_score = get_match_score(soup=match_soup)
        team_name_long = get_team_names_long(soup=match_soup)
        team_id = get_team_ids(soup=match_soup)
        team_elo = get_team_elos(soup=match_soup)
        print(f'MATCH {match_num}/{len(match_ids)}')
        match_num+=1
        # Looping through each map in a series (match)
            # Sets the information that changes between maps
            # creates lists for each variable in order of players retrieved
        for i, game_soup in enumerate(game_soups):
            game_index = i
            team_name_short = get_team_names_short(game_soup=game_soup)
            player_id = get_player_ids(game_soups[i])
            player_names = get_player_names(game_soups[i])
            player_agent = get_player_agents(game_soups[i])
            map = get_game_map(game_soups[i])
            rounds_played = get_game_rounds_played(game_soups[i])
            player_adr = get_player_adrs(game_soups[i])
            player_kills = get_player_kills(game_soups[i])
            player_deaths = get_player_deaths(game_soups[i])
            player_assists = get_player_assists(game_soups[i])
            game_score = get_game_score(game_soups[i])

            # Loops through all players playing a map
            for index, player_name in enumerate(player_names):
                # Team 1
                if index <= 4:
                    player_team_long = team_name_long[0]
                    player_team_short = team_name_short[0]
                    player_team_id = team_id[0]
                    player_team_elo = team_elo[0]
                    player_opponent_long = team_name_long[1]
                    player_opponent_short = team_name_short[5]
                    player_opponent_id = team_id[1]
                    player_opponent_elo = team_elo[1]
                # Team 2
                else:
                    player_team_long = team_name_long[1]
                    player_team_short = team_name_short[5]
                    player_team_id = team_id[1]
                    player_team_elo = team_elo[1]
                    player_opponent_long = team_name_long[0]
                    player_opponent_short = team_name_short[0]
                    player_opponent_id = team_id[0]
                    player_opponent_elo = team_elo[0]
                # Building a row for each player
                data = [
                    match_id,
                    match_date,
                    match_style,
                    #'match_event': [],
                    match_score,
                    game_index,
                    map,
                    game_score,
                    player_agent[index],
                    rounds_played,
                    player_id[index],
                    player_name,
                    player_team_id,
                    player_team_long,
                    player_team_short,
                    player_team_elo,
                    player_adr[index],
                    player_kills[index],
                    player_deaths[index],
                    player_assists[index],
                    player_kpr,
                    player_opponent_id,
                    player_opponent_long,
                    player_opponent_short,
                    player_opponent_elo
                ]
                # Applying the row to an exisitng dataset
                if dataset is not None:
                    dataset.loc[len(dataset)] = data
                # or a new one
                else:
                    data_frame.loc[len(data_frame)] = data 
    # Returning the appended dataset
    if dataset is not None:
        return dataset
    # or the new one
    return data_frame

# Returns the date of the match
def get_match_date(id=None, match_soup=None)->str:
    if match_soup is None:
        match_soup = get_soup(str(id))
    date = RequestString(match_soup.find(class_="moment-tz-convert").text)
    date.remove_newlines() 
    date.remove_tabs() 
    return date.strip('\n').strip('\t')

# Returns the match style (i.e. Bo3)
def get_match_style(id=None, soup=None)->str:
    if not soup:
        soup = get_soup(str(id))
    match_style = RequestString(soup.find_all(class_="match-header-vs-note")[1].text)
    match_style.remove_newlines()
    match_style.remove_tabs()
    return match_style.strip('\n').strip('\t')

# Returns the event that the match took place in
def get_match_event(id=None, soup=None)->str:
    if not soup:
        soup = get_soup(str(id))
    return soup.find(class_="match-header-event").text

# Returns the match score in a string (2:1)
def get_match_score(id=None, soup=None)->str:
    if not soup:
        soup = get_soup(str(id))
    total_score = RequestString(soup.find(class_="js-spoiler").text)
    total_score.remove_tabs() 
    total_score.remove_newlines() 
    return total_score.strip('\n').strip('\t').replace('\t', '').replace('\n', '')

# Returns the full team name listed on VLR
def get_team_names_long(id=None, soup=None)->str:
    if not soup:
        soup = get_soup(str(id))
    #team_tab = soup.find(class_="match-header-vs")
    team_names = [RequestString(result.text).strip('\n').strip('\t') for result in soup.find_all(class_="wf-title-med")]
    return team_names

# Returns shortened versions of the team names
def get_team_names_short(id=None, game_soup=None):
    if game_soup is None:
        game_soup = get_game_soups(id)[0] #Teams stay the same between maps so using map 1 to determine order is ok
    player_teams = []
    player_teams_html = game_soup.find_all("a", href=True)
    for htelements in player_teams_html:
        player_teams.append(htelements.text.split('\n')[-2].replace('\t', ''))
    return player_teams

# Returns team ids for a match - [Team1, Team2]
def get_team_ids(id=None, soup=None):
    if not soup:
        soup = get_soup(str(id))
    team_ids = []
    team_tab = soup.find(class_="match-header-vs")
    for i in range(2):
        team_ids.append(int(team_tab.find("a", class_=f"match-header-link wf-link-hover mod-{i+1}").get('href').split('/')[2]))
    return team_ids

# Returns vlr ratings for both teams [Team1, Team2]
def get_team_elos(id=None, soup=None):
    team_elos = []
    if not soup:
        soup = get_soup(str(id))
    team_tab = soup.find(class_="match-header-vs")
    team_names = [RequestString(result.text).strip('\n').strip('\t') for result in soup.find_all(class_="wf-title-med")]
    for result in team_tab.find_all(class_="match-header-link-name-elo"):
        if RequestString(result.text).strip('\n').strip('\t').strip('\n').strip('[').strip(']') == '':
            team_elos.append(-1)
            continue
        team_elos.append(int(RequestString(result.text).strip('\n').strip('\t').strip('\n').strip('[').strip(']')))
    return team_elos

# Returns reversed vlr ratings for both teams [Team2, Team1]
def get_opponent_elos(id=None, soup=None):
    opponent_elos = []
    if not soup:
        soup = get_soup(str(id))
    team_tab = soup.find(class_="match-header-vs")
    for result in team_tab.find_all(class_="match-header-link-name-elo"):
        if RequestString(result.text).strip('\n').strip('\t').strip('\n').strip('[').strip(']') == '':
            opponent_elos.append(-1)
            continue
        opponent_elos.append(int(RequestString(result.text).strip('\n').strip('\t').strip('\n').strip('[').strip(']')))
    return opponent_elos[::-1]

# Returns reversed team ids for both teams [Team2, Team1]
def get_opponent_ids(id=None, soup=None):
    if not soup:
        soup = get_soup(str(id))
    opponent_ids = []
    team_tab = soup.find(class_="match-header-vs")
    for i in range(2):
        opponent_ids.append(int(team_tab.find("a", class_=f"match-header-link wf-link-hover mod-{i+1}").get('href').split('/')[2]))
    return opponent_ids[::-1]

# Returns a list of names in a map, in retrieved order from vlr
def get_player_names(game_soup=None):
    player_names_html = game_soup.find_all(class_="text-of")
    player_names = []
    for htelement in player_names_html:
        player_names.append(RequestString(htelement.text).split(' ')[0].replace('\t', '').replace('\n', ''))
    return player_names

# Returns a list of kill # in a map, in retrieved order from vlr
def get_player_kills(game_soup=None):
    player_kills_html = game_soup.find_all(class_="mod-stat mod-vlr-kills")
    player_kills = []
    for htelement in player_kills_html:
        if RequestString(htelement.text).strip().split("\n")[0] == '':
            player_kills.append('***')
        else:
            player_kills.append(int(RequestString(htelement.text).strip().split("\n")[0]))
    return player_kills

# Returns a list of death # in a map, in retrieved order from vlr
def get_player_deaths(game_soup=None):
    player_deaths_html = game_soup.find_all(class_="mod-stat mod-vlr-deaths")
    player_deaths = []
    for htelement in player_deaths_html:
        if RequestString(htelement.find(class_="stats-sq").text).replace('/', '').strip().split("\n")[0] == '':
            player_deaths.append('***')
        else:
            player_deaths.append(int(RequestString(htelement.find(class_="stats-sq").text).replace('/', '').strip().split("\n")[0]))
    return player_deaths

# Returns a list of assist # in a map, in retrieved order from vlr
def get_player_assists(game_soup=None):
    player_assists_html = game_soup.find_all(class_="mod-stat mod-vlr-assists")
    player_assists = []
    for htelement in player_assists_html:
        if RequestString(htelement.text).strip().split("\n")[0] == '':
            player_assists.append('***')
        else:
            player_assists.append(int(RequestString(htelement.text).strip().split("\n")[0]))
    return player_assists

# Returns the score of an individual map (13:7) (Team1 Score, Team2 Score)
def get_game_score(game_soup=None):
    game_score = f"{game_soup.find_all(class_='score')[0].text}: {game_soup.find_all(class_='score')[1].text}"
    return game_score

# Returns the total amount of rounds played in a map
def get_game_rounds_played(game_soup=None):
    return int(game_soup.find_all(class_='score')[0].text) + int(game_soup.find_all(class_='score')[1].text)

# Returns the map played
def get_game_map(game_soup=None):
    map_div = game_soup.find(class_='map')
    map = map_div.find('span', style='position: relative;').text.replace("PICK", '').replace('\n', '').replace('\t', '')
    return map
    
# Returns a list of adr # in a map, in retrieved order from vlr
def get_player_adrs(game_soup=None):
    player_adr_html = game_soup.find_all(class_="stats-sq mod-combat")
    player_adrs = []
    for htelement in player_adr_html:
        if RequestString(htelement.text).strip().split("\n")[0] == '':
            player_adrs.append('***')
        else:
            player_adrs.append(int(RequestString(htelement.text).strip().split("\n")[0]))
    return player_adrs

# Returns a list of agents in a map, in retreived order from vlr
def get_player_agents(game_soup=None):
    players_agents_images = game_soup.find_all('img')
    players_agents = []
    if len(players_agents_images) < 10:
        for i in range(0,10):
            players_agents.append('***')
    for image in players_agents_images:
        if (image.get("title")):
            players_agents.append(image.get("title"))
    return players_agents
    
# Returns a list of player ids in a map, in retrieved order from vlr
def get_player_ids(game_soup=None):
    player_ids = []
    player_ids_html = game_soup.find_all("a", href=True)
    for htelements in player_ids_html:
        player_ids.append((htelements)['href'].split('/')[2])
    return player_ids

# Returns a reversed list of short team names in retrieved order
def get_opponent_name_short(id=None, game_soup=None):
    if game_soup is None:
        game_soup = get_game_soups(id)[0] #Teams stay the same between maps so using map 1 to determine order is ok
    player_teams = []
    player_teams_html = game_soup.find_all("a", href=True)
    for htelements in player_teams_html:
        player_teams.append(htelements.text.split('\n')[-2].replace('\t', ''))
    return player_teams[::-1]

# Returns a reversed list of long team names (Team2, Team1)
def get_opponent_name_long(id=None, soup=None):
    if not soup:
        soup = get_soup(str(id))
    team_names = [RequestString(result.text).strip('\n').strip('\t') for result in soup.find_all(class_="wf-title-med")]
    return team_names[::-1]

# Gets player info from profile page
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

# Fetches a list of match ids from a given number of previous matches
# user defined length
def get_player_match_ids(id: int, amount: int = 1):
    match_ids = []
    for i in range(int(amount/50) + 1):
        player_matches_soup = get_soup(PLAYER + MATCHES + str(id) + '/?page=' + str(i+1))
        matches = player_matches_soup.find_all("a", class_="wf-card fc-flex m-item")
        for match in matches:
            match_ids.append(match.get("href").split('/')[1]) 
    return match_ids[0:amount]

# Fetches a list of match ids from previous games a team has played in. 
# user defined list length
def get_team_match_ids(id: int, amount: int = 1):
    match_ids = []
    for i in range(int(amount/50) + 1):
        player_matches_soup = get_soup(TEAM + MATCHES + str(id) + '/?page=' + str(i+1))
        matches = player_matches_soup.find_all("a", class_="wf-card fc-flex m-item")
        for match in matches:
            match_ids.append(match.get("href").split('/')[1]) 
    return match_ids[0:amount]

# Converts a python dictionary to json format
def to_json(filename: str, data: dict, indent=4, append=False):
    with open(f"{filename}.json", "a") as f:
        json.dump(data, f, indent=indent)
        f.write('\n')  # Add a newline after each JSON object for readability

# Converts a pandas datafram to a .csv file
def to_csv(self : pd.DataFrame, filename='default.csv'):
    self.to_csv(filename + '.csv', index=False)
