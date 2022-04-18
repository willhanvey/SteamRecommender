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
        self.games_dict = {}
        self.get_player_info()
        self.filter_games()

    def get_player_info(self):
        ''' Gets information about the player from teh API and takes what we need'''
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
        print(self.playerinfo)

    def filter_games(self):
        ''' Gets information about the player's games from the API and takes what we need'''
        url = f'http://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/?key={self.key}&steamid={self.id}&format=json'
        while True:
            r = requests.get(url)
            try:
                self.total_games = r.json()['response']['game_count']
                self.game_data = []
                for value in r.json()['response']['games']:
                    self.game_data.append((value['playtime_forever'], value['appid']))
                break
            except KeyError:
                print('The Steam API encountered an error. Please try running the code again.')
                sys.exit()
        self.game_data.sort(reverse=True)
        print(self.persona, self.total_games, self.game_data)
        self.get_game_info()
        self.top_genres()

    def get_game_info(self):
        ''' This pulls data from the json file (hopefully to be replaced
            with mongo db later) and gets info about the games
        '''
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
        # Get genres of top 15 most played games
        # Ensuring code doesn't break if user doesn't have many games
        print(f'Getting genres for {self.persona}...')
        top_games = min(15, len(self.games_dict))
        counter = 0
        genre_list = []
        for key in self.games_dict:
            if counter == top_games:
                break

            r = requests.get(f'http://store.steampowered.com/api/appdetails?appids={key}')
            if r.json() != None:
                if r.json()[key]['success'] == True:
                    genre = r.json()[key]['data']['genres']
                    if len(genre) > 1:
                        for subdict in genre:
                            genre_list.append(subdict['description'])
                    elif len(genre) == 1:
                        genre_list.append(genre[0]['description'])
                elif r.json()[key]['success'] == False:
                    print(self.games_dict[key])
            counter += 1
        self.top_genres = self.get_top(genre_list)
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
    # FOR FRIENDS:
    # Top games in most similar friends (based on top genres)
    # DO COSINE SIMILARITY WITH OTHER USERS TO GET MOST SIMILAR
    # RECOMMEND OTHER TOP GAMES FROM PUBLISHERS/DEVS OF USER'S TOP GAMES


    def __str__(self):
        return self.persona

