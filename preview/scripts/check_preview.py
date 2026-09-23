"""Check that the frontend preview is self-contained and cannot transact."""

from __future__ import annotations

import json
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1] / "dist"


class Page(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.ids: set[str] = set()
        self.references: list[str] = []
        self.noindex = False
        self.titles: list[str] = []
        self._title = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if values.get("id"):
            self.ids.add(values["id"] or "")
        if tag == "meta" and values.get("name") == "robots":
            self.noindex = "noindex" in (values.get("content") or "")
        if tag == "title":
            self._title = True
        for attr in ("src", "href", "poster"):
            if values.get(attr):
                self.references.append(values[attr] or "")

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self._title = False

    def handle_data(self, data: str) -> None:
        if self._title:
            self.titles.append(data)


def check() -> None:
    pages: dict[str, Page] = {}
    for name in ("index.html", "menu.html"):
        source = (ROOT / name).read_text(encoding="utf-8")
        assert "Design Preview" in source, name
        assert "not connected" in source, name
        assert "/api/orders" not in source and "/api/reservations" not in source, name
        page = Page()
        page.feed(source)
        assert page.noindex, f"{name} must stay noindex"
        assert page.titles, f"{name} needs a title"
        pages[name] = page

    for name, page in pages.items():
        for ref in page.references:
            parsed = urlsplit(ref)
            if parsed.scheme or parsed.netloc or ref.startswith(("tel:", "data:")):
                continue
            target_name = unquote(parsed.path) or name
            target = ROOT / target_name
            assert target.is_file(), f"{name}: missing {ref}"
            if parsed.fragment and target.suffix == ".html":
                assert parsed.fragment in pages[target.name].ids, f"{name}: missing anchor {ref}"

    items = json.loads((ROOT / "menu.json").read_text(encoding="utf-8"))
    assert len(items) >= 60, "Menu preview is missing published dishes"
    assert all(set(item) == {"id", "name", "category", "description", "image"} for item in items)
    assert not any("price" in item or "available" in item for item in items)
    assert (ROOT / "media" / "plov.mp4").stat().st_size > 1_000_000
    print(f"Checked {len(pages)} pages and {len(items)} published dishes")


if __name__ == "__main__":
    check()
