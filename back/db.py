import json

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, scoped_session

import utils

with open('config.json', 'r') as f:
    config = json.load(f)
engine = create_engine(
    f"postgresql://{config['DB_USER']}:{config['DB_PASSWORD']}@{config['DB_HOST']}:{config['DB_PORT']}/{config['DB_NAME']}",
    pool_pre_ping=True
)
session_factory = sessionmaker(bind=engine)
Session = scoped_session(session_factory)


def stop_pool():
    engine.dispose()
    print("PostgreSQL pool closed.")


def select_list():
    with Session() as session:
        query = text(
            """
            SELECT DISTINCT snp 
            FROM snps2
            """
        )
        result = session.execute(query)
        return [row.snp for row in result]


def select_parent(snp):
    with Session() as session:
        query = text(
            """
            SELECT snp
            FROM childs
            WHERE (
                SELECT snp 
                FROM synonyms 
                WHERE :snp = ANY(synonyms)
            ) = ANY (childs)
            LIMIT 1
            """
        )
        result = session.execute(query,
                                 {
                                     "snp": snp
                                 }).fetchone()
        return result[0] if result else None


def select_centroids_dispersion(snp, size):
    with Session() as session:
        query = text(
            """
            SELECT snp,
                   centroids
            FROM   snps2
            WHERE  size = :size
                   AND snp IN (SELECT Unnest(childs)
                               FROM   childs
                               WHERE  snp IN (SELECT snp
                                              FROM   synonyms
                                              WHERE  :snp = ANY ( synonyms ))); 
            """
        )
        result = session.execute(query,
                                 {
                                     "snp": snp,
                                     "size": size
                                 })
        return [utils.transform_row(row) for row in result]


def select_centroids_union(a_points, b_points, size, start, end):
    with Session() as session:
        query = text(
            """
            SELECT     s.snp,
                       s.centroids
            FROM       snps2  AS s
            INNER JOIN tmrcas AS t
            ON         s.snp = t.snp
            WHERE      s.size = :size
            AND        t.tmrca BETWEEN :start AND :end
            AND        (
                EXISTS (
                    SELECT 1
                    FROM   Unnest(s.centroids) AS c
                    WHERE  0 = ANY (
                        SELECT c <-> ap
                        FROM   unnest(cast(:a_points AS point[])) AS ap
                    )
                )
                OR
                EXISTS (
                    SELECT 1
                    FROM   Unnest(s.centroids) AS c
                    WHERE  0 = ANY (
                        SELECT c <-> bp
                        FROM   unnest(cast(:b_points AS point[])) AS bp
                    )
                )
            );
            """
        )
        result = session.execute(query, {
            "size": str(size),
            "a_points": [f"({p[1]},{p[0]})" for p in a_points],
            "b_points": [f"({p[1]},{p[0]})" for p in b_points],
            "start": start,
            "end": end
        })
        return [utils.transform_row(row) for row in result]


def select_centroids_subtraction(a_points, b_points, size, start, end):
    with Session() as session:
        query = text(
            """
            SELECT     s.snp,
                       s.centroids
            FROM       snps2  AS s
            INNER JOIN tmrcas AS t
            ON         s.snp = t.snp
            WHERE      s.size = :size
            AND        t.tmrca BETWEEN :start AND        :end
            AND        EXISTS
                       (
                              SELECT 1
                              FROM   Unnest(s.centroids) AS c
                              WHERE  0 = ANY
                                     (
                                            SELECT c <-> ap
                                            FROM   unnest(cast(:a_points AS point[])) AS ap ) )
            AND        NOT EXISTS
                       (
                              SELECT 1
                              FROM   Unnest(s.centroids) AS c
                              WHERE  0 = ANY
                                     (
                                            SELECT c <-> bp
                                            FROM   unnest(cast(:b_points AS point[])) AS bp ) );
            """
        )
        result = session.execute(query, {
            "size": str(size),
            "a_points": [f"({p[1]},{p[0]})" for p in a_points],
            "b_points": [f"({p[1]},{p[0]})" for p in b_points],
            "start": start,
            "end": end
        })
        return [utils.transform_row(row) for row in result]


def select_centroids_intersection(a_points, b_points, size, start, end):
    with Session() as session:
        query = text(
            """
            SELECT     s.snp,
                       s.centroids
            FROM       snps2  AS s
            INNER JOIN tmrcas AS t
            ON         s.snp = t.snp
            WHERE      s.size = :size
            AND        t.tmrca BETWEEN :start AND        :end
            AND        EXISTS
                       (
                              SELECT 1
                              FROM   Unnest(s.centroids) AS c
                              WHERE  0 = ANY
                                     (
                                            SELECT c <-> ap
                                            FROM   unnest(cast(:a_points AS point[])) AS ap ) )
            AND        EXISTS
                       (
                              SELECT 1
                              FROM   Unnest(s.centroids) AS c
                              WHERE  0 = ANY
                                     (
                                            SELECT c <-> bp
                                            FROM   unnest(cast(:b_points AS point[])) AS bp ) );
            """
        )
        result = session.execute(query, {
            "size": str(size),
            "a_points": [f"({p[1]},{p[0]})" for p in a_points],
            "b_points": [f"({p[1]},{p[0]})" for p in b_points],
            "start": start,
            "end": end
        })
        return [utils.transform_row(row) for row in result]


def select_centroids_xor(a_points, b_points, size, start, end):
    with Session() as session:
        query = text(
            """
            SELECT     s.snp,
                       s.centroids
            FROM       snps2  AS s
            INNER JOIN tmrcas AS t
            ON         s.snp = t.snp
            WHERE      s.size = :size
            AND        t.tmrca BETWEEN :start AND        :end
            AND        (
                       (
                              EXISTS (
                                     SELECT 1
                                     FROM   Unnest(s.centroids) AS c
                                     WHERE  0 = ANY (
                                            SELECT c <-> ap
                                            FROM   unnest(cast(:a_points AS point[])) AS ap ) )
                              AND NOT EXISTS (
                                     SELECT 1
                                     FROM   Unnest(s.centroids) AS c
                                     WHERE  0 = ANY (
                                            SELECT c <-> bp
                                            FROM   unnest(cast(:b_points AS point[])) AS bp ) )
                       )
                       OR
                       (
                              EXISTS (
                                     SELECT 1
                                     FROM   Unnest(s.centroids) AS c
                                     WHERE  0 = ANY (
                                            SELECT c <-> bp
                                            FROM   unnest(cast(:b_points AS point[])) AS bp ) )
                              AND NOT EXISTS (
                                     SELECT 1
                                     FROM   Unnest(s.centroids) AS c
                                     WHERE  0 = ANY (
                                            SELECT c <-> ap
                                            FROM   unnest(cast(:a_points AS point[])) AS ap ) )
                       )
            );
            """
        )
        result = session.execute(query, {
            "size": str(size),
            "a_points": [f"({p[1]},{p[0]})" for p in a_points],
            "b_points": [f"({p[1]},{p[0]})" for p in b_points],
            "start": start,
            "end": end
        })
        return [utils.transform_row(row) for row in result]
