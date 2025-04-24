import sqlite3
import random
from datetime import datetime

# Open persistent connection
con = sqlite3.connect("image_database2.db")
cur = con.cursor()

# Create schema (simplified)
cur.executescript("""
CREATE TABLE IF NOT EXISTS raw_image (
    id INTEGER PRIMARY KEY,
    image_data BLOB,
    timestamp TEXT,
    quality REAL
);

CREATE TABLE IF NOT EXISTS processed_image (
    id INTEGER PRIMARY KEY,
    raw_image_id INTEGER,
    image_data BLOB,
    processing_details TEXT,
    timestamp TEXT,
    FOREIGN KEY (raw_image_id) REFERENCES raw_image(id)
);

CREATE TABLE IF NOT EXISTS found_objects (
    id INTEGER PRIMARY KEY,
    image_id INTEGER,
    x REAL, y REAL, z REAL,
    color TEXT, shape TEXT,
    confidence REAL,
    position_error REAL,
    FOREIGN KEY (image_id) REFERENCES raw_image(id)
);
""")
con.commit()

# Reusable insert statements
insert_raw = "INSERT INTO raw_image VALUES (?, ?, ?, ?)"
insert_processed = "INSERT INTO processed_image VALUES (?, ?, ?, ?, ?)"
insert_found = "INSERT INTO found_objects VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)"

# Insert rows one by one
for i in range(1, 10):
    ts = datetime.now().isoformat()
    blob = bytes(random.getrandbits(8) for _ in range(3840 * 2160 * 3))
    quality = round(random.uniform(0.5, 1.0), 2)

    with con:
        cur.execute(insert_raw, (i, blob, ts, quality))
        cur.execute(insert_processed, (i, i, blob, "processed", ts))

        for j in range(3):
            obj_id = i * 10 + j
            x, y, z = [round(random.uniform(0, 100), 2) for _ in range(3)]
            color = random.choice(["red", "green", "blue"])
            shape = random.choice(["circle", "square"])
            conf = round(random.uniform(0.7, 1.0), 2)
            err = round(random.uniform(0.0, 5.0), 2)
            cur.execute(insert_found, (obj_id, i, x,
                        y, z, color, shape, conf, err))
