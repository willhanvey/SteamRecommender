import requests
from pymongo import MongoClient
import json
import sys
from playerclass import Player
from collections import Counter
from Neo4jClass import Neo4jDatabase


def get_data():
    """
    :return: A dictionary with the player's friends taken from the API
    """
    friendnetworkdict = {}
    id = USER_ID
    url = f'http://api.steampowered.com/ISteamUser/GetFriendList/v0001/?key={KEY}&steamid={USER_ID}&relationship=friend'
    r = requests.get(url)
    friendnetworkdict[id] = []
    if r.json() != {}:
        for value in r.json()['friendslist']['friends']:
            oid = value['steamid']
            url = f'http://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/?key={KEY}&steamid={oid}&format=json'
            r = requests.get(url)
            if r.json()['response'] != {}:
                if r.json()['response']['game_count'] > 0:
                    friendnetworkdict[id].append(value['steamid'])
    print(friendnetworkdict)
    return friendnetworkdict


def get_games(gamedict, id):
    """
    :param gamedict: A dictionary of games to be filled
    :param id: The ID of the player to get the games for
    :return: Returns a dict of the player's games from the API
    """
    url = f'http://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/?key={KEY}&steamid={id}&format=json'
    r = requests.get(url)
    while r.json() is None:
        print('Infinite')
        r = requests.get(url)
        print('Failed in get_games')
    try:
        gamedict[id] = r.json()['response']['games']
    except KeyError:
        print(id)
        print('The Steam API encountered an error. Please quit and try again.')
        sys.exit()
    return gamedict


def initialize():
    """
    :return: Creates a global USER_ID variable for the user and a global KEY variable for the API
    """
    with open('steamapikey.txt', 'r') as infile:
        global KEY
        KEY = infile.readline()
    valid = False
    while valid is not False:
        global USER_ID
        USER_ID = str(input('Please enter your steam ID:\n'))
        url = f'http://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/?key={KEY}&steamid={USER_ID}&format=json'
        r = requests.get(url)
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
    """
    :param friendnetworkdict: A dictionary containing the friend network of the player
    :return: The player's friends as a list and a list of the player objects as a list
    """
    friends = set()
    gamedict = {}
    players = []
    for key, value in friendnetworkdict.items():
        friends.add(key)
        for friend in value:
            friends.add(friend)
    for friend in friends:
        gamedict = get_games(gamedict, friend)
        try:
            playerobj = Player(friend, gamedict, KEY)
            players.append(playerobj)
        except:
            pass
    return friends, players


def get_unique(list1, list2):
    """
    :param list1: A list
    :param list2: A list
    :return: A list of the unique items from both lists
    """
    unique = set()
    for val in list1:
        unique.add(val)
    for val in list2:
        unique.add(val)
    return list(unique)


def most_similar(players):
    """
    :param players: The list of player objects
    :return: A dictionary with the cosine similarities between the user and their friends
    """
    sim_list = []
    sim_dict = {}
    for player in players:
        if player.id == USER_ID:
            player_games = list(player.games_dict.keys())
            break
    for other_player in players:
        if player.id != other_player.id:
            print(other_player)
            other_games = list(other_player.games_dict.keys())
            unique = get_unique(player_games, other_games)
            player_vec = vec(player_games, unique)
            comparison_vec = vec(other_games, unique)
            sim_list.append([cosine_similarity(player_vec, comparison_vec), other_player.persona])
    sim_list.sort(reverse=True)
    for sim, persona in sim_list:
        sim_dict[persona] = sim
    return sim_dict


def vec(myinterests, all_interests):
    """
    :param myinterests: The user's list of items
    :param all_interests: The list of all items
    :return: A combined list of the user's list and the list of all items
    """
    # Produces a vector that contains the number of times each word is used
    # per speech for all the most common words

    # Making a new list just to contain the words
    my_words = []
    for i in range(len(myinterests)):
        my_words.append(myinterests[i])

    all_interests = list(all_interests)
    vector = []

    # Appending the words if they are in the all words list
    for i in range(len(all_interests)):
        if all_interests[i] in my_words:
            idx = my_words.index(all_interests[i])
            vector.append(1)
        else:
            vector.append(0)

    return vector


