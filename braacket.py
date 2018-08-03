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
        # pretty straight forward. the leagues are their name
        # in the url, however as you'll see later on, players
        # have a unique id assigned to them that we have to 
        # extract with BeautifulSoup

        # player cache is laid out as such:
        # {
        #   'tag1': 'uuid',
        #   'tag2': 'uuid',
        #   'tag3': 'uuid',
        #   ...
        # }
        r = requests.get(
            'https://braacket.com/league/'
            f'{self.league}/player?rows=999999999')
            # dear braacket, please never disable this upperbound
        soup = BeautifulSoup(r.text, 'html.parser')
        # <table class='table table-hover'> -v
        # <tbody> -> <tr> -> <td> -> <a> {player}
        players = soup.select("table.table.table-hover a")
        self.player_cache = {}
        # /league/{league}/player/XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX
        url_extract = re.compile(r'.*\/([^\/]*)')
        for player in players:
            # BeautifulSoup returns exactly one empty
            # player, not sure why...
            if not player.string:
                continue
            # match // extract, potential for a mtg fuse spell
            uuid = url_extract.match(player['href']).group(1)
            self.player_cache[player.string] = uuid

    def player_search(self, tag):
        probability_list = []
        # use SequenceMatcher to run the match ratio of each
        # tag in the cache against the searched tag. if the top
        # match is >.90, we'll automatically choose it, otherwise
        # return the list of the top 3 matches and their ratios
        # (user will have to type-check the return value to 
        # determine the appopriate course of action)
        for key in list(self.player_cache.keys()):
            probability = SequenceMatcher(
                None, tag.lower(), key.lower()
                ).ratio()
            p_dict = {}
            p_dict['tag'] = key
            p_dict['uuid'] = self.player_cache[key]
            p_dict['probability'] = probability
            probability_list.append(p_dict)
        # once the probability list is populated,
        # sort it by probability, most likely to least
        probability_list = sorted(
            probability_list, 
            key=lambda prob: 1-prob['probability'])
        if probability_list[0]['probability'] >= 0.9:
            # {
            #   'tag': matched tag
            #   'uuid': uuid 
            #   'probability': probability (float)
            # }
            return probability_list[0]
        # top 3 results, same as above but in a list
        # sorted from most likely to least likely
        return probability_list[:3]

    def player_stats(self, uuid):
        r = requests.get(
            'https://braacket.com/league/'
            f'{self.league}/player/{uuid}')
        soup = BeautifulSoup(r.text, 'html.parser')
        player_stats = {} # gonna fill this w/ a lot of stuff
        # :: TAG ::      
        # tag can be found in: 
        # <tr> -> <td> -> <h4 class='ellipsis'>
        tag = soup.select("tr td h4.ellipsis")[0].get_text().strip()
        player_stats['tag'] = tag
        # :: RANKING :: 
        ranking_info = soup.select(
            'section div.row div.col-lg-6 '
            'div.panel.panel-default.my-box-shadow '
            'div.panel-body '
            'div.my-dashboard-values-main')[0].stripped_strings # generator
        ranking_info = [text for text in ranking_info] # array !
        rank_int = int(ranking_info[0]) # rank
        out_of_extract = re.compile(r'\/ ([0-9]+)$')
        out_of = out_of_extract.match(ranking_info[2]).group(1) # '/ XXXX'
        out_of_int = int(out_of)
        ranking = {
            'rank': rank_int,
            'out_of': out_of_int 
        }
        # get info from the rest of the sub-panels
        # these can be things like, the date range of
        # the player, the ranking type, their raw score,
        # the activity requirements, and whether or not
        # the player meets said requirement. 
        sub_panels = soup.select(
            'section div.row div.col-lg-6 '
            'div.panel.panel-default.my-box-shadow '
            'div.panel-body '
            'div.my-dashboard-values-sub')
        sub_panels_stripped = {}
        for panel in sub_panels:
            panel_array = [text for text in panel.stripped_strings]
            # take the 1st item, lower its case, and make it the key.
            # take the rest of the items in the array, and join them with
            # a space and make it the value.
            sub_panels_stripped[panel_array[0].lower()] = ' '.join(panel_array[1:])
            ranking = {**ranking, **sub_panels_stripped} # merge into ranking dict
        # example: 
        # {
        #   'rank': 33, (int)
        #   'out_of': 2333, (int)
        #   'score': '1234', (str)
        #   'type': 'TrueSkill™', (str)
        #   'date': '04 December 2017 - 31 December 2018', (str)
        #   'activity requirement': 'Requires 4 tournaments played within last 4 months' (str)
        # }
        player_stats['ranking'] = ranking
        return player_stats

test = Braacket('NCMelee')
test.player_search('smash.live save state')
test.player_stats('A3F079E2-CAB3-463B-8D4E-6F43A0126759')
