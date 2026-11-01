BEGIN;

DROP TABLE IF EXISTS enrollment_events;
DELETE FROM schema_migrations WHERE version = '001';

COMMIT;