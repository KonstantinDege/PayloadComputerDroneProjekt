from payloadcomputerdroneprojekt.mission_computer.scan_planer \
    import plan_scan, export_geojson


start = [48.76816699, 11.33711226]
polygon = []
end = start
h = 12
fov = 66
ratio = 0.6
mission = plan_scan(
    polygon_latlon=polygon,
    start_latlon=start,
    end_latlon=end,
    altitude=h,
    fov_deg=fov,
    overlap_ratio=ratio
)

export_geojson(mission, filename="scan_mission.geojson")
