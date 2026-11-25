DROP TABLE IF EXISTS zips CASCADE;
DROP TYPE IF EXISTS zip_status CASCADE;

CREATE TYPE zip_status AS ENUM (
  'pending',
  'processing',
  'completed',
  'failed'
);

CREATE TABLE
  zips (
    id SERIAL PRIMARY KEY,
    status zip_status NOT NULL DEFAULT 'pending',
    name VARCHAR(255) NOT NULL,
    date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
  );
