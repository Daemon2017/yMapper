import json

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
            FROM snps3
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
        result = session.execute(query, {
            "snp": snp
        }).fetchone()
        return result[0] if result else None


def select_centroids_dispersion(snp, size):
    with Session() as session:
        query = text(
            """
            SELECT snp,
                   centroids
            FROM   snps3
            WHERE  size = :size
                   AND snp IN (SELECT Unnest(childs)
                               FROM   childs
                               WHERE  snp IN (SELECT snp
                                              FROM   synonyms
                                              WHERE  :snp = ANY ( synonyms ))); 
            """
        )
        result = session.execute(query, {
            "snp": snp,
            "size": size
        })
        return [dict(row._mapping) for row in result]


def select_homeland(parent_snp, size):
    with Session() as session:
        query = text("""
            WITH target_parent AS (
                SELECT sy.snp AS p_name, t.tmrca AS p_tmrca 
                FROM synonyms sy
                JOIN tmrcas t ON sy.snp = t.snp
                WHERE :parent_snp = ANY(sy.synonyms)
                LIMIT 1
            ),
            target_sons AS (
                SELECT unnest(c.childs) AS son_name
                FROM childs c
                JOIN target_parent p ON c.snp = p.p_name
            ),
            son_metrics AS (
                SELECT 
                    s.centroids, 
                    ABS(p.p_tmrca - t.tmrca) AS dt
                FROM snps3 s
                JOIN tmrcas t ON s.snp = t.snp
                JOIN target_sons ts ON s.snp = ts.son_name
                CROSS JOIN target_parent p
                WHERE s.size = :size
            )
            SELECT 
                h3_index,
                json_agg(json_build_object('dt', m.dt)) AS sons_info
            FROM son_metrics m, unnest(m.centroids) AS h3_index
            GROUP BY h3_index
        """)
        result = session.execute(query, {
            "parent_snp": parent_snp,
            "size": str(size)
        })
        return [dict(row._mapping) for row in result]


def select_centroids_union(a_points, b_points, size, start, end):
    with Session() as session:
        query = text(
            """
            SELECT     s.snp,
                       s.centroids
            FROM       snps3  AS s
            INNER JOIN tmrcas AS t
            ON s.snp = t.snp
            WHERE      s.size = :size
            AND        t.tmrca BETWEEN :start AND :end
            AND        (s.centroids && :a_points OR s.centroids && :b_points)
            """
        )
        result = session.execute(query, {
            "size": str(size),
            "a_points": a_points,
            "b_points": b_points,
            "start": start,
            "end": end
        })
        return [dict(row._mapping) for row in result]


def select_centroids_subtraction(a_points, b_points, size, start, end):
    with Session() as session:
        query = text(
            """
            SELECT     s.snp,
                       s.centroids
            FROM       snps3  AS s
            INNER JOIN tmrcas AS t
            ON s.snp = t.snp
            WHERE      s.size = :size
            AND        t.tmrca BETWEEN :start AND :end
            AND        s.centroids && :a_points AND NOT (s.centroids && :b_points)
            """
        )
        result = session.execute(query, {
            "size": str(size),
            "a_points": a_points,
            "b_points": b_points,
            "start": start,
            "end": end
        })
        return [dict(row._mapping) for row in result]


def select_centroids_intersection(a_points, b_points, size, start, end):
    with Session() as session:
        query = text(
            """
            SELECT     s.snp,
                       s.centroids
            FROM       snps3  AS s
            INNER JOIN tmrcas AS t
            ON s.snp = t.snp
            WHERE      s.size = :size
            AND        t.tmrca BETWEEN :start AND :end
            AND        s.centroids && :a_points
            AND        s.centroids && :b_points
            """
        )
        result = session.execute(query, {
            "size": str(size),
            "a_points": a_points,
            "b_points": b_points,
            "start": start,
            "end": end
        })
        return [dict(row._mapping) for row in result]


def select_centroids_xor(a_points, b_points, size, start, end):
    with Session() as session:
        query = text(
            """
            SELECT     s.snp,
                       s.centroids
            FROM       snps3  AS s
            INNER JOIN tmrcas AS t
            ON s.snp = t.snp
            WHERE      s.size = :size
            AND        t.tmrca BETWEEN :start AND :end
            AND        (s.centroids && :a_points) != (s.centroids && :b_points)
            """
        )
        result = session.execute(query, {
            "size": str(size),
            "a_points": a_points,
            "b_points": b_points,
            "start": start,
            "end": end
        })
        return [dict(row._mapping) for row in result]
