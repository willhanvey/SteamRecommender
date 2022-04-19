from neo4j import GraphDatabase
from playerclass import Player


class Neo4jDatabase:

    def __init__(self, url, user, password):
        self.driver = GraphDatabase.driver(url, auth=(user, password))

    def close(self):
        self.driver.close()


    def create_player_graph(self, player):
        with self.driver.session() as tx:
            username = player.persona
            player_games = player.games_dict

            tx.run("CREATE (p1:Player { username: $username }) ",
                   username=username)

            for key in player_games.keys():
                game_name = player_games[key]["Name"]
                publisher_name = player_games[key]["Publisher"]
                developer_name = player_games[key]["Developer"]
                try:
                    genres = player_games[key]["Genres"]
                except KeyError:
                    genres = []

                query = (
                    "MATCH (p1:Player) WHERE p1.username = $username "
                    "MERGE (g:Game { name: $name}) "
                    "CREATE (p1)-[:Owns { playtime: $playtime }]->(g) "
                )
                tx.run(query, username=username, name=game_name, price=player_games[key]["Price"],
                       playtime=player_games[key]["Playtime"])

                query = (
                    "MATCH (g:Game) WHERE g.name = $game_name "
                    "MERGE (p:Publisher { name: $publisher_name}) "
                    "MERGE (p)-[:Published]->(g) "
                )
                tx.run(query, game_name=game_name, publisher_name=publisher_name)


                query = (
                    "MATCH (g:Game) WHERE g.name = $game_name "
                    "MERGE (d:Developer { name: $developer_name}) "
                    "MERGE (d)-[:Developed]->(g) "
                )
                tx.run(query, game_name=game_name, developer_name=developer_name)

                for genre_name in genres:
                    query = (
                        "MATCH (g:Game) WHERE g.name = $game_name "
                        "MERGE (n:Genre { name: $genre_name }) "
                        "MERGE (g)-[:Has]->(n) "
                    )
                    tx.run(query, game_name=game_name, genre_name=genre_name)




    def create_graph(self, player):
        with self.driver.session() as session:
            session.write_transaction(self.create_player_graph, player)


    # def print_greeting(self, message):
    #     with self.driver.session() as session:
    #         greeting = session.write_transaction(self._create_and_return_greeting, message)
    #         print(greeting)
    #
    #
    # @staticmethod
    # def _create_and_return_greeting(tx, message):
    #     result = tx.run("CREATE (a:Greeting) "
    #                     "SET a.message = $message "
    #                     "RETURN a.message + ' from node '+ id(a)", message=message)
    #     return result.single()[0]

if __name__ == "__main__":
    greeter = Neo4jDatabase("bolt://localhost:7687", "neo4j", "*ENTER PASSWORD HERE*")

    # put your steam id and key below i dont rly know what the games is for so i put in an empty list []
    # player = Player()

    greeter.create_graph(Player)

    greeter.close()
