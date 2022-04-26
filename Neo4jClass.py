from neo4j import GraphDatabase


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

    def run_game_query(self, query):
        with self.driver.session() as session:
            result = (session.run(query))
            games_list = []
            for x in result:
                games_list.append(list(dict(x[0]).values())[0])
        return games_list