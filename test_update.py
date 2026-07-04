#!/usr/bin/env python3
"""Tests for update.py — run with: python -m unittest test_update -v

Astronomy expectations are anchored to independently known facts:
- Galactic center (Sgr A*): RA 17h45.7m, Dec -29.0deg.
- At June solstice the core transits within ~45 min of local solar midnight.
- From lat ~22N its transit altitude is 90 - |22 - (-29)| ~= 39 deg.
- Nov-Jan the core sits on the Sun's side of the sky: invisible all night.
- In February it only clears the horizon in the pre-dawn hours.
- In mid-October it is already up at dusk and sets before midnight.
"""

import unittest
from datetime import datetime

import update
from update import TW

# Reference observer: Kenting area (site's primary region).
LAT, LON = 21.95, 120.85


def local(y, mo, d, h, mi=0):
    return datetime(y, mo, d, h, mi, tzinfo=TW)


class TestDarkWindow(unittest.TestCase):
    def test_june_astronomical_night(self):
        """Kenting, June 21: astro dusk ~20:15, astro dawn ~03:55 (+/- tolerance)."""
        dusk, dawn = update.sun_dark_window(local(2026, 6, 21, 17), LAT, LON)
        self.assertEqual(dusk.date().isoformat(), "2026-06-21")
        self.assertTrue(local(2026, 6, 21, 19, 45) <= dusk <= local(2026, 6, 21, 20, 40),
                        f"dusk={dusk}")
        self.assertEqual(dawn.date().isoformat(), "2026-06-22")
        self.assertTrue(local(2026, 6, 22, 3, 25) <= dawn <= local(2026, 6, 22, 4, 25),
                        f"dawn={dawn}")


class TestCoreInfo(unittest.TestCase):
    def test_june_transit_near_solar_midnight(self):
        info = update.get_core_info(local(2026, 6, 21, 17), LAT, LON)
        self.assertTrue(info["visible"])
        t = info["transit_local"]
        self.assertTrue(local(2026, 6, 21, 23, 10) <= t <= local(2026, 6, 22, 0, 35),
                        f"transit={t}")

    def test_transit_altitude_from_kenting(self):
        info = update.get_core_info(local(2026, 6, 21, 17), LAT, LON)
        self.assertTrue(37 <= info["transit_alt"] <= 41, f"alt={info['transit_alt']}")

    def test_december_core_invisible(self):
        info = update.get_core_info(local(2026, 12, 10, 17), LAT, LON)
        self.assertFalse(info["visible"])
        self.assertTrue(info["reason"])  # human-readable explanation exists

    def test_february_predawn_only(self):
        info = update.get_core_info(local(2026, 2, 15, 17), LAT, LON)
        self.assertTrue(info["visible"])
        ws = info["window_start"]
        self.assertEqual(ws.date().isoformat(), "2026-02-16")  # after midnight
        self.assertTrue(1 <= ws.hour <= 5, f"window_start={ws}")

    def test_october_early_evening_window(self):
        info = update.get_core_info(local(2026, 10, 15, 17), LAT, LON)
        self.assertTrue(info["visible"])
        we = info["window_end"]
        self.assertEqual(we.date().isoformat(), "2026-10-15")  # sets before midnight
        self.assertTrue(we.hour <= 22, f"window_end={we}")

    def test_window_lies_within_dark_hours(self):
        info = update.get_core_info(local(2026, 7, 4, 17), LAT, LON)
        self.assertTrue(info["visible"])
        self.assertTrue(info["dusk"] <= info["window_start"] < info["window_end"] <= info["dawn"])
        self.assertTrue(info["window_start"] <= info["peak_local"] <= info["window_end"])


class TestWeather(unittest.TestCase):
    def test_fetch_weather_returns_cloud_and_rain(self):
        """Live Open-Meteo call: both metrics present and in 0-100."""
        w = update.fetch_weather(LAT, LON)
        self.assertFalse(w.get("failed", False))
        for key in ("rain", "cloud", "cloud_early", "cloud_late"):
            self.assertIn(key, w)
            self.assertTrue(0 <= w[key] <= 100, f"{key}={w[key]}")


class TestScoring(unittest.TestCase):
    def test_clear_sky_beats_cloudy(self):
        clear = {"cloud": 10, "rain": 5}
        cloudy = {"cloud": 80, "rain": 5}
        self.assertLess(update.badness(clear), update.badness(cloudy))

    def test_cloud_weighs_more_than_rain(self):
        low_cloud_high_rain = {"cloud": 20, "rain": 60}
        high_cloud_low_rain = {"cloud": 60, "rain": 20}
        self.assertLess(update.badness(low_cloud_high_rain),
                        update.badness(high_cloud_low_rain))


class TestLocations(unittest.TestCase):
    def test_unified_pool_has_full_metadata(self):
        self.assertGreaterEqual(len(update.LOCATIONS), 10)
        for loc in update.LOCATIONS:
            for key in ("name", "region", "lat", "lon", "maps", "desc"):
                self.assertIn(key, loc, f"{loc.get('name', '?')} missing {key}")


class TestBuildPage(unittest.TestCase):
    def _fake_locs(self, n):
        return [dict(name=f"L{i}", region="R", lat=22.0, lon=121.0, maps="22,121",
                     desc="d", rain=10 + i, cloud=20 + i,
                     cloud_early=25 + i, cloud_late=15 + i) for i in range(n)]

    def test_summer_page_shows_cloud_and_dynamic_core(self):
        now = local(2026, 7, 4, 17)
        moon = update.get_moon(now)
        core = update.get_core_info(now, LAT, LON)
        html = update.build_page("2026-07-04", "六", moon, core,
                                 self._fake_locs(5), self._fake_locs(3))
        self.assertIn("雲量", html)
        self.assertNotIn("本季不可見", html)
        # peak label must come from computed transit, not the old hardcoded copy
        self.assertIn(core["peak_local"].strftime("%H:%M"), html)

    def test_winter_page_flags_core_season(self):
        now = local(2026, 12, 10, 17)
        moon = update.get_moon(now)
        core = update.get_core_info(now, LAT, LON)
        html = update.build_page("2026-12-10", "四", moon, core,
                                 self._fake_locs(5), self._fake_locs(3))
        self.assertIn("本季不可見", html)


if __name__ == "__main__":
    unittest.main(verbosity=2)
