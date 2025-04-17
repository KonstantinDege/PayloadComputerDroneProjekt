import os
import duckdb

# Connect to the DuckDB database (or create it if it doesn't exist)
if os.path.exists('image_database.duckdb'):
    os.remove('image_database.duckdb')
conn = duckdb.connect('image_database.duckdb')

# Create tables
conn.execute("""
CREATE TABLE raw_image (
    id INTEGER PRIMARY KEY,
    image_data BLOB,
    timestamp TIMESTAMP,
    quality FLOAT
);

CREATE TABLE processed_image (
    id INTEGER PRIMARY KEY,
    raw_image_id INTEGER,
    image_data BLOB,
    timestamp TIMESTAMP,
    FOREIGN KEY (raw_image_id) REFERENCES raw_image(id)
);

CREATE TABLE found_objects (
    id INTEGER PRIMARY KEY,
    image_id INTEGER,
    x FLOAT,
    y FLOAT,
    z FLOAT,
    color TEXT,
    shape TEXT,
    confidence FLOAT,
    FOREIGN KEY (image_id) REFERENCES raw_image(id)
);

CREATE TABLE filtered_objects (
    id INTEGER PRIMARY KEY,
    x FLOAT,
    y FLOAT,
    z FLOAT,
    color TEXT,
    shape TEXT,
);

CREATE TABLE filtered_object_components (
    filtered_object_id INTEGER,
    found_object_id INTEGER,
    FOREIGN KEY (filtered_object_id) REFERENCES filtered_objects(id),
    FOREIGN KEY (found_object_id) REFERENCES found_objects(id)
);
""")
