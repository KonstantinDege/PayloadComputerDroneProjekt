from payloadcomputerdroneprojekt.mission_computer.scan_planer \
    import plan_scan, export_geojson


start = [48.76816699, 11.33711226]
polygon = [
    [
        48.768507937,
        11.335972589
    ],
    [
        48.768264215,
        11.335724609
    ],
    [
        48.767507641,
        11.337241328
    ],
    [
        48.767967946,
        11.337684988
    ],
    [
        48.768289057,
        11.336764446
    ],
    [
        48.768198401,
        11.336264879
    ],
    [
        48.768358661,
        11.336291073
    ]
]
end = start
h = 12
fov = 66
ratio = 0.4
mission = plan_scan(
    polygon_latlon=polygon,
    start_latlon=start,
    end_latlon=end,
    altitude=h,
    fov_deg=fov,
    overlap_ratio=ratio
)

export_geojson(mission, filename="scan_mission.geojson")
