const storageKey = "cookidoo-mcp-theme";
const languageStorageKey = "cookidoo-mcp-language";
const root = document.documentElement;
const systemThemeQuery = window.matchMedia("(prefers-color-scheme: dark)");
const themeCycle = ["system", "light", "dark"];
const supportedLanguages = new Set(["en", "de", "sv", "ro", "ru"]);
let currentThemePreference = "system";

function normalizedLanguage(value) {
  return value?.toLowerCase().split(/[-_]/)[0] ?? "";
}

function savedLanguage() {
  try {
    const language = normalizedLanguage(localStorage.getItem(languageStorageKey));
    return supportedLanguages.has(language) ? language : null;
  } catch {
    return null;
  }
}

function browserLanguage() {
  const candidates = [...(navigator.languages ?? []), navigator.language];
  for (const candidate of candidates) {
    const language = normalizedLanguage(candidate);
    if (supportedLanguages.has(language)) return language;
  }
  return "en";
}

function rememberLanguage(language) {
  const normalized = normalizedLanguage(language);
  if (!supportedLanguages.has(normalized)) return;
  try {
    localStorage.setItem(languageStorageKey, normalized);
  } catch {
    // Navigation still works when storage is unavailable.
  }
}

function redirectToPreferredLanguage() {
  const currentLanguage = normalizedLanguage(root.lang);
  if (currentLanguage !== "en") return false;

  const preferredLanguage = savedLanguage() ?? browserLanguage();
  if (preferredLanguage === "en") return false;

  const target = document.querySelector(
    `[data-language="${preferredLanguage}"]`,
  );
  if (!target?.href) return false;

  const targetUrl = new URL(target.href);
  targetUrl.search = window.location.search;
  targetUrl.hash = window.location.hash;
  window.location.replace(targetUrl.href);
  return true;
}

redirectToPreferredLanguage();

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
    const labels = {
      system: toggle.dataset.labelSystem ?? "System",
      light: toggle.dataset.labelLight ?? "Light",
      dark: toggle.dataset.labelDark ?? "Dark",
    };
    const currentLabel =
      preference === "system"
        ? labels.system
        : theme === "light"
          ? labels.light
          : labels.dark;
    const currentIndex = themeCycle.indexOf(preference);
    const nextPreference = themeCycle[(currentIndex + 1) % themeCycle.length];
    const nextTheme = resolveTheme(nextPreference);
    const nextLabel =
      nextPreference === "system"
        ? labels.system
        : nextTheme === "light"
          ? labels.light
          : labels.dark;
    toggle.textContent = currentLabel;
    toggle.setAttribute(
      "aria-label",
      (toggle.dataset.ariaTemplate ??
        "Theme: {current}. Switch to {next} theme")
        .replace("{current}", currentLabel)
        .replace("{next}", nextLabel),
    );
    toggle.title =
      preference === "system"
        ? (toggle.dataset.titleSystem ?? "Theme follows this device")
        : (toggle.dataset.titleSelected ?? "{current} theme selected").replace(
            "{current}",
            currentLabel,
          );
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

const languagePicker = document.querySelector("[data-language-picker]");
languagePicker?.querySelectorAll("[data-language]").forEach((link) => {
  link.addEventListener("click", () => {
    rememberLanguage(link.dataset.language);
  });
});

document.addEventListener("click", (event) => {
  if (languagePicker?.open && !languagePicker.contains(event.target)) {
    languagePicker.open = false;
  }
});

