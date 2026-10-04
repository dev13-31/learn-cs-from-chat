# learn-cs-from-chat 🎓

> **Note**: This project is an adapted and enhanced version of [pstack's `show-me-your-work` skill](https://github.com/cursor/plugins/tree/main/pstack/skills/show-me-your-work).

---

## Overview

**`learn-cs-from-chat`** transforms autonomous AI agent decision logs into an interactive computer science masterclass. Designed with the persona of a **Senior CS Professor mentoring a physics / materials science undergraduate**, it bridges computational tools with scientific thinking, explaining *why* software engineering choices are made using clear physical and mathematical intuition.

---

## 🌟 Key Features

- **4-Column Causal Decision Chain**: Replaces noisy logs with a continuous causal thread:
  1. `what the agent did`
  2. `why decided to do it`
  3. `what happened after doing it`
  4. `what decision taken next and why`
- **Rich Interactive HTML Dashboard**: Auto-generates a responsive dark/light notebook dashboard featuring interactive Mermaid.js progression diagrams and searchable topic tags (`#Python`, `#Bash`, `#Git`, `#LaTeX`, `#ML/AI`, `#Data/Math`).
- **In-Page Jargon Buster Tooltips**: Hover over software engineering and numerical methods (e.g. *Savitzky-Golay*, *NumPy vectorization*, *FWHM*, *Git branching*) to reveal instant definitions and physics/math analogies.
- **Core Function Syntax & Argument Explanations**: Under *"How do I run this myself?"*, isolates the 2–4 most critical operations with concise argument comments, conceptual ASCII data flowcharts, and 1-click copyable scripts.
- **Terminal & Obsidian Markdown Guide**: Produces an audit-proof, GitHub-flavored Markdown document with native `<details><summary>` expandable drawers.
- **Full-Context Web AI with Temporary Chat**: One-click **`[🌐 Ask on Web AI ↗]`** links open ChatGPT pre-loaded with full session context, agent observations, and `temporary-chat=true` enabled to prevent history clutter.
- **Safe & Offline-First Viewing**: 100% self-contained static HTML (`file:///`) with an optional local viewer bound strictly to `127.0.0.1` (zero network exposure).

---

## 📁 Repository Structure

```
learn-cs-from-chat/
├── SKILL.md                                 # Skill instructions & Senior CS Mentor prompt
├── README.md                                # Project documentation
├── references/
│   └── decision-log-template.tsv           # Canonical 4-column TSV header
└── scripts/
    ├── log_decision.py                     # CLI logger & auto-compiler
    ├── render_cs_mentor.py                 # Standalone TSV -> HTML + MD compiler
    ├── serve_decisions.py                  # Strict 127.0.0.1 localhost viewer
    ├── log.ps1                             # Windows PowerShell wrapper
    └── log.sh                              # Unix / macOS Bash wrapper
```

---

## 🚀 Quick Start

### 1. Log a Decision Step
Use the CLI logger to record an action; it automatically creates the directory, updates the TSV, and compiles the HTML & Markdown guides:

```bash
python scripts/log_decision.py \
  --dir "D:/gemini/CS decisions/my-session" \
  --slug "my-session" \
  --did "Parsed raw XRD CSV data and removed background slope with Savitzky-Golay filter" \
  --why "Raw spectrometer data has background fluorescence noise that distorts peak fitting" \
  --happened "Baseline shifted to zero; peak SNR improved from 4.2 to 18.5" \
  --next "Fit Gaussian-Lorentzian peaks to determine full-width half-maximum (FWHM)"
```

Or via PowerShell:
```powershell
.\scripts\log.ps1 -dir "D:/gemini/CS decisions/my-session" -slug "my-session" -did "..." -why "..." -happened "..." -next "..."
```

### 2. View Outputs
- **Direct File**: Double-click `D:/gemini/CS decisions/my-session/my-session.html` in your browser.
- **Local Server**: Run `python scripts/serve_decisions.py` to browse all recorded sessions at `http://127.0.0.1:8080/`.

---

## License

MIT License. See [LICENSE](LICENSE) for details.
