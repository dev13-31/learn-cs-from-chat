#!/usr/bin/env python3
"""
render_cs_mentor.py - Senior Computer Scientist Mentor Dashboard & Guide Generator
Converts a 4-column decision log TSV into:
  1. A rich, interactive, self-contained HTML dashboard with:
     - Mermaid.js state flowchart
     - Solution #1: In-Page Jargon Buster with Physics & Math Analogies
     - Option 3: Instant 1-Click Accordion answers (Why, Step-by-step, Code snippet)
       plus optional 1-click external Web AI hyperlink!
     - Real-time search and topic filter pills
  2. A clean, terminal- and Obsidian-friendly Markdown study guide with
     native <details><summary> collapsible mentor answers and code blocks.
  3. Central D:/gemini/CS decisions/ master catalog (INDEX.md and index.html).
Standard library only: zero external pip dependencies.
"""

import os
import sys
import csv
import html
import json
import re
import argparse
import urllib.parse
from pathlib import Path
from datetime import datetime

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Solution #1: Physics & Math Analogies for Computing Terms
PHYSICS_ANALOGIES_GLOSSARY = {
    "numpy": {
        "title": "NumPy & Vectorization",
        "def": "C-compiled contiguous array operations that eliminate Python scalar loops.",
        "analogy": "Plane-wave illumination of a crystal: an operator acts on the entire state vector simultaneously, rather than raster-scanning atom by atom."
    },
    "scipy": {
        "title": "SciPy (Scientific Algorithms)",
        "def": "Numerical optimization, peak-finding, ODE solvers, and signal processing.",
        "analogy": "A precision laboratory spectrometer bench implemented in software with calibrated mathematical instruments."
    },
    "savitzky-golay": {
        "title": "Savitzky-Golay Filter",
        "def": "Local polynomial convolution that smooths noisy data without flattening peaks.",
        "analogy": "A moving least-squares window that filters high-frequency thermal vibration noise while strictly conserving peak area, width, and height."
    },
    "pseudo-voigt": {
        "title": "Pseudo-Voigt Profile",
        "def": "Linear combination of Gaussian and Lorentzian peak functions.",
        "analogy": "Convolving instrumental resolution (Gaussian) with intrinsic lifetime and finite crystallite domain broadening (Lorentzian)."
    },
    "fwhm": {
        "title": "FWHM (Full Width at Half Maximum)",
        "def": "The width of a spectral/diffraction peak at 50% of its maximum intensity.",
        "analogy": "Heisenberg uncertainty principle in reciprocal space: peak width Δk is inversely proportional to real-space crystal domain size L."
    },
    "scherrer": {
        "title": "Scherrer Equation",
        "def": "D = K*λ / (β * cos(θ)), relating peak broadening β to crystallite size D.",
        "analogy": "Finite-size diffraction interference: with fewer lattice planes N, destructive interference outside the exact Bragg angle is incomplete."
    },
    "git": {
        "title": "Git & Version Control",
        "def": "Cryptographically hashed directed acyclic graph (DAG) of immutable project states.",
        "analogy": "Quantum state-space snapshots: discrete transitions between eigenstates with zero possibility of undefined intermediate states."
    },
    "branch": {
        "title": "Git Branch",
        "def": "An isolated pointer to a commit lineage for testing changes safely.",
        "analogy": "Exploring a parallel thermodynamic path or virtual state trajectory before collapsing it back into the ground state."
    },
    "baseline": {
        "title": "Baseline Subtraction",
        "def": "Removing underlying continuum slope or curvature from spectral data.",
        "analogy": "Subtracting incoherent background scattering (Compton/Bremsstrahlung) to isolate coherent Bragg diffraction peaks."
    },
    "idempotent": {
        "title": "Idempotent Operation",
        "def": "An operation where f(f(x)) = f(x); re-running it changes nothing.",
        "analogy": "A quantum projection operator P² = P, or a polarizing filter: passing light through a second identical polarizer leaves it unchanged."
    },
    "convergence": {
        "title": "Optimization Convergence",
        "def": "Algorithm reaches a stable solution where gradient magnitude is below tolerance ε.",
        "analogy": "A physical system relaxing to its global thermodynamic free energy minimum (∇V = 0)."
    },
    "latex": {
        "title": "LaTeX Math Typesetting",
        "def": "Semantic typesetting system separating content logic from layout rendering.",
        "analogy": "Formal tensor notation: rigorous mathematical truth separated from arbitrary graphical depiction."
    },
    "nan": {
        "title": "NaN (Not a Number)",
        "def": "IEEE floating-point representation for undefined or missing values (e.g. 0/0).",
        "analogy": "A detector blind spot or unphysical singularity that must be masked before integrating."
    },
    "pipe": {
        "title": "Unix / Bash Pipeline (|)",
        "def": "Streaming stdout of one program directly into stdin of the next in memory.",
        "analogy": "Laminar fluid flow through a sequence of selective membranes without filling intermediate storage tanks."
    },
    "agentic": {
        "title": "Agentic Reasoning Loop",
        "def": "Autonomous cycle of perception, tool execution, and reflection.",
        "analogy": "A PID closed-loop feedback controller: sensor telemetry is compared to setpoint to produce a correcting actuator pulse."
    }
}

TECH_KEYWORDS = {
    "Python": [r"\bpython\b", r"\.py\b", r"\bdef\b", r"\bimport\b", r"\bnumpy\b", r"\bpandas\b", r"\bmatplotlib\b", r"\bscipy\b", r"\bvirtualenv\b", r"\bvenv\b", r"\bpip\b"],
    "Bash/Linux": [r"\bbash\b", r"\bsh\b", r"\blinux\b", r"\bcat\b", r"\bgrep\b", r"\bawk\b", r"\bsed\b", r"\bcurl\b", r"\bpowershell\b", r"\bpipe\b", r"\bstdout\b", r"\bstdin\b", r"\bchmod\b"],
    "Git": [r"\bgit\b", r"\bcommit\b", r"\bbranch\b", r"\bworktree\b", r"\bmerge\b", r"\brevert\b", r"\bdiff\b", r"\bcheckout\b", r"\bstash\b", r"\bpr\b"],
    "ML/AI": [r"\bml\b", r"\bai\b", r"\bmodel\b", r"\btraining\b", r"\bloss\b", r"\bweights\b", r"\binference\b", r"\bgradient\b", r"\bdataset\b", r"\bcluster\b", r"\bregression\b"],
    "Agentic AI": [r"\bagent\b", r"\bprompt\b", r"\bhallucinat\b", r"\btool\b", r"\breflection\b", r"\breasoning\b", r"\bloop\b", r"\bsubagent\b", r"\bcontext window\b"],
    "LaTeX": [r"\blatex\b", r"\btex\b", r"\bequation\b", r"\bmath\b", r"\bbibtex\b", r"\bcompile\b"],
    "Data/Math": [r"\bxrd\b", r"\bfft\b", r"\bmatrix\b", r"\beigen\b", r"\bvector\b", r"\bfitting\b", r"\bpeak\b", r"\bnoise\b", r"\bconvergence\b"]
}

def detect_tags(text: str) -> list[str]:
    tags = []
    text_lower = text.lower()
    for tag, patterns in TECH_KEYWORDS.items():
        if any(re.search(pat, text_lower) for pat in patterns):
            tags.append(tag)
    return tags if tags else ["CS Concept"]

def clean_cell(text: str) -> str:
    """Strip leading quotes used to prevent spreadsheet formula injection."""
    text = text.strip()
    if text.startswith("'") and len(text) > 1 and text[1] in ("=", "+", "-", "@"):
        return text[1:]
    return text

