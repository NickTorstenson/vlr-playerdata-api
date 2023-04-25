import vlrscraperv2 as vlrs
import pandas as pd

import vlrstatsapi as vapi

#sapi.get_match_by_id(183777)
#print(sapi.get_player_infos(864))
#sapi.to_json("T1-PRX-bothgame", sapi.get_match_by_id(167393))
#print(len(sapi.get_player_match_ids(864, 3)))
#sapi.to_json(sapi.get_team_match_ids(5248, 4))

americas = [
    2406,
    6961,
    2359,
    188,
    7389,
    1034,
    2,
    120,
    5248,
    2355
]
emea = [
    2593,
    1184,
    474,
    4915,
    2059,
    2304,
    1001,
    7035,
    8877,
    397
]
pacific =[
    8185,
    624,
    17,
    6199,
    14,
    5448,
    878,
    918,
    278,
    8304
]
# #
# all_regions = americas + emea + pacific
# print(all_regions)
# data = []
# unique_matches = []
# matches = []
# for team in all_regions:
#     matches += vlrs.get_team_match_ids(team, 50)
#     unique_matches = list(set(matches))
#     print(len(unique_matches))

print(vlrs.get_match_player_data([64566]))
#vlrs.to_csv(vlrs.get_match_player_data(unique_matches), 'bigassdata(Last50)')
