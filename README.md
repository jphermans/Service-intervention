# Atlas Copco Tightening Intervention

A modern, installable web app for **Atlas Copco service technicians** to generate, sign, and print tightening intervention reports on any device — phone, tablet, or desktop. Works fully offline once installed.

![Form screenshot](docs/screenshot-form.png)

---

## ✨ Features

### 📋 Smart form
- **Auto-formatted dates** — DD/MM/YYYY across every device, with a built-in calendar picker
- **24-hour time inputs** — HH:MM, auto-inserted colon as you type
- **6-character unique report IDs** — base36, collision-checked against the local database
- **46 inline tooltips** — hover any label for guidance on what to fill in

### ⏱ Work & travel time tracking
- Dynamic rows with **auto-calculated durations** (handles overnight crossings)
- Live **totals** at the bottom of each table
- Pre-validated time format, no AM/PM ambiguity ever

### ✍️ Signatures
- Draw with mouse, finger, or stylus
- Names auto-fill from Contact / Technician fields
- Signatures **persist with the report** — visible on the saved card and on the printed PDF
- Date stamps preserved on re-print

### 📦 Reports & data
- **Save Report** — persists to local storage with signatures + time tables + everything
- **Save to JSON** — download a portable backup with a descriptive filename (`<customer>_<date>_<id>.json`)
- **Load from JSON** — round-trip restore of every field
- **Clone** — copy a saved report into a fresh form
- **Delete** individual or all reports

### 📄 Print to PDF
- 3-page A4 layout: form fields + Psets/notes + work/travel/signatures + saved audit trail
- Compact print styles, hides buttons and decorative chrome

### 📱 Installable PWA
- Add to Home Screen on Android / iOS
- Install as standalone app on desktop Chrome/Edge
- **Service worker pre-caches the app shell** — full offline use after first load
- Branded teal theme, 192/512/maskable icons

### 📱 Mobile-friendly
- Custom date/time inputs scale gracefully on 390 px-wide screens
- Action buttons stack vertically on mobile (full-width)
- Work Time / Travel Time tables scroll horizontally instead of being truncated
- The calendar picker is touch-friendly and stays on-screen

![Mobile view](docs/screenshot-mobile.png)

### 🧪 Built-in demo
- **Fill Demo** button loads a complete Stellantis NV scenario
- Safety confirm before overwriting real data
- One click to see every feature in action

---

## 🚀 Quick start

### Open it in your browser
The app is a single `index.html` with no build step:

```bash
# Option 1 — open the file directly
open index.html         # macOS
xdg-open index.html     # Linux

# Option 2 — serve it locally (recommended for PWA + service worker)
python3 -m http.server 8765
# then visit http://localhost:8765
```

### Install as an app
- **Android Chrome / Edge** → menu → *Install app*
- **iOS Safari** → Share → *Add to Home Screen*
- **Desktop Chrome / Edge** → install icon in the address bar

Once installed it opens full-screen, runs offline, and behaves like a native app.

---

## 📖 How to use

1. **Fill the report** — type or paste your data. Every label has a tooltip explaining what to enter.
2. **Sign** — toggle the signature section, draw on both pads with your finger, mouse, or stylus.
3. **Track time** — add rows for each work block and travel leg. Durations and totals are calculated automatically.
4. **Save Report** — the entry appears in the *Saved Reports* list with full details, time tables, and signature thumbnails.
5. **Print to PDF** — open the browser print dialog and choose *Save as PDF*. Hand the file to the customer.
6. **Back up** — *Save to JSON* downloads a portable file with a descriptive name like `stellantis-nv-aartselaar-plant_2025-12-04_VCXMFB.json` (customer name sanitized, ISO date, report ID). *Load from JSON* restores it on any device.
7. **Fill Demo** — explore the app with one click (asks for confirmation before overwriting real data).

### Tips
- The form is a single page — scroll to find any section.
- After saving, the form resets its **id** and date but keeps your data so you can keep working. Click *Clear* to start truly fresh.
- Signatures **survive Save Report** — they only wipe on *Clear*, *Clone*, or *Load from JSON*.

---

## 🖼 Screenshots

### The filled form
![Form](docs/screenshot-form.png)

### Printed PDF — work & travel tables + signatures
![PDF](docs/screenshot-pdf.png)

### Saved report card (in the form view)
![Saved card](docs/screenshot-saved-card.png)

---

## 🛠 Tech stack

| | |
|---|---|
| **App** | Single-file `index.html` — vanilla HTML/CSS/JS, no build step |
| **PWA** | `manifest.json` + `sw.js` (cache-first strategy) |
| **Icons** | SVG sources in `icons/`, exported to PNG at 32/180/192/512 px |
| **Storage** | Browser `localStorage` for reports; `FileReader` + `Blob` for JSON I/O |
| **Dependencies** | None |

### Architecture notes

- **Single source of truth** — every report lives in `localStorage` under the key `reports` as a JSON array. The form reads/writes this array directly.
- **Custom date & time inputs** — the native `<input type="date">` and `<input type="time">` were replaced because too many browsers ignore the `lang` attribute and fall back to the OS locale (MM/DD/YYYY or AM/PM). The custom inputs always show DD/MM/YYYY and HH:MM (24h), independent of platform.
- **Signature persistence** — the canvas pixel data is captured with `toDataURL('image/png')` and stored as a base64 string on the report. Restoring is just `drawImage` back onto a fresh canvas.
- **Service worker** — pre-caches the app shell on install, falls back to `index.html` for navigation when offline, and serves cached files before the network on every subsequent load.

---

## 📁 Project layout

```
intervention-report/
├── index.html                ← the whole app (HTML + CSS + JS)
├── manifest.json             ← PWA manifest
├── sw.js                     ← service worker
├── icons/
│   ├── icon.svg              ← source vector
│   ├── icon-maskable.svg     ← maskable variant
│   ├── icon-192.png          ← Android home screen
│   ├── icon-512.png          ← Android splash
│   ├── icon-maskable-512.png ← adaptive launcher
│   ├── apple-touch-icon.png  ← iOS home screen (180×180)
│   └── favicon-32.png        ← browser tab
├── docs/                     ← screenshots used by this README
└── .gitignore
```

---

## 🤝 Contributing

This is an internal tool for Atlas Copco service engineers. If you have suggestions or bug reports, open an issue on this repo.

When working on the form:

1. Use `lang="en-GB"` (already set) so any future native inputs respect the right format.
2. New time-table rows must call `addTimeRow(tbodyId, data)` — it wires up the auto-calculation.
3. New persistent fields must be added to `fieldMap` (for `collectFormData` / `fillForm`) and the JSON save handler.
4. Signatures should always round-trip through `collectSignatures()` / `restoreSignatures()`.
5. Test offline: open DevTools → Application → Service Workers → check **Offline**, then reload.

---

## 📄 License

Internal use, Atlas Copco. All rights reserved.

---

<p align="center">
  <sub>Built for service technicians who need a fast, offline-capable report tool that just works on any device.</sub>
</p>