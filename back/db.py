import ydb
import ydb.iam

db_key_path = 'key.json'
database = '/ru-central1/b1gq47q3820jil5087ik/etnorddlk3a95odcbev7'


def _create_driver():
    driver_config = ydb.DriverConfig(
        endpoint='grpcs://ydb.serverless.yandexcloud.net:2135',
        database=database,
        credentials=ydb.iam.ServiceAccountCredentials.from_file(db_key_path),
    )
    driver = ydb.Driver(driver_config)
    try:
        driver.wait(fail_fast=True, timeout=5)
    except Exception:
        driver.stop()
        raise
    return driver


_driver = _create_driver()
_pool = ydb.QuerySessionPool(_driver)


def get_session_pool():
    return _pool


def warm_up():
    try:
        _pool.execute_with_retries("SELECT 1;")
        print("YDB connection warmed up successfully.")
    except Exception as e:
        print(f"Failed to warm up YDB: {e}")


def stop_pool():
    global _pool, _driver
    if _pool:
        _pool.stop()
        _pool = None
    if _driver:
        _driver.stop()
        _driver = None


def select_list():
    result_sets = _pool.execute_with_retries(
        """
        SELECT DISTINCT snp
        FROM snps
        """,
        {},
    )
    return [row.snp for row in result_sets[0].rows]


def select_snp(snp):
    result_sets = _pool.execute_with_retries(
        """
        DECLARE $snp AS Utf8;
        SELECT snp
        FROM synonyms
        WHERE synonym = $snp
        LIMIT 1;
        """,
        {
            '$snp': snp,
        },
    )
    return result_sets[0].rows


def select_parent(snp):
    result_sets = _pool.execute_with_retries(
        """
        DECLARE $snp AS Utf8;
        SELECT parent
        FROM relations
        WHERE child IN (
            SELECT synonyms.snp
            FROM synonyms
            WHERE synonym = $snp
        )
        LIMIT 1;
        """,
        {
            '$snp': snp,
        },
    )
    return result_sets[0].rows[0]


def select_centroids(snp, size):
    result_sets = _pool.execute_with_retries(
        """
        DECLARE $snp AS Utf8;
        DECLARE $size AS Utf8;
        SELECT snp, centroids
        FROM snps
        WHERE size = $size
        AND snp IN (
            SELECT child
            FROM relations
            WHERE parent IN (
                SELECT synonyms.snp
                FROM synonyms
                WHERE synonym = $snp
            )
        );
        """,
        {
            '$snp': snp,
            '$size': size
        },
    )
    return result_sets[0].rows
