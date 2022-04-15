import requests
import json
import time
import sys

friendnetworkdict = []

url1 = 'http://api.steampowered.com/ISteamUser/GetFriendList/v0001/?key='
url2 = '&steamid='
url3 = '&relationship=friend'

gamesurl1 = 'http://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/?key='
gamesurl3 = '&format=json'


class Player:

    playercount = 0

    def __init__(self, id, games):
        Player.playercount += 1
        self.id = id
        self.games = games
        self.get_player_info()
        self.filter_games()

    def get_player_info(self):
        ''' Gets information about the player from teh API and takes what we need'''
        url = f'http://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key={KEY}&steamids={self.id}'
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
        url = f'http://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/?key={KEY}&steamid={self.id}&format=json'
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
        self.game_data.sort(reverse=True)
        print(self.persona, self.total_games, self.game_data)
        self.get_game_info()
        self.top_genres()

    def get_game_info(self):
        ''' This pulls data from the json file (hopefully to be replaced
            with mongo db later) and gets info about the games
        '''
        print(f'Getting game info for {self.persona}...')
        with open('steam_data_final.json', 'r') as infile:
            data = json.load(infile)
            self.games_dict = {}
            for tup in self.game_data:
                game_id = str(tup[1])
                try:
                    loc = data[game_id]
                    self.games_dict[game_id] = {'Name': loc['name'], 'Playtime': int(tup[0]),
                                                'Developer': loc['developer'],
                                                'Publisher': loc['publisher'], 'Positive': loc['positive'],
                                                'Negative': loc['negative'], 'Owners': loc['owners'],
                                                'Price': loc['initialprice']}
                except KeyError:
                    pass

        return

    def top_genres(self):
        # Get genres of top 10  most played games
        # Ensuring code doesn't break if user doesn't have many games
        top_games = min(15, len(self.games_dict))
        counter = 0
        genre_list = []
        for key in self.games_dict:
            if counter == 10:
                break

            try:
                r = requests.get(f'http://store.steampowered.com/api/appdetails?appids={key}')
                if r.json() != None:
                    if r.json()[key]['success'] == True:
                        genre = r.json()[key]['data']['genres']
                        if len(genre) > 1:
                            for subdict in genre:
                                genre_list.append(subdict['description'])
                        elif len(genre) == 1:
                            genre_list.append(genre[0]['description'])
            except KeyError:
                pass
            counter += 1
        self.top_genres = self.get_top(genre_list)
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


def get_data(id=0):
    ''' Gets the player's friend list from the API'''
    friendnetworkdict = {}
    if id == 0:
        id = USER_ID
    url = url1 + KEY + url2 + id + url3
    r = requests.get(url)
    friendnetworkdict[id] = []
    if r.json() != {}:
        for value in r.json()['friendslist']['friends']:
            r = requests.get(gamesurl1 + KEY + url2 + value['steamid'] + gamesurl3)
            if r.json()['response'] != {}:
                if r.json()['response']['game_count'] > 0:
                    friendnetworkdict[id].append(value['steamid'])
    return friendnetworkdict


def get_games(gamedict, id):
    ''' Gets the player's games from the API'''
    url = gamesurl1 + KEY + url2 + id + gamesurl3
    r = requests.get(url)
    while r.json() == None:
        r = requests.get(url)
        print('Failed in get_games')
    try:
        gamedict[id] = r.json()['response']['games']
    except KeyError:
        print('The Steam API encountered an error. Please quit and try again.')
    return gamedict


def initialize():
    ''' Starts the file'''
    with open('steamapikey.txt', 'r') as infile:
        global KEY
        KEY = infile.readline()
    valid = False
    while valid == False:
        global USER_ID
        #USER_ID = str(input('Please enter your steam ID:\n'))
        USER_ID = '76561198323942078'
        r = requests.get(gamesurl1 + KEY + url2 + USER_ID + gamesurl3)

        try:
            if r.json()['response'] == {}:
                print('You may have entered the wrong ID or your profile may be private. Please try again.')
            elif r.json()['response']['game_count'] == 0:
                print('Your profile may be private. Please try again.')
            else:
                print('Now loading...')
                return
        except json.decoder.JSONDecodeError:
            print('You have entered an invalid ID. Please try again.')

def create_objects(friendnetworkdict):
    ''' Driver for getting games and info about player's friends '''
    friends = set()
    gamedict = {}
    players = []
    for key, value in friendnetworkdict.items():
        friends.add(key)
        for friend in value:
            friends.add(friend)
    for friend in friends:
        gamedict = get_games(gamedict, friend)
        playerobj = Player(friend, gamedict)
        players.append(playerobj)
    return friends, players

def unique_keys(dict_1, dict_2):
    '''
    :param dict_1: A dictionary
    :param dict_2: A dictionary
    :return: A set of the keys of both dictionaries
    '''
    unique_keys = set()
    for key in dict_1.keys():
        unique_keys.add(key)
    for key in dict_2.keys():
        unique_keys.add(key)
    return unique_keys

def most_similar(players, id=None):
    if id == None:
        id = USER_ID
    for player in players:
        if player.id == id:
            break
    player_words = player.top_genres
    for other_player in players:
        if player.id != other_player.id:
            other_words = other_player.top_genres
            unique = unique_keys(player_words, other_words)
            print(vec(player_words, unique))
            print(vec(other_words, unique))
            print(unique)
            print(player_words)

def vec(myinterests, all_interests):
    ''' In the middle of testing this function, trying to get cosine similarity workign'''
    # Produces a vector that contains the number of times each word is used
    # per speech for all the most common words

    # Making a new list just to contain the words
    my_words = []
    for i in range(len(myinterests)):
        my_words.append(myinterests[i][0])

    all_interests = list(all_interests)
    vector = []

    # Appending the words if they are in the all words list
    for i in range(len(all_interests)):
        if all_interests[i] in my_words:
            idx = my_words.index(all_interests[i])
            vector.append(myinterests[idx][1])
        else:
            vector.append(0)

    return vector

def mag(v):
    """ Magnitude of the vector, v = [vx, vy, vz, ...] """
    return sum([i ** 2 for i in v]) ** .5

def dot(u, v):
    """ Dot product of two vectors """
    return sum([i * j for i, j in zip(u, v)])

def cosine_similarity(self, u, v):
    cos_theta = dot(u, v) / (mag(u) * mag(v))
    return cos_theta

    ''' Next steps: 

    Gets initial stats about the user's games: most played genres, most common categories, etc.
    Getting a working connection with MongoDB to use for the database instead of the file directly
    Converting games and player information into 
    
    Edge cases: What if the player doesn't have friends? What if htey have less than 3? Etc.'''


def main():
    initialize()
    friendnetworkdict = get_data()
    friends, players = create_objects(friendnetworkdict)
    print(friends, players)
    most_similar(players)


if __name__ == '__main__':
    main()