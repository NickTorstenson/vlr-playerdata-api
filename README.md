# vlr-playerdata-api
Unofficial JSON API for the valorant website vlr.gg

## installation:
clone the repo  and install the package locally with respectively: 
```
git clone git@github.com:michelececcacci/thespike-api.git
cd thespike-api
sudo python3 -m pip install ./
```
Then, you can simply import the package anywhere with 
```python3 
from thespikeapi import thespikeapi
```
## Available functions
* [`get_matches_by_status`](#matches-by-status)
* [`get_match_by_id()`](#match-by-id)
* [`get_top_n()`](#get-top-n)
* [`get_news()`](#get-news)

```
#### Match by id
Takes the id of the wanted match, and retrieves info about it. Here showing only one player for brevity

request: 
```python
get_match_by_id(43000, show_match_info=False)
```
```json
[
    [
        {
            "name": "atakaptan",
            "link": "/player/6510/atakaptan",
            "player id": "6510",
            "team": "FUT Esports",
            "team id": 1184,
            "team elo": 1837,
            "opponent": "Galatasaray Esports",
            "opponent id": 4572,
            "opponent elo": 1560,
            "agent": "omen",
            "map": "ascent",
            "kills": 18,
            "deaths": 8,
            "assists": 9,
            "adr": 199,
            "kpr": 1.06,
            "rounds played": 17
        }
    ]
]

### This project is still work in progress, so feel free to suggest ways to make it better or make contribution to the codebase!
