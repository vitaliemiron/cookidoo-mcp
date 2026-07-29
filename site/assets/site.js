const storageKey = "cookidoo-mcp-theme";
const root = document.documentElement;
const systemThemeQuery = window.matchMedia("(prefers-color-scheme: dark)");
const themeCycle = ["system", "light", "dark"];
let currentThemePreference = "system";

function resolveTheme(preference) {
  if (preference === "system") {
    return systemThemeQuery.matches ? "dark" : "light";
  }
  return preference;
}

function setThemePreference(preference, persist = true) {
  const theme = resolveTheme(preference);
  currentThemePreference = preference;
  root.dataset.theme = theme;
  const themeColor = document.querySelector('meta[name="theme-color"]');
  if (themeColor) {
    themeColor.content = theme === "light" ? "#fffaf2" : "#020617";
  }

  if (persist) {
    try {
      if (preference === "system") {
        localStorage.removeItem(storageKey);
      } else {
        localStorage.setItem(storageKey, preference);
      }
    } catch {
      // Storage can be unavailable in strict privacy modes; the theme still works.
    }
  }

  const toggle = document.querySelector("[data-theme-toggle]");
  if (toggle) {
    const currentLabel =
      preference === "system"
        ? "System"
        : theme === "light"
          ? "Light"
          : "Dark";
    const currentIndex = themeCycle.indexOf(preference);
    const nextPreference = themeCycle[(currentIndex + 1) % themeCycle.length];
    toggle.textContent = currentLabel;
    toggle.setAttribute(
      "aria-label",
      `Theme: ${currentLabel.toLowerCase()}. Switch to ${nextPreference} theme`,
    );
    toggle.title =
      preference === "system"
        ? "Theme follows this device"
        : `${currentLabel} theme selected`;
  }
}

try {
  const savedPreference = localStorage.getItem(storageKey);
  if (savedPreference === "light" || savedPreference === "dark") {
    currentThemePreference = savedPreference;
  }
} catch {
  // Follow the device theme when storage is unavailable.
}
setThemePreference(currentThemePreference, false);

document.querySelector("[data-theme-toggle]")?.addEventListener("click", () => {
  const currentIndex = themeCycle.indexOf(currentThemePreference);
  const nextPreference = themeCycle[(currentIndex + 1) % themeCycle.length];
  setThemePreference(nextPreference);
});

systemThemeQuery.addEventListener("change", () => {
  if (currentThemePreference === "system") {
    setThemePreference("system", false);
  }
});

const menu = document.querySelector("[data-navigation]");
const menuToggle = document.querySelector("[data-menu-toggle]");

menuToggle?.addEventListener("click", () => {
  const isOpen = menu?.dataset.open === "true";
  if (menu) menu.dataset.open = String(!isOpen);
  menuToggle.setAttribute("aria-expanded", String(!isOpen));
});

menu?.querySelectorAll("a").forEach((link) => {
  link.addEventListener("click", () => {
    menu.dataset.open = "false";
    menuToggle?.setAttribute("aria-expanded", "false");
  });
});

const helpDisclosures = Array.from(document.querySelectorAll("details.help"));

helpDisclosures.forEach((disclosure) => {
  disclosure.addEventListener("toggle", () => {
    if (!disclosure.open) return;
    helpDisclosures.forEach((other) => {
      if (other !== disclosure) other.open = false;
    });
  });
});

document.addEventListener("click", (event) => {
  helpDisclosures.forEach((disclosure) => {
    if (!disclosure.contains(event.target)) disclosure.open = false;
  });
});

document.addEventListener("keydown", (event) => {
  if (event.key !== "Escape") return;
  const openDisclosure = document.querySelector("details.help[open]");
  if (!openDisclosure) return;
  openDisclosure.open = false;
  openDisclosure.querySelector("summary")?.focus();
});

const reducedMotion = window.matchMedia(
  "(prefers-reduced-motion: reduce)",
).matches;

const revealItems = document.querySelectorAll("[data-reveal]");
if (reducedMotion || !("IntersectionObserver" in window)) {
  revealItems.forEach((item) => item.classList.add("is-visible"));
} else {
  const revealObserver = new IntersectionObserver(
    (entries, observer) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add("is-visible");
          observer.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.14 },
  );
  revealItems.forEach((item) => revealObserver.observe(item));
}

