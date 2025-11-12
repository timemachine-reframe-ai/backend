from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine

def ensure_reports_failure_reason_column(engine: Engine) -> None:
    """
    Alembic 없이 운영 중 컬럼이 없을 수 있어, 앱 시작 시 안전하게 추가한다.
    - Postgres/SQLite: ALTER TABLE ... ADD COLUMN failure_reason TEXT
    - MySQL: TEXT NULL
    권한이 없거나 실패해도 앱은 계속 뜨게 하고, 로그만 남기는 식으로 사용 권장.
    """
    insp = inspect(engine)
    try:
        cols = [c["name"] for c in insp.get_columns("reports")]
    except Exception:
        return  

    if "failure_reason" in cols:
        return

    dialect = engine.dialect.name
    sql = "ALTER TABLE reports ADD COLUMN failure_reason TEXT"
    if dialect == "mysql":
        sql = "ALTER TABLE reports ADD COLUMN failure_reason TEXT NULL"
    try:
        with engine.begin() as conn:
            conn.execute(text(sql))
    except Exception:
        pass
