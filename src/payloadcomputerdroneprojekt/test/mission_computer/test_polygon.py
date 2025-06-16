import unittest
import os
from payloadcomputerdroneprojekt.mission_computer.scan_planer \
    import plan_scan, export_geojson


class TestPolygonScanPlan(unittest.TestCase):
    def setUp(self):
        self.polygon = [
            [48.767642, 11.337281],
            [48.767535, 11.337174],
            [48.767722, 11.336517],
            [48.768063, 11.336072],
            [48.768167, 11.336196]
        ]
        self.start = [48.767642, 11.337281]
        # self.end = (48.767722, 11.336799)
        self.end = self.start
        self.altitude = 10
        self.fov_deg = 60
        self.overlap_ratio = 0.2

    def test_plan_scan_returns_mission(self):
        mission = plan_scan(
            polygon_latlon=self.polygon,
            start_latlon=self.start,
            end_latlon=self.end,
            altitude=self.altitude,
            fov_deg=self.fov_deg,
            overlap_ratio=self.overlap_ratio
        )
        self.assertIsNotNone(mission)
        self.assertTrue(hasattr(mission, "__iter__")
                        or isinstance(mission, dict))

    def test_export_geojson_creates_file(self):
        mission = plan_scan(
            polygon_latlon=self.polygon,
            start_latlon=self.start,
            end_latlon=self.end,
            altitude=self.altitude,
            fov_deg=self.fov_deg,
            overlap_ratio=self.overlap_ratio
        )
        filename = "test_scan_mission.geojson"
        export_geojson(mission, filename=filename)
        self.assertTrue(os.path.exists(filename))
        os.remove(filename)

    def test_invalid_polygon_raises(self):
        invalid_polygon = [(48.767642, 11.337281)]  # Not enough points
        with self.assertRaises(Exception):
            plan_scan(
                polygon_latlon=invalid_polygon,
                start_latlon=self.start,
                end_latlon=self.end,
                altitude=self.altitude,
                fov_deg=self.fov_deg,
                overlap_ratio=self.overlap_ratio
            )


if __name__ == "__main__":
    unittest.main()
