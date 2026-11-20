import json
import shutil
import struct
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class CatGrowthTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = (ROOT / "web" / "app.js").read_text(encoding="utf-8")
        cls.ui = (ROOT / "web" / "cat-companion-ui.js").read_text(encoding="utf-8")
        cls.growth = (ROOT / "web" / "cat-growth.js").read_text(encoding="utf-8")
        cls.css = (ROOT / "web" / "cat-companion-ui.css").read_text(encoding="utf-8")
        cls.index = (ROOT / "web" / "index.html").read_text(encoding="utf-8")
        cls.locales = json.loads((ROOT / "web" / "locales.json").read_text(encoding="utf-8"))

    def test_six_transparent_stage_models_are_valid_pngs(self):
        names = ("kitten", "growing", "young", "adult", "veteran", "legend")
        for name in names:
            path = ROOT / "web" / "assets" / f"cat-growth-{name}.png"
            data = path.read_bytes()
            self.assertEqual(data[:8], b"\x89PNG\r\n\x1a\n", name)
            width, height, depth, color = struct.unpack(">IIBB", data[16:26])
            self.assertEqual((width, height, depth, color), (1199, 1312, 8, 6), name)
            self.assertGreater(len(data), 100_000, name)

    def test_level_boundaries_map_to_the_six_models(self):
        node = shutil.which("node")
        if not node:
            self.skipTest("Node.js is unavailable")
        script = """
          const fs=require('fs'),vm=require('vm');
          const sandbox={window:{},document:{addEventListener(){}}};
          vm.runInNewContext(fs.readFileSync('web/cat-growth.js','utf8'),sandbox);
          const f=sandbox.window.CatGrowth.forLevel;
          const got=[1,2,5,6,10,11,15,16,20,21,99].map(n=>f(n).id);
          const want=['kitten','growing','growing','young','young','adult','adult','veteran','veteran','legend','legend'];
          if(JSON.stringify(got)!==JSON.stringify(want))process.exit(3);
        """
        subprocess.run([node, "-e", script], cwd=ROOT, check=True, capture_output=True, text=True)

    def test_real_cat_stage_is_rendered_with_equipment_inside_same_growth_layer(self):
        self.assertIn("growth?.asset||'/assets/cat-companion.png'", self.ui)
        self.assertIn("<div class=\"cat-growth-model\">${wearLayers(equipment,growth?.id)}", self.ui)
        self.assertIn("${overlays}</span></div>", self.ui)
        self.assertIn("window.CatGrowth?.forLevel(catLevel)", self.ui)
        self.assertIn("data-cat-level=\"${catLevel}\"", self.ui)
        self.assertIn("catGrowthAssetForLevel?.(appState.profile.level)", self.app)

    def test_growth_notification_only_follows_same_profile_level_increase(self):
        self.assertIn("nextLevel>previous.level", self.app)
        self.assertIn("previous.id===String(appState.profile.id||profileId)", self.app)
        self.assertIn("cpp-adventure-level-up", self.growth)
        self.assertIn("setTimeout(()=>{if(overlay.isConnected)close()},4400)", self.growth)
        self.assertIn("prefers-reduced-motion:reduce", self.css)

    def test_all_growth_ui_text_is_localized_in_tr_and_ru(self):
        keys = ("catStageKitten", "catStageGrowing", "catStageYoung", "catStageAdult", "catStageVeteran", "catStageLegend", "catGrowthTitle", "catGrowthLevel", "catGrowthCompanion", "catGrowthClose")
        for language in ("tr", "ru"):
            app = self.locales["modules"]["ui"][language]["app"]
            for key in keys:
                self.assertTrue(app.get(key), f"missing {language}.ui.app.{key}")

    def test_growth_module_loads_before_application_and_old_level_logic_is_untouched(self):
        self.assertLess(self.index.index('/cat-growth.js'), self.index.index('/app.js'))
        self.assertIn("lvl * 120", (ROOT / "server.py").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
