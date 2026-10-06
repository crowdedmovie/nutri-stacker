"""Single source of tokens shared by native widgets and custom components."""
import json
from functools import lru_cache
from pathlib import Path


@lru_cache(maxsize=1)
def load_tokens() -> dict:
    return json.loads(Path(__file__).with_name("tokens.json").read_text(encoding="utf-8"))


def css_variables(theme: str = "light", selector: str = ":root") -> str:
    tokens = load_tokens()
    values = {}
    for group, entries in tokens.items():
        if group not in {"light", "dark"}:
            values.update({f"{group}-{key}": value for key, value in entries.items()})
    values.update(tokens["dark" if theme == "dark" else "light"])
    declarations = ";".join(f"--ns-{key}:{value}" for key, value in values.items())
    return f"{selector}{{{declarations}}}"