document.addEventListener("keydown", (event) => {
  if (event.key !== "Escape" || !languagePicker?.open) return;
  languagePicker.open = false;
  languagePicker.querySelector("summary")?.focus();
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
  button.setAttribute("aria-live", "polite");
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

const setupWizard = document.querySelector("[data-setup-wizard]");

if (setupWizard) {
  const stepNames = ["Your device", "Your AI app", "Private file", "Copy setup"];
  const steps = Array.from(setupWizard.querySelectorAll("[data-wizard-step]"));
  const progressButtons = Array.from(
    document.querySelectorAll("[data-go-step]"),
  );
  const progress = document.querySelector("[data-wizard-progress]");
  const progressFill = document.querySelector("[data-progress-fill]");
  const progressLabel = document.querySelector("[data-progress-label]");
  const status = setupWizard.querySelector("[data-wizard-status]");
  const pathInput = setupWizard.querySelector("[data-env-path]");
  let activeStep = 1;
  let highestStep = 1;
  let suggestedPath = "";

  const deviceLabels = {
    macos: "macOS",
    linux: "Linux",
    windows: "Windows",
  };
  const clientLabels = {
    codex: "Codex",
    claude: "Claude Desktop",
    vscode: "VS Code",
  };
  const pathSuggestions = {
    macos: "/Users/your-name/.config/cookidoo-mcp/cookidoo.env",
    linux: "/home/your-name/.config/cookidoo-mcp/cookidoo.env",
    windows: "C:/Users/your-name/.config/cookidoo-mcp/cookidoo.env",
  };

  function selectedValue(name) {
    return setupWizard.querySelector(`input[name="${name}"]:checked`)?.value;
  }

  function setError(name, message) {
    const error = setupWizard.querySelector(`[data-error-for="${name}"]`);
    if (error) error.textContent = message;
  }

  function shellQuote(value) {
    return `'${value.replaceAll("'", `'\"'\"'`)}'`;
  }

  function powershellQuote(value) {
    return `'${value.replaceAll("'", "''")}'`;
  }

  function commandPath(value, device) {
    return device === "windows"
      ? powershellQuote(value)
      : shellQuote(value);
  }

  function validatePath() {
    const device = selectedValue("device");
    const value = pathInput?.value.trim() ?? "";
    let message = "";

    if (!value) {
      message = "Enter the absolute path where the private file should live.";
    } else if (device === "windows" && !/^[a-zA-Z]:[\\/]/.test(value)) {
      message = "Use a complete Windows path, for example C:/Users/name/cookidoo.env.";
    } else if (device !== "windows" && !value.startsWith("/")) {
      message = "Use a complete path beginning with /, not ~ or a relative folder.";
    }

    setError("env-path", message);
    pathInput?.setAttribute("aria-invalid", String(Boolean(message)));
    return !message;
  }

  function validateStep(step) {
    if (step === 1 && !selectedValue("device")) {
      setError("device", "Choose the computer you are using.");
      setupWizard.querySelector('input[name="device"]')?.focus();
      return false;
    }

    if (step === 2) {
      const client = selectedValue("client");
      if (!client) {
        setError("client", "Choose the AI app you want to connect.");
        setupWizard.querySelector('input[name="client"]')?.focus();
        return false;
      }
      if (selectedValue("device") === "linux" && client === "claude") {
        setError(
          "client",
          "Claude Desktop’s official local-server guide supports macOS and Windows. Choose Codex or VS Code for Linux.",
        );
        setupWizard.querySelector('input[name="client"]:checked')?.focus();
        return false;
      }
    }

    if (step === 3 && !validatePath()) {
      pathInput?.focus();
      return false;
    }
    return true;
  }

  function buildResult() {
    const device = selectedValue("device");
    const client = selectedValue("client");
    const envPath = pathInput?.value.trim() ?? "";
    if (!device || !client || !envPath) return;

    const installCommand = setupWizard.querySelector("[data-install-command]");
    const fileCommand = setupWizard.querySelector("[data-file-command]");
    const clientTitle = setupWizard.querySelector("[data-client-config-title]");
    const clientInstruction = setupWizard.querySelector(
      "[data-client-instruction]",
    );
    const clientConfig = setupWizard.querySelector("[data-client-config]");
    const clientSource = setupWizard.querySelector("[data-client-source]");
    const verifyInstruction = setupWizard.querySelector(
      "[data-verify-instruction]",
    );
    const verifyCommand = setupWizard.querySelector("[data-verify-command]");
    const verifyShell = setupWizard.querySelector("[data-verify-shell]");
    const resultSummary = setupWizard.querySelector("[data-result-summary]");
    const platformNote = setupWizard.querySelector("[data-platform-note]");

    if (resultSummary) {
      resultSummary.textContent = `${clientLabels[client]} on ${deviceLabels[device]}, using ${envPath}`;
    }
    if (installCommand) {
      installCommand.textContent =
        device === "windows"
          ? 'powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"'
          : "curl -LsSf https://astral.sh/uv/install.sh | sh";
    }
    if (fileCommand) {
      fileCommand.textContent =
        device === "windows"
          ? `$envFile = ${powershellQuote(envPath)}
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $envFile) | Out-Null
if (-not (Test-Path $envFile)) { New-Item -ItemType File -Path $envFile | Out-Null }
notepad $envFile`
          : `env_file=${shellQuote(envPath)}
mkdir -p "$(dirname "$env_file")"
touch "$env_file"
chmod 600 "$env_file"
\${EDITOR:-nano} "$env_file"`;
    }

    const stdioConfig = {
      command: "uvx",
      args: ["cookidoo-mcp", "--env-file", envPath],
    };
    if (clientTitle) clientTitle.textContent = `Connect ${clientLabels[client]}`;
    if (verifyShell) verifyShell.hidden = client !== "codex";

    if (client === "codex") {
      if (clientInstruction) {
        clientInstruction.textContent =
          "Run this once in a terminal. Codex app, CLI, and IDE extension share MCP configuration on the same host.";
      }
      if (clientConfig) {
        clientConfig.textContent = `codex mcp add cookidoo -- uvx cookidoo-mcp --env-file ${commandPath(envPath, device)}`;
      }
      if (clientSource) {
        clientSource.textContent =
          "You can also use Settings → MCP servers → Add server, choose STDIO, then enter the same command and arguments.";
      }
      if (verifyInstruction) {
        verifyInstruction.textContent =
          "Restart the app or IDE extension after changing setup. In a terminal, list configured servers:";
      }
      if (verifyCommand) verifyCommand.textContent = "codex mcp list";
    } else if (client === "claude") {
      const configLocation =
        device === "windows"
          ? "%APPDATA%\\Claude\\claude_desktop_config.json"
          : "~/Library/Application Support/Claude/claude_desktop_config.json";
      if (clientInstruction) {
        clientInstruction.textContent = `Open Claude Desktop → Settings → Developer → Edit Config. Add or merge this server in ${configLocation}:`;
      }
      if (clientConfig) {
        clientConfig.textContent = JSON.stringify(
          { mcpServers: { cookidoo: stdioConfig } },
          null,
          2,
        );
      }
      if (clientSource) {
        clientSource.textContent =
          "Keep any existing mcpServers entries when merging the generated block.";
      }
      if (verifyInstruction) {
        verifyInstruction.textContent =
          "Save the file, fully quit Claude Desktop, reopen it, and look for the MCP server indicator beside the conversation input.";
      }
    } else {
      if (clientInstruction) {
        clientInstruction.textContent =
          "Run MCP: Open User Configuration from the VS Code Command Palette, then add or merge this server:";
      }
      if (clientConfig) {
        clientConfig.textContent = JSON.stringify(
          {
            servers: {
              cookidoo: { type: "stdio", ...stdioConfig },
            },
          },
          null,
          2,
        );
      }
      if (clientSource) {
        clientSource.textContent =
          "Use remote user configuration instead if the server should run inside WSL, SSH, or a development container.";
      }
      if (verifyInstruction) {
        verifyInstruction.textContent =
          "Run MCP: List Servers, select cookidoo, and start it. If it reports an error, choose Show Output for the startup log.";
      }
    }

    if (platformNote) {
      if (device === "windows") {
        platformNote.innerHTML =
          "<strong>Windows verification</strong><p>Package installation, the command launcher, and private-file loading run on a real <code>windows-latest</code> CI machine. Client UI formats follow current primary documentation and may vary slightly by app version.</p>";
      } else {
        platformNote.innerHTML =
          "<strong>One safe final check</strong><p>Ask the assistant to connect to Cookidoo before requesting any recipe or planning change. Keep write approvals enabled until you are comfortable with the tools.</p>";
      }
    }
  }

  function showStep(step, announce = true) {
    activeStep = step;
    highestStep = Math.max(highestStep, step);
    steps.forEach((element) => {
      element.hidden = Number(element.dataset.wizardStep) !== step;
    });

    progressButtons.forEach((button, index) => {
      const buttonStep = index + 1;
      button.disabled = buttonStep > highestStep;
      button.toggleAttribute("aria-current", buttonStep === step);
      button.closest("li")?.classList.toggle("is-complete", buttonStep < step);
    });

    const percent = ((step - 1) / (steps.length - 1)) * 100;
    if (progressFill) progressFill.style.width = `${percent}%`;
    if (progressLabel) progressLabel.textContent = `Step ${step} of ${steps.length}`;
    if (progress) {
      progress.setAttribute("aria-valuenow", String(step));
      progress.setAttribute(
        "aria-valuetext",
        `Step ${step} of ${steps.length}: ${stepNames[step - 1]}`,
      );
    }
    if (announce && status) {
      status.textContent = `Now on step ${step}: ${stepNames[step - 1]}.`;
    }
    steps[step - 1]?.querySelector(".wizard-heading")?.focus();
  }

  setupWizard.querySelectorAll('input[name="device"]').forEach((input) => {
    input.addEventListener("change", () => {
      setError("device", "");
      const nextSuggestion = pathSuggestions[input.value];
      if (pathInput && (!pathInput.value || pathInput.value === suggestedPath)) {
        pathInput.value = nextSuggestion;
      }
      suggestedPath = nextSuggestion;
    });
  });

  setupWizard.querySelectorAll('input[name="client"]').forEach((input) => {
    input.addEventListener("change", () => setError("client", ""));
  });
  pathInput?.addEventListener("blur", validatePath);
  pathInput?.addEventListener("input", () => {
    if (pathInput.getAttribute("aria-invalid") === "true") validatePath();
  });

  setupWizard.querySelectorAll("[data-next-step]").forEach((button) => {
    button.addEventListener("click", () => {
      if (!validateStep(activeStep)) return;
      if (activeStep === 3) buildResult();
      showStep(Math.min(steps.length, activeStep + 1));
    });
  });
  setupWizard.querySelectorAll("[data-previous-step]").forEach((button) => {
    button.addEventListener("click", () => showStep(Math.max(1, activeStep - 1)));
  });
  progressButtons.forEach((button) => {
    button.addEventListener("click", () => {
      const target = Number(button.dataset.goStep);
      if (target <= highestStep) showStep(target);
    });
  });

  showStep(1, false);
}

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
