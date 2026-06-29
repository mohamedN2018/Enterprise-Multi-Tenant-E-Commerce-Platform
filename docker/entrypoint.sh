#!/usr/bin/env sh
# Container entrypoint: wait for the database, migrate, collect static, then run CMD.
set -e

echo "==> Waiting for the database to become available..."
python - <<'PY'
import sys
import time

import environ

env = environ.Env()
cfg = env.db("DATABASE_URL", default="postgres://marketplace:marketplace@db:5432/marketplace")
dsn = (
    f"host={cfg['HOST']} port={cfg.get('PORT') or 5432} "
    f"dbname={cfg['NAME']} user={cfg['USER']} password={cfg['PASSWORD']}"
)

import psycopg  # noqa: E402

for attempt in range(1, 61):
    try:
        psycopg.connect(dsn, connect_timeout=3).close()
        print("==> Database is ready.")
        break
    except Exception:
        print(f"    database unavailable, retry {attempt}/60...")
        time.sleep(1)
else:
    print("==> Database not reachable; aborting.", file=sys.stderr)
    sys.exit(1)
PY

echo "==> Applying migrations..."
python manage.py migrate --noinput

echo "==> Collecting static files..."
python manage.py collectstatic --noinput || true

echo "==> Starting: $*"
exec "$@"
