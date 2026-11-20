import json
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class LocaleCatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = json.loads((ROOT / "web" / "locales.json").read_text(encoding="utf-8"))

    def test_every_catalog_module_has_nonempty_parallel_tr_and_ru_content(self):
        catalog = self.catalog

        def compare(left, right, location):
            if isinstance(left, list):
                self.assertIsInstance(right, list, location)
                self.assertEqual(len(left), len(right), location)
                self.assertTrue(all(isinstance(value, str) and value.strip() for value in left), location)
                self.assertTrue(all(isinstance(value, str) and value.strip() for value in right), location)
                return
            self.assertEqual(set(left), set(right), location)
            for key in left:
                path = f"{location}.{key}"
                if isinstance(left[key], dict):
                    self.assertIsInstance(right[key], dict, path)
                    compare(left[key], right[key], path)
                elif isinstance(left[key], list):
                    self.assertIsInstance(right[key], list, path)
                    self.assertEqual(len(left[key]), len(right[key]), path)
                    self.assertTrue(all(isinstance(v, str) and v.strip() for v in left[key]), path)
                    self.assertTrue(all(isinstance(v, str) and v.strip() for v in right[key]), path)
                else:
                    self.assertIsInstance(left[key], str, path)
                    self.assertIsInstance(right[key], str, path)
                    self.assertTrue(left[key].strip(), path)
                    self.assertTrue(right[key].strip(), path)

        compare(catalog["tr"], catalog["ru"], "core")
        for name, translations in catalog["modules"].items():
            if name == "pairs":
                for key, pair in translations.items():
                    self.assertEqual(set(pair), {"tr", "ru"}, f"pairs.{key}")
                    self.assertTrue(pair["tr"].strip(), f"pairs.{key}.tr")
                    self.assertTrue(pair["ru"].strip(), f"pairs.{key}.ru")
            else:
                compare(translations["tr"], translations["ru"], name)

    def test_runtime_catalog_loads_and_switches_language_without_reload(self):
        script = r"""
const fs = require('fs'), vm = require('vm');
global.window = global;
global.localStorage = {getItem: () => 'tr'};
global.document = {documentElement: {lang: 'tr'}};
const catalog = JSON.parse(fs.readFileSync('web/locales.json', 'utf8'));
global.fetch = async () => ({ok: true, json: async () => catalog});
vm.runInThisContext(fs.readFileSync('web/i18n.js', 'utf8'));
CppAdventureI18n.ready.then(() => {
  const before = L('stats.title');
  const mapTitleTr = L('pairs.rpg.025');
  const mapTitleRu = CppAdventureI18n.t('pairs.rpg.025', 'ru');
  CppAdventureI18n.setLanguage('ru');
  const after = L('stats.title');
  const zones = CppAdventureI18n.module('worldZones');
  console.log(JSON.stringify({before, after, mapTitleTr, mapTitleRu, zones: zones.length, audit: CppAdventureI18n.audit()}));
}).catch(error => { console.error(error); process.exitCode = 1; });
"""
        result = subprocess.run(["node", "-e", script], cwd=ROOT, capture_output=True, text=True, encoding="utf-8", timeout=15)
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout.strip())
        self.assertNotEqual(payload["before"], payload["after"])
        self.assertNotEqual(payload["mapTitleTr"], payload["mapTitleRu"])
        self.assertNotIn("pairs.", payload["mapTitleRu"])
        self.assertEqual(payload["zones"], 20)
        self.assertTrue(payload["audit"]["ok"], payload["audit"]["mismatches"][:10])

    def test_map_art_and_locale_catalog_are_served_offline_by_local_server(self):
        page = (ROOT / "web" / "index.html").read_text(encoding="utf-8")
        self.assertIn('<script src="/i18n.js"></script>', page)
        self.assertTrue((ROOT / "web" / "assets" / "cpp-world-map.svg").is_file())
        self.assertIn('/assets/cpp-world-map.svg', (ROOT / "web" / "rpg-ui.js").read_text(encoding="utf-8"))
        app = (ROOT / "web" / "app.js").read_text(encoding="utf-8")
        self.assertIn("document.dispatchEvent(new Event('cpp-adventure-language-changed'))", app)
        self.assertNotIn("window.dispatchEvent(new Event('cpp-adventure-language-changed'))", app)

    def test_static_navigation_and_toolbar_labels_are_localized(self):
        page = (ROOT / "web" / "index.html").read_text(encoding="utf-8")
        app = (ROOT / "web" / "app.js").read_text(encoding="utf-8")
        for key in ("statsNav", "devtoolsNav", "settingsTitle", "soundTitle", "profilesTitle"):
            self.assertIn(key, self.catalog["tr"])
            self.assertIn(key, self.catalog["ru"])
        self.assertIn('data-i="statsNav"', page)
        self.assertIn('data-i="devtoolsNav"', page)
        self.assertIn("$$('[data-i-title]').forEach", app)
        self.assertIn("b.dataset.iTitle='saveLoad'", app)

    def test_stage27_workshop_arena_and_splash_copy_uses_localized_catalog(self):
        workshop = self.catalog["modules"]["workshop"]
        for key in ("newProjectName", "cancel", "confirmDelete", "fileExists", "keepOneFile"):
            self.assertIn(key, workshop["tr"])
            self.assertIn(key, workshop["ru"])
        workshop_ui = (ROOT / "web" / "project-workshop.js").read_text(encoding="utf-8")
        self.assertIn("c.newProjectName", workshop_ui)
        self.assertIn("c.keepOneFile", workshop_ui)
        arena_ui = (ROOT / "web" / "arena-ui.js").read_text(encoding="utf-8")
        self.assertIn("L('ui.app.arenaTestDescription',{count:arena.tests})", arena_ui)
        splash = self.catalog["modules"]["splash"]
        self.assertIn("screenLabel", splash["tr"])
        self.assertIn("screenLabel", splash["ru"])
        self.assertIn("screenLabel", (ROOT / "web" / "splash.js").read_text(encoding="utf-8"))

    def test_language_switch_button_accessibility_label_is_bilingual(self):
        self.assertEqual(self.catalog["tr"]["languageToggleLabel"], "Dili değiştir")
        self.assertEqual(self.catalog["ru"]["languageToggleLabel"], "Сменить язык")
        page = (ROOT / "web" / "index.html").read_text(encoding="utf-8")
        self.assertIn('data-i-aria="languageToggleLabel"', page)

    def test_stage28_cat_crew_art_is_local_and_tr_ru_labeled(self):
        asset = ROOT / "web" / "assets" / "cat-crew-atlas.png"
        self.assertTrue(asset.is_file())
        self.assertLess(asset.stat().st_size, 3_000_000)
        self.assertEqual(asset.read_bytes()[25], 6, "source atlas should keep its RGBA alpha channel")
        app = (ROOT / "web" / "app.js").read_text(encoding="utf-8")
        css = (ROOT / "web" / "visual-upgrade.css").read_text(encoding="utf-8")
        roles = ("professor", "teacher", "hacker", "debugger", "wizard", "boss")
        for role in roles:
            tile = ROOT / "web" / "assets" / f"cat-{role}.png"
            self.assertTrue(tile.is_file(), f"missing isolated {role} portrait")
            data = tile.read_bytes()
            self.assertEqual(data[:8], b"\x89PNG\r\n\x1a\n")
            self.assertEqual((int.from_bytes(data[16:20], "big"), int.from_bytes(data[20:24], "big")), (512, 512))
            self.assertEqual(data[25], 6, f"{role} portrait should preserve transparency")
            self.assertIn(f"['{role}'", app)
            self.assertIn(f"cat-${{role}}.png", app)
            for suffix in ("Role", "Desc", "Action"):
                key = f"cat{role.title()}{suffix}"
                for language in ("tr", "ru"):
                    self.assertTrue(self.catalog["modules"]["ui"][language]["app"].get(key), f"missing {language}.{key}")
        self.assertIn("grid-template-columns:repeat(3,minmax(0,1fr))", css)
        self.assertIn("data-cat-action", app)
        self.assertIn("CppAdventureCatGuide", app)
        for role, key in (("professor", "catProfessor"), ("teacher", "catTeacher"), ("hacker", "catHacker"), ("debugger", "catDebugger"), ("wizard", "catWizard"), ("boss", "catBoss")):
            self.assertIn(f"'{role}','{key}'", app)
        self.assertIn('href="/visual-upgrade.css"', (ROOT / "web" / "index.html").read_text(encoding="utf-8"))
        for key in ("catCrewTitle", "catProfessor", "catTeacher", "catHacker", "catDebugger", "catWizard", "catBoss"):
            self.assertIn(key, self.catalog["modules"]["ui"]["tr"]["app"])
            self.assertIn(key, self.catalog["modules"]["ui"]["ru"]["app"])

    def test_profile_picker_body_uses_central_tr_ru_catalog(self):
        app = (ROOT / "web" / "app.js").read_text(encoding="utf-8")
        profile_picker = app.split("function renderProfiles()", 1)[1].split("function profileForm(", 1)[0]
        for key in ("profile", "switch", "noProfiles", "create", "select", "leaderboard"):
            self.assertIn(f"tr('{key}')", profile_picker)


if __name__ == "__main__":
    unittest.main()