def parse_tsv(tsv_path: Path) -> list[dict]:
    rows = []
    if not tsv_path.exists():
        return rows
    with open(tsv_path, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.reader(f, delimiter="\t")
        header = next(reader, None)
        if not header:
            return rows
        for row in reader:
            if not row or not any(row):
                continue
            while len(row) < 4:
                row.append("")
            rows.append({
                "did": clean_cell(row[0]),
                "why": clean_cell(row[1]),
                "happened": clean_cell(row[2]),
                "next": clean_cell(row[3]),
                "tags": detect_tags(f"{row[0]} {row[1]} {row[2]} {row[3]}")
            })
    return rows

def annotate_jargon_html(text: str) -> str:
    """Solution #1: Wrap recognized technical terms with interactive hover tooltip elements."""
    escaped_text = html.escape(text)
    terms_sorted = sorted(PHYSICS_ANALOGIES_GLOSSARY.keys(), key=len, reverse=True)
    
    for term in terms_sorted:
        info = PHYSICS_ANALOGIES_GLOSSARY[term]
        pattern = re.compile(rf"\b({re.escape(term)})\b", re.IGNORECASE)
        
        def repl(match):
            matched_str = match.group(1)
            t_title = html.escape(info["title"])
            t_def = html.escape(info["def"])
            t_analogy = html.escape(info["analogy"])
            return (
                f'<span class="jargon-term">'
                f'<span class="jargon-label">{matched_str}</span>'
                f'<span class="tooltip-box">'
                f'<span class="tt-header">⚛️ {t_title}</span>'
                f'<span class="tt-def">{t_def}</span>'
                f'<span class="tt-analogy"><strong>Physics Analogy:</strong> {t_analogy}</span>'
                f'</span>'
                f'</span>'
            )
        
        escaped_text = pattern.sub(repl, escaped_text)
        
    return escaped_text

def build_code_guide_md(core_ops: list[dict], conceptual_flow: str, full_code: str) -> str:
    """Renders the Markdown guide for 'How do I run this myself?' with the core operations,
    concise parameter comments, conceptual flowchart, and complete runnable script."""
    n = len(core_ops)
    num_map = {1: "this operation", 2: "these two operations", 3: "these three operations", 4: "these four operations", 5: "these five operations"}
    count_str = num_map.get(n, f"these {n} operations")
    
    lines = [
        "#### 💡 The Most Important Lines",
        "",
        f"> *You do not need to memorize the entire program. Understand {count_str} first.*",
        ""
    ]
    for op in core_ops:
        lines.append(f"##### {op['title']}")
        lines.append(f"```{op.get('lang', 'python')}")
        lines.append(op['code'])
        lines.append("```")
        lines.append("")
        
    if conceptual_flow:
        lines.append("**Conceptually:**")
        lines.append("")
        lines.append("```text")
        lines.append(conceptual_flow)
        lines.append("```")
        lines.append("")
        
    lines.append("---")
    lines.append("")
    lines.append("##### 💻 Complete Self-Contained Script")
    lines.append("")
    lines.append(f"```python\n{full_code}\n```")
    return "\n".join(lines)

def build_code_guide_html(core_ops: list[dict], conceptual_flow: str, full_code: str, code_block_id: str) -> str:
    """Renders the HTML guide for 'How do I run this myself?' with syntax cards,
    concise parameter comments, conceptual flowchart, and complete copyable script."""
    n = len(core_ops)
    num_map = {1: "this operation", 2: "these two operations", 3: "these three operations", 4: "these four operations", 5: "these five operations"}
    count_str = num_map.get(n, f"these {n} operations")
    
    ops_html = []
    for op in core_ops:
        op_title_esc = html.escape(op['title'])
        op_code_esc = html.escape(op['code'])
        ops_html.append(f"""
        <div class="op-card">
          <div class="op-title">{op_title_esc}</div>
          <div class="code-container mini-code">
            <pre><code>{op_code_esc}</code></pre>
          </div>
        </div>
        """)
    ops_joined = "\n".join(ops_html)
    
    flow_html = ""
    if conceptual_flow:
        flow_esc = html.escape(conceptual_flow)
        flow_html = f"""
        <div class="concept-flow-card">
          <div class="flow-title">Conceptually:</div>
          <pre class="flow-pre">{flow_esc}</pre>
        </div>
        """
        
    code_escaped = html.escape(full_code)
    full_script_html = f"""
    <div class="full-script-section">
      <div class="full-script-header">
        <span>💻 Complete Self-Contained Script</span>
        <button class="copy-code-btn" onclick="copyCode(this, '{code_block_id}')">📋 Copy Code</button>
      </div>
      <div class="code-container">
        <pre><code id="{code_block_id}">{code_escaped}</code></pre>
      </div>
    </div>
    """
    
    return f"""
    <div class="core-ops-intro">
      <div class="ops-badge">💡 The Most Important Lines</div>
      <p class="ops-subtitle">You do not need to memorize the entire program. Understand {count_str} first.</p>
    </div>
    <div class="core-operations">
      {ops_joined}
    </div>
    {flow_html}
    {full_script_html}
    """

def get_mentor_qna(idx: int, row: dict, session_title: str = "Computational Workflow") -> dict:
    """Option 3: Generates pre-rendered Senior CS Mentor answers for the 3 simple questions,
    including detailed rationale, step-by-step breakdown, and syntax/argument breakdown with flowcharts."""
    text_corpus = (row["did"] + " " + row["why"]).lower()
    did_short = row["did"][:60] + "..." if len(row["did"]) > 60 else row["did"]

    q_why = f"In Step {idx} ('{did_short}'), why did you choose this specific approach instead of an alternative?"
    q_steps = f"Can you explain what Step {idx} ('{did_short}') actually does step-by-step in simple terms?"
    q_code = f"Can you show me a simple, working code example so I can try Step {idx} on my own?"

    # Full context bundle for external AI assistance
    context_header = (
        f"I am an undergraduate science student (physics/materials background) learning scientific computing and programming.\n\n"
        f"Session: {session_title}\n"
        f"Step {idx} Context:\n"
        f"- What was done: {row['did']}\n"
        f"- Why it was done: {row['why']}\n"
        f"- What happened / observation: {row['happened']}\n"
        f"- Next step: {row['next']}\n\n"
    )

    full_prompt_why = (
        f"{context_header}"
        f"Question:\n"
        f"Why was this specific approach chosen for Step {idx} instead of common alternatives? "
        f"What are the main engineering/scientific trade-offs, advantages, and system considerations?\n\n"
        f"Please explain clearly and pedagogically as a Senior Computer Science Mentor."
    )

    full_prompt_steps = (
        f"{context_header}"
        f"Question:\n"
        f"Can you explain step-by-step what actually happens under the hood in Step {idx} in clear, beginner-friendly terms?\n\n"
        f"Please explain clearly and pedagogically as a Senior Computer Science Mentor."
    )

    full_prompt_code = (
        f"{context_header}"
        f"Question:\n"
        f"For Step {idx}, can you provide:\n"
        f"1. 'The most important lines': highlight the core function syntax with concise comments explaining what each argument means,\n"
        f"2. A simple conceptual ASCII flow chart (e.g. Input -> Core Operation -> Output), and\n"
        f"3. A complete, runnable Python/Bash script so I can run and test this myself?\n\n"
        f"Please explain clearly and pedagogically as a Senior Computer Science Mentor."
    )

    web_url_why = f"https://chatgpt.com/?q={urllib.parse.quote(full_prompt_why)}&temporary-chat=true"
    web_url_steps = f"https://chatgpt.com/?q={urllib.parse.quote(full_prompt_steps)}&temporary-chat=true"
    web_url_code = f"https://chatgpt.com/?q={urllib.parse.quote(full_prompt_code)}&temporary-chat=true"

    # Contextual custom explanations based on domain keywords
    if any(k in text_corpus for k in ["xrd", "csv", "parse", "numpy", "read"]):
        ans_why = (
            "Standard libraries like <code>pandas.read_csv()</code> assume uniform tabular data starting from row 1, "
            "and will throw parser errors on instrument files containing metadata headers (detector settings, scan speeds, voltages). "
            "Parsing directly into NumPy with header skipping loads raw numerical values into contiguous C-memory, running orders of magnitude faster without parser crashes."
        )
        ans_steps = (
            "1. <strong>Header inspection</strong>: Scan initial lines to identify where numeric data starts.<br>"
            "2. <strong>Column extraction</strong>: Read the 2-theta angles (x-axis) and intensity counts (y-axis).<br>"
            "3. <strong>Array allocation</strong>: Convert values into contiguous 1D 64-bit float NumPy arrays.<br>"
            "4. <strong>Sanity check</strong>: Verify zero NaN (missing) values before downstream mathematical operations."
        )
        core_ops = [
            {
                "title": "A. Load numerical data bypassing instrument metadata",
                "code": (
                    "data = np.genfromtxt(\n"
                    "    'xrd_sample.csv',  # Filepath to raw spectrometer CSV export\n"
                    "    delimiter=',',     # Separator character between numerical columns\n"
                    "    skip_header=15     # Number of metadata header lines to skip at file start\n"
                    ")"
                ),
                "lang": "python"
            },
            {
                "title": "B. Unpack coordinates into contiguous 1D float arrays",
                "code": (
                    "two_theta = data[:, 0]  # Column index 0: Diffraction angle 2θ in degrees\n"
                    "intensity = data[:, 1]  # Column index 1: Measured detector photon counts"
                ),
                "lang": "python"
            }
        ]
        conceptual_flow = (
            "raw spectrometer CSV (with 15 metadata header rows)\n"
            "                 ↓\n"
            "      np.genfromtxt(skip_header=15)\n"
            "                 ↓\n"
            "contiguous 1D NumPy arrays (two_theta, intensity)"
        )
        full_code = (
            "import numpy as np\n\n"
            "# 1. Skip instrument header metadata lines and load numeric columns directly\n"
            "data = np.genfromtxt('xrd_sample.csv', delimiter=',', skip_header=15)\n"
            "two_theta = data[:, 0]\n"
            "intensity = data[:, 1]\n\n"
            "print(f'Loaded {len(two_theta)} points from {two_theta[0]:.2f}° to {two_theta[-1]:.2f}°')\n"
            "assert not np.isnan(intensity).any(), 'Detector array contains missing NaN values!'"
        )

    elif any(k in text_corpus for k in ["baseline", "polynomial", "savitzky", "smooth"]):
        ans_why = (
            "Raw spectrometer scans suffer from background fluorescence and amorphous scattering that lift the baseline. "
            "A naive moving average broadens and flattens narrow Bragg peaks, corrupting crystallite size calculations. "
            "Fitting a low-degree polynomial baseline and applying Savitzky-Golay smoothing preserves the true peak height, width, and area while eliminating high-frequency detector noise."
        )
        ans_steps = (
            "1. <strong>Anchor selection</strong>: Locate baseline points in regions where no Bragg peaks exist.<br>"
            "2. <strong>Polynomial fitting</strong>: Fit a low-order polynomial to model the background continuum.<br>"
            "3. <strong>Background subtraction</strong>: Subtract the fitted baseline curve from raw intensities.<br>"
            "4. <strong>Savitzky-Golay convolution</strong>: Apply a local least-squares polynomial to smooth high-frequency ripple without flattening peaks."
        )
        core_ops = [
            {
                "title": "A. Fit and subtract polynomial baseline continuum",
                "code": (
                    "# Model background curvature with low-degree polynomial\n"
                    "poly_coeffs = np.polyfit(\n"
                    "    two_theta,     # Independent x coordinates (diffraction angle 2θ)\n"
                    "    intensity,     # Dependent y values (raw measured photon counts)\n"
                    "    deg=3          # Polynomial degree (captures gentle background curvature)\n"
                    ")\n"
                    "poly_bg = np.polyval(poly_coeffs, two_theta)\n"
                    "subtracted = np.maximum(intensity - poly_bg, 0)  # Clamp negative floor to 0"
                ),
                "lang": "python"
            },
            {
                "title": "B. Smooth experimental data with Savitzky-Golay filter",
                "code": (
                    "smoothed = savgol_filter(\n"
                    "    subtracted,        # Input signal array with baseline removed\n"
                    "    window_length=11,  # Moving window size in data points (must be odd integer)\n"
                    "    polyorder=3        # Degree of polynomial fitted inside each window\n"
                    ")"
                ),
                "lang": "python"
            }
        ]
        conceptual_flow = (
            "noisy XRD\n"
            "   ↓\n"
            "np.polyfit / np.polyval (deg=3 baseline subtraction)\n"
            "   ↓\n"
            "baseline-corrected XRD\n"
            "   ↓\n"
            "Savitzky-Golay filter (window=11, polyorder=3)\n"
            "   ↓\n"
            "smooth XRD with preserved Bragg peak shape & area"
        )
        full_code = (
            "import numpy as np\n"
            "from scipy.signal import savgol_filter\n\n"
            "# 1. Model background polynomial and subtract from raw signal\n"
            "poly_coeffs = np.polyfit(two_theta, intensity, deg=3)\n"
            "poly_bg = np.polyval(poly_coeffs, two_theta)\n"
            "subtracted = np.maximum(intensity - poly_bg, 0)\n\n"
            "# 2. Smooth high-frequency noise while strictly preserving peak shape and area\n"
            "smoothed = savgol_filter(subtracted, window_length=11, polyorder=3)\n"
            "print('Baseline leveled to zero and smoothed successfully.')"
        )

    elif any(k in text_corpus for k in ["git", "branch", "commit"]):
        ans_why = (
            "In computational research, reproducibility is paramount. Working directly on the <code>main</code> branch risks leaving your working codebase broken if an experimental script fails. "
            "Creating an isolated feature branch preserves working code and allows you to test new filters and run unit tests safely before merging."
        )
        ans_steps = (
            "1. <strong>Branch creation</strong>: Create and switch to a feature branch: <code>git checkout -b feature/xrd-baseline</code>.<br>"
            "2. <strong>Verification</strong>: Run automated unit tests to confirm the data pipeline produces valid output.<br>"
            "3. <strong>Staging</strong>: Stage the modified files: <code>git add scripts/xrd_baseline.py</code>.<br>"
            "4. <strong>Atomic commit</strong>: Commit with a descriptive message explaining the transformation and result."
        )
        core_ops = [
            {
                "title": "A. Create isolated workspace feature branch",
                "code": (
                    "git checkout -b feature/xrd-baseline\n"
                    "    # -b: creates new branch 'feature/xrd-baseline' and switches to it\n"
                    "    # Isolates experimental code from the production 'main' branch"
                ),
                "lang": "bash"
            },
            {
                "title": "B. Stage verified scripts into index",
                "code": (
                    "git add scripts/clean_xrd.py tests/test_baseline.py\n"
                    "    # Selects exact modified files to be included in the snapshot"
                ),
                "lang": "bash"
            },
            {
                "title": "C. Record permanent state checkpoint",
                "code": (
                    "git commit -m 'feat(xrd): implement polynomial baseline subtraction'\n"
                    "    # -m: audit message explaining the transformation for lab provenance"
                ),
                "lang": "bash"
            }
        ]
        conceptual_flow = (
            "working directory changes\n"
            "           ↓\n"
            "git checkout -b (branch isolation)\n"
            "           ↓\n"
            "git add (staging index)\n"
            "           ↓\n"
            "git commit (immutable state checkpoint)"
        )
        full_code = (
            "# Create isolated feature branch, verify pipeline, and commit\n"
            "git checkout -b feature/xrd-baseline\n"
            "pytest tests/test_baseline.py\n"
            "git add scripts/clean_xrd.py tests/test_baseline.py\n"
            "git commit -m 'feat(xrd): implement polynomial baseline subtraction with unit tests'"
        )

    elif any(k in text_corpus for k in ["pseudo-voigt", "scherrer", "crystallite", "fwhm", "peak"]):
        ans_why = (
            "Experimental diffraction peaks in real materials are a convolution of instrumental resolution (Gaussian) and finite domain size/microstrain (Lorentzian). "
            "A pure Gaussian underestimates the tails, while a pure Lorentzian overestimates broadening. Pseudo-Voigt combines both linearly. "
            "Once peak width (FWHM) is extracted, the Scherrer equation gives the volume-weighted mean crystallite size."
        )
        ans_steps = (
            "1. <strong>Peak detection</strong>: Identify approximate peak centers using <code>scipy.signal.find_peaks</code>.<br>"
            "2. <strong>Profile fitting</strong>: Fit Pseudo-Voigt profiles using non-linear least squares (<code>scipy.optimize.curve_fit</code>).<br>"
            "3. <strong>Width extraction</strong>: Extract FWHM (Full Width at Half Maximum) in radians and correct for instrumental broadening.<br>"
            "4. <strong>Scherrer calculation</strong>: Apply $D = \\frac{K\\lambda}{\\beta \\cos\\theta}$ to calculate crystallite diameter in nanometers."
        )
        core_ops = [
            {
                "title": "A. Detect Bragg peak positions",
                "code": (
                    "peaks, _ = find_peaks(\n"
                    "    smoothed,        # 1D array of smoothed intensity counts\n"
                    "    prominence=500,  # Minimum vertical prominence above surrounding baseline\n"
                    "    width=5          # Minimum width of peak in data points\n"
                    ")"
                ),
                "lang": "python"
            },
            {
                "title": "B. Compute crystallite size using Scherrer equation",
                "code": (
                    "# Scherrer formula: D = (K * λ) / (β * cos(θ))\n"
                    "d_crystallite_nm = (K * wavelength_nm) / (beta_rad * np.cos(theta_rad))\n"
                    "    # K = 0.94                Dimensionless shape factor (spherical crystallites)\n"
                    "    # wavelength_nm = 0.15406 Cu Kα X-ray source wavelength in nm\n"
                    "    # beta_rad                FWHM peak broadening in radians (instrument-corrected)\n"
                    "    # theta_rad               Bragg angle θ in radians (= 2θ / 2)"
                ),
                "lang": "python"
            }
        ]
        conceptual_flow = (
            "smoothed diffraction spectrum\n"
            "          ↓\n"
            "find_peaks & peak fitting (extract center 2θ and FWHM width β)\n"
            "          ↓\n"
            "Scherrer Equation: D = (K·λ) / (β·cos θ)\n"
            "          ↓\n"
            "volume-weighted mean crystallite size (nm)"
        )
        full_code = (
            "import numpy as np\n"
            "from scipy.signal import find_peaks\n\n"
            "def scherrer_equation(fwhm_deg, two_theta_deg, wavelength_nm=0.15406, K=0.94):\n"
            "    theta_rad = np.radians(two_theta_deg / 2.0)\n"
            "    beta_rad = np.radians(fwhm_deg)\n"
            "    return (K * wavelength_nm) / (beta_rad * np.cos(theta_rad))\n\n"
            "# Locate peak centers and calculate crystallite size\n"
            "peaks, _ = find_peaks(smoothed, prominence=500, width=5)\n"
            "peak_2theta = two_theta[peaks[0]]\n"
            "size_nm = scherrer_equation(fwhm_deg=0.35, two_theta_deg=peak_2theta)\n"
            "print(f'Peak at 2θ = {peak_2theta:.2f}° -> Mean Crystallite Size: {size_nm:.1f} nm')"
        )

    elif any(k in text_corpus for k in ["export", "vector", "svg", "figure", "dpi"]):
        ans_why = (
            "Raster formats (PNG, JPG) become pixelated and blurry when printed in scientific papers or magnified on high-resolution displays. "
            "Vector formats like SVG store mathematical curves, lines, and text fonts, guaranteeing infinitely sharp publication quality at any zoom level with compact file sizes."
        )
        ans_steps = (
            "1. <strong>Figure dimensions</strong>: Set standard journal column dimensions (e.g. 6x4 inches) and legible font sizes.<br>"
            "2. <strong>Overlay rendering</strong>: Plot raw experimental data points alongside fitted mathematical curves.<br>"
            "3. <strong>Labeling & units</strong>: Add explicit axis labels with proper units ($2\\theta$ in degrees, intensity in a.u.).<br>"
            "4. <strong>Vector export</strong>: Save directly to vector SVG and high-resolution 300-DPI raster."
        )
        core_ops = [
            {
                "title": "A. Initialize journal-dimension figure canvas",
                "code": (
                    "fig, ax = plt.subplots(\n"
                    "    figsize=(6, 4),  # Figure width and height in inches (journal standard)\n"
                    "    dpi=300          # Dots-per-inch resolution (meets 300+ publication criteria)\n"
                    ")"
                ),
                "lang": "python"
            },
            {
                "title": "B. Export to lossless vector format",
                "code": (
                    "fig.savefig(\n"
                    "    'xrd_publication_plot.svg',  # Destination filepath for vector output\n"
                    "    format='svg',                 # Scalable Vector Graphics (infinitely scalable lines)\n"
                    "    bbox_inches='tight'           # Automatically crop unnecessary whitespace borders\n"
                    ")"
                ),
                "lang": "python"
            }
        ]
        conceptual_flow = (
            "experimental counts + mathematical fit\n"
            "                 ↓\n"
            "matplotlib canvas (figsize=6x4, dpi=300)\n"
            "                 ↓\n"
            "fig.savefig(format='svg', bbox_inches='tight')\n"
            "                 ↓\n"
            "infinitely scalable publication vector figure"
        )
        full_code = (
            "import matplotlib.pyplot as plt\n\n"
            "fig, ax = plt.subplots(figsize=(6, 4), dpi=300)\n"
            "ax.plot(two_theta, intensity, 'k.', alpha=0.3, label='Raw Detector Counts')\n"
            "ax.plot(two_theta, smoothed, 'r-', lw=1.5, label='Fitted Spectrum')\n"
            "ax.set_xlabel(r'Diffraction Angle $2\\theta$ (°)')\n"
            "ax.set_ylabel('Intensity (Counts)')\n"
            "ax.legend(frameon=False)\n"
            "fig.savefig('xrd_publication_plot.svg', format='svg', bbox_inches='tight')\n"
            "print('Saved publication vector plot: xrd_publication_plot.svg')"
        )

    else:
        ans_why = f"This approach was selected to satisfy the operational goal: {row['why']}. Executing it directly produced the outcome: {row['happened']}."
        ans_steps = (
            f"1. <strong>Goal</strong>: Address requirement: {row['why']}.<br>"
            f"2. <strong>Execution</strong>: Execute operation: {row['did']}.<br>"
            f"3. <strong>Observation</strong>: Verify result: {row['happened']}.<br>"
            f"4. <strong>Next Step</strong>: Proceed to: {row['next']}."
        )
        did_short_clean = row["did"][:50]
        core_ops = [
            {
                "title": "A. Primary operational command",
                "code": (
                    f"# Action: {row['did']}\n"
                    f"# Rationale: {row['why']}"
                ),
                "lang": "python"
            }
        ]
        conceptual_flow = (
            f"Initial System State\n"
            f"          ↓\n"
            f"Execute: {did_short_clean}...\n"
            f"          ↓\n"
            f"Observed State: {row['happened'][:40]}..."
        )
        full_code = (
            f"# Demonstration snippet for step {idx}\n"
            f"print('Action:', {repr(row['did'])})\n"
            f"print('Goal:', {repr(row['why'])})\n"
            f"print('Observed:', {repr(row['happened'])})"
        )

    md_guide = build_code_guide_md(core_ops, conceptual_flow, full_code)

    return {
        "why": {
            "label": "❓ Why do it this way?",
            "title": "Why Choose This Approach?",
            "question": q_why,
            "answer": ans_why,
            "code": None,
            "web_url": web_url_why
        },
        "steps": {
            "label": "🔍 Explain step-by-step",
            "title": "Step-by-Step Breakdown",
            "question": q_steps,
            "answer": ans_steps,
            "code": None,
            "web_url": web_url_steps
        },
        "code": {
            "label": "💻 How do I run this myself?",
            "title": "Core Syntax & Runnable Code",
            "question": q_code,
            "answer": "Here is the syntax of the most important functions, conceptual flow, and complete script:",
            "core_ops": core_ops,
            "conceptual_flow": conceptual_flow,
            "full_code": full_code,
            "code": full_code,
            "md_guide": md_guide,
            "web_url": web_url_code
        }
    }

def generate_mermaid_diagram(rows: list[dict]) -> str:
    if not rows:
        return "graph TD;\n    Start[Start of Session] --> End[No decisions logged yet];"
    lines = ["graph TD", "    classDef stepNode fill:#1e293b,stroke:#38bdf8,stroke-width:2px,color:#f8fafc;", "    classDef obsNode fill:#0f172a,stroke:#34d399,stroke-width:1.5px,color:#f1f5f9;"]
    for i, r in enumerate(rows, 1):
        did_short = re.sub(r'["\']', '', (r["did"][:40] + "...") if len(r["did"]) > 40 else r["did"])
        happened_short = re.sub(r'["\']', '', (r["happened"][:40] + "...") if len(r["happened"]) > 40 else r["happened"])
        lines.append(f'    S{i}["Step {i}: {did_short}"]:::stepNode')
        lines.append(f'    O{i}["Obs {i}: {happened_short}"]:::obsNode')
        lines.append(f'    S{i} --> O{i}')
        if i < len(rows):
            lines.append(f'    O{i} -->|Strategic Next| S{i+1}')
    return "\n".join(lines)

def build_markdown(session_slug: str, session_title: str, rows: list[dict]) -> str:
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    mermaid = generate_mermaid_diagram(rows)
    
    md_lines = [
        f"# 🎓 CS Masterclass: {session_title}",
        f"",
        f"> **Audience**: Undergraduate Science Student (Physics/Materials/Math) Learning Computing  ",
        f"> **Session Instance**: `{session_slug}`  ",
        f"> **Last Updated**: `{now_str}`  ",
        f"> **Quick Links**: [📊 Interactive HTML Dashboard](./{session_slug}.html) | [📑 Raw TSV Log](./{session_slug}.tsv)",
        f"",
        f"---",
        f"",
        f"## 🗺️ Decision & Causal Progression Flow",
        f"",
        f"```mermaid",
        mermaid,
        f"```",
        f"",
        f"---",
        f"",
        f"## 📋 Canonical Decision Summary",
        f"",
        f"| # | What the Agent Did | Why Decided to Do It | What Happened After Doing It | Next Decision & Rationale | Key CS Topics |",
        f"|---|-------------------|----------------------|------------------------------|---------------------------|---------------|"
    ]

    for idx, r in enumerate(rows, 1):
        tags_str = ", ".join(f"`{t}`" for t in r["tags"])
        did_esc = r["did"].replace("|", "\\|")
        why_esc = r["why"].replace("|", "\\|")
        hap_esc = r["happened"].replace("|", "\\|")
        nxt_esc = r["next"].replace("|", "\\|")
        md_lines.append(f"| {idx} | {did_esc} | {why_esc} | {hap_esc} | {nxt_esc} | {tags_str} |")

    md_lines.extend([
        "",
        "---",
        "",
        "## 👨‍🏫 Senior Computer Scientist's Field Commentary & Expandable Explanations",
        ""
    ])

    for idx, r in enumerate(rows, 1):
        tags_badges = " ".join(f"`#{t}`" for t in r["tags"])
        qna = get_mentor_qna(idx, r, session_title=session_title)
        
        # Clean HTML tags for markdown rendering
        clean_ans_why = re.sub(r"<[^>]+>", "", qna["why"]["answer"])
        clean_ans_steps = qna["steps"]["answer"].replace("<br>", "\n").replace("<strong>", "**").replace("</strong>", "**")
        code_block = f"```python\n{qna['code']['code']}\n```" if qna["code"]["code"] else ""

        md_lines.extend([
            f"### Step {idx}: {r['did']}",
            f"{tags_badges}",
            f"",
            f"- **🎯 The Action**: {r['did']}",
            f"- **💡 Why It Was Done (The Science / System Context)**: {r['why']}",
            f"- **🔬 What Was Observed (Feedback & Telemetry)**: {r['happened']}",
            f"- **🚀 Next Strategic Step**: {r['next']}",
            f"",
            f"> [!TIP]",
            f"> **Mentor Note for Science Students**  ",
            f"> In scientific computing and computational physics, treating actions as reproducible state transitions ensures your analysis code is audit-proof. Notice how `{r['did']}` produced an observable signal `{r['happened']}`, which constrained the next hypothesis `{r['next']}`.",
            f"",
            f"<details>",
            f"<summary><b>❓ Why do it this way?</b> (Click to expand explanation)</summary>",
            f"",
            f"{clean_ans_why}",
            f"",
            f"[🌐 Ask on Web AI ↗]({qna['why']['web_url']})",
            f"</details>",
            f"",
            f"<details>",
            f"<summary><b>🔍 Explain step-by-step</b> (Click to expand beginner breakdown)</summary>",
            f"",
            f"{clean_ans_steps}",
            f"",
            f"[🌐 Ask on Web AI ↗]({qna['steps']['web_url']})",
            f"</details>",
            f"",
            f"<details>",
            f"<summary><b>💻 How do I run this myself?</b> (Click to view core syntax & copyable code)</summary>",
            f"",
            f"{qna['code']['md_guide']}",
            f"",
            f"[🌐 Ask on Web AI ↗]({qna['code']['web_url']})",
            f"</details>",
            f""
        ])

    md_lines.extend([
        "---",
        "",
        "## 🛠️ Undergraduate Computing Toolkit & Best Practices",
        "- **Python Tip**: Always separate raw experimental data from derived arrays; maintain idempotent data processing pipelines.",
        "- **Linux/Bash Tip**: Pipe commands (`|`) to stream data without writing intermediate temporary files to disk whenever possible.",
        "- **Git Tip**: Treat commits like experimental lab-book entries with clear, single-purpose changes and descriptive messages.",
        "- **Agentic Workflow Tip**: Provide verification hooks (unit tests, diff checks, assertions) so the AI agent verifies its own output before continuing.",
        "",
        f"_Generated automatically by Antigravity Senior CS Mentor Skill (`learn-cs-from-chat`)._"
    ])

    return "\n".join(md_lines)

def build_html(session_slug: str, session_title: str, rows: list[dict]) -> str:
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    total_steps = len(rows)
    all_tags = sorted(list(set(tag for r in rows for tag in r["tags"])))
    mermaid_diagram = generate_mermaid_diagram(rows)
    
    # Render Cards with Solution #1 (Jargon Tooltips) and Option 3 (Instant 1-Click Accordion)
    cards_html = []
    for idx, r in enumerate(rows, 1):
        tags_badges = "".join(f'<span class="badge" data-tag="{html.escape(t)}">#{html.escape(t)}</span> ' for t in r["tags"])
        
        # Solution #1: Jargon Buster Annotation
        annotated_did = annotate_jargon_html(r["did"])
        annotated_why = annotate_jargon_html(r["why"])
        annotated_happened = annotate_jargon_html(r["happened"])
        annotated_next = annotate_jargon_html(r["next"])
        
        # Option 3: Pre-rendered Mentor Q&A with 1-Click Accordions
        qna = get_mentor_qna(idx, r, session_title=session_title)
        
        panel_why_id = f"ans-{idx}-why"
        panel_steps_id = f"ans-{idx}-steps"
        panel_code_id = f"ans-{idx}-code"
        code_block_id = f"code-elem-{idx}"
        
        code_guide_html = build_code_guide_html(
            qna["code"]["core_ops"],
            qna["code"]["conceptual_flow"],
            qna["code"]["full_code"],
            code_block_id
        )
        
        card = f"""
        <div class="decision-card" data-step="{idx}" data-tags="{html.escape(','.join(r['tags']))}">
          <div class="card-header">
            <span class="step-num">Step {idx}</span>
            <div class="card-tags">{tags_badges}</div>
          </div>
          
          <div class="grid-section">
            <div class="section-box action-box">
              <div class="box-title">🎯 What the Agent Did</div>
              <div class="box-content">{annotated_did}</div>
            </div>
            
            <div class="section-box why-box">
              <div class="box-title">💡 Why Decided to Do It</div>
              <div class="box-content">{annotated_why}</div>
            </div>
            
            <div class="section-box happened-box">
              <div class="box-title">🔬 What Happened After Doing It</div>
              <div class="box-content">{annotated_happened}</div>
            </div>
            
            <div class="section-box next-box">
              <div class="box-title">🚀 Next Decision & Rationale</div>
              <div class="box-content">{annotated_next}</div>
            </div>
          </div>

          <!-- Option 3: 1-Click Accordion Prompts Drawer -->
          <div class="prompts-drawer">
            <div class="prompts-title">
              <span>💡</span> <strong>One-Click Questions: Click any question to reveal the Senior CS Mentor's explanation:</strong>
            </div>
            <div class="prompt-chips-container">
              <button class="prompt-chip" onclick="toggleAnswer('{panel_why_id}', this)">
                <span class="chip-icon">❓</span> Why do it this way?
              </button>
              <button class="prompt-chip" onclick="toggleAnswer('{panel_steps_id}', this)">
                <span class="chip-icon">🔍</span> Explain step-by-step
              </button>
              <button class="prompt-chip" onclick="toggleAnswer('{panel_code_id}', this)">
                <span class="chip-icon">💻</span> How do I run this myself?
              </button>
            </div>

            <!-- Accordion Answer Panels (Slide open on click) -->
            <div id="{panel_why_id}" class="mentor-answer-panel" style="display: none;">
              <div class="ans-header">
                <span class="ans-title">❓ Why Choose This Approach?</span>
                <a href="{html.escape(qna['why']['web_url'])}" target="_blank" class="ask-ext-btn">🌐 Ask on Web AI ↗</a>
              </div>
              <div class="ans-body">{qna['why']['answer']}</div>
            </div>

            <div id="{panel_steps_id}" class="mentor-answer-panel" style="display: none;">
              <div class="ans-header">
                <span class="ans-title">🔍 Step-by-Step Beginner Breakdown</span>
                <a href="{html.escape(qna['steps']['web_url'])}" target="_blank" class="ask-ext-btn">🌐 Ask on Web AI ↗</a>
              </div>
              <div class="ans-body">{qna['steps']['answer']}</div>
            </div>

            <div id="{panel_code_id}" class="mentor-answer-panel" style="display: none;">
              <div class="ans-header">
                <span class="ans-title">💻 How Do I Run This Myself? (Core Operations & Script)</span>
                <a href="{html.escape(qna['code']['web_url'])}" target="_blank" class="ask-ext-btn">🌐 Ask on Web AI ↗</a>
              </div>
              <div class="ans-body">
                {code_guide_html}
              </div>
            </div>
          </div>

          <div class="mentor-callout">
            <span class="mentor-icon">👨‍🏫</span>
            <div class="mentor-text">
              <strong>Senior CS Mentor Insight:</strong> Every computational action alters system state. Observing <em>"{html.escape(r['happened'])}"</em> directly constrained the decision boundary for step {idx+1 if idx < total_steps else 'completion'}. Hover over dotted terms for quick concept explanations!
            </div>
          </div>
        </div>
        """
        cards_html.append(card)

    cards_joined = "\n".join(cards_html) if cards_html else "<p class='empty-state'>No decisions recorded yet in this session.</p>"

    tag_buttons = '<button class="filter-btn active" data-filter="all">All Topics</button>'
    for t in all_tags:
        tag_buttons += f' <button class="filter-btn" data-filter="{html.escape(t)}">{html.escape(t)}</button>'

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>CS Decisions: {html.escape(session_title)}</title>
  <!-- Mermaid.js for interactive flowchart -->
  <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
  <script>
    if (typeof mermaid !== 'undefined') {{
      mermaid.initialize({{ startOnLoad: true, theme: 'dark', securityLevel: 'loose' }});
    }}
  </script>
  <style>
    :root {{
      --bg-primary: #0f172a;
      --bg-secondary: #1e293b;
      --bg-card: #1e293b;
      --bg-hover: #334155;
      --border-color: #334155;
      --accent: #38bdf8;
      --accent-green: #34d399;
      --accent-purple: #c084fc;
      --accent-amber: #fbbf24;
      --text-main: #f8fafc;
      --text-muted: #94a3b8;
      --font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    }}

    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      background-color: var(--bg-primary);
      color: var(--text-main);
      font-family: var(--font-family);
      line-height: 1.6;
      padding: 24px;
    }}

    .container {{
      max-width: 1200px;
      margin: 0 auto;
    }}

    /* Top Navigation & Links */
    .top-bar {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding-bottom: 20px;
      border-bottom: 1px solid var(--border-color);
      margin-bottom: 24px;
      flex-wrap: wrap;
      gap: 12px;
    }}

    .brand {{
      display: flex;
      align-items: center;
      gap: 10px;
      font-size: 1.25rem;
      font-weight: 700;
      color: var(--accent);
    }}

    .nav-links {{
      display: flex;
      gap: 12px;
    }}

    .nav-btn {{
      background: var(--bg-secondary);
      color: var(--text-main);
      text-decoration: none;
      padding: 8px 16px;
      border-radius: 8px;
      font-size: 0.875rem;
      font-weight: 500;
      border: 1px solid var(--border-color);
      transition: all 0.2s ease;
    }}

    .nav-btn:hover {{
      background: var(--bg-hover);
      border-color: var(--accent);
      color: var(--accent);
    }}

    /* Header Banner */
    .hero {{
      background: linear-gradient(135deg, rgba(30, 41, 59, 0.8) 0%, rgba(15, 23, 42, 0.9) 100%);
      border: 1px solid var(--border-color);
      border-radius: 12px;
      padding: 24px;
      margin-bottom: 24px;
      position: relative;
    }}

    .hero h1 {{
      font-size: 1.875rem;
      font-weight: 800;
      margin-bottom: 8px;
      color: #ffffff;
    }}

    .hero-meta {{
      display: flex;
      gap: 20px;
      font-size: 0.875rem;
      color: var(--text-muted);
      flex-wrap: wrap;
    }}

    .hero-meta span strong {{
      color: var(--text-main);
    }}

    /* Metrics Grid */
    .stats-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 16px;
      margin-bottom: 24px;
    }}

    .stat-card {{
      background: var(--bg-secondary);
      border: 1px solid var(--border-color);
      border-radius: 10px;
      padding: 16px;
      display: flex;
      flex-direction: column;
    }}

    .stat-val {{
      font-size: 1.75rem;
      font-weight: 700;
      color: var(--accent);
    }}

    .stat-label {{
      font-size: 0.8125rem;
      color: var(--text-muted);
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }}

    /* Diagram Section */
    .diagram-panel {{
      background: var(--bg-secondary);
      border: 1px solid var(--border-color);
      border-radius: 12px;
      padding: 20px;
      margin-bottom: 24px;
      overflow-x: auto;
    }}

    .diagram-panel h2 {{
      font-size: 1.125rem;
      margin-bottom: 16px;
      color: var(--accent-green);
      display: flex;
      align-items: center;
      gap: 8px;
    }}

    /* Filter Controls */
    .filter-bar {{
      display: flex;
      gap: 12px;
      margin-bottom: 20px;
      flex-wrap: wrap;
      align-items: center;
    }}

    .search-input {{
      background: var(--bg-secondary);
      border: 1px solid var(--border-color);
      color: var(--text-main);
      padding: 10px 16px;
      border-radius: 8px;
      font-size: 0.875rem;
      min-width: 260px;
      outline: none;
    }}

    .search-input:focus {{
      border-color: var(--accent);
    }}

    .filter-pills {{
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
    }}

    .filter-btn {{
      background: var(--bg-secondary);
      border: 1px solid var(--border-color);
      color: var(--text-muted);
      padding: 6px 12px;
      border-radius: 6px;
      font-size: 0.8125rem;
      cursor: pointer;
      transition: all 0.2s;
    }}

    .filter-btn.active, .filter-btn:hover {{
      background: var(--accent);
      color: #0f172a;
      font-weight: 600;
      border-color: var(--accent);
    }}

    /* Decision Cards */
    .decision-card {{
      background: var(--bg-secondary);
      border: 1px solid var(--border-color);
      border-radius: 12px;
      padding: 20px;
      margin-bottom: 24px;
      transition: border-color 0.15s ease;
    }}

    .decision-card:hover {{
      border-color: var(--accent);
    }}

    .card-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 16px;
    }}

    .step-num {{
      font-size: 0.9375rem;
      font-weight: 700;
      background: rgba(56, 189, 248, 0.15);
      color: var(--accent);
      padding: 4px 12px;
      border-radius: 6px;
      border: 1px solid rgba(56, 189, 248, 0.3);
    }}

    .badge {{
      display: inline-block;
      font-size: 0.75rem;
      padding: 3px 8px;
      border-radius: 4px;
      background: #334155;
      color: #cbd5e1;
      font-weight: 500;
    }}

    .grid-section {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
      gap: 16px;
      margin-bottom: 16px;
    }}

    .section-box {{
      background: rgba(15, 23, 42, 0.6);
      border: 1px solid rgba(51, 65, 85, 0.6);
      border-radius: 8px;
      padding: 14px;
      position: relative;
    }}

    .box-title {{
      font-size: 0.75rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      margin-bottom: 6px;
    }}

    .action-box .box-title {{ color: var(--accent); }}
    .why-box .box-title {{ color: var(--accent-amber); }}
    .happened-box .box-title {{ color: var(--accent-green); }}
    .next-box .box-title {{ color: var(--accent-purple); }}

    .box-content {{
      font-size: 0.9375rem;
      color: var(--text-main);
      word-break: break-word;
    }}

    /* Solution #1: Jargon Tooltip Styling */
    .jargon-term {{
      position: relative;
      display: inline-block;
      cursor: help;
      border-bottom: 1.5px dotted var(--accent);
      color: #e0f2fe;
      font-weight: 500;
    }}

    .jargon-term .tooltip-box {{
      visibility: hidden;
      opacity: 0;
      width: 280px;
      background: #0f172a;
      border: 1px solid var(--accent);
      color: #f8fafc;
      text-align: left;
      border-radius: 8px;
      padding: 12px;
      position: absolute;
      z-index: 1000;
      bottom: 125%;
      left: 50%;
      transform: translateX(-50%);
      box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.7), 0 8px 10px -6px rgba(0, 0, 0, 0.7);
      transition: opacity 0.2s ease, visibility 0.2s ease;
      font-size: 0.8125rem;
      line-height: 1.45;
      pointer-events: none;
    }}

    .jargon-term:hover .tooltip-box,
    .jargon-term:focus-within .tooltip-box {{
      visibility: visible;
      opacity: 1;
    }}

    .tooltip-box .tt-header {{
      display: block;
      color: var(--accent);
      font-weight: 700;
      margin-bottom: 4px;
      font-size: 0.875rem;
      border-bottom: 1px solid #334155;
      padding-bottom: 3px;
    }}

    .tooltip-box .tt-def {{
      display: block;
      color: #cbd5e1;
      margin-bottom: 6px;
    }}

    .tooltip-box .tt-analogy {{
      display: block;
      background: rgba(56, 189, 248, 0.08);
      border-left: 2px solid var(--accent);
      padding: 4px 6px;
      border-radius: 0 4px 4px 0;
      color: #e2e8f0;
    }}

    /* Option 3: Accordion Prompts Drawer */
    .prompts-drawer {{
      background: rgba(15, 23, 42, 0.4);
      border: 1px dashed var(--border-color);
      border-radius: 8px;
      padding: 14px;
      margin-bottom: 16px;
    }}

    .prompts-title {{
      font-size: 0.8125rem;
      color: var(--text-muted);
      margin-bottom: 10px;
      display: flex;
      align-items: center;
      gap: 6px;
    }}

    .prompt-chips-container {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-bottom: 12px;
    }}

    .prompt-chip {{
      background: #1e293b;
      border: 1px solid #475569;
      color: #f1f5f9;
      padding: 7px 14px;
      border-radius: 6px;
      font-size: 0.8125rem;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 6px;
      transition: all 0.15s ease;
    }}

    .prompt-chip:hover {{
      background: var(--bg-hover);
      border-color: var(--accent);
      color: var(--accent);
    }}

    .prompt-chip.active-chip {{
      background: rgba(56, 189, 248, 0.2);
      border-color: var(--accent);
      color: var(--accent);
      font-weight: 600;
    }}

    /* Expanded Accordion Answer Panels */
    .mentor-answer-panel {{
      background: rgba(15, 23, 42, 0.9);
      border: 1px solid var(--accent);
      border-radius: 8px;
      padding: 16px;
      margin-top: 10px;
      animation: slideDown 0.2s ease-out;
    }}

    @keyframes slideDown {{
      from {{ opacity: 0; transform: translateY(-6px); }}
      to {{ opacity: 1; transform: translateY(0); }}
    }}

    .ans-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      border-bottom: 1px solid #334155;
      padding-bottom: 8px;
      margin-bottom: 10px;
      flex-wrap: wrap;
      gap: 8px;
    }}

    .ans-title {{
      font-size: 0.9375rem;
      font-weight: 700;
      color: var(--accent);
    }}

    .ask-ext-btn {{
      font-size: 0.75rem;
      color: var(--accent-green);
      text-decoration: none;
      background: rgba(52, 211, 153, 0.1);
      border: 1px solid rgba(52, 211, 153, 0.3);
      padding: 4px 10px;
      border-radius: 4px;
      transition: all 0.2s;
    }}

    .ask-ext-btn:hover {{
      background: rgba(52, 211, 153, 0.25);
      border-color: var(--accent-green);
    }}

    .ans-body {{
      font-size: 0.875rem;
      color: #e2e8f0;
      line-height: 1.55;
      margin-bottom: 12px;
    }}

    /* Code Container in Answer */
    .code-container {{
      background: #090d16;
      border: 1px solid #334155;
      border-radius: 6px;
      overflow: hidden;
      margin-top: 10px;
    }}

    .code-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      background: #131c2e;
      padding: 6px 12px;
      font-size: 0.75rem;
      color: #94a3b8;
      border-bottom: 1px solid #334155;
    }}

    .copy-code-btn {{
      background: #1e293b;
      border: 1px solid #475569;
      color: #f1f5f9;
      padding: 3px 8px;
      border-radius: 4px;
      font-size: 0.75rem;
      cursor: pointer;
    }}

    .copy-code-btn:hover {{
      background: var(--accent);
      color: #0f172a;
    }}

    /* Core Operations & Syntax Guide */
    .core-ops-intro {{
      background: rgba(56, 189, 248, 0.08);
      border-left: 3px solid var(--accent);
      border-radius: 0 6px 6px 0;
      padding: 10px 14px;
      margin-bottom: 14px;
    }}

    .ops-badge {{
      font-size: 0.8125rem;
      font-weight: 700;
      color: var(--accent);
      text-transform: uppercase;
      letter-spacing: 0.05em;
      margin-bottom: 3px;
    }}

    .ops-subtitle {{
      font-size: 0.875rem;
      color: #cbd5e1;
      font-style: italic;
      margin: 0;
    }}

    .core-operations {{
      display: flex;
      flex-direction: column;
      gap: 12px;
      margin-bottom: 16px;
    }}

    .op-card {{
      background: rgba(15, 23, 42, 0.7);
      border: 1px solid rgba(51, 65, 85, 0.8);
      border-radius: 6px;
      padding: 10px 12px;
    }}

    .op-title {{
      font-size: 0.8125rem;
      font-weight: 700;
      color: #f1f5f9;
      margin-bottom: 6px;
    }}

    .mini-code {{
      margin-top: 4px;
      background: #090d16;
      border: 1px solid #1e293b;
      border-radius: 4px;
      padding: 8px 10px;
    }}

    .mini-code pre {{
      padding: 0;
      margin: 0;
      background: transparent;
    }}

    .mini-code code {{
      font-family: Consolas, Monaco, "Courier New", monospace;
      font-size: 0.8125rem;
      color: #7dd3fc;
      line-height: 1.45;
      display: block;
      white-space: pre;
    }}

    /* Conceptual Flow Card */
    .concept-flow-card {{
      background: #090d16;
      border: 1px dashed var(--accent-green);
      border-radius: 6px;
      padding: 12px 14px;
      margin-bottom: 16px;
    }}

    .flow-title {{
      font-size: 0.8125rem;
      font-weight: 700;
      color: var(--accent-green);
      text-transform: uppercase;
      letter-spacing: 0.05em;
      margin-bottom: 6px;
    }}

    .flow-pre {{
      font-family: Consolas, Monaco, "Courier New", monospace;
      font-size: 0.8125rem;
      color: #a7f3d0;
      line-height: 1.5;
      margin: 0;
      padding: 0;
      white-space: pre;
      background: transparent;
    }}

    .full-script-section {{
      margin-top: 14px;
      border-top: 1px solid #334155;
      padding-top: 12px;
    }}

    .full-script-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 6px;
      font-size: 0.8125rem;
      font-weight: 600;
      color: #cbd5e1;
    }}

    pre {{
      padding: 12px;
      overflow-x: auto;
      font-family: Consolas, Monaco, "Courier New", monospace;
      font-size: 0.8125rem;
      color: #38bdf8;
      line-height: 1.45;
    }}

    .mentor-callout {{
      display: flex;
      gap: 12px;
      background: rgba(56, 189, 248, 0.07);
      border-left: 3px solid var(--accent);
      padding: 12px 16px;
      border-radius: 0 8px 8px 0;
      font-size: 0.875rem;
      color: #e2e8f0;
      align-items: center;
    }}

    .mentor-icon {{
      font-size: 1.25rem;
    }}

    .footer {{
      text-align: center;
      padding: 24px 0;
      font-size: 0.8125rem;
      color: var(--text-muted);
      border-top: 1px solid var(--border-color);
      margin-top: 40px;
    }}

    @media (max-width: 768px) {{
      body {{ padding: 12px; }}
      .grid-section {{ grid-template-columns: 1fr; }}
      .jargon-term .tooltip-box {{ width: 240px; }}
    }}
  </style>
