import requests
import json
import time

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
                print('Failed:', self.persona)
                time.sleep(1)
        self.game_data.sort(reverse=True)
        print(self.persona, self.total_games, self.game_data)
        self.get_game_info()

    def get_game_info(self):
        ''' In the middle of debugging this function. This pulls data from the json file (hopefully to be replaced
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
                except:
                    pass

        print(self.persona, '\n', self.games_dict)

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
        print(r.json())
        for value in r.json()['friendslist']['friends']:
            print(value['steamid'])
            r = requests.get(gamesurl1 + KEY + url2 + value['steamid'] + gamesurl3)
            print(r.json())
            if r.json()['response'] != {}:
                if r.json()['response']['game_count'] > 0:
                    print(value['steamid'])
                    friendnetworkdict[id].append(value['steamid'])
                    print(friendnetworkdict)
    print(friendnetworkdict)
    return friendnetworkdict


def get_games(gamedict, id):
    ''' Gets the player's games from the API'''
    url = gamesurl1 + KEY + url2 + id + gamesurl3
    r = requests.get(url)
    gamedict[id] = r.json()['response']['games']
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

def get_friends(friendnetworkdict):
    ''' Driver for getting games and info about player's friends '''
    friends = set()
    gamedict = {}
    players = []
    for key, value in friendnetworkdict.items():
        friends.add(key)
        for friend in value:
            friends.add(friend)
    print(friends)
    for friend in friends:
        gamedict = get_games(gamedict, friend)
        playerobj = Player(friend, gamedict)
        players.append(playerobj)
    return friends, players

    ''' Next steps: 

    Gets initial stats about the user's games: most played genres, most common categories, etc.
    Getting a working connection with MongoDB to use for the database instead of the file directly
    Converting games and player information into NEO4J'''


def main():
    initialize()
    friendnetworkdict = get_data()
    print(friendnetworkdict)
    friends, gamedict = get_friends(friendnetworkdict)


if __name__ == '__main__':
    main()