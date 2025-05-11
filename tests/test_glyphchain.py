# test_glyphchain.py

import unittest
import os
import json
import subprocess
from glyphchain_core import Glyph, GlyphEchoLog
from glyphchain_utils import timestamp_glyph, verify_glyph_timestamp, check_ots_installed
from datetime import datetime

class TestGlyph(unittest.TestCase):

    def setUp(self):
        self.glyph = Glyph(
            glyph_id="GLYPH-TEST",
            name="Test Glyph",
            creator="UnitTester",
            core_concepts=["Concept1", "Concept2"]
        )
        self.glyph.set_dedication("Test dedication", "UnitTester")
        self.glyph.set_closing(["Line one", "Line two"])

    def test_manifest_generation(self):
        self.assertEqual(self.glyph.name, "Test Glyph")
        self.assertEqual(self.glyph.dedication["author"], "UnitTester")
        self.assertTrue("timestamp" in self.glyph.to_dict())

    def test_save_and_load_manifest(self):
        test_path = "test_manifest.json"
        self.glyph.save(test_path)
        with open(test_path) as f:
            data = json.load(f)
        self.assertEqual(data["creator"], "UnitTester")
        os.remove(test_path)

    def test_load_user_glyph(self):
        user_path = "glyphs/MAB-PRIME/MAB-PRIME_manifest.json"
        if not os.path.exists(user_path):
            self.skipTest("User glyph manifest not found")
        with open(user_path) as f:
            glyph = json.load(f)
        self.assertIn("glyph_id", glyph)
        self.assertIsInstance(glyph["core_concepts"], list)
        self.assertGreater(len(glyph["core_concepts"]), 0)
        self.assertIn("timestamp", glyph)
        try:
            datetime.fromisoformat(glyph["timestamp"].replace("Z", ""))
        except ValueError:
            self.fail("Timestamp is not in valid ISO 8601 format")

class TestEchoLog(unittest.TestCase):

    def test_add_echo_entry(self):
        echo = GlyphEchoLog()
        echo.add_entry(
            node_id="NODE-1",
            vector="⊗_EXAMPLE",
            assertion="Test assertion",
            trace_id="TRACE-123",
            symbol="*",
            meaning="Example meaning"
        )
        self.assertEqual(len(echo.entries), 1)
        self.assertEqual(echo.entries[0]["node_id"], "NODE-1")

    def test_save_echo_log(self):
        echo = GlyphEchoLog()
        echo.add_entry(
            node_id="NODE-2",
            vector="⊗_SAVE",
            assertion="Persistence test"
        )
        test_log = "test_echo_log.json"
        echo.save(test_log)
        with open(test_log) as f:
            data = json.load(f)
        self.assertEqual(data[0]["vector"], "⊗_SAVE")
        os.remove(test_log)

class TestTimestamping(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Check if OpenTimestamps CLI is available before running tests"""
        cls.ots_available = check_ots_installed()
        if not cls.ots_available:
            print("Warning: OpenTimestamps CLI not found. Skipping timestamp tests.")
            print("Install with: pip install opentimestamps-client")

    def setUp(self):
        """Create a test glyph for timestamping"""
        self.glyph = Glyph(
            glyph_id="TEST-TIMESTAMP",
            name="Test Timestamp Glyph",
            creator="UnitTester",
            core_concepts=["Testing", "Timestamping"]
        )
        self.glyph.set_dedication("Test dedication", "UnitTester")
        self.glyph.set_closing(["Test closing"])
        
        # Save test glyph
        self.test_dir = "test_output"
        os.makedirs(self.test_dir, exist_ok=True)
        self.manifest_path = os.path.join(self.test_dir, "test_timestamp_manifest.json")
        self.glyph.save(self.manifest_path)

    def tearDown(self):
        """Clean up test files"""
        if os.path.exists(self.manifest_path):
            os.remove(self.manifest_path)
        ots_path = f"{os.path.splitext(self.manifest_path)[0]}.ots"
        if os.path.exists(ots_path):
            os.remove(ots_path)
        if os.path.exists(self.test_dir) and not os.listdir(self.test_dir):
            os.rmdir(self.test_dir)

    @unittest.skipIf(not check_ots_installed(), "OpenTimestamps CLI not available")
    def test_timestamp_creation(self):
        """Test creating a timestamp for a glyph manifest"""
        ots_path, timestamp_hash = timestamp_glyph(self.manifest_path)
        
        # Check that .ots file was created
        self.assertTrue(os.path.exists(ots_path))
        self.assertTrue(ots_path.endswith('.ots'))
        
        # Check that hash was returned
        self.assertIsInstance(timestamp_hash, str)
        self.assertTrue(len(timestamp_hash) > 0)

    @unittest.skipIf(not check_ots_installed(), "OpenTimestamps CLI not available")
    def test_timestamp_verification(self):
        """Test verifying a timestamp"""
        # Create timestamp first
        ots_path, _ = timestamp_glyph(self.manifest_path)
        
        # Verify the timestamp
        success, message = verify_glyph_timestamp(self.manifest_path, ots_path)
        
        # Check verification result
        self.assertTrue(success)
        self.assertIn("Success! Bitcoin block", message)

    @unittest.skipIf(not check_ots_installed(), "OpenTimestamps CLI not available")
    def test_timestamp_invalid_file(self):
        """Test timestamping with invalid file"""
        with self.assertRaises(FileNotFoundError):
            timestamp_glyph("nonexistent_file.json")

    @unittest.skipIf(not check_ots_installed(), "OpenTimestamps CLI not available")
    def test_verify_invalid_ots(self):
        """Test verification with invalid .ots file"""
        # Create a dummy .ots file
        dummy_ots = f"{os.path.splitext(self.manifest_path)[0]}.ots"
        with open(dummy_ots, 'w') as f:
            f.write("invalid ots data")
        
        # Try to verify
        success, message = verify_glyph_timestamp(self.manifest_path, dummy_ots)
        self.assertFalse(success)
        self.assertTrue(len(message) > 0)

if __name__ == '__main__':
    unittest.main()
