import pandas as pd
import matplotlib.pyplot as plt
import networkx as nx
from py2neo import Graph, Node, Relationship

class Neo4jQueries:
    def __init__(self, neo4j_connector):
        """
        Initialise la classe avec un connecteur Neo4j
        
        Args:
            neo4j_connector: Instance de Neo4jConnector
        """
        self.neo4j = neo4j_connector
        self.graph = self.neo4j.graph if self.neo4j else None
    
    def query_14_actor_with_most_films(self):
        """
        14. Trouve l'acteur ayant joué dans le plus grand nombre de films
        
        Returns:
            tuple: (nom de l'acteur, nombre de films)
        """
        if not self.graph:
            return None, 0
            
        query = """
        MATCH (a:Actor)-[:A_JOUE_DANS]->(f:Film)
        WITH a, count(f) AS film_count
        RETURN a.name AS actor_name, film_count
        ORDER BY film_count DESC
        LIMIT 1
        """
        
        result = self.graph.run(query).data()
        if result:
            return result[0]["actor_name"], result[0]["film_count"]
        else:
            return None, 0
    
    def query_15_actors_played_with_anne_hathaway(self):
        """
        15. Liste des acteurs ayant joué dans des films avec Anne Hathaway
        
        Returns:
            list: Liste de dictionnaires (acteur, films)
        """
        if not self.graph:
            return []
            
        query = """
        MATCH (anne:Actor {name: "Anne Hathaway"})-[:A_JOUE_DANS]->(f:Film)<-[:A_JOUE_DANS]-(other:Actor)
        WHERE other.name <> "Anne Hathaway"
        WITH other, collect(f.title) AS films
        RETURN other.name AS actor_name, films
        ORDER BY other.name
        """
        
        result = self.graph.run(query).data()
        return result
    
    def query_16_actor_with_highest_revenue(self):
        """
        16. Trouve l'acteur ayant joué dans des films totalisant le plus de revenus
    
        Returns:
            tuple: (nom de l'acteur, revenu total)
        """
        if not self.graph:
            return None, 0
    
        query = """
        MATCH (a:Actor)-[:A_JOUE_DANS]->(f:Film)
        WHERE f.revenue IS NOT NULL AND f.revenue <> ""
        WITH a, sum(toFloat(f.revenue)) AS total_revenue
        RETURN a.name AS actor_name, total_revenue
        ORDER BY total_revenue DESC
        LIMIT 1
        """
    
        result = self.graph.run(query).data()
        if result:
            return result[0]["actor_name"], result[0]["total_revenue"]
        else:
            return None, 0

    
    def query_17_average_votes(self):
        """
        17. Calcule la moyenne des votes
        
        Returns:
            float: Moyenne des votes
        """
        if not self.graph:
            return 0
            
        query = """
        MATCH (f:Film)
        WHERE f.votes IS NOT NULL
        RETURN avg(f.votes) AS avg_votes
        """
        
        result = self.graph.run(query).data()
        if result:
            return result[0]["avg_votes"]
        else:
            return 0
    
    def query_18_most_represented_genre(self):
        """
        18. Détermine le genre le plus représenté
        
        Returns:
            tuple: (genre, nombre de films)
        """
        if not self.graph:
            return None, 0
            
        # Note: Vous devrez d'abord créer des nœuds Genre et des relations APPARTIENT_AU
        # Si cela n'a pas été fait, cette requête ne retournera rien
        
        query = """
        MATCH (g:Genre)<-[:APPARTIENT_AU]-(f:Film)
        WITH g, count(f) AS film_count
        RETURN g.name AS genre, film_count
        ORDER BY film_count DESC
        LIMIT 1
        """
        
        result = self.graph.run(query).data()
        if result:
            return result[0]["genre"], result[0]["film_count"]
        else:
            # Plan B: Vérifier si le genre est stocké comme propriété des films
            query_alt = """
            MATCH (f:Film)
            WHERE f.genre IS NOT NULL
            RETURN f.genre AS genre, count(*) AS film_count
            ORDER BY film_count DESC
            LIMIT 1
            """
            
            result_alt = self.graph.run(query_alt).data()
            if result_alt:
                return result_alt[0]["genre"], result_alt[0]["film_count"]
            
            return None, 0
    
    def query_19_films_with_your_costars(self, team_member_name):
        """
        19. Trouve les films des acteurs ayant joué avec un membre de l'équipe
        
        Args:
            team_member_name (str): Nom du membre de l'équipe
            
        Returns:
            list: Liste de films
        """
        if not self.graph:
            return []
            
        query = """
        MATCH (you:Actor {name: $member_name})-[:A_JOUE_DANS]->(f1:Film)<-[:A_JOUE_DANS]-(costar:Actor),
              (costar)-[:A_JOUE_DANS]->(f2:Film)
        WHERE f1 <> f2
        RETURN DISTINCT f2.title AS film_title, f2.year AS year
        ORDER BY year DESC, film_title
        """
        
        result = self.graph.run(query, member_name=team_member_name).data()
        return result
    
    def query_20_director_with_most_actors(self):
        """
        20. Trouve le réalisateur ayant travaillé avec le plus d'acteurs
        
        Returns:
            tuple: (nom du réalisateur, nombre d'acteurs)
        """
        if not self.graph:
            return None, 0
            
        query = """
        MATCH (d:Director)-[:A_REALISE]->(f:Film)<-[:A_JOUE_DANS]-(a:Actor)
        WITH d, count(DISTINCT a) AS actor_count
        RETURN d.name AS director_name, actor_count
        ORDER BY actor_count DESC
        LIMIT 1
        """
        
        result = self.graph.run(query).data()
        if result:
            return result[0]["director_name"], result[0]["actor_count"]
        else:
            return None, 0
    
    def query_21_most_connected_films(self, limit=10):
        """
        21. Trouve les films les plus "connectés" (avec le plus d'acteurs en commun)
        
        Args:
            limit (int): Nombre de films à retourner
            
        Returns:
            list: Liste de dictionnaires (film1, film2, acteurs_communs)
        """
        if not self.graph:
            return []
            
        query = """
        MATCH (f1:Film)<-[:A_JOUE_DANS]-(a:Actor)-[:A_JOUE_DANS]->(f2:Film)
        WHERE id(f1) < id(f2)
        WITH f1, f2, collect(a.name) AS common_actors
        RETURN f1.title AS film1, f2.title AS film2, 
               length(common_actors) AS common_actor_count,
               common_actors
        ORDER BY common_actor_count DESC
        LIMIT $limit
        """
        
        result = self.graph.run(query, limit=limit).data()
        return result
    
    def query_22_actors_with_most_directors(self, limit=5):
        """
        22. Trouve les 5 acteurs ayant joué avec le plus de réalisateurs
        
        Args:
            limit (int): Nombre d'acteurs à retourner
            
        Returns:
            list: Liste de dictionnaires (acteur, nombre de réalisateurs)
        """
        if not self.graph:
            return []
            
        query = """
        MATCH (a:Actor)-[:A_JOUE_DANS]->(f:Film)<-[:A_REALISE]-(d:Director)
        WITH a, count(DISTINCT d) AS director_count, collect(DISTINCT d.name) AS directors
        RETURN a.name AS actor_name, director_count, directors
        ORDER BY director_count DESC
        LIMIT $limit
        """
        
        result = self.graph.run(query, limit=limit).data()
        return result
    
    def query_23_recommend_film_for_actor(self, actor_name):
        """
        23. Recommande un film à un acteur en fonction des genres où il a joué
        
        Args:
            actor_name (str): Nom de l'acteur
            
        Returns:
            list: Liste de films recommandés
        """
        if not self.graph:
            return []
            
        # Plan B si pas de nœuds Genre
        query_alt = """
        // Trouver les films où l'acteur a joué
        MATCH (a:Actor {name: $actor_name})-[:A_JOUE_DANS]->(f:Film)
        WITH a, collect(f.id) AS actor_films
        
        // Trouver tous les films
        MATCH (f:Film)
        WHERE NOT f.id IN actor_films
        
        // Trier par rating et votes
        RETURN f.title AS film_title, f.year AS year, f.rating AS rating, f.votes AS votes
        ORDER BY f.rating DESC, f.votes DESC
        LIMIT 5
        """
        
        try:
            result = self.graph.run(query_alt, actor_name=actor_name).data()
            return result
        except Exception as e:
            print(f"Erreur dans query_23: {e}")
            return []
    
    def query_24_create_influence_relationships(self):
        """
        24. Crée des relations INFLUENCE_PAR entre réalisateurs basées sur similarités de genres
        
        Returns:
            int: Nombre de relations créées
        """
        if not self.graph:
            return 0
            
        # Cette requête crée des relations INFLUENCE_PAR si les réalisateurs ont travaillé sur
        # des films de genres similaires
        
        query = """
        // Trouver les genres par réalisateur
        MATCH (d:Director)-[:A_REALISE]->(f:Film)
        WITH d, collect(f.genre) AS genres
        
        // Comparer les réalisateurs
        MATCH (d2:Director)-[:A_REALISE]->(f2:Film)
        WHERE id(d) < id(d2)
        WITH d, d2, genres, collect(f2.genre) AS genres2
        
        // Calculer similarité (simple : nombre de genres en commun)
        WITH d, d2, 
             [g IN genres WHERE g IN genres2] AS common_genres,
             size(genres) AS d1_genres_count,
             size(genres2) AS d2_genres_count
        WHERE size(common_genres) > 0
        
        // Créer la relation si similarité > seuil
        WITH d, d2, common_genres,
             size(common_genres)*1.0 / (d1_genres_count + d2_genres_count - size(common_genres)) AS jaccard_index
        WHERE jaccard_index > 0.3
        
        // Créer la relation
        MERGE (d)-[r:INFLUENCE_PAR]->(d2)
        SET r.similarity = jaccard_index,
            r.common_genres = common_genres
        
        RETURN count(r) AS relationship_count
        """
        
        result = self.graph.run(query).data()
        if result:
            return result[0]["relationship_count"]
        else:
            return 0
    
    def query_25_shortest_path_between_actors(self, actor1_name, actor2_name):
        """
        25. Trouve le chemin le plus court entre deux acteurs
        
        Args:
            actor1_name (str): Nom du premier acteur
            actor2_name (str): Nom du deuxième acteur
            
        Returns:
            list: Liste des nœuds du chemin
        """
        if not self.graph:
            return []
            
        query = """
        MATCH path = shortestPath(
          (a1:Actor {name: $actor1})-[:A_JOUE_DANS|:A_REALISE*..10]-(a2:Actor {name: $actor2})
        )
        RETURN [node IN nodes(path) | CASE
            WHEN node:Actor THEN {type: 'Actor', name: node.name}
            WHEN node:Film THEN {type: 'Film', title: node.title}
            ELSE {type: 'Unknown', id: id(node)}
        END] AS path_nodes
        """
        
        try:
            result = self.graph.run(query, actor1=actor1_name, actor2=actor2_name).data()
            if result:
                return result[0]["path_nodes"]
            else:
                # Essayer une requête alternative avec moins de contraintes
                query_alt = """
                MATCH path = shortestPath(
                  (a1:Actor {name: $actor1})-[*..6]-(a2:Actor {name: $actor2})
                )
                RETURN [node IN nodes(path) | CASE
                    WHEN node:Actor THEN {type: 'Actor', name: node.name}
                    WHEN node:Film THEN {type: 'Film', title: node.title}
                    ELSE {type: 'Unknown', id: id(node)}
                END] AS path_nodes
                """
                alt_result = self.graph.run(query_alt, actor1=actor1_name, actor2=actor2_name).data()
                if alt_result:
                    return alt_result[0]["path_nodes"]
                return []
        except Exception as e:
            print(f"Erreur dans query_25: {e}")
            return []
    
    def query_26_actor_communities(self, max_communities=5):
        """
        26. Analyse les communautés d'acteurs
        
        Args:
            max_communities (int): Nombre maximum de communautés à retourner
            
        Returns:
            tuple: (DataFrame des communautés, graphe NetworkX pour visualisation)
        """
        if not self.graph:
            return None, None
            
        # Approche alternative sans GDS
        return self._query_26_without_gds(max_communities)
    
    def _query_26_without_gds(self, max_communities=5):
        """
        Implémentation alternative de l'analyse des communautés sans GDS
        """
        if not self.graph:
            return None, None
            
        # Requête simple pour trouver des groupes d'acteurs ayant joué ensemble
        query = """
        MATCH (f:Film)<-[:A_JOUE_DANS]-(a:Actor)
        WITH f, collect(a) AS actors
        WHERE size(actors) >= 3
        WITH [a IN actors | a.name] AS actor_names, count(f) AS film_count
        RETURN actor_names, film_count
        ORDER BY film_count DESC, size(actor_names) DESC
        LIMIT $max_communities
        """
        
        communities = self.graph.run(query, max_communities=max_communities).data()
        
        if not communities:
            return None, None
        
        # Convertir en DataFrame
        df = pd.DataFrame([{
            'communityId': i,
            'actors': community['actor_names'],
            'film_count': community['film_count'],
            'community_size': len(community['actor_names'])
        } for i, community in enumerate(communities)])
        
        # Visualisation avec NetworkX
        G = nx.Graph()
        
        for i, community in enumerate(communities):
            actor_names = community['actor_names']
            
            # Ajouter des nœuds pour chaque acteur
            for actor in actor_names:
                G.add_node(actor, community=i)
            
            # Ajouter des arêtes entre tous les acteurs d'une même communauté
            for idx, actor1 in enumerate(actor_names):
                for actor2 in actor_names[idx+1:]:
                    G.add_edge(actor1, actor2, weight=1)
        
        return df, G
    
    # Questions transversales
    def query_28_recommend_films_based_on_actor_preferences(self, actor_name, limit=5):
        """
        28. Recommande des films aux utilisateurs en fonction des préférences d'un acteur
        
        Args:
            actor_name (str): Nom de l'acteur
            limit (int): Nombre de films à recommander
            
        Returns:
            list: Liste de films recommandés
        """
        if not self.graph:
            return []
            
        # Alternative si pas de nœuds Genre
        query_alt = """
        // Trouver les acteurs qui ont joué avec l'acteur cible
        MATCH (a:Actor {name: $actor_name})-[:A_JOUE_DANS]->(f:Film)<-[:A_JOUE_DANS]-(costar:Actor)
        
        // Trouver les films des co-stars où l'acteur cible n'a pas joué
        MATCH (costar)-[:A_JOUE_DANS]->(other_film:Film)
        WHERE NOT (a)-[:A_JOUE_DANS]->(other_film)
        
        // Agrégation par film
        WITH other_film, count(DISTINCT costar) AS costar_count
        
        // Trier et retourner
        RETURN other_film.title AS title, 
               other_film.year AS year,
               costar_count AS common_actor_count
        ORDER BY common_actor_count DESC, other_film.votes DESC
        LIMIT $limit
        """
        
        try:
            result = self.graph.run(query_alt, actor_name=actor_name, limit=limit).data()
            return result
        except Exception as e:
            print(f"Erreur dans query_28: {e}")
            return []
    
    def query_29_create_competition_relationship(self):
        """
        29. Crée une relation "concurrence" entre réalisateurs de films similaires la même année
        
        Returns:
            int: Nombre de relations créées
        """
        if not self.graph:
            return 0
            
        query = """
        // Trouver les paires de réalisateurs avec des films sortis la même année
        MATCH (d1:Director)-[:A_REALISE]->(f1:Film),
              (d2:Director)-[:A_REALISE]->(f2:Film)
        WHERE d1 <> d2
        AND f1.year = f2.year
        AND f1 <> f2
        
        // Vérifier si les films sont similaires (même genre)
        WITH d1, d2, f1, f2
        WHERE f1.genre IS NOT NULL AND f2.genre IS NOT NULL
        AND any(g IN split(f1.genre, ",") WHERE g IN split(f2.genre, ","))
        
        // Créer la relation de concurrence
        MERGE (d1)-[r:EN_CONCURRENCE_AVEC]->(d2)
        ON CREATE SET r.count = 1,
                      r.years = [f1.year],
                      r.film_pairs = [[f1.title, f2.title]]
        ON MATCH SET r.count = r.count + 1,
                     r.years = CASE WHEN NOT f1.year IN r.years THEN r.years + f1.year ELSE r.years END,
                     r.film_pairs = r.film_pairs + [[f1.title, f2.title]]
        
        RETURN count(r) AS new_relationships
        """
        
        try:
            result = self.graph.run(query).data()
            if result:
                # Compter toutes les relations EN_CONCURRENCE_AVEC
                count_query = """
                MATCH ()-[r:EN_CONCURRENCE_AVEC]->()
                RETURN count(r) AS total_relationships
                """
                count_result = self.graph.run(count_query).data()
                return count_result[0]["total_relationships"]
            else:
                return 0
        except Exception as e:
            print(f"Erreur dans query_29: {e}")
            return 0
    
    def query_30_analyze_director_actor_collaborations(self, min_collaborations=2):
        """
        30. Identifie et analyse les collaborations fréquentes entre réalisateurs et acteurs
        
        Args:
            min_collaborations (int): Nombre minimum de collaborations
            
        Returns:
            tuple: (DataFrame des collaborations, DataFrame des statistiques commerciales)
        """
        if not self.graph:
            return None, None
            
        # Identifier les collaborations fréquentes
        query_collaborations = """
        MATCH (d:Director)-[:A_REALISE]->(f:Film)<-[:A_JOUE_DANS]-(a:Actor)
        WITH d, a, collect(f) AS films
        WHERE size(films) >= $min_collaborations
        
        RETURN d.name AS director, 
               a.name AS actor, 
               size(films) AS collaboration_count,
               [f IN films | f.title] AS film_titles
        ORDER BY collaboration_count DESC
        """
        
        # Analyser le succès commercial de ces collaborations
        query_commercial = """
        MATCH (d:Director)-[:A_REALISE]->(f:Film)<-[:A_JOUE_DANS]-(a:Actor)
        WITH d, a, collect(f) AS films
        WHERE size(films) >= $min_collaborations
        
        WITH d, a, films,
             [f IN films | f.revenue] AS revenues,
             [f IN films | f.votes] AS votes
        
        RETURN d.name AS director,
               a.name AS actor,
               size(films) AS collaboration_count,
               avg(revenues) AS avg_revenue,
               avg(votes) AS avg_votes
        ORDER BY avg_revenue DESC
        """
        
        try:
            collaborations = self.graph.run(query_collaborations, min_collaborations=min_collaborations).data()
            commercial = self.graph.run(query_commercial, min_collaborations=min_collaborations).data()
            
            return pd.DataFrame(collaborations), pd.DataFrame(commercial)
        except Exception as e:
            print(f"Erreur dans query_30: {e}")
            return None, None