def mag(v):
    """ Magnitude of the vector, v = [vx, vy, vz, ...] """
    return sum([i ** 2 for i in v]) ** .5


def dot(u, v):
    """ Dot product of two vectors """
    return sum([i * j for i, j in zip(u, v)])


def cosine_similarity(u, v):
    """ Calculates the cosine similarity of two vectors """
    cos_theta = dot(u, v) / (mag(u) * mag(v))
    return cos_theta


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


def call_and_recommend(appids, collection, field, field_value):
    """
    :param appids: The list of appids that the player has owned and been recommended
    :param collection: The pymongo collection object
    :param field: The pymongo field that is being sorted by
    :param field_value: The value in the pymongo field that is being looked for
    :return: The updated list of appids and the name of the game being recommended
    """
    genres = (collection.find({field: field_value}).sort("positive", -1).limit(10))
    for genre_rec in genres:
        if genre_rec["appid"] not in appids:
            appids.append(genre_rec["appid"])
            return appids, genre_rec["name"]


def genre_recs(player, appids, collection):
    """
    :param player: The player object
    :param appids: The list of appids that the player has owned and been recommended
    :param collection: The pymongo collection object
    :return: The list of appids updated with games recommended based on genres the player likes
    """
    top_genres = {k: v for k, v in sorted(player.top_genres_list.items(), key=lambda item: item[1], reverse=True)}
    top_genre = list(top_genres.keys())[0]
    second_genre = list(top_genres.keys())[1]
    recommended_games = []
    # Getting the top game of the player's most liked genre based on the top-rated game in that genre
    appids, game_name = call_and_recommend(appids, collection, "genre", top_genre)
    print(f'Because you like games in the {top_genre} genre, we recommend {game_name}!')
    recommended_games.append(game_name)
    appids, game_name = call_and_recommend(appids, collection, "genre", second_genre)
    print(f'Because you like games in the {second_genre} genre, we recommend {game_name}!')
    recommended_games.append(game_name)
    return appids, recommended_games


def dev_recs(player, appids, collection):
    """
    :param player: The player object
    :param appids: The list of appids that the player has owned and been recommended
    :param collection: The pymongo collection object
    :return: The list of appids updated with games recommended based on developers the player likes
    """
    dev_list = [subdict['Developer'] for subdict in player.games_dict.values()]
    devs = Counter(dev_list).most_common(2)
    recommended_games = []
    for dev in devs:
        top_dev = dev[0]
        appids, game_name = call_and_recommend(appids, collection, "developer", top_dev)
        print(f'Because you like games developed by {top_dev}, we recommend {game_name}!')
        recommended_games.append(game_name)
    return appids, recommended_games


def pub_recs(player, appids, collection):
    """
    :param player: The player object
    :param appids: The list of appids that the player has owned and been recommended
    :param collection: The pymongo collection object
    :return: The list of appids updated with games recommended based on publishers the player likes
    """
    pub_list = [subdict['Publisher'] for subdict in player.games_dict.values()]
    pubs = Counter(pub_list).most_common(2)
    recommended_games = []
    for pub in pubs:
        top_pub = pub[0]
        appids, game_name = call_and_recommend(appids, collection, "publisher", top_pub)
        print(f'Because you like games published by {top_pub}, we recommend {game_name}!')
        recommended_games.append(game_name)
    return appids, recommended_games


def player_recommendations(player):
    """
    :param player: The player's class
    :return: Prints the game recommendations based on player information and returns appids list
    """
    client = MongoClient()
    db = client.SteamGames
    collection = db.Games
    appids = [sublist['appid'] for sublist in player.games[player.id]]
    recommended_games = []
    for rec in (genre_recs, dev_recs, pub_recs):
        appids, reced_games = rec(player, appids, collection)
        recommended_games.append(reced_games)
    return recommended_games


