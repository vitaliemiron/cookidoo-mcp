import ast
import json
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlparse
from xml.etree import ElementTree


ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"
BASE_PATH = "/cookidoo-mcp/"


class LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []
        self.ids: set[str] = set()
        self.has_viewport = False
        self.has_main = False
        self.has_skip_link = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        element_id = values.get("id")
        if element_id:
            self.ids.add(element_id)

        if tag == "meta" and values.get("name") == "viewport":
            self.has_viewport = True
        if tag == "main":
            self.has_main = True
        if tag == "a" and "skip-link" in (values.get("class") or "").split():
            self.has_skip_link = True

        for attribute in ("href", "src"):
            value = values.get(attribute)
            if value:
                self.links.append(value)


def _server_tool_names() -> set[str]:
    tree = ast.parse((ROOT / "server.py").read_text(encoding="utf-8"))
    names: set[str] = set()
    for node in tree.body:
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for decorator in node.decorator_list:
            if (
                isinstance(decorator, ast.Call)
                and isinstance(decorator.func, ast.Attribute)
                and isinstance(decorator.func.value, ast.Name)
                and decorator.func.value.id == "mcp"
                and decorator.func.attr == "tool"
            ):
                names.add(node.name)
    return names


def _local_target(page: Path, value: str) -> tuple[Path, str | None] | None:
    parsed = urlparse(value)
    if parsed.scheme or parsed.netloc or value.startswith(("mailto:", "tel:", "data:")):
        return None

    fragment = unquote(parsed.fragment) or None
    path = unquote(parsed.path)
    if not path:
        return page, fragment
    if path.startswith(BASE_PATH):
        target = SITE / path.removeprefix(BASE_PATH)
    elif path.startswith("/"):
        return None
    else:
        target = page.parent / path

    if path.endswith("/") or target.is_dir():
        target = target / "index.html"
    return target.resolve(), fragment


def test_tool_catalog_matches_server_tools() -> None:
    catalog = json.loads((SITE / "tools.json").read_text(encoding="utf-8"))
    catalog_names = {tool["name"] for tool in catalog["tools"]}

    assert catalog_names == _server_tool_names()
    assert len(catalog["tools"]) == 16
    assert all(tool["signature"] and tool["description"] for tool in catalog["tools"])


def test_html_pages_are_accessible_and_local_links_resolve() -> None:
    pages = sorted(SITE.rglob("*.html"))
    assert pages

    parsed_pages: dict[Path, LinkParser] = {}
    for page in pages:
        parser = LinkParser()
        parser.feed(page.read_text(encoding="utf-8"))
        parsed_pages[page.resolve()] = parser
        assert parser.has_viewport, f"{page} has no viewport meta tag"
        assert parser.has_main, f"{page} has no main landmark"
        assert parser.has_skip_link, f"{page} has no skip link"

    for page, parser in parsed_pages.items():
        for value in parser.links:
            local = _local_target(page, value)
            if local is None:
                continue
            target, fragment = local
            assert target.exists(), f"{page}: broken local reference {value}"
            if fragment and target.suffix == ".html":
                target_parser = parsed_pages.get(target)
                assert target_parser is not None, f"{page}: cannot inspect {value}"
                assert fragment in target_parser.ids, f"{page}: missing fragment {value}"


def test_ai_resources_cover_every_documentation_area() -> None:
    llms = (SITE / "llms.txt").read_text(encoding="utf-8")
    full = (SITE / "llms-full.txt").read_text(encoding="utf-8")

    for path in (
        "/docs/",
        "/docs/tools/",
        "/docs/guided-cooking/",
        "/docs/automation/",
        "/docs/testing/",
        "/tools.json",
    ):
        assert path in llms
    for rule in ("Required step separation", "UTF-16", "16. upload_custom_recipe"):
        assert rule in full


def test_homepage_uses_a_clear_consumer_journey() -> None:
    homepage = (SITE / "index.html").read_text(encoding="utf-8")

    assert "From idea to dinner." in homepage
    assert "Spend less time managing meals" not in homepage
    assert homepage.count('class="journey-number"') == 5
    for owner in ("AI conversation", "Cookidoo MCP", "Another MCP"):
        assert owner in homepage
    for action in (
        "Find an idea",
        "Make the recipe yours",
        "Plan your week",
        "Prepare the list",
        "Order when you are ready",
    ):
        assert action in homepage
    assert 'details class="help' in homepage


def test_readme_is_friendly_to_people_and_safe_for_agents() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")

    assert "**From idea to dinner.**" in readme
    assert 'width="680"' in readme
    for label in (
        "Motivation—why use it?",
        "How it works",
        "Visual story",
        "Getting-started guide",
        "Planning and shopping",
        "Safety and reliability",
    ):
        assert label in readme
    assert "read [`AGENTS.md`](AGENTS.md) completely" in readme
    assert "only after the user explicitly agrees" in readme
    assert "Repository stars require user consent" in agents


def test_sitemap_pages_exist() -> None:
    tree = ElementTree.parse(SITE / "sitemap.xml")
    namespace = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    urls = [node.text for node in tree.findall("s:url/s:loc", namespace)]

    assert len(urls) == 7
    for url in urls:
        assert url is not None
        parsed = urlparse(url)
        assert parsed.netloc == "vitaliemiron.github.io"
        assert parsed.path.startswith(BASE_PATH)
        target = SITE / parsed.path.removeprefix(BASE_PATH)
        if parsed.path.endswith("/"):
            target /= "index.html"
        assert target.exists(), f"sitemap target does not exist: {url}"
