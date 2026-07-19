import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = (
    ROOT
    / "skills"
    / "music"
    / "research-music"
    / "scripts"
    / "collect_discography_data.py"
)
FIXTURES = Path(__file__).with_name("fixtures")


class CollectorCliTests(unittest.TestCase):
    def run_collector(self, directory, *extra_args):
        output = Path(directory) / "discography.json"
        result = subprocess.run([
            sys.executable, str(SCRIPT), "Example Artist",
            "--fixture-dir", str(FIXTURES),
            "--circle-json", str(FIXTURES / "circle_album_week.json"),
            "--period-start", "2025-01-01",
            "--period-end", "2025-01-07",
            "--output", str(output),
            *extra_args,
        ], text=True, capture_output=True)
        return result, output

    def test_fixture_mode_outputs_complete_release_inventory(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "discography.json"
            csv_output = Path(directory) / "observations.csv"
            result, output = self.run_collector(directory, "--csv", str(csv_output))
            self.assertEqual(0, result.returncode, result.stderr)
            payload = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual("Example Artist", payload["artist"]["name"])
            self.assertEqual(["First EP", "First Album"], [row["title"] for row in payload["releases"]])
            self.assertEqual(["chart_rank", "shipment_net_returns"], [row["measurement_type"] for row in payload["observations"]])
            self.assertTrue(csv_output.is_file())

    def test_default_analysis_keeps_non_default_records_in_inventory(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture_dir = Path(directory) / "fixtures"
            fixture_dir.mkdir()
            for source in FIXTURES.iterdir():
                target = fixture_dir / source.name
                target.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
            releases_path = fixture_dir / "musicbrainz_release_groups.json"
            releases = json.loads(releases_path.read_text(encoding="utf-8"))
            releases["release-groups"].append({
                "id": "rg-3",
                "title": "Best Collection",
                "first-release-date": "2027-03-04",
                "primary-type": "Album",
                "secondary-types": ["Compilation"],
            })
            releases_path.write_text(json.dumps(releases), encoding="utf-8")
            output = Path(directory) / "discography.json"
            result = subprocess.run([
                sys.executable, str(SCRIPT), "Example Artist",
                "--fixture-dir", str(fixture_dir),
                "--circle-json", str(fixture_dir / "circle_album_week.json"),
                "--period-start", "2025-01-01",
                "--period-end", "2025-01-07",
                "--output", str(output),
            ], text=True, capture_output=True)
            self.assertEqual(0, result.returncode, result.stderr)
            payload = json.loads(output.read_text(encoding="utf-8"))
            compilation = next(
                row for row in payload["releases"] if row["title"] == "Best Collection"
            )
            self.assertFalse(compilation["default_included"])
            self.assertNotIn(compilation["release_group_id"], payload["analysis_release_group_ids"])
            self.assertEqual(3, len(payload["releases"]))

    def test_fixture_artist_selection_honors_mbid_and_reports_ambiguity(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture_dir = Path(directory) / "fixtures"
            fixture_dir.mkdir()
            for source in FIXTURES.iterdir():
                target = fixture_dir / source.name
                target.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
            artists_path = fixture_dir / "musicbrainz_artist.json"
            artists = json.loads(artists_path.read_text(encoding="utf-8"))
            artists["artists"].append({
                "id": "artist-mbid-2",
                "name": "Example Artist",
                "country": "JP",
                "score": 80,
                "disambiguation": "different artist",
            })
            artists_path.write_text(json.dumps(artists), encoding="utf-8")

            output = Path(directory) / "default.json"
            default_result = subprocess.run([
                sys.executable, str(SCRIPT), "Example Artist",
                "--fixture-dir", str(fixture_dir),
                "--output", str(output),
            ], text=True, capture_output=True)
            self.assertEqual(0, default_result.returncode, default_result.stderr)
            default_payload = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual("artist-mbid-1", default_payload["artist"]["id"])
            self.assertIn("MusicBrainz top artist candidate selected; verify same-name ambiguity", default_payload["warnings"])

            explicit_output = Path(directory) / "explicit.json"
            explicit_result = subprocess.run([
                sys.executable, str(SCRIPT), "Example Artist",
                "--fixture-dir", str(fixture_dir),
                "--artist-mbid", "artist-mbid-2",
                "--output", str(explicit_output),
            ], text=True, capture_output=True)
            self.assertEqual(0, explicit_result.returncode, explicit_result.stderr)
            explicit_payload = json.loads(explicit_output.read_text(encoding="utf-8"))
            self.assertEqual("artist-mbid-2", explicit_payload["artist"]["id"])

            unknown_output = Path(directory) / "unknown.json"
            unknown_result = subprocess.run([
                sys.executable, str(SCRIPT), "Example Artist",
                "--fixture-dir", str(fixture_dir),
                "--artist-mbid", "unknown-mbid",
                "--output", str(unknown_output),
            ], text=True, capture_output=True)
            self.assertNotEqual(0, unknown_result.returncode)
            self.assertIn("--artist-mbid was not present in MusicBrainz candidates", unknown_result.stderr)
            self.assertFalse(unknown_output.exists())

    def test_chart_input_without_period_creates_no_output(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "discography.json"
            result = subprocess.run([
                sys.executable, str(SCRIPT), "Example Artist",
                "--fixture-dir", str(FIXTURES),
                "--circle-json", str(FIXTURES / "circle_album_week.json"),
                "--output", str(output),
            ], text=True, capture_output=True)
            self.assertEqual(2, result.returncode)
            self.assertFalse(output.exists())

    def test_csv_parent_failure_leaves_no_output_files(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "discography.json"
            blocked_parent = Path(directory) / "not-a-directory"
            blocked_parent.write_text("blocked", encoding="utf-8")
            csv_output = blocked_parent / "observations.csv"
            result, _ = self.run_collector(directory, "--csv", str(csv_output))
            self.assertNotEqual(0, result.returncode)
            self.assertFalse(output.exists())
            self.assertFalse(csv_output.exists())

    def test_same_json_and_csv_target_is_rejected_before_output(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "combined-output"
            result = subprocess.run([
                sys.executable, str(SCRIPT), "Example Artist",
                "--fixture-dir", str(FIXTURES),
                "--circle-json", str(FIXTURES / "circle_album_week.json"),
                "--period-start", "2025-01-01",
                "--period-end", "2025-01-07",
                "--output", str(output),
                "--csv", str(output),
            ], text=True, capture_output=True)
            self.assertNotEqual(0, result.returncode)
            self.assertIn("--output and --csv must be different paths", result.stderr)
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
