import math
import json
from shapely.geometry import Polygon, LineString
from shapely.affinity import rotate
from pyproj import Transformer


def fov_to_ground_footprint(altitude_m, fov_deg):
    return 2 * altitude_m * math.tan(math.radians(fov_deg / 2))


def latlon_to_utm(polygon_latlon, epsg="32632"):
    lats, lons = zip(*polygon_latlon)
    transformer = Transformer.from_crs(
        "epsg:4326", f"epsg:{epsg}", always_xy=True)
    utm_coords = [transformer.transform(lon, lat)
                  for lat, lon in polygon_latlon]
    return Polygon(utm_coords), transformer


def utm_to_latlon(coords, transformer):
    result = []
    for x, y in coords:
        if not math.isfinite(x) or not math.isfinite(y):
            print(f"🚨 Ungültige UTM-Koordinate: {(x, y)}")
            continue  # oder raise
        lat, lon = transformer.transform(x, y, direction='INVERSE')
        result.append((lat, lon))
    return result


def generate_scan_lines(polygon, spacing, angle_deg=0):
    rotated = rotate(polygon, -angle_deg, origin='centroid', use_radians=False)
    minx, miny, maxx, maxy = rotated.bounds

    # 👉 Beginne bei halbem Abstand (statt miny) um oberen Rand zu erfassen
    y = miny + spacing / 2
    lines = []
    while y <= maxy:
        line = LineString([(minx, y), (maxx, y)])
        intersect = line.intersection(rotated)
        if not intersect.is_empty:
            segments = []
            if intersect.geom_type == "MultiLineString":
                for seg in intersect.geoms:
                    coords = list(seg.coords)

                    segments.append(coords)
            elif intersect.geom_type == "LineString":
                coords = list(intersect.coords)

                segments = [coords]
            lines.extend(segments)
        y += spacing
    return [rotate(LineString(i), angle_deg, origin=polygon.centroid,
                   use_radians=False) for i in lines]


def calculate_heading(lat1, lon1, lat2, lon2, transformer):
    x1, y1 = transformer.transform(lon1, lat1)
    x2, y2 = transformer.transform(lon2, lat2)

    dx = x2 - x1
    dy = y2 - y1

    angle_rad = math.atan2(dx, dy)  # East is X, North is Y
    heading_deg = math.degrees(angle_rad)
    heading_deg = (heading_deg + 180) % 360  # Normalize to [0, 360)

    return heading_deg


def plan_scan(polygon_latlon, start_latlon, end_latlon, altitude,
              fov_deg, overlap_ratio, epsg="32632"):
    footprint = fov_to_ground_footprint(altitude, fov_deg)
    spacing = footprint * (1 - overlap_ratio)

    polygon_utm, transformer = latlon_to_utm(polygon_latlon, epsg)
    # Rotate to minimize scan distance
    min_len = float('inf')
    best_angle = 0
    for angle in range(0, 180, 5):
        lines = generate_scan_lines(polygon_utm, spacing, angle)
        total_len = sum(i.length for i in lines)
        if total_len < min_len:
            min_len = total_len
            best_angle = angle

    scan_lines = generate_scan_lines(polygon_utm, spacing, best_angle)
    scan_latlon = [utm_to_latlon(list(line.coords), transformer)
                   for line in scan_lines]

    # Build mission route
    route = [start_latlon] + \
        [pt[::-1] for line in scan_latlon for pt in line] + [end_latlon]

    route_with_heading = []
    for i in range(len(route) - 1):
        heading = calculate_heading(*route[i], *route[i + 1], transformer)
        route_with_heading.append((*route[i], heading))
    route_with_heading.append((*route[-1], route_with_heading[-1][2]))

    return {
        "scan_polygon": polygon_latlon,
        "scan_lines": scan_latlon,
        "route": route_with_heading
    }


def export_geojson(scan_data, filename="scan_mission.geojson"):
    features = []

    # Scan area
    poly = scan_data["scan_polygon"] + [scan_data["scan_polygon"][0]]
    features.append({
        "type": "Feature",
        "properties": {"type": "scan_area"},
        "geometry": {
            "type": "Polygon",
            "coordinates": [[(lon, lat) for lat, lon in poly]]
        }
    })

    # Flight path
    features.append({
        "type": "Feature",
        "properties": {"type": "flight_path"},
        "geometry": {
            "type": "LineString",
            "coordinates": [(lon, lat) for lat, lon, _ in scan_data["route"]]
        }
    })

    # Waypoints
    for i, (lat, lon, heading) in enumerate(scan_data["route"]):
        features.append({
            "type": "Feature",
            "properties": {
                "type": "waypoint",
                "index": i,
                "heading": heading
            },
            "geometry": {
                "type": "Point",
                "coordinates": [lon, lat]
            }
        })

    geojson = {
        "type": "FeatureCollection",
        "features": features
    }

    with open(filename, "w") as f:
        json.dump(geojson, f, indent=2)
    print(f"✔ GeoJSON saved as: {filename}")
