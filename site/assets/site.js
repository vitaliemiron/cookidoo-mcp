const storageKey = "cookidoo-mcp-theme";
const root = document.documentElement;

function setTheme(theme) {
  root.dataset.theme = theme;
  const toggle = document.querySelector("[data-theme-toggle]");
  if (toggle) {
    toggle.textContent = theme === "light" ? "Dark" : "Light";
    toggle.setAttribute(
      "aria-label",
      `Switch to ${theme === "light" ? "dark" : "light"} theme`,
    );
  }
}

try {
  const savedTheme = localStorage.getItem(storageKey);
  if (savedTheme === "light" || savedTheme === "dark") {
    setTheme(savedTheme);
  }
} catch {
  setTheme(root.dataset.theme === "light" ? "light" : "dark");
}

document.querySelector("[data-theme-toggle]")?.addEventListener("click", () => {
  const nextTheme = root.dataset.theme === "light" ? "dark" : "light";
  try {
    localStorage.setItem(storageKey, nextTheme);
  } catch {
    // Storage can be unavailable in strict privacy modes; the theme still works.
  }
  setTheme(nextTheme);
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
