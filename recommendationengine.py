import requests
from pymongo import MongoClient
import json
import time
import sys
import pprint
from playerclass import Player
friendnetworkdict = []

url1 = 'http://api.steampowered.com/ISteamUser/GetFriendList/v0001/?key='
url2 = '&steamid='
url3 = '&relationship=friend'

gamesurl1 = 'http://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/?key='
gamesurl3 = '&format=json'


def get_data(id=0):
    ''' Gets the player's friend list from the API'''
    friendnetworkdict = {}
    if id == 0:
        id = USER_ID
    url = url1 + KEY + url2 + id + url3
    r = requests.get(url)
    friendnetworkdict[id] = []
    if r.json() != {}:
        counter = 0
        for value in r.json()['friendslist']['friends']:
            r = requests.get(gamesurl1 + KEY + url2 + value['steamid'] + gamesurl3)
            if r.json()['response'] != {}:
                if r.json()['response']['game_count'] > 0:
                    friendnetworkdict[id].append(value['steamid'])
                    counter += 1
                    if counter == 4:
                        break
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
        playerobj = Player(friend, gamedict, KEY)
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
            pass
    else:
        player_words = player.top_genres
        for other_player in players:
            if player.id != other_player.id:
                other_words = other_player.top_genres
                unique = unique_keys(player_words, other_words)
                print(unique)

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

def load_into_mongo():
    # setting up the mongo connection and creating a new database
    client = MongoClient()
    db = client.SteamGames
    collection = db.Games
    db.drop_collection(collection)

    # reading the json data
    with open('steam_data_final.json') as f:
        file_data = json.load(f)

    # turning the json dict to a list
    games_list = []
    for key in file_data.keys():
        file_data[key]["appid"] = key
        games_list.append(file_data[key])

    # inserting games into the database
    collection.insert_many(games_list)

def main():
    initialize()
    friendnetworkdict = get_data()
    friends, players = create_objects(friendnetworkdict)
    print(friends, players)
    most_similar(players)


if __name__ == '__main__':
    main()