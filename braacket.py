from bs4 import BeautifulSoup
import requests
import re 
from difflib import SequenceMatcher

class Braacket:
    
    def __init__(self, league):
        # https://braacket.com/league/{league}
        # https://braacket.com/league/{league}/player?rows=999999999
        # ie: 'NCMelee'
        self.league = league
        self.update_player_cache()
        return

    def update_player_cache(self):
        r = requests.get(
            'https://braacket.com/league/'
            f'{self.league}/player?rows=999999999'
        )
        soup = BeautifulSoup(r.text, 'html.parser')
        # <table class='table table-hover'> -v
        # <tbody> -> <tr> -> <td> -> <a> {player}
        players = soup.select("table.table.table-hover a")
        self.player_cache = {}
        url_extract = re.compile(r'.*\/([^\/]*)')
        for player in players:
            if not player.string:
                continue
            player_id = url_extract.match(player['href']).group(1)
            self.player_cache[player.string] = player_id

    def get_player(self, tag):
        print(f"Searching for '{tag}'...")
        probability_list = []
        for key in list(self.player_cache.keys()):
            probability = SequenceMatcher(None, tag.lower(), key.lower()).ratio()
            p_dict = {}
            p_dict['tag'] = key
            p_dict['probability'] = probability
            probability_list.append(p_dict)
        probability_list = sorted(
            probability_list, key=lambda prob: 1-prob['probability']
        )
        print("Top 3 results:")
        for result in probability_list[:3]:
            tag = result['tag']
            prob = result['probability']
            print(f'"{tag}", {prob}')

test = Braacket('NCMelee')
test.get_player('smash.live save state')
