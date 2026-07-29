"""Build static localized marketing pages from the English source pages."""

from __future__ import annotations

import argparse
import html
from html.parser import HTMLParser
import json
from pathlib import Path, PurePosixPath
import posixpath
import re
import sys
from urllib.parse import urlsplit, urlunsplit


ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"
BASE_URL = "https://vitaliemiron.github.io/cookidoo-mcp/"
SOURCE_PAGES = (
    PurePosixPath("index.html"),
    PurePosixPath("presentation/index.html"),
)
LOCALIZED_DIRECTORIES = {
    PurePosixPath("."),
    PurePosixPath("presentation"),
}
LOCALES = {
    "de": {"code": "DE", "og_locale": "de_DE"},
    "sv": {"code": "SV", "og_locale": "sv_SE"},
    "ro": {"code": "RO", "og_locale": "ro_RO"},
    "ru": {"code": "RU", "og_locale": "ru_RU"},
}
COUNTER_SUFFIXES = {
    "de": {"-day": " Tage"},
    "sv": {"-day": " dagar"},
    "ro": {"-day": " zile"},
    "ru": {"-day": " дней"},
}
TRANSLATED_ATTRIBUTES = {
    "aria-label",
    "data-aria-template",
    "data-label-dark",
    "data-label-light",
    "data-label-system",
    "data-title-selected",
    "data-title-system",
    "placeholder",
    "title",
}
PRESERVED_MESSAGES = {
    "?",
    "→",
    "↓",
    "1",
    "2",
    "3",
    "4",
    "5",
    "7",
    "16",
    "24h",
    "1×",
    "CM",
    "Cookidoo MCP",
    "GitHub",
    "English",
    "Deutsch",
    "Svenska",
    "Română",
    "Русский",
    "llms.txt",
    "tools.json",
}


def normalized_message(value: str) -> str:
    return " ".join(value.split())


def should_preserve(value: str) -> bool:
    if value in PRESERVED_MESSAGES:
        return True
    return bool(re.fullmatch(r"[\d\s./×?→↓+\-–—]+", value))


def page_url(page: PurePosixPath, locale: str) -> str:
    directory = page.parent
    localized = PurePosixPath(locale)
    if directory != PurePosixPath("."):
        localized /= directory
    suffix = "" if str(localized) == "." else f"{localized.as_posix()}/"
    return f"{BASE_URL}{suffix}"


def resolve_local_path(page: PurePosixPath, raw_path: str) -> PurePosixPath:
    joined = posixpath.normpath(
        posixpath.join(page.parent.as_posix(), raw_path)
    )
    return PurePosixPath(joined)


def localized_link(
    value: str,
    source_page: PurePosixPath,
    target_page: PurePosixPath,
    locale: str,
) -> str:
    parsed = urlsplit(value)
    if (
        parsed.scheme
        or parsed.netloc
        or value.startswith(("mailto:", "tel:", "data:"))
        or not parsed.path
        or parsed.path.startswith("/")
    ):
        return value

    resolved = resolve_local_path(source_page, parsed.path)
    is_directory = parsed.path.endswith("/")
    if resolved in LOCALIZED_DIRECTORIES and is_directory:
        resolved = PurePosixPath(locale) / resolved

    relative = posixpath.relpath(
        resolved.as_posix(),
        start=target_page.parent.as_posix(),
    )
    if is_directory:
        relative = f"{relative.rstrip('/')}/"
    elif parsed.path.startswith("./") and not relative.startswith((".", "/")):
        relative = f"./{relative}"

    return urlunsplit(("", "", relative, parsed.query, parsed.fragment))


