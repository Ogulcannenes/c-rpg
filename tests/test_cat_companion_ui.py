import json
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class CatCompanionVisualUiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.locales = json.loads((ROOT / "web" / "locales.json").read_text(encoding="utf-8"))
        cls.script = (ROOT / "web" / "cat-companion-ui.js").read_text(encoding="utf-8")
        cls.index = (ROOT / "web" / "index.html").read_text(encoding="utf-8")
        cls.svg = ET.parse(ROOT / "web" / "assets" / "cat-wearables.svg").getroot()

    def test_accessory_art_has_separate_layer_for_every_shop_item(self):
        ids = {node.attrib.get("id") for node in self.svg.iter()}
        for item in ("wizard", "crown", "bow", "headset", "scarf", "moon-cape", "backpack", "raincoat", "yarn", "fish"):
            self.assertIn(item, ids)
            self.assertIn(f"{item}", self.script)
        self.assertEqual(self.svg.attrib["viewBox"], "0 0 1199 1312")

    def test_preview_is_client_only_and_dressing_uses_profile_api(self):
        self.assertIn("let previewItems = {}", self.script)
        self.assertIn("const [slot,id] of Object.entries(previewItems)", self.script)
        self.assertIn("if(next[slot]===id)delete next[slot];else next[slot]=id", self.script)
        self.assertIn("equipment[slot]=id", self.script)
        self.assertIn("Object.entries(previewItems).some", self.script)
        self.assertIn("previewItems={}", self.script)

    def test_bow_art_is_scaled_to_stay_above_the_cat_eyes(self):
        bow = next(node for node in self.svg.iter() if node.attrib.get("id") == "bow")
        group = next(node for node in bow if node.tag.endswith("g"))
        self.assertIn("scale(.62)", group.attrib.get("transform", ""))
        self.assertIn("/api/companion/equip", self.script)
        self.assertIn("/api/companion/loadout/save", self.script)
        self.assertIn("/api/companion/loadout/apply", self.script)
        self.assertIn("/api/companion/loadout/delete", self.script)
        self.assertIn("/api/shop/buy", self.script)

    def test_stage_2_copy_is_loaded_and_all_new_ui_text_has_tr_and_ru(self):
        self.assertIn("/cat-companion-ui.js", self.index)
        self.assertIn("/cat-companion-ui.css", self.index)
        required = ("catPreviewing", "catWearingNow", "catLayerNote", "catClearPreview", "catTryBeforeBuy", "catTryOn", "catOwned", "catRemove", "catOutfits", "catOutfitName", "catSaveOutfit", "catApplyOutfit", "catNameRequired", "catOutfitSaved", "catOutfitApplied", "catSlot_head", "catSlot_ears", "catSlot_neck", "catSlot_back", "catSlot_body", "catSlot_toy")
        for language in ("tr", "ru"):
            app = self.locales["modules"]["ui"][language]["app"]
            for key in required:
                self.assertTrue(app.get(key), f"missing {language}.ui.app.{key}")

    def test_loadouts_remain_profile_scoped_and_owned_items_are_rendered(self):
        self.assertIn("p.companion_loadouts||[]", self.script)
        self.assertIn("new Set(p.owned_items||[])", self.script)
        self.assertIn("equipped_items", self.script)


if __name__ == "__main__":
    unittest.main()
