<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Project BIOS — README</title>
<link href="https://fonts.googleapis.com/css2?family=Space+Mono:ital,wght@0,400;0,700;1,400&family=Syne:wght@400;600;700;800&display=swap" rel="stylesheet">
<style>
  :root {
    --bg: #0a0c0f;
    --surface: #111318;
    --surface2: #181c24;
    --border: #1f2533;
    --border-bright: #2e3a50;
    --text: #c8d4e8;
    --text-dim: #5a6a85;
    --text-bright: #eaf0fc;
    --accent: #3be8b0;
    --accent2: #5b8dee;
    --accent3: #f5a623;
    --accent4: #e85b5b;
    --mono: 'Space Mono', monospace;
    --sans: 'Syne', sans-serif;
  }

  * { margin: 0; padding: 0; box-sizing: border-box; }

  html { scroll-behavior: smooth; }

  body {
    background: var(--bg);
    color: var(--text);
    font-family: var(--mono);
    font-size: 14px;
    line-height: 1.75;
    min-height: 100vh;
  }

  /* Scanline overlay */
  body::before {
    content: '';
    position: fixed;
    inset: 0;
    background: repeating-linear-gradient(
      0deg,
      transparent,
      transparent 2px,
      rgba(0,0,0,0.08) 2px,
      rgba(0,0,0,0.08) 4px
    );
    pointer-events: none;
    z-index: 9999;
  }

  .page {
    max-width: 920px;
    margin: 0 auto;
    padding: 0 24px 80px;
  }

  /* ─── HERO ─────────────────────────────────── */
  .hero {
    padding: 64px 0 48px;
    border-bottom: 1px solid var(--border);
    position: relative;
    overflow: hidden;
  }

  .hero::after {
    content: 'BIOS';
    position: absolute;
    right: -20px;
    top: 10px;
    font-family: var(--sans);
    font-size: 180px;
    font-weight: 800;
    color: rgba(59, 232, 176, 0.04);
    letter-spacing: -8px;
    pointer-events: none;
    user-select: none;
  }

  .badge-row {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
    margin-bottom: 24px;
  }

  .badge {
    font-family: var(--mono);
    font-size: 10px;
    padding: 3px 10px;
    border-radius: 2px;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    font-weight: 700;
  }
  .badge-green  { background: rgba(59,232,176,0.12); color: var(--accent);  border: 1px solid rgba(59,232,176,0.25); }
  .badge-blue   { background: rgba(91,141,238,0.12); color: var(--accent2); border: 1px solid rgba(91,141,238,0.25); }
  .badge-orange { background: rgba(245,166,35,0.12); color: var(--accent3); border: 1px solid rgba(245,166,35,0.25); }
  .badge-red    { background: rgba(232,91,91,0.12);  color: var(--accent4); border: 1px solid rgba(232,91,91,0.25);  }

  .hero-title {
    font-family: var(--sans);
    font-size: clamp(36px, 6vw, 64px);
    font-weight: 800;
    color: var(--text-bright);
    letter-spacing: -1px;
    line-height: 1.05;
    margin-bottom: 16px;
  }

  .hero-title span { color: var(--accent); }

  .hero-subtitle {
    font-family: var(--mono);
    font-size: 15px;
    color: var(--text-dim);
    max-width: 560px;
    line-height: 1.7;
    border-left: 2px solid var(--accent);
    padding-left: 16px;
    margin-top: 20px;
  }

  /* ─── NAV / TOC ─────────────────────────────── */
  .toc {
    display: flex;
    gap: 0;
    flex-wrap: wrap;
    border-bottom: 1px solid var(--border);
    margin-bottom: 0;
    position: sticky;
    top: 0;
    background: rgba(10,12,15,0.95);
    backdrop-filter: blur(8px);
    z-index: 100;
  }

  .toc a {
    font-family: var(--mono);
    font-size: 11px;
    text-decoration: none;
    color: var(--text-dim);
    padding: 12px 16px;
    border-bottom: 2px solid transparent;
    transition: color 0.2s, border-color 0.2s;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    white-space: nowrap;
  }

  .toc a:hover {
    color: var(--accent);
    border-bottom-color: var(--accent);
  }

  /* ─── SECTIONS ───────────────────────────────── */
  .section {
    padding: 56px 0 40px;
    border-bottom: 1px solid var(--border);
    animation: fadeup 0.5s ease both;
  }

  @keyframes fadeup {
    from { opacity: 0; transform: translateY(12px); }
    to   { opacity: 1; transform: translateY(0); }
  }

  .section-label {
    font-family: var(--mono);
    font-size: 10px;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: var(--accent);
    margin-bottom: 10px;
    display: flex;
    align-items: center;
    gap: 10px;
  }

  .section-label::after {
    content: '';
    flex: 1;
    height: 1px;
    background: var(--border-bright);
    max-width: 80px;
  }

  .section-title {
    font-family: var(--sans);
    font-size: 28px;
    font-weight: 700;
    color: var(--text-bright);
    margin-bottom: 20px;
    letter-spacing: -0.3px;
  }

  p {
    color: var(--text);
    margin-bottom: 14px;
    max-width: 700px;
  }

  strong { color: var(--text-bright); font-weight: 700; }

  /* ─── PHILOSOPHY PILLARS ─────────────────────── */
  .pillars {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
    gap: 12px;
    margin-top: 24px;
  }

  .pillar {
    background: var(--surface);
    border: 1px solid var(--border);
    border-top: 2px solid var(--accent);
    padding: 20px;
    border-radius: 4px;
    transition: border-color 0.2s, transform 0.2s;
  }

  .pillar:nth-child(2) { border-top-color: var(--accent2); }
  .pillar:nth-child(3) { border-top-color: var(--accent3); }
  .pillar:nth-child(4) { border-top-color: var(--accent4); }

  .pillar:hover { transform: translateY(-2px); border-color: var(--border-bright); }

  .pillar-title {
    font-family: var(--sans);
    font-size: 13px;
    font-weight: 700;
    color: var(--text-bright);
    margin-bottom: 8px;
  }

  .pillar-body {
    font-size: 12px;
    color: var(--text-dim);
    line-height: 1.6;
  }

  /* ─── DRIVE VARS ─────────────────────────────── */
  .drive-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
    gap: 12px;
    margin: 24px 0;
  }

  .drive-card {
    background: var(--surface);
    border: 1px solid var(--border);
    padding: 20px 20px 16px;
    border-radius: 4px;
    position: relative;
    overflow: hidden;
  }

  .drive-card::before {
    content: '';
    position: absolute;
    bottom: 0; left: 0;
    height: 2px;
    width: 100%;
    background: var(--accent);
  }

  .drive-card:nth-child(2)::before { background: var(--accent2); }
  .drive-card:nth-child(3)::before { background: var(--accent3); }

  .drive-icon {
    font-size: 22px;
    margin-bottom: 12px;
  }

  .drive-name {
    font-family: var(--sans);
    font-size: 15px;
    font-weight: 700;
    color: var(--text-bright);
    margin-bottom: 6px;
  }

  .drive-desc {
    font-size: 11px;
    color: var(--text-dim);
    line-height: 1.6;
  }

  /* ─── CODE BLOCK ─────────────────────────────── */
  .code-block {
    background: var(--surface);
    border: 1px solid var(--border-bright);
    border-left: 3px solid var(--accent);
    border-radius: 4px;
    padding: 20px 24px;
    margin: 24px 0;
    overflow-x: auto;
    position: relative;
  }

  .code-block-label {
    position: absolute;
    top: -1px; right: 12px;
    font-size: 9px;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: var(--accent);
    background: var(--surface);
    padding: 3px 8px;
    border: 1px solid var(--border-bright);
    border-top: none;
    border-radius: 0 0 3px 3px;
  }

  .code-block pre {
    font-family: var(--mono);
    font-size: 13px;
    color: var(--accent);
    white-space: pre;
  }

  .code-comment { color: var(--text-dim); }
  .code-keyword { color: var(--accent2); }
  .code-string  { color: var(--accent3); }

  /* ─── EMOTION TABLE ──────────────────────────── */
  .signal-table {
    width: 100%;
    border-collapse: collapse;
    margin: 24px 0;
    font-size: 13px;
  }

  .signal-table th {
    font-family: var(--sans);
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: var(--text-dim);
    padding: 10px 16px;
    text-align: left;
    border-bottom: 1px solid var(--border-bright);
  }

  .signal-table td {
    padding: 14px 16px;
    border-bottom: 1px solid var(--border);
    vertical-align: top;
    line-height: 1.5;
  }

  .signal-table tr:last-child td { border-bottom: none; }

  .signal-table tr:hover td { background: var(--surface); }

  .signal-name {
    font-family: var(--sans);
    font-weight: 700;
    color: var(--text-bright);
  }

  .signal-drive  .signal-name { color: var(--accent);  }
  .signal-fear   .signal-name { color: var(--accent4); }
  .signal-stress .signal-name { color: var(--accent3); }

  .signal-table td:first-child { width: 100px; }

  /* ─── MEMORY CARDS ───────────────────────────── */
  .memory-split {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 16px;
    margin: 24px 0;
  }

  @media (max-width: 600px) {
    .memory-split { grid-template-columns: 1fr; }
    .pillars { grid-template-columns: 1fr 1fr; }
    .drive-grid { grid-template-columns: 1fr; }
  }

  .mem-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 4px;
    padding: 24px;
  }

  .mem-card-header {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 16px;
  }

  .mem-tag {
    font-size: 9px;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    padding: 3px 8px;
    border-radius: 2px;
    font-weight: 700;
  }

  .mem-semantic { background: rgba(59,232,176,0.1); color: var(--accent); border: 1px solid rgba(59,232,176,0.2); }
  .mem-episodic { background: rgba(91,141,238,0.1); color: var(--accent2); border: 1px solid rgba(91,141,238,0.2); }

  .mem-title {
    font-family: var(--sans);
    font-size: 15px;
    font-weight: 700;
    color: var(--text-bright);
  }

  .mem-list {
    list-style: none;
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .mem-list li {
    font-size: 12px;
    color: var(--text-dim);
    padding-left: 14px;
    position: relative;
    line-height: 1.5;
  }

  .mem-list li::before {
    content: '→';
    position: absolute;
    left: 0;
    color: var(--accent);
    font-size: 10px;
    top: 2px;
  }

  .mem-episodic .mem-list li::before { color: var(--accent2); }

  /* ─── ROADMAP ─────────────────────────────────── */
  .roadmap {
    display: flex;
    flex-direction: column;
    gap: 0;
    margin: 24px 0;
    position: relative;
  }

  .roadmap::before {
    content: '';
    position: absolute;
    left: 19px; top: 20px; bottom: 20px;
    width: 1px;
    background: var(--border-bright);
  }

  .roadmap-item {
    display: flex;
    align-items: flex-start;
    gap: 20px;
    padding: 14px 0;
  }

  .roadmap-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: var(--border-bright);
    border: 2px solid var(--border-bright);
    margin-top: 6px;
    flex-shrink: 0;
    position: relative;
    z-index: 1;
    margin-left: 15px;
    transition: background 0.2s;
  }

  .roadmap-item:hover .roadmap-dot {
    background: var(--accent);
    border-color: var(--accent);
    box-shadow: 0 0 8px rgba(59,232,176,0.4);
  }

  .roadmap-text {
    font-family: var(--sans);
    font-size: 14px;
    font-weight: 600;
    color: var(--text);
  }

  .roadmap-sub {
    font-size: 11px;
    color: var(--text-dim);
    margin-top: 2px;
    font-family: var(--mono);
  }

  /* ─── CONSTRAINTS ─────────────────────────────── */
  .constraint-list {
    display: flex;
    flex-direction: column;
    gap: 10px;
    margin: 24px 0;
  }

  .constraint-item {
    display: flex;
    align-items: center;
    gap: 14px;
    background: var(--surface);
    border: 1px solid var(--border);
    padding: 14px 18px;
    border-radius: 4px;
  }

  .constraint-x {
    font-size: 14px;
    color: var(--accent4);
    font-weight: 700;
    flex-shrink: 0;
  }

  .constraint-text {
    font-size: 13px;
    color: var(--text);
  }

  .constraint-reason {
    font-size: 11px;
    color: var(--text-dim);
    margin-top: 2px;
  }

  /* ─── GOAL ARBITRATION ────────────────────────── */
  .gsm-stack {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 4px;
    overflow: hidden;
    margin: 24px 0;
  }

  .gsm-header {
    background: var(--surface2);
    padding: 10px 16px;
    font-size: 10px;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    color: var(--text-dim);
    border-bottom: 1px solid var(--border);
    display: flex;
    gap: 20px;
  }

  .gsm-row {
    display: flex;
    align-items: center;
    gap: 16px;
    padding: 14px 16px;
    border-bottom: 1px solid var(--border);
    transition: background 0.15s;
  }

  .gsm-row:last-child { border-bottom: none; }
  .gsm-row:hover { background: var(--surface2); }

  .gsm-priority {
    font-family: var(--sans);
    font-size: 11px;
    font-weight: 800;
    color: var(--text-dim);
    width: 28px;
    text-align: center;
  }

  .priority-high { color: var(--accent4); }
  .priority-mid  { color: var(--accent3); }
  .priority-low  { color: var(--accent2); }

  .gsm-name {
    font-family: var(--sans);
    font-weight: 700;
    font-size: 13px;
    color: var(--text-bright);
    min-width: 140px;
  }

  .gsm-trigger {
    font-size: 11px;
    color: var(--text-dim);
    flex: 1;
  }

  .gsm-badge {
    font-size: 9px;
    padding: 2px 7px;
    border-radius: 2px;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    font-weight: 700;
  }

  .gsm-interrupt { background: rgba(232,91,91,0.12); color: var(--accent4); border: 1px solid rgba(232,91,91,0.2); }
  .gsm-persist   { background: rgba(59,232,176,0.08); color: var(--accent);  border: 1px solid rgba(59,232,176,0.15); }

  /* ─── FOOTER ─────────────────────────────────── */
  .footer {
    padding: 40px 0 20px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 12px;
  }

  .footer-brand {
    font-family: var(--sans);
    font-size: 12px;
    font-weight: 700;
    color: var(--text-dim);
    letter-spacing: 0.1em;
    text-transform: uppercase;
  }

  .footer-brand span { color: var(--accent); }

  .footer-note {
    font-size: 11px;
    color: var(--text-dim);
  }

