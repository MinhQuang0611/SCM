#!/bin/bash
set -e

##############################################################################
# Patched copy of code/evaluation/env/init-databases_mssql.sh
#
# Upstream waits a fixed `sleep 15` for SQL Server to accept connections, then
# runs sqlcmd under `set -e`. On this machine SQL Server 2022 spends longer
# than that upgrading its `model` database on first boot, so the first sqlcmd
# fails with "Login timeout expired" / TCP 0x2749 and `set -e` kills the
# container (exit 1) before any .bak is restored.
#
# Only change: the fixed sleep becomes a readiness poll with a hard cap.
# Everything else is byte-for-byte upstream. Mounted over the entrypoint via
# docker/compose.all-dialects.yml so the clone stays unmodified.
##############################################################################

SA_PASSWORD="${MSSQL_SA_PASSWORD:-Y.sa123123}"
DROP_DATABASE_IF_EXISTS="${DROP_DATABASE_IF_EXISTS:-true}"
echo "DROP_DATABASE_IF_EXISTS = $DROP_DATABASE_IF_EXISTS"

# Start SQL Server in the background (container method)
/opt/mssql/bin/sqlservr &

echo "[init_from_bak.sh] Waiting for SQL Server to accept connections..."
READY=0
for attempt in $(seq 1 60); do
  if sqlcmd -S localhost -No -U SA -P "$SA_PASSWORD" -Q "SELECT 1" >/dev/null 2>&1; then
    echo "[init_from_bak.sh] SQL Server ready after ${attempt} attempt(s)."
    READY=1
    break
  fi
  sleep 5
done

if [ "$READY" -ne 1 ]; then
  echo "[init_from_bak.sh] ERROR: SQL Server did not accept connections within 300s." >&2
  exit 1
fi

# Directory containing backup files
BACKUP_DIR="/app/mssql_table_dumps"


if [ ! -d "$BACKUP_DIR" ]; then
  echo "Warning: Directory $BACKUP_DIR does not exist or is not mounted, cannot automatically restore databases (.bak)."
  echo "If you need to restore databases from .bak files, please place them in $BACKUP_DIR inside the container."
  # Can exit directly with exit 1 or keep bcp logic as fallback
  exit 0
fi

# Get all .bak files
shopt -s nullglob
BAK_FILES=("$BACKUP_DIR"/*.bak)

if [ ${#BAK_FILES[@]} -eq 0 ]; then
  echo "Warning: No .bak files found in $BACKUP_DIR, skipping restoration."
  # Can also fallback to original bcp method here
  exit 0
fi

# Function: Drop database if it exists
drop_database_if_exists() {
  local db_name="$1"
  echo "Checking if database [$db_name] exists and dropping it if so..."

  # First attempt: If database exists, set to single user mode and force disconnect all connections
  sqlcmd \
    -S localhost \
    -No \
    -d master \
    -U SA -P "$SA_PASSWORD" \
    -Q "
      IF DB_ID('$db_name') IS NOT NULL
      BEGIN
        ALTER DATABASE [$db_name] SET SINGLE_USER WITH ROLLBACK IMMEDIATE;
        PRINT 'Set to SINGLE_USER and rollback immediate.';
      END
    "

  # Second attempt: Safely drop the database (will not error if it doesn't exist)
  sqlcmd \
    -S localhost \
    -No \
    -d master \
    -U SA -P "$SA_PASSWORD" \
    -Q "
      DROP DATABASE IF EXISTS [$db_name];
      PRINT 'Dropped database if existed: $db_name';
    "
}

echo "=== Starting database restoration from .bak files ==="

for bak_file in "${BAK_FILES[@]}"; do
  # Extract database name from backup file (e.g., "debit_card_specializing_template.bak" => "debit_card_specializing")
  filename="$(basename "$bak_file")"
  db_name="${filename%_template.bak}"  # Remove '_template.bak' suffix

  echo ">>> Found backup file: $bak_file => database [$db_name]"


  # If configured to drop before creating:
  if [ "${DROP_DATABASE_IF_EXISTS,,}" = "true" ]; then
    drop_database_if_exists "$db_name"
  fi

  # Perform restoration
  echo ">>> Restoring database [$db_name] from $bak_file"
  sqlcmd \
    -S localhost \
    -No \
    -U SA \
    -P "$SA_PASSWORD" \
    -d master \
    -Q "
      RESTORE DATABASE [$db_name]
      FROM DISK = N'${bak_file}'
      WITH REPLACE,
           RECOVERY,
           STATS = 5;
    "
  echo "Restoration completed: database [$db_name]"
done

echo "=== All available .bak databases have been restored! ==="

# Keep container running
tail -f /dev/null