const counters = document.querySelectorAll("[data-counter]");
if (!reducedMotion && "IntersectionObserver" in window) {
  const counterObserver = new IntersectionObserver(
    (entries, observer) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        const element = entry.target;
        const target = Number(element.dataset.counter);
        const suffix = element.dataset.suffix ?? "";
        const startTime = performance.now();
        const duration = 700;

        function updateCounter(now) {
          const progress = Math.min((now - startTime) / duration, 1);
          const eased = 1 - Math.pow(1 - progress, 3);
          element.textContent = `${Math.round(target * eased)}${suffix}`;
          if (progress < 1) requestAnimationFrame(updateCounter);
        }

        requestAnimationFrame(updateCounter);
        observer.unobserve(element);
      });
    },
    { threshold: 0.7 },
  );

  counters.forEach((counter) => {
    counter.textContent = `0${counter.dataset.suffix ?? ""}`;
    counterObserver.observe(counter);
  });
}

document.querySelectorAll(".code-shell").forEach((shell) => {
  const code = shell.querySelector("code");
  if (!code) return;
  const button = document.createElement("button");
  button.type = "button";
  button.className = "copy-button";
  button.textContent = "Copy";
  button.setAttribute("aria-label", "Copy code to clipboard");
  button.addEventListener("click", async () => {
    try {
      await navigator.clipboard.writeText(code.textContent ?? "");
      button.textContent = "Copied";
    } catch {
      button.textContent = "Select + copy";
    }
    window.setTimeout(() => {
      button.textContent = "Copy";
    }, 1800);
  });
  shell.append(button);
});

const searchInput = document.querySelector("[data-doc-search]");
const searchItems = Array.from(document.querySelectorAll("[data-search-item]"));
const searchStatus = document.querySelector("[data-search-status]");
const noResults = document.querySelector("[data-no-results]");

function filterDocumentation() {
  const query = searchInput?.value.trim().toLocaleLowerCase() ?? "";
  let matches = 0;

  searchItems.forEach((item) => {
    const haystack = (
      item.dataset.searchText ??
      item.textContent ??
      ""
    ).toLocaleLowerCase();
    const isMatch = !query || haystack.includes(query);
    item.hidden = !isMatch;
    if (isMatch) matches += 1;
  });

  if (searchStatus) {
    searchStatus.textContent = query
      ? `${matches} matching tool${matches === 1 ? "" : "s"}`
      : `${searchItems.length} tools available`;
  }
  if (noResults) noResults.hidden = matches !== 0;
}

searchInput?.addEventListener("input", filterDocumentation);
if (searchInput) filterDocumentation();

const storyFrames = Array.from(document.querySelectorAll(".story-frame"));
const storyLinks = Array.from(
  document.querySelectorAll("[data-story-progress] a"),
);

if (storyFrames.length && "IntersectionObserver" in window) {
  const storyObserver = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        storyFrames.forEach((frame) => frame.classList.remove("is-active"));
        entry.target.classList.add("is-active");
        storyLinks.forEach((link) => {
          const isCurrent = link.hash === `#${entry.target.id}`;
          if (isCurrent) {
            link.setAttribute("aria-current", "step");
          } else {
            link.removeAttribute("aria-current");
          }
        });
      });
    },
    { threshold: 0.58 },
  );
  storyFrames.forEach((frame) => storyObserver.observe(frame));
}

if (storyFrames.length) {
  document.addEventListener("keydown", (event) => {
    if (!["ArrowDown", "ArrowUp", "PageDown", "PageUp"].includes(event.key)) {
      return;
    }
    const activeIndex = Math.max(
      0,
      storyFrames.findIndex((frame) => frame.classList.contains("is-active")),
    );
    const direction =
      event.key === "ArrowDown" || event.key === "PageDown" ? 1 : -1;
    const nextIndex = Math.min(
      storyFrames.length - 1,
      Math.max(0, activeIndex + direction),
    );
    if (nextIndex !== activeIndex) {
      event.preventDefault();
      storyFrames[nextIndex].scrollIntoView({
        behavior: reducedMotion ? "auto" : "smooth",
      });
    }
  });
}