</head>
<body>
  <div class="container">
    <header class="top-bar">
      <div class="brand">
        <span>👨‍🏫</span> CS Decision Mentor
      </div>
      <div class="nav-links">
        <a href="./{html.escape(session_slug)}.md" class="nav-btn">📖 View Markdown Guide</a>
        <a href="./{html.escape(session_slug)}.tsv" class="nav-btn">📑 Raw TSV File</a>
        <a href="../INDEX.md" class="nav-btn">🗂️ All Sessions</a>
      </div>
    </header>

    <section class="hero">
      <h1>{html.escape(session_title)}</h1>
      <div class="hero-meta">
        <span>Session ID: <strong>{html.escape(session_slug)}</strong></span>
        <span>Target: <strong>Science Undergrad Learning Computing</strong></span>
        <span>Updated: <strong>{now_str}</strong></span>
      </div>
    </section>

    <section class="stats-grid">
      <div class="stat-card">
        <span class="stat-val">{total_steps}</span>
        <span class="stat-label">Causal Decisions Logged</span>
      </div>
      <div class="stat-card">
        <span class="stat-val">{len(all_tags)}</span>
        <span class="stat-label">Computing Focus Areas</span>
      </div>
      <div class="stat-card">
        <span class="stat-val">1-Click</span>
        <span class="stat-label">Instant Pre-Rendered Q&A</span>
      </div>
    </section>

    <section class="diagram-panel">
      <h2>🗺️ Sequential Decision & Hypothesis Progression</h2>
      <div class="mermaid">
{mermaid_diagram}
      </div>
    </section>

    <section class="filter-bar">
      <input type="text" id="searchInput" class="search-input" placeholder="🔍 Search decisions, python code, bash, git...">
      <div class="filter-pills" id="filterPills">
        {tag_buttons}
      </div>
    </section>

    <section id="cardsList">
      {cards_joined}
    </section>

    <footer class="footer">
      Generated by <strong>learn-cs-from-chat</strong> (Antigravity Senior CS Mentor Skill) • Stored at <code>D:/gemini/CS decisions/{html.escape(session_slug)}/</code>
    </footer>
  </div>

  <script>
    // Live Search and Tag Filter
    const searchInput = document.getElementById('searchInput');
    const filterBtns = document.querySelectorAll('.filter-btn');
    const cards = document.querySelectorAll('.decision-card');
    let currentTag = 'all';

    function filterCards() {{
      const query = searchInput.value.toLowerCase();
      cards.forEach(card => {{
        const text = card.innerText.toLowerCase();
        const tags = card.getAttribute('data-tags') || '';
        const matchesQuery = !query || text.includes(query);
        const matchesTag = currentTag === 'all' || tags.split(',').includes(currentTag);
        card.style.display = (matchesQuery && matchesTag) ? 'block' : 'none';
      }});
    }}

    searchInput.addEventListener('input', filterCards);

    filterBtns.forEach(btn => {{
      btn.addEventListener('click', () => {{
        filterBtns.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        currentTag = btn.getAttribute('data-filter');
        filterCards();
      }});
    }});

    // Option 3: 1-Click Accordion Toggle
    function toggleAnswer(panelId, btn) {{
      const panel = document.getElementById(panelId);
      const drawer = btn.closest('.prompts-drawer');
      const allPanels = drawer.querySelectorAll('.mentor-answer-panel');
      const allChips = drawer.querySelectorAll('.prompt-chip');
      
      const isOpen = panel.style.display === 'block';
      
      allPanels.forEach(p => p.style.display = 'none');
      allChips.forEach(c => c.classList.remove('active-chip'));
      
      if (!isOpen) {{
        panel.style.display = 'block';
        btn.classList.add('active-chip');
      }}
    }}

    // Copy Code Helper
    function copyCode(btn, codeElemId) {{
      const codeElem = document.getElementById(codeElemId);
      if (!codeElem) return;
      navigator.clipboard.writeText(codeElem.innerText).then(() => {{
        const originalText = btn.innerText;
        btn.innerText = "✅ Copied!";
        setTimeout(() => {{ btn.innerText = originalText; }}, 2000);
      }}).catch(err => {{
        console.error('Failed to copy code: ', err);
      }});
    }}
  </script>
