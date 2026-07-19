import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "skills" / "research-artist-discography" / "scripts" / "collect_discography_data.py"
FIXTURES = Path(__file__).with_name("fixtures")


class CollectorCliTests(unittest.TestCase):
    def test_fixture_mode_outputs_complete_release_inventory(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "discography.json"
            csv_output = Path(directory) / "observations.csv"
            result = subprocess.run([
                sys.executable, str(SCRIPT), "Example Artist",
                "--fixture-dir", str(FIXTURES),
                "--circle-json", str(FIXTURES / "circle_album_week.json"),
                "--period-start", "2025-01-01",
                "--period-end", "2025-01-07",
                "--output", str(output),
                "--csv", str(csv_output),
            ], text=True, capture_output=True)
            self.assertEqual(0, result.returncode, result.stderr)
            payload = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual("Example Artist", payload["artist"]["name"])
            self.assertEqual(["First EP", "First Album"], [row["title"] for row in payload["releases"]])
            self.assertEqual(["chart_rank", "shipment_net_returns"], [row["measurement_type"] for row in payload["observations"]])
            self.assertTrue(csv_output.is_file())


if __name__ == "__main__":
    unittest.main()
