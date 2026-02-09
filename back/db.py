import json
import re

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, scoped_session

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


def parse_pg_point_array(pg_string):
    if not pg_string:
        return []
    points = re.findall(r"\(([-+]?\d*\.?\d+),([-+]?\d*\.?\d+)\)", pg_string)
    return [[float(p[0]), float(p[1])] for p in points]


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
        raw_results = [dict(row._mapping) for row in result]
        for row in raw_results:
            if isinstance(row['centroids'], str):
                row['centroids'] = parse_pg_point_array(row['centroids'])
        return raw_results


def select_centroids_similarity(points_include, points_exclude, size, start, end):
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
                                            SELECT c <->                            p
                                            FROM   unnest(cast(:points_include AS point[])) AS p ) )
            AND        NOT EXISTS
                       (
                              SELECT 1
                              FROM   Unnest(s.centroids) AS c
                              WHERE  0 = ANY
                                     (
                                            SELECT c <-> bp
                                            FROM   unnest(cast(:points_exclude AS point[])) AS bp ) );
            """
        )
        result = session.execute(query, {
            "size": str(size),
            "points_include": "{" + ",".join([f'"{(p[1], p[0])}"' for p in points_include]) + "}",
            "points_exclude": "{" + ",".join([f'"{(p[1], p[0])}"' for p in points_exclude]) + "}",
            "start": start,
            "end": end
        })
        raw_results = [dict(row._mapping) for row in result]
        for row in raw_results:
            if isinstance(row['centroids'], str):
                row['centroids'] = parse_pg_point_array(row['centroids'])
        return raw_results
