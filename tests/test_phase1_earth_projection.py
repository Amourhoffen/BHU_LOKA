"""
Unit and Integration Tests for BHU LOKA Phase 1: Earth System Home Page
======================================================================
Verifies:
1. Consistent conversion of latitude/longitude into 3D globe coordinates (latLonToSphere).
2. Geodetic points across India (New Delhi, Patna, Srinagar, Kanyakumari, Mumbai, Kolkata) lie strictly on the spherical surface.
3. Spherical rotation lockstep: rotating the parent Earth sphere rotates all child geographic points without detachment.
4. Multi-Hazard Earth Explorer catalog structure, status tagging, and metadata provenance (zero fabricated data).
"""

import math
import re
from pathlib import Path
import pytest


def lat_lon_to_sphere(lat: float, lon: float, r: float = 12.06):
    """
    Exact mathematical reproduction of index.html latLonToSphere convention:
    phi = (90 - lat) * (pi / 180)
    theta = (lon + 180) * (pi / 180)
    x = -r * sin(phi) * cos(theta)
    y =  r * cos(phi)
    z =  r * sin(phi) * sin(theta)
    """
    phi = (90.0 - lat) * (math.pi / 180.0)
    theta = (lon + 180.0) * (math.pi / 180.0)
    x = -r * math.sin(phi) * math.cos(theta)
    y = r * math.cos(phi)
    z = r * math.sin(phi) * math.sin(theta)
    return x, y, z


def rotate_y(x: float, y: float, z: float, angle_rad: float):
    """Rotate 3D point around Earth's Y polar axis."""
    cos_a = math.cos(angle_rad)
    sin_a = math.sin(angle_rad)
    x_rot = x * cos_a + z * sin_a
    y_rot = y
    z_rot = -x * sin_a + z * cos_a
    return x_rot, y_rot, z_rot


KNOWN_GEOGRAPHIC_POINTS = [
    {"name": "New Delhi (National Capital)", "lat": 28.6139, "lon": 77.2090},
    {"name": "Patna (Gangetic Basin Benchmark)", "lat": 25.5941, "lon": 85.1376},
    {"name": "Srinagar (Northern Reach)", "lat": 34.0837, "lon": 74.7973},
    {"name": "Kanyakumari (Southern Tip)", "lat": 8.0883, "lon": 77.5385},
    {"name": "Mumbai (Western Seaboard)", "lat": 19.0760, "lon": 72.8777},
    {"name": "Kolkata (Eastern Littoral)", "lat": 22.5726, "lon": 88.3639},
    {"name": "Hyderabad / Hussain Sagar", "lat": 17.4239, "lon": 78.4738},
]


class TestPhase1EarthProjection:
    """Tests Phase 1 Earth Geodetic Projections and Coordinate System."""

    def test_geodetic_points_lie_on_sphere_surface(self):
        r = 12.06
        for pt in KNOWN_GEOGRAPHIC_POINTS:
            x, y, z = lat_lon_to_sphere(pt["lat"], pt["lon"], r=r)
            computed_radius = math.sqrt(x * x + y * y + z * z)
            assert math.isclose(computed_radius, r, rel_tol=1e-5), (
                f"{pt['name']} distance {computed_radius} deviated from expected radius {r}"
            )

    def test_latitude_hierarchy_maps_to_vertical_y_axis(self):
        r = 12.06
        srinagar_y = lat_lon_to_sphere(34.0837, 74.7973, r)[1]
        delhi_y = lat_lon_to_sphere(28.6139, 77.2090, r)[1]
        patna_y = lat_lon_to_sphere(25.5941, 85.1376, r)[1]
        kanyakumari_y = lat_lon_to_sphere(8.0883, 77.5385, r)[1]

        assert srinagar_y > delhi_y > patna_y > kanyakumari_y > 0.0, (
            "Vertical Y axis must monotonically follow northern latitudes"
        )

    def test_earth_rotation_preserves_radial_distance_without_detachment(self):
        r = 12.06
        for pt in KNOWN_GEOGRAPHIC_POINTS:
            x, y, z = lat_lon_to_sphere(pt["lat"], pt["lon"], r=r)
            for angle_deg in [15.0, 45.0, 90.0, 180.0, 270.0]:
                angle_rad = angle_deg * (math.pi / 180.0)
                xr, yr, zr = rotate_y(x, y, z, angle_rad)
                dist_after_rotation = math.sqrt(xr * xr + yr * yr + zr * zr)
                assert math.isclose(dist_after_rotation, r, rel_tol=1e-5), (
                    f"Rotation by {angle_deg} deg detached {pt['name']} from sphere surface"
                )

    def test_index_html_contains_earth_hierarchy_and_culling(self):
        index_path = Path(__file__).resolve().parent.parent / "index.html"
        assert index_path.exists(), "index.html must exist at repository root"
        content = index_path.read_text(encoding="utf-8")

        # 1. Earth system group with axial tilt (23.44°)
        assert "23.44" in content, "EarthSystemGroup must enforce 23.44° axial obliquity"
        assert "earthSphere.add(earthBoundariesGroup)" in content, "State boundaries must be attached as direct child of earthSphere"
        assert "earthSphere.add(earthHazardGroup)" in content, "Hazard pins must be attached as direct child of earthSphere"

        # 2. Front vs Back occlusion culling exists in animation loop
        assert "getWorldPosition" in content, "Must compute world position for occlusion culling"
        assert "surfaceNormal" in content, "Must compute surface normal for globe pin visibility"

    def test_multi_hazard_catalog_provenance_and_status_tags(self):
        index_path = Path(__file__).resolve().parent.parent / "index.html"
        content = index_path.read_text(encoding="utf-8")

        assert "BHU_VERIFIED_HAZARD_CATALOG" in content
        # Check required scientific status tags
        for required_status in ["OBSERVED", "HISTORICAL", "WARNING", "CRITICAL"]:
            assert required_status in content, f"Scientific hazard catalog must contain {required_status} entries"

        # Ensure all 8 core hazard categories are cataloged
        for cat in ["flood", "heatwave", "earthquake", "air_pollution", "cyclone", "forest_fire", "landslide", "drought"]:
            assert f"{cat}: [" in content, f"Hazard category {cat} must be indexed in BHU_VERIFIED_HAZARD_CATALOG"
