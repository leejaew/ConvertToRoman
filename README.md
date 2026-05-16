# ConvertToRoman

A minimal Flask web application that converts numbers between **integers (1–3999)** and **Roman numerals**, in both directions.

The project began as a small CLI script and was expanded into a full web app with a clean, modern UI, hardened HTTP security headers, and a layered architecture that keeps the conversion logic, validation rules, and HTTP layer cleanly separated.

---

## Features

- **Two-way conversion** — Integer → Roman and Roman → Integer in a single tabbed interface.
- **Client- and server-side validation** — instant feedback in the browser, with the server always re-validating independently.
- **Strict Content-Security-Policy** — no inline scripts, no inline event handlers, no third-party JavaScript.
- **XSS-safe rendering** — every value injected into the DOM is escaped on both sides.
- **Zero JavaScript dependencies** — vanilla JS, no build step, no bundler.
- **Production-ready** — runs under Gunicorn for deployment, Flask's dev server for local work.

---

## Project structure

```
.
├── app.py              # Flask entry point: routes + security middleware
├── converter.py        # Pure conversion logic (int_to_roman / roman_to_int)
├── validator.py        # Input validation rules (typed tuple return)
├── main.py             # Original CLI script (kept for reference)
├── static/
│   ├── app.js          # Client-side validation, fetch, UI state
│   └── style.css       # All styles
├── templates/
│   └── index.html      # Pure markup, references static assets via url_for
├── requirements.txt
├── LICENSE
└── README.md
```

`converter.py` and `validator.py` do **not** import Flask — they can be used from a CLI, a test suite, or a different web framework without modification.

---

## Getting started

### Prerequisites

- Python 3.10 or newer
- `pip`

### Install

```bash
git clone https://github.com/leejaew/ConvertToRoman.git
cd ConvertToRoman
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Run (development)

```bash
python app.py
```

Then open <http://localhost:5000>.

### Run (production)

```bash
gunicorn --bind=0.0.0.0:5000 app:app
```

---

## HTTP API

The web UI uses a single JSON endpoint that you can also call directly.

### `POST /convert`

| Field    | Required when            | Description                          |
| -------- | ------------------------ | ------------------------------------ |
| `mode`   | always                   | `"to_roman"` or `"to_int"`           |
| `number` | `mode == "to_roman"`     | Integer between 1 and 3999           |
| `roman`  | `mode == "to_int"`       | Roman numeral, max length 15         |

**Success response (`200`):**

```json
{ "result": "MMXXVI", "input": "2026", "mode": "to_roman" }
```

**Error response (`400`):**

```json
{ "error": "Number must be a whole integer between 1 and 3999." }
```

### Examples

```bash
# Integer → Roman
curl -X POST http://localhost:5000/convert \
     -d "mode=to_roman&number=1994"
# → {"input":"1994","mode":"to_roman","result":"MCMXCIV"}

# Roman → Integer
curl -X POST http://localhost:5000/convert \
     -d "mode=to_int&roman=MCMXCIV"
# → {"input":"MCMXCIV","mode":"to_int","result":"1994"}
```

---

## Conversion rules

- Integer range: **1 – 3999** (standard Roman numerals do not represent 0, negatives, or values ≥ 4000).
- Accepted Roman characters: `M`, `D`, `C`, `L`, `X`, `V`, `I` (case-insensitive on input; normalised internally).
- Subtractive notation is enforced (`IV`, `IX`, `XL`, `XC`, `CD`, `CM`); invalid forms such as `IIII` or `VV` are rejected.

---

## Security

Every response sets the following headers:

| Header                      | Value                                                            |
| --------------------------- | ---------------------------------------------------------------- |
| `Content-Security-Policy`   | `default-src 'self'; script-src 'self'; …` (no inline scripts)   |
| `X-Content-Type-Options`    | `nosniff`                                                        |
| `X-Frame-Options`           | `DENY`                                                           |
| `X-XSS-Protection`          | `1; mode=block`                                                  |
| `Referrer-Policy`           | `strict-origin-when-cross-origin`                                |

All event handlers are bound via `addEventListener` in `static/app.js` — no `onclick=` / `onsubmit=` attributes exist in the markup, so the strict CSP can be enforced.

---

## License

Released under the [MIT License](./LICENSE).
