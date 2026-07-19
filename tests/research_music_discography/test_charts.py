import json
import os
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
FIXTURES = Path(__file__).with_name("fixtures")
sys.path.insert(
    0,
    os.fspath(ROOT / "skills" / "music" / "research-music" / "scripts"),
)

from research_artist_discography.charts import parse_circle_album, parse_oricon_album


class ChartParserTests(unittest.TestCase):
    def test_circle_emits_rank_and_shipment_observations_separately(self):
        payload = json.loads((FIXTURES / "circle_album_week.json").read_text(encoding="utf-8"))
        rows = parse_circle_album(payload, "https://circlechart.kr/example", "2025-01-01", "2025-01-07")
        self.assertEqual(["chart_rank", "shipment_net_returns"], [row.measurement_type for row in rows])
        self.assertEqual([1, 12345], [row.value for row in rows])

    def test_oricon_public_rank_does_not_become_estimated_sales(self):
        html = (FIXTURES / "oricon_album_week.html").read_text(encoding="utf-8")
        rows = parse_oricon_album(html, "https://www.oricon.co.jp/rank/ja/w/example/", "2025-01-01", "2025-01-07")
        self.assertEqual(1, len(rows))
        self.assertEqual("chart_rank", rows[0].measurement_type)
        self.assertNotEqual("estimated_sale", rows[0].measurement_type)


if __name__ == "__main__":
    unittest.main()