</body>
</html>
"""
    return html_content

def update_central_catalog(hub_dir: Path):
    """Update D:/gemini/CS decisions/INDEX.md and index.html listing all recorded sessions."""
    sessions = []
    if not hub_dir.exists():
        return

    for item in sorted(hub_dir.iterdir()):
        if item.is_dir() and not item.name.startswith("."):
            tsv_files = list(item.glob("*.tsv"))
            if tsv_files:
                tsv_path = tsv_files[0]
                rows = parse_tsv(tsv_path)
                mtime = tsv_path.stat().st_mtime
                mod_date = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M")
                title = item.name.replace("-", " ").replace("_", " ").title()
                sessions.append({
                    "slug": item.name,
                    "title": title,
                    "count": len(rows),
                    "date": mod_date,
                    "first_action": rows[0]["did"] if rows else "No steps",
                    "tags": list(set(t for r in rows for t in r["tags"]))
                })

    sessions.sort(key=lambda s: s["date"], reverse=True)

    index_md = [
        "# 🗂️ CS Decisions Library (D:/gemini/CS decisions/)",
        "",
        "> Master repository of agentic decision trails translated into computer science masterclasses for undergraduate science students.",
        "",
        "| Session Slug | Focus / First Step | Steps | Key Topics | Last Updated | Dashboard Link | Guide Link |",
        "|---|---|---|---|---|---|---|"
    ]

    for s in sessions:
        tags_str = ", ".join(f"`{t}`" for t in s["tags"]) if s["tags"] else "`General`"
        action_short = (s["first_action"][:50] + "...") if len(s["first_action"]) > 50 else s["first_action"]
        index_md.append(f"| **{s['slug']}** | {action_short} | {s['count']} | {tags_str} | {s['date']} | [📊 HTML](./{s['slug']}/{s['slug']}.html) | [📖 MD](./{s['slug']}/{s['slug']}.md) |")

    index_md.append("\n_Maintained automatically by the Antigravity Senior CS Mentor Skill._\n")

    with open(hub_dir / "INDEX.md", "w", encoding="utf-8") as f:
        f.write("\n".join(index_md))

    table_rows_html = []
    for s in sessions:
        tags_html = " ".join(f'<span style="background:#334155;color:#e2e8f0;padding:2px 8px;border-radius:4px;font-size:0.75rem;">#{html.escape(t)}</span>' for t in s["tags"])
        table_rows_html.append(f"""
        <tr>
          <td><strong style="color:#38bdf8;">{html.escape(s['slug'])}</strong></td>
          <td>{html.escape(s['first_action'])}</td>
          <td><span style="background:rgba(56,189,248,0.15);color:#38bdf8;padding:2px 8px;border-radius:4px;font-weight:600;">{s['count']}</span></td>
          <td>{tags_html}</td>
          <td>{s['date']}</td>
          <td><a href="./{html.escape(s['slug'])}/{html.escape(s['slug'])}.html" style="color:#38bdf8;text-decoration:none;font-weight:600;">📊 View Dashboard</a></td>
          <td><a href="./{html.escape(s['slug'])}/{html.escape(s['slug'])}.md" style="color:#34d399;text-decoration:none;font-weight:600;">📖 Study Guide</a></td>
        </tr>
        """)

    index_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>CS Decisions Library</title>
  <style>
    body {{ background: #0f172a; color: #f8fafc; font-family: -apple-system, sans-serif; padding: 32px; }}
    .container {{ max-width: 1200px; margin: 0 auto; }}
    h1 {{ color: #38bdf8; margin-bottom: 8px; }}
    p.subtitle {{ color: #94a3b8; margin-bottom: 24px; }}
    table {{ width: 100%; border-collapse: collapse; background: #1e293b; border-radius: 8px; overflow: hidden; }}
    th, td {{ padding: 14px 16px; text-align: left; border-bottom: 1px solid #334155; }}
    th {{ background: #0f172a; color: #94a3b8; text-transform: uppercase; font-size: 0.75rem; letter-spacing: 0.05em; }}
    tr:hover {{ background: #334155; }}
  </style>
</head>
<body>
  <div class="container">
    <h1>👨‍🏫 CS Decisions Library</h1>
    <p class="subtitle">Directory: <code>D:/gemini/CS decisions/</code> • All session decision trails translated into CS lessons</p>
    <table>
      <thead>
        <tr>
          <th>Session Slug</th>
          <th>Initial Action</th>
          <th>Steps</th>
          <th>Topics</th>
          <th>Last Updated</th>
          <th>Dashboard</th>
          <th>Guide</th>
        </tr>
      </thead>
      <tbody>
        {"".join(table_rows_html)}
      </tbody>
    </table>
  </div>
</body>
</html>"""

    with open(hub_dir / "index.html", "w", encoding="utf-8") as f:
        f.write(index_html)

