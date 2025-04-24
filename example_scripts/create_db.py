import duckdb
import random
import time
from datetime import datetime

# Connect to DuckDB (file-based)
con = duckdb.connect("image_database8.duckdb")

# Create schema
con.execute("""
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
    processing_details TEXT,
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
    position_error FLOAT,
    FOREIGN KEY (image_id) REFERENCES raw_image(id)
);

CREATE TABLE filtered_objects (
    id INTEGER PRIMARY KEY,
    image_id INTEGER,
    x FLOAT,
    y FLOAT,
    z FLOAT,
    color TEXT,
    shape TEXT,
    position_error FLOAT,
);

CREATE TABLE filtered_object_components (
    filtered_object_id INTEGER,
    found_object_id INTEGER,
    FOREIGN KEY (filtered_object_id) REFERENCES filtered_objects(id),
    FOREIGN KEY (found_object_id) REFERENCES found_objects(id)
);
""")


# Reusable insert statements
insert_raw = "INSERT INTO raw_image (id, image_data, timestamp, quality) VALUES (?, ?, ?, ?)"
insert_processed = "INSERT INTO processed_image (id, raw_image_id, image_data, processing_details, timestamp) VALUES (?, ?, ?, ?, ?)"
insert_found = "INSERT INTO found_objects (id, image_id, x, y, z, color, shape, confidence, position_error) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)"

start = time.time()

# Simulate single-row computation + insert loop
for i in range(1, 10):  # simulate 100 inserts after computation
    # Example computed data
    ts = datetime.now()
    quality = round(random.uniform(0.5, 1.0), 2)
    blob = bytes(random.getrandbits(8)
                 for _ in range(1080 * 720 * 3))  # ~25MB 4K image

    con.execute(insert_raw, (i, blob, ts, quality))
    con.execute(insert_processed, (i, i, blob, "processed", ts))

    for j in range(3):  # pretend we found 3 objects in this image
        obj_id = i * 10 + j
        x, y, z = [round(random.uniform(0, 100), 2) for _ in range(3)]
        color = random.choice(["red", "green", "blue"])
        shape = random.choice(["circle", "square"])
        conf = round(random.uniform(0.7, 1.0), 2)
        err = round(random.uniform(0.0, 5.0), 2)

        con.execute(insert_found, (obj_id, i, x,
                    y, z, color, shape, conf, err))


print(f"Inserted 1000 images + related objects in {time.time() - start:.2f} seconds.")
