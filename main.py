import flet as ft

from app.storage import ensure_storage, load_foods, load_targets
from app.ui import NutriStackerApp


def main(page: ft.Page) -> None:
    page.title = "Nutri Stacker"
    page.theme_mode = ft.ThemeMode.SYSTEM
    page.theme = ft.Theme(color_scheme_seed=ft.Colors.GREEN, use_material3=True)
    page.dark_theme = ft.Theme(color_scheme_seed=ft.Colors.GREEN, use_material3=True)

    ensure_storage()
    foods, foods_error = load_foods()
    targets, targets_error = load_targets()
    NutriStackerApp(page, foods, targets, foods_error, targets_error).mount()


if __name__ == "__main__":
    ft.run(main)
