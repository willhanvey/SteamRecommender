from neo4j import GraphDatabase
from playerclass import Player


class Neo4jDatabase:

    def __init__(self, url, user, password):
        self.driver = GraphDatabase.driver(url, auth=(user, password))

    def close(self):
        self.driver.close()


    @staticmethod
    def create_player_graph(tx, player):
        username = player.persona
        player_games = player.games_dict
        developers = []
        publishers = []

        tx.run("CREATE (p1:Player { username: $username }) ",
               username=username)

        for key in player_games.keys():
            game_name = player_games[key]["Name"]
            publisher_name = player_games[key]["Publisher"]
            developer_name = player_games[key]["Developer"]

            query = (
                "MATCH (p1:Player) WHERE p1.username = $username "
                "CREATE (g:Game { name: $name, price: $price}) "
                "CREATE (p1)-[:Owns { playtime: $playtime }]->(g) "
            )
            tx.run(query, username=username, name=game_name, price=player_games[key]["Price"],
                   playtime=player_games[key]["Playtime"])

            if publisher_name in publishers:
                query = (
                    "MATCH (g:Game) WHERE g.name = $game_name "
                    "MATCH (p:Publisher) WHERE p.name = $publisher_name "
                    "CREATE (p)-[:Published]->(g) "
                )
                tx.run(query, game_name=game_name, publisher_name=publisher_name)
            else:
                publishers.append(publisher_name)
                query = (
                    "MATCH (g:Game) WHERE g.name = $game_name "
                    "CREATE (p:Publisher { name: $publisher_name}) "
                    "CREATE (p)-[:Published]->(g) "
                )
                tx.run(query, game_name=game_name, publisher_name=publisher_name)


            if developer_name in developers:
                query = (
                    "MATCH (g:Game) WHERE g.name = $game_name "
                    "MATCH (d:Developer) WHERE d.name = $developer_name "
                    "CREATE (d)-[:Developed]->(g) "
                )
                tx.run(query, game_name=game_name, developer_name=developer_name)
            else:
                developers.append(developer_name)
                query = (
                    "MATCH (g:Game) WHERE g.name = $game_name "
                    "CREATE (d:Developer { name: $developer_name}) "
                    "CREATE (d)-[:Developed]->(g) "
                )
                tx.run(query, game_name=game_name, developer_name=developer_name)





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
    greeter = Neo4jDatabase("bolt://localhost:7687", "neo4j", "*PUT YOUR PASSWORD HERE*")

    # put your steam id and key below i dont rly know what the games is for so i put in an empty list []
    # player = Player()

    greeter.create_graph(player)

    greeter.close()
