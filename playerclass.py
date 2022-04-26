from pymongo import MongoClient
import requests
import sys

class Player:

    playercount = 0

    def __init__(self, id, games, key):
        Player.playercount += 1
        self.id = id
        self.games = games
        self.key = key
        self.game_data, self.top_genres_list = [], []
        self.total_games = None
        self.playerinfo, self.games_dict = {}, {}
        self.persona, self.timecreated, self.lastlogoff, self.countrycode, self.statecode = None, None, None, None, None
        self.get_player_info()
        self.filter_games()

    def get_player_info(self):
        """
        :return: Gets information about the player from the API and saves it to state variables
        """
        url = f'http://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key={self.key}&steamids={self.id}'
        r = requests.get(url)
        for value in r.json()['response']['players']:
            self.persona = value['personaname']
            self.timecreated = value['timecreated']
            self.lastlogoff = value['lastlogoff']
            try:
                self.countrycode = value['loccountrycode']
            except KeyError:
                self.countrycode = 'NA'
            try:
                self.statecode = value['locstatecode']
            except KeyError:
                self.statecode = 'NA'
        self.playerinfo = {'ID': self.id, 'Persona': self.persona, 'Time Created': self.timecreated,
                           'Last Logoff': self.lastlogoff, 'Country': self.countrycode, 'State': self.statecode}

    def filter_games(self):
        """
        :return: Gets information about a player's games from the API and saves to state variables
        """
        url = f'http://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/?key={self.key}&steamid={self.id}' \
              f'&format=json'
        while True:
            r = requests.get(url)
            try:
                self.total_games = r.json()['response']['game_count']
                for value in r.json()['response']['games']:
                    self.game_data.append((value['playtime_forever'], value['appid']))
                break
            except KeyError:
                print('The Steam API encountered an error. Please try running the code again.')
                sys.exit()
        self.game_data.sort(reverse=True)
        self.get_game_info()
        self.top_genres()

    def get_game_info(self):
        """
        :return: Pulls data from the mongo db to create a dictionary that is saved to a state variable
        """
        print(f'Getting game info for {self.persona}...')
        client = MongoClient()
        db = client.SteamGames
        collection = db.Games
        for tup in self.game_data:
            game_id = str(tup[1])
            loc = collection.find_one({"appid": int(game_id)})
            if loc != []:
                try:
                    self.games_dict[game_id] = {'Name': loc['name'], 'Playtime': int(tup[0]),
                                                'Developer': loc['developer'],
                                                'Publisher': loc['publisher'], 'Positive': loc['positive'],
                                                'Negative': loc['negative'], 'Owners': loc['owners'],
                                                'Price': loc['initialprice']}
                except TypeError:
                    pass
            else:
                print('FAIL')
        print('Got game info')
        return

    def top_genres(self):
        """
        :return: Gets genres of the user's most played games and saves to state variables
        """
        print(f'Getting genres for {self.persona}...')
        top_games = min(15, len(self.games_dict))
        counter = 0
        genre_list = []
        for key in self.games_dict:
            if counter == top_games:
                break

            r = requests.get(f'http://store.steampowered.com/api/appdetails?appids={key}')
            if r.json() is not None:
                if r.json()[key]['success'] is True:
                    genre = r.json()[key]['data']['genres']
                    self.games_dict[key]['Genres'] = []
                    if len(genre) > 1:
                        for subdict in genre:
                            genre_list.append(subdict['description'])
                            self.games_dict[key]['Genres'].append(subdict['description'])
                    elif len(genre) == 1:
                        genre_list.append(genre[0]['description'])
                        self.games_dict[key]['Genres'].append(genre[0]['description'])
                elif r.json()[key]['success'] == False:
                    print(self.games_dict[key])
            counter += 1
        self.top_genres_list = self.get_top(genre_list)
        print('Done getting genres')
        return

    @staticmethod
    def get_top(list):
        dict = {}
        for _ in list:
            if _ in dict:
                dict[_] += 1
            else:
                dict[_] = 1
        return dict

    def __str__(self):
        return self.persona