def friend_recommendations(cosine_dict, player, recommended_games, neo):
    """
    :param cosine_dict: A dictionary of the most similar players
    :param player: The player object
    :param recommended_games: A list of games the player owns and has been recommended already
    :param neo: The neo4j database
    :return: Prints game recommendations
    """

    # Making a recommendation based on a game that a lot of the player's friends play
    result = neo.run_game_query("match (p:Player) - [r] -> (g:Game) return g, count(r) AS Num_Owners order by \
                                Num_Owners desc limit 25")
    for game in result:
        if game not in recommended_games:
            print(f'The game that the highest number of your friends have that you don\'t is {game}, so check it out!')
            recommended_games.append(game)
            break

    # Making a recommendation based on players who have also played a lot of the player's top game
    most_played = recommended_games[0]
    result = neo.run_game_query("match (g2:Game) <- [r2] - (p:Player) - [r] -> (g:Game {name: \"" + most_played + "\"})\
                                return g2, count(g2) order by count(g2) desc limit 25")
    for game in result:
        if game not in recommended_games:
            print(f'Fans of your top game, {most_played}, have also played a lot of {game}, so you might like it!')
            recommended_games.append(game)
            break

    # Making a recommendation based on the player's most similar friend's most played game
    friend = list(cosine_dict.keys())[0]
    result = neo.run_game_query("match(n) <- [r] - (p:Player {username: \"" + friend + "\"}) return n as Top_Games,\
                                r.playtime as Playtime order by r.playtime desc limit 25")
    for game in result:
        if game not in recommended_games:
            print(f'Your most similar friend based on game libraries, {friend}, has been playing a lot of {game}, so '
                  f'you might want to try it!')
            recommended_games.append(game)
            break

    # Making a recommendation based on the player who plays the most games from the most similar developer
    dev_list = [subdict['Developer'] for subdict in player.games_dict.values()]
    top_dev = (Counter(dev_list).most_common(2))[0][0]
    result = neo.run_game_query("CALL {match (d: Developer {name: \"" + top_dev + "\"}) -[] -> (g:Game)<- [r] - \
                                (p:Player) return p, count(r) as Num order by Num desc limit 1 } match (n) <- [r] - \
                                (p) return n as Games, r.playtime as Playtime order by r.playtime desc limit 25")
    for game in result:
        if game not in recommended_games:
            print(f'Your friends who also enjoy games by your most played developer, {top_dev}, also enjoy {game}!')
            recommended_games.append(game)
            break

    # Making a recommendation based on the player who plays the most games from the most similar publisher
    pub_list = [subdict['Publisher'] for subdict in player.games_dict.values()]
    top_pub = (Counter(pub_list).most_common(2))[0][0]
    result = neo.run_game_query("CALL {match (p:Publisher {name: \"" + top_pub + "\"}) -[] -> (g:Game)<- [r] - \
                                (p2:Player) return p2, count(r) as Num order by Num desc limit 1 } match (n) <- [r] - \
                                (p2) return n as Games, r.playtime as Playtime order by r.playtime desc limit 25")
    for game in result:
        if game not in recommended_games:
            print(f'Your friends who also enjoy games by your most played publisher, {top_pub}, also enjoy {game}!')
            recommended_games.append(game)
            break

    print('\nHopefully, you can play and enjoy some of these games!')


def get_recommendations(cosine_dict, player, neodb):
    """
    :param cosine_dict: A dictionary of the most similar players
    :param player: The player object
    :param neodb: The neo4j database
    :return: None
    """
    print('\nFirst, for some games recommended based on your interests:')
    recommended_games = player_recommendations(player)
    print('\nNow, for some games recommended based on your friends\' interests:')
    game_names = [player.games_dict[subdict]['Name'] for subdict in player.games_dict]
    game_names = game_names + recommended_games
    friend_recommendations(cosine_dict, player, game_names, neodb)


def main():
    initialize()
    friendnetworkdict = get_data()
    friends, players = create_objects(friendnetworkdict)
    cosine_dict = most_similar(players)
    with open("neo4jpassword.txt", "r") as infile:
        neopassword = infile.readline()
    neodb = Neo4jDatabase("bolt://localhost:7687", "neo4j", neopassword)
    for player in players:
        neodb.create_player_graph(player)
    for player in players:
        if player.id == USER_ID:
            get_recommendations(cosine_dict, player, neodb)


if __name__ == '__main__':
    main()
