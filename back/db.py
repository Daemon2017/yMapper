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
            FROM snps
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


def select_centroids(snp, size):
    with Session() as session:
        query = text(
            """
            SELECT snp, centroids
            FROM snps
            WHERE size = :size
            AND snp IN (
                SELECT unnest(childs)
                FROM childs
                WHERE snp IN (
                    SELECT snp 
                    FROM synonyms 
                    WHERE :snp = ANY(synonyms)
                )
            )
            """
        )
        result = session.execute(query,
                                 {
                                     "snp": snp,
                                     "size": size
                                 })
        return [dict(row._mapping) for row in result]