def main():
    parser = argparse.ArgumentParser(description="Render CS Mentor HTML and MD with Option 3 1-Click Accordions")
    parser.add_argument("--dir", type=str, required=True, help="Session folder path, e.g. D:/gemini/CS decisions/bandgap-dft")
    parser.add_argument("--slug", type=str, required=False, help="Session slug identifier")
    parser.add_argument("--title", type=str, required=False, help="Human-friendly session title")
    args = parser.parse_args()

    session_dir = Path(args.dir).resolve()
    session_slug = args.slug or session_dir.name
    session_title = args.title or session_slug.replace("-", " ").replace("_", " ").title()

    session_dir.mkdir(parents=True, exist_ok=True)
    tsv_path = session_dir / f"{session_slug}.tsv"

    rows = parse_tsv(tsv_path)
    
    # 1. Render Markdown
    md_content = build_markdown(session_slug, session_title, rows)
    md_path = session_dir / f"{session_slug}.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_content)

    # 2. Render HTML
    html_content = build_html(session_slug, session_title, rows)
    html_path = session_dir / f"{session_slug}.html"
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    # 3. Update central catalog
    hub_dir = session_dir.parent
    if hub_dir.name == "CS decisions":
        update_central_catalog(hub_dir)

    print(f"Successfully rendered with Option 3 (Instant 1-Click Accordions):")
    print(f"  HTML Dashboard: {html_path}")
    print(f"  Markdown Guide: {md_path}")

if __name__ == "__main__":
    main()
