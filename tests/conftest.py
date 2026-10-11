import os
import tempfile
from pathlib import Path
import pytest

@pytest.fixture(scope="session", autouse=True)
def isolated_test_database():
    """
    Guarantees automated test isolation.
    Tests run entirely against a temporary SQLite database,
    never mutating data/civic_issues.db.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        test_db_path = Path(tmpdir) / "test_civic_issues.db"
        os.environ["CIVILENS_DB_PATH"] = str(test_db_path)
        os.environ["CIVILENS_DEMO_MODE"] = "true"

        from app.config import settings
        settings.db_path = str(test_db_path)
        settings.civilens_demo_mode = True

        from app.db.database import rebind_database, init_db
        rebind_database(test_db_path)
        init_db()

        from app.core.demo_store import demo_store
        demo_store.reload()

        yield test_db_path
