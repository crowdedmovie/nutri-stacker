"""Exercise real Streamlit reruns while isolating all persistent user files."""
import json
import logging
import unittest
from contextlib import ExitStack
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

import app.storage as storage
from app.calculations import calculate_totals
from app.config import DEFAULT_TARGETS
from ui.tokens import load_tokens
from ui.live_input import _renderer

# AppTest intentionally runs with a synthetic script context.
logging.getLogger("streamlit.runtime.scriptrunner_utils.script_run_context").setLevel(logging.ERROR)

ROOT = Path(__file__).resolve().parents[1]


class AppIntegrationTests(unittest.TestCase):
    def setUp(self):
        # Each AppTest creates its own component registry (a fresh server runtime).
        _renderer.cache_clear()
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        self.temp = Path(self.stack.enter_context(TemporaryDirectory(prefix="nutri-ui-")))
        for name, filename in [("TARGETS_FILE", "targets.json"), ("PREFERENCES_FILE", "prefs.json"), ("LIVE_STATE_FILE", "live.json"), ("MEALS_DIR", "meals")]:
            self.stack.enter_context(patch.object(storage, name, self.temp / filename))
        self.app = AppTest.from_file(str(ROOT / "main.py"), default_timeout=15).run()
        self.assertHealthy()

    def assertHealthy(self):
        self.assertEqual([error.message for error in self.app.exception], [])

    def addFood(self):
        picker = self.app.selectbox(key="simple_food_picker")
        picker.select(picker.options[0]).run()
        self.assertHealthy()
        return next(iter(self.app.session_state["meal_items"]))

    def test_add_quantity_recomputes_same_render_and_remove(self):
        food = self.addFood()
        self.app.number_input(key=f"qty_{food}").set_value(250.0).run()
        self.assertHealthy()
        self.assertEqual(self.app.session_state["meal_items"][food], 250.0)
        foods, _ = storage.load_foods()
        calories = calculate_totals({food: 250.0}, foods)[0]["Calories"]
        html = " ".join(element.proto.body for element in self.app.get("html"))
        self.assertIn(f"{calories:.0f} kcal", html)
        self.app.button(key=f"selected_food_remove_{food}").click().run()
        self.assertHealthy()
        self.assertEqual(self.app.session_state["meal_items"], {})

    def test_save_load_restores_items_and_name(self):
        food = self.addFood()
        self.app.text_input(key="saved_meal_name").set_value("Test lunch").run()
        self.app.button(key="save-meal").click().run()
        self.assertHealthy()
        self.assertEqual(len(list((self.temp / "meals").glob("*.json"))), 1)
        self.app.button(key=f"selected_food_remove_{food}").click().run()
        self.app.text_input(key="saved_meal_name").set_value("Other name").run()
        self.app.button(key="load-meal").click().run()
        self.assertHealthy()
        self.assertIn(food, self.app.session_state["meal_items"])
        self.assertEqual(self.app.text_input(key="saved_meal_name").value, "Test lunch")

    def test_empty_save_validates_without_creating_file(self):
        self.app.button(key="save-meal").click().run()
        self.assertHealthy()
        self.assertTrue(self.app.error)
        self.assertEqual(list((self.temp / "meals").glob("*.json")), [])

    def test_targets_save_and_reset_callbacks(self):
        self.app.number_input(key="target_Calories").set_value(2400.0).run()
        self.app.button(key="save-targets").click().run()
        self.assertHealthy()
        self.assertEqual(json.loads((self.temp / "targets.json").read_text())["macros"]["Calories"], 2400.0)
        self.app.button(key="reset-targets").click().run()
        self.assertHealthy()
        self.assertEqual(self.app.number_input(key="target_Calories").value, DEFAULT_TARGETS["macros"]["Calories"])

    def test_recommendation_updates_target_widgets(self):
        self.app.button(key="apply-recommendation").click().run()
        self.assertHealthy()
        self.assertGreater(self.app.number_input(key="target_Calories").value, 0)
        self.assertIsNotNone(self.app.session_state["notice"])

    def test_advanced_catalog_favorite_sort_and_add(self):
        self.app.radio(key="food_search_mode").set_value("advanced").run()
        self.assertHealthy()
        favorite = next(button for button in self.app.button if button.key.startswith("food_favorite_toggle_"))
        food = favorite.key.removeprefix("food_favorite_toggle_")
        favorite.click().run()
        self.app.checkbox(key="food_favorites_only").check().run()
        self.assertHealthy()
        toggles = [button for button in self.app.button if button.key.startswith("food_meal_toggle_")]
        self.assertEqual(len(toggles), 1)
        self.assertIn(food, self.app.session_state["favorite_foods"])
        self.app.button(key="food_sort_mode_button").click().run()
        self.assertEqual(self.app.session_state["food_sort_mode"], "asc")
        self.app.button(key=f"food_meal_toggle_{food}").click().run()
        self.assertHealthy()
        self.assertIn(food, self.app.session_state["meal_items"])

    def test_language_and_persisted_live_state(self):
        food = self.addFood()
        self.app.selectbox(key="language_selector").set_value("en").run()
        self.assertHealthy()
        self.assertEqual(self.app.tabs[0].label, "Meal")
        new_app = AppTest.from_file(str(ROOT / "main.py"), default_timeout=15).run()
        self.assertEqual([error.message for error in new_app.exception], [])
        self.assertIn(food, new_app.session_state["meal_items"])
        self.assertEqual(new_app.selectbox(key="language_selector").value, "en")


class DesignSystemTests(unittest.TestCase):
    def test_native_theme_matches_tokens(self):
        import tomllib
        config = tomllib.loads((ROOT / ".streamlit/config.toml").read_text())
        for mode in ("light", "dark"):
            tokens = load_tokens()[mode]
            for option, token in [("primaryColor", "action"), ("backgroundColor", "surface"), ("secondaryBackgroundColor", "surface-secondary"), ("textColor", "text"), ("borderColor", "border")]:
                self.assertEqual(config["theme"][mode][option], tokens[token])

    def test_gallery_renders_all_native_states(self):
        _renderer.cache_clear()
        gallery = AppTest.from_file(str(ROOT / "design_system.py"), default_timeout=15).run()
        self.assertEqual([error.message for error in gallery.exception], [])
        self.assertTrue(gallery.button(key="gallery-disabled").disabled)
        self.assertTrue(gallery.text_input(key="gallery-input-disabled").disabled)
        self.assertTrue(gallery.selectbox(key="gallery-select-disabled").disabled)
        gallery.text_input(key="gallery-name").set_value("Lunch").run()
        gallery.selectbox(key="gallery-select").select("Dîner").run()
        self.assertEqual([error.message for error in gallery.exception], [])
        self.assertEqual(gallery.text_input(key="gallery-name").value, "Lunch")


if __name__ == "__main__":
    unittest.main()
