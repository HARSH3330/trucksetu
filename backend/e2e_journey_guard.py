"""Read-only browser setup: preserve all existing local rows; never reset."""
import psycopg
from pathlib import Path
from alembic.config import Config
from alembic.script import ScriptDirectory
from e2e_database import safe_database_url
raw=safe_database_url().replace('postgresql+psycopg://','postgresql://',1)
config=Config();config.set_main_option('script_location',str(Path(__file__).parent/'migrations'))
head=ScriptDirectory.from_config(config).get_current_head()
with psycopg.connect(raw,connect_timeout=5) as db:
    assert db.execute('SELECT current_database(),current_user').fetchone()==('transivox_e2e','transivox_e2e_user')
    assert db.execute('SELECT version_num FROM alembic_version').fetchone()[0]==head
print('Current migrated dedicated local DB verified; existing rows preserved; no reset')
