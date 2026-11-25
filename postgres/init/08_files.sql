DROP TABLE IF EXISTS files CASCADE;

CREATE TABLE
  files (
    id SERIAL PRIMARY KEY,
    name VARCHAR(256) NOT NULL,
    zip_id INT NOT NULL REFERENCES zips (id) ON DELETE CASCADE,
    rustfs_object_id INT NOT NULL REFERENCES rustfs_objects (id) ON DELETE CASCADE
  );

CREATE INDEX files_zip_id_idx ON files (zip_id);
CREATE INDEX files_rustfs_object_id_idx ON files (rustfs_object_id);

ALTER TABLE files ADD FOREIGN KEY (zip_id) REFERENCES zips (id) ON DELETE CASCADE DEFERRABLE INITIALLY IMMEDIATE;
ALTER TABLE files ADD FOREIGN KEY (rustfs_object_id) REFERENCES rustfs_objects (id) ON DELETE CASCADE DEFERRABLE INITIALLY IMMEDIATE;