</style>
</head>
<body>
<div class="page">

  <!-- HERO -->
  <header class="hero">
    <div class="badge-row">
      <span class="badge badge-green">v0.1.0-alpha</span>
      <span class="badge badge-blue">No Neural Nets</span>
      <span class="badge badge-orange">Deterministic</span>
      <span class="badge badge-red">Experimental</span>
    </div>
    <h1 class="hero-title">Project <span>BIOS</span></h1>
    <p class="hero-subtitle">
      Intelligent behavior emerging from the interaction of simple systems — inspired by biology, without copying it blindly.
    </p>
  </header>

  <!-- TOC -->
  <nav class="toc">
    <a href="#philosophy">Philosophy</a>
    <a href="#drives">Drives</a>
    <a href="#affective">Affective</a>
    <a href="#goals">Goals</a>
    <a href="#memory">Memory</a>
    <a href="#constraints">Constraints</a>
    <a href="#roadmap">Roadmap</a>
  </nav>

  <!-- PHILOSOPHY -->
  <section class="section" id="philosophy">
    <div class="section-label">01 — Core Philosophy</div>
    <h2 class="section-title">Design Foundations</h2>
    <p>Project BIOS is built on the principle that <strong>complex behavior should emerge from the interaction of simple, explainable systems</strong> — not from opaque trained models or handcrafted rule trees.</p>
    <div class="pillars">
      <div class="pillar">
        <div class="pillar-title">Embodiment First</div>
        <div class="pillar-body">Cognition is deeply tied to the body and its environment. No disembodied reasoning.</div>
      </div>
      <div class="pillar">
        <div class="pillar-title">Internal Drives</div>
        <div class="pillar-body">No behavior trees or hardcoded rules. Behavior arises from physiological needs and emotional signals.</div>
      </div>
      <div class="pillar">
        <div class="pillar-title">Understandable Emergence</div>
        <div class="pillar-body">Systems whose behavior can always be explained, traced, and debugged by a human.</div>
      </div>
      <div class="pillar">
        <div class="pillar-title">Determinism</div>
        <div class="pillar-body">Everything is reproducible. Full scientific rigor for experimentation and replication.</div>
      </div>
    </div>
  </section>

  <!-- HOMEOSTATIC DRIVES -->
  <section class="section" id="drives">
    <div class="section-label">02 — Homeostatic Drives</div>
    <h2 class="section-title">Physiological Variables</h2>
    <p>The agent is governed by internal physiological variables that create <strong>homeostatic pressure</strong>. As energy drops, <code>Drive</code> increases, pushing the agent toward food-seeking behavior — natural motivation without explicit rules.</p>

    <div class="drive-grid">
      <div class="drive-card">
        <div class="drive-icon">⚡</div>
        <div class="drive-name">Energy</div>
        <div class="drive-desc">Metabolic resource consumed continuously. The primary driver of urgent behavior.</div>
      </div>
      <div class="drive-card">
        <div class="drive-icon">🛡</div>
        <div class="drive-name">Integrity</div>
        <div class="drive-desc">Physical health. Damaged by hazards, influences fear and stress thresholds.</div>
      </div>
      <div class="drive-card">
        <div class="drive-icon">🫙</div>
        <div class="drive-name">Reserves</div>
        <div class="drive-desc">Stored energy from food. Buffers against acute energy depletion events.</div>
      </div>
    </div>

    <div class="code-block">
      <span class="code-block-label">Python</span>
      <pre><span class="code-comment"># Drive scaling — non-linear urgency mirrors real biological hunger</span>