class LocalizingParser(HTMLParser):
    def __init__(
        self,
        *,
        locale: str,
        source_page: PurePosixPath,
        translations: dict[str, str],
    ) -> None:
        super().__init__(convert_charrefs=False)
        self.locale = locale
        self.source_page = source_page
        self.target_page = PurePosixPath(locale) / source_page
        self.translations = translations
        self.output: list[str] = []
        self.skip_depth = 0
        self.missing: set[str] = set()

    def translate(self, value: str) -> str:
        message = normalized_message(value)
        if not message or should_preserve(message):
            return value
        translated = self.translations.get(message)
        if translated is None:
            self.missing.add(message)
            return value
        return translated

    def translated_data(self, data: str) -> str:
        if self.skip_depth:
            return data
        message = normalized_message(data)
        if not message or should_preserve(message):
            return data
        translated = self.translations.get(message)
        if translated is None:
            self.missing.add(message)
            return data
        leading = data[: len(data) - len(data.lstrip())]
        trailing = data[len(data.rstrip()) :]
        return f"{leading}{html.escape(translated, quote=False)}{trailing}"

    def rendered_attributes(
        self,
        tag: str,
        attrs: list[tuple[str, str | None]],
    ) -> str:
        values = dict(attrs)
        rendered: list[tuple[str, str | None]] = []
        for name, original in attrs:
            value = original
            if tag == "html" and name == "lang":
                value = self.locale
            elif name in {"href", "src"} and value:
                value = localized_link(
                    value,
                    self.source_page,
                    self.target_page,
                    self.locale,
                )
            elif name in TRANSLATED_ATTRIBUTES and value:
                value = self.translate(value)
            elif name == "data-suffix" and value:
                value = COUNTER_SUFFIXES[self.locale].get(value, value)
            elif (
                tag == "meta"
                and name == "content"
                and (
                    values.get("name") == "description"
                    or values.get("property")
                    in {"og:title", "og:description", "og:image:alt"}
                )
                and value
            ):
                value = self.translate(value)

            if (
                tag == "link"
                and values.get("rel") == "canonical"
                and name == "href"
            ):
                value = page_url(self.source_page, self.locale)
            if (
                tag == "meta"
                and values.get("property") == "og:url"
                and name == "content"
            ):
                value = page_url(self.source_page, self.locale)
            if (
                tag == "meta"
                and values.get("property") == "og:locale"
                and name == "content"
            ):
                value = LOCALES[self.locale]["og_locale"]
            if (
                tag == "a"
                and values.get("data-language")
                and name == "aria-current"
            ):
                continue
            rendered.append((name, value))

        if tag == "a" and values.get("data-language") == self.locale:
            rendered.append(("aria-current", "page"))

        parts = []
        for name, value in rendered:
            if value is None:
                parts.append(name)
            else:
                parts.append(f'{name}="{html.escape(value, quote=True)}"')
        return f" {' '.join(parts)}" if parts else ""

    def handle_decl(self, decl: str) -> None:
        self.output.append(f"<!{decl}>")

    def handle_starttag(
        self,
        tag: str,
        attrs: list[tuple[str, str | None]],
    ) -> None:
        self.output.append(f"<{tag}{self.rendered_attributes(tag, attrs)}>")
        if tag in {"script", "style", "code", "pre"}:
            self.skip_depth += 1

    def handle_startendtag(
        self,
        tag: str,
        attrs: list[tuple[str, str | None]],
    ) -> None:
        self.output.append(f"<{tag}{self.rendered_attributes(tag, attrs)}>")

    def handle_endtag(self, tag: str) -> None:
        self.output.append(f"</{tag}>")
        if tag in {"script", "style", "code", "pre"} and self.skip_depth:
            self.skip_depth -= 1

    def handle_data(self, data: str) -> None:
        self.output.append(self.translated_data(data))

    def handle_comment(self, data: str) -> None:
        self.output.append(f"<!--{data}-->")

    def handle_entityref(self, name: str) -> None:
        self.output.append(f"&{name};")

    def handle_charref(self, name: str) -> None:
        self.output.append(f"&#{name};")

    def handle_pi(self, data: str) -> None:
        self.output.append(f"<?{data}>")


def load_translations(locale: str) -> dict[str, str]:
    path = SITE / "i18n" / f"{locale}.json"
    document = json.loads(path.read_text(encoding="utf-8"))
    if document.get("locale") != locale:
        raise ValueError(f"{path}: locale must be {locale}")
    messages = document.get("messages")
    if not isinstance(messages, dict) or not all(
        isinstance(key, str) and isinstance(value, str)
        for key, value in messages.items()
    ):
        raise ValueError(f"{path}: messages must be a string-to-string object")
    overrides_path = SITE / "i18n" / "overrides.json"
    overrides = json.loads(overrides_path.read_text(encoding="utf-8"))
    locale_overrides = overrides.get(locale)
    if not isinstance(locale_overrides, dict) or not all(
        isinstance(key, str) and isinstance(value, str)
        for key, value in locale_overrides.items()
    ):
        raise ValueError(
            f"{overrides_path}: {locale} must be a string-to-string object"
        )
    return {**messages, **locale_overrides}


def render_page(
    source_page: PurePosixPath,
    locale: str,
    translations: dict[str, str],
) -> tuple[str, set[str]]:
    parser = LocalizingParser(
        locale=locale,
        source_page=source_page,
        translations=translations,
    )
    parser.feed((SITE / source_page).read_text(encoding="utf-8"))
    parser.close()
    return "".join(parser.output), parser.missing


def build(*, check: bool) -> None:
    failures: list[str] = []
    for locale in LOCALES:
        translations = load_translations(locale)
        for source_page in SOURCE_PAGES:
            rendered, missing = render_page(
                source_page,
                locale,
                translations,
            )
            if missing:
                formatted = "\n  - ".join(sorted(missing))
                failures.append(
                    f"{locale}/{source_page} is missing:\n  - {formatted}"
                )
                continue

            target = SITE / locale / source_page
            if check:
                if not target.exists() or target.read_text(
                    encoding="utf-8"
                ) != rendered:
                    failures.append(f"{target} is not up to date")
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(rendered, encoding="utf-8")

    if failures:
        raise RuntimeError("\n".join(failures))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail when generated localized pages are missing or stale",
    )
    arguments = parser.parse_args()
    try:
        build(check=arguments.check)
    except (OSError, ValueError, RuntimeError) as error:
        print(error, file=sys.stderr)
        raise SystemExit(1) from error


if __name__ == "__main__":
    main()