drive = (MAX_ENERGY - current_energy) / MAX_ENERGY

<span class="code-comment"># As current_energy → 0, drive → 1.0 (maximum urgency)</span>
<span class="code-comment"># As current_energy → MAX, drive → 0.0 (satiated, low priority)</span></pre>
    </div>
  </section>

  <!-- AFFECTIVE SYSTEM -->
  <section class="section" id="affective">
    <div class="section-label">03 — Affective System</div>
    <h2 class="section-title">Emotion &amp; Hormone Engine</h2>
    <p>The <strong>EmotionHormoneEngine</strong> translates body state and sensory input into three key signals. These act as <em>modulators</em> — influencing both goal selection and low-level motor commands.</p>

    <table class="signal-table">
      <thead>
        <tr>
          <th>Signal</th>
          <th>Trigger</th>
          <th>Effect on Behavior</th>
        </tr>
      </thead>
      <tbody>
        <tr class="signal-drive">
          <td><span class="signal-name">Drive</span></td>
          <td>Low energy</td>
          <td>Increases food-seeking priority, suppresses exploratory behavior</td>
        </tr>
        <tr class="signal-fear">
          <td><span class="signal-name">Fear</span></td>
          <td>Hazard proximity</td>
          <td>Strong avoidance response + thrust boost override</td>
        </tr>
        <tr class="signal-stress">
          <td><span class="signal-name">Stress</span></td>
          <td>Wall proximity + damage</td>
          <td>Modulates thrust magnitude and interrupts current goals</td>
        </tr>
      </tbody>
    </table>
  </section>

  <!-- GOAL ARBITRATION -->
  <section class="section" id="goals">
    <div class="section-label">04 — Goal Arbitration</div>
    <h2 class="section-title">Goal Stack Manager</h2>
    <p>The <strong>GSM</strong> implements persistent, interruptible behavior. Goals carry priority scores and persistence durations. Higher-priority goals can interrupt lower ones, preventing chaotic frame-by-frame behavioral switching.</p>

    <div class="gsm-stack">
      <div class="gsm-header">
        <span style="width:28px">PRI</span>
        <span style="min-width:140px">Goal</span>
        <span>Trigger Condition</span>
        <span>Type</span>
      </div>
      <div class="gsm-row">
        <div class="gsm-priority priority-high">P1</div>
        <div class="gsm-name">Avoid Hazard</div>
        <div class="gsm-trigger">Fear signal above threshold — hazard within detection range</div>
        <div class="gsm-badge gsm-interrupt">Interrupt</div>
      </div>
      <div class="gsm-row">
        <div class="gsm-priority priority-high">P2</div>
        <div class="gsm-name">Seek Food</div>
        <div class="gsm-trigger">Drive signal above threshold — energy below critical</div>
        <div class="gsm-badge gsm-interrupt">Interrupt</div>
      </div>
      <div class="gsm-row">
        <div class="gsm-priority priority-mid">P3</div>
        <div class="gsm-name">Explore</div>
        <div class="gsm-trigger">Low drive, no hazards — biased by semantic memory map</div>
        <div class="gsm-badge gsm-persist">Persist</div>
      </div>
      <div class="gsm-row">
        <div class="gsm-priority priority-low">P4</div>
        <div class="gsm-name">Idle</div>
        <div class="gsm-trigger">All higher goals inactive or satisfied</div>
        <div class="gsm-badge gsm-persist">Persist</div>
      </div>
    </div>
  </section>

  <!-- MEMORY -->
  <section class="section" id="memory">
    <div class="section-label">05 — Memory Systems</div>
    <h2 class="section-title">Semantic &amp; Episodic Memory</h2>
    <p>Two complementary memory architectures work in parallel — one mapping space, the other recording significant life events.</p>

    <div class="memory-split">
      <div class="mem-card">
        <div class="mem-card-header">
          <span class="mem-tag mem-semantic">Semantic</span>
          <span class="mem-title">Cognitive Map</span>
        </div>
        <ul class="mem-list">
          <li>Dead-reckoning odometry with landmark-based drift correction</li>
          <li>Sparse grid encoding hazard and food "place cells"</li>
          <li>Generates spatial bias vectors to guide planning</li>
          <li>Persistent spatial awareness without continuous sensing</li>
        </ul>
      </div>
      <div class="mem-card">
        <div class="mem-card-header">
          <span class="mem-tag mem-episodic">Episodic</span>
          <span class="mem-title">Autobiographical</span>
        </div>
        <ul class="mem-list">
          <li>Welford's online algorithm for statistical surprise detection</li>
          <li>Emotional intensity × surprise score determines retention</li>
          <li>Stores critical events: near-death, starvation, major recoveries</li>
          <li>Foundation for future memory consolidation pipeline</li>
        </ul>
      </div>
    </div>
  </section>

  <!-- CONSTRAINTS -->
  <section class="section" id="constraints">
    <div class="section-label">06 — Design Constraints</div>
    <h2 class="section-title">Intentional Limitations</h2>
    <p>These are not gaps — they are deliberate design choices. We believe understanding how simple systems create complex behavior is more valuable at this stage than chasing benchmark scores.</p>

    <div class="constraint-list">
      <div class="constraint-item">
        <div class="constraint-x">✕</div>
        <div>
          <div class="constraint-text">No Neural Networks</div>
          <div class="constraint-reason">All behavior must trace back to interpretable logic and state variables</div>
        </div>
      </div>
      <div class="constraint-item">
        <div class="constraint-x">✕</div>
        <div>
          <div class="constraint-text">No Reinforcement Learning</div>
          <div class="constraint-reason">Prevents emergent behavior that cannot be explained or reproduced analytically</div>
        </div>
      </div>
      <div class="constraint-item">
        <div class="constraint-x">✕</div>
        <div>
          <div class="constraint-text">No Large Language Models</div>
          <div class="constraint-reason">Cognition should emerge from architecture, not from compressed internet knowledge</div>
        </div>
      </div>
    </div>
  </section>

  <!-- ROADMAP -->
  <section class="section" id="roadmap">
    <div class="section-label">07 — Roadmap</div>
    <h2 class="section-title">Theoretical Milestones</h2>
    <p>Upcoming research directions and architectural expansions planned for Project BIOS.</p>

    <div class="roadmap">
      <div class="roadmap-item">
        <div class="roadmap-dot"></div>
        <div>
          <div class="roadmap-text">Memory Consolidation</div>
          <div class="roadmap-sub">Episodic → Semantic transfer; generalizing experience into spatial priors</div>
        </div>
      </div>
      <div class="roadmap-item">
        <div class="roadmap-dot"></div>
        <div>
          <div class="roadmap-text">Intrinsic Motivation & Curiosity</div>
          <div class="roadmap-sub">Information-theoretic novelty signal driving exploratory behavior</div>
        </div>
      </div>
      <div class="roadmap-item">
        <div class="roadmap-dot"></div>
        <div>
          <div class="roadmap-text">Hierarchical Planning</div>
          <div class="roadmap-sub">Multi-timescale goal decomposition over the cognitive map</div>
        </div>
      </div>
      <div class="roadmap-item">
        <div class="roadmap-dot"></div>
        <div>
          <div class="roadmap-text">Value Learning</div>
          <div class="roadmap-sub">Deriving preferences from homeostatic outcomes, not hand-specified rewards</div>
        </div>
      </div>
    </div>
  </section>

  <!-- FOOTER -->
  <footer class="footer">
    <div class="footer-brand">Project <span>BIOS</span></div>
    <div class="footer-note">Built on first principles. No black boxes.</div>
  </footer>

</div>
</body>
</html>