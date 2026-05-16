/**
 * app.js — Client-side logic for the Roman Numeral Converter.
 *
 * Structure:
 *   1. DOM helpers        — thin wrappers around repetitive DOM operations
 *   2. HTML escaping      — XSS-safe text insertion
 *   3. UI state           — result-box rendering (success / error)
 *   4. Mode validators    — client-side input checks per conversion mode
 *   5. API client         — single fetch wrapper for /convert
 *   6. Event handlers     — tab switching, reference toggle, form submit
 *   7. Initialisation     — wires up listeners once the DOM is ready
 *
 * Design notes:
 *   - No external libraries. The app is simple enough that vanilla JS is
 *     cleaner and faster to load than any framework.
 *   - Client-side validation mirrors server-side rules (validator.py) to
 *     give instant feedback without a round trip. The server always
 *     re-validates independently — the client check is a UX convenience only.
 *   - All user-supplied strings rendered into the DOM go through escapeHtml
 *     to prevent XSS even though the server only returns safe values.
 */

"use strict";

/* ── 1. DOM helpers ────────────────────────────────────────────────────── */

/**
 * Shorthand for document.getElementById. Reduces noise in handlers.
 * @param {string} id
 * @returns {HTMLElement}
 */
function byId(id) {
  return document.getElementById(id);
}

/* ── 2. HTML escaping ──────────────────────────────────────────────────── */

/**
 * Escape a value before inserting it into innerHTML.
 *
 * Used as a last-resort safeguard when building HTML strings manually.
 * Prefer textContent for plain text nodes — only use innerHTML when
 * you need to compose multiple tagged elements in one assignment.
 *
 * @param {*} value — any value; will be coerced to string first.
 * @returns {string} HTML-safe string.
 */
function escapeHtml(value) {
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

/* ── 3. UI state ───────────────────────────────────────────────────────── */

/**
 * Render an error message into the result box.
 *
 * Replaces any existing result (success or error) so the box always
 * reflects the most recent attempt.
 *
 * @param {HTMLElement} box   — the .result-box element.
 * @param {string}      msg   — human-readable error text.
 */
function showError(box, msg) {
  box.className = "result-box show error-state";
  // Build with innerHTML so we can inject the class; message is escaped.
  box.innerHTML = '<p class="error-msg">' + escapeHtml(msg) + "</p>";
}

/**
 * Render a successful conversion result into the result box.
 *
 * @param {HTMLElement} box    — the .result-box element.
 * @param {string}      result — the converted value (Roman or integer).
 * @param {string}      mode   — "to_roman" | "to_int", used to label output.
 */
function showSuccess(box, result, mode) {
  const label = mode === "to_roman" ? "Roman numeral" : "Integer";
  box.className = "result-box show success";
  box.innerHTML =
    '<div class="result-label">' + escapeHtml(label) + "</div>" +
    '<div class="result-value">' + escapeHtml(result) + "</div>";
}

/**
 * Hide the result box and clear its content.
 * Called when the user starts editing the input after a previous attempt.
 *
 * @param {HTMLElement} box — the .result-box element.
 */
function clearResult(box) {
  box.className = "result-box"; // removes "show", hides the element
  box.innerHTML = "";
}

/* ── 4. Mode validators ────────────────────────────────────────────────── */

/**
 * Client-side rules for the Integer → Roman mode.
 *
 * Mirrors validate_integer_input() in validator.py.
 * Returns null on success, or an error string on failure.
 *
 * @param {string} raw — trimmed value from the number input.
 * @returns {string|null}
 */
function validateIntegerInput(raw) {
  if (!raw) return "Please enter a number.";

  const num = Number(raw);
  // Number() returns NaN for non-numeric strings; isInteger rejects floats.
  if (!Number.isInteger(num) || num < 1 || num > 3999) {
    return "Number must be a whole integer between 1 and 3999.";
  }

  return null; // valid
}

/**
 * Client-side rules for the Roman → Integer mode.
 *
 * Mirrors validate_roman_input() in validator.py.
 * Returns null on success, or an error string on failure.
 *
 * @param {string} raw — trimmed value from the Roman numeral input.
 * @returns {string|null}
 */
function validateRomanInput(raw) {
  if (!raw) return "Please enter a Roman numeral.";

  if (raw.length > 15) return "Input is too long.";

  // Character-set pre-check gives a more specific error than the full regex.
  if (!/^[MDCLXVImdclxvi]+$/.test(raw)) {
    return "Only M, D, C, L, X, V, I characters are allowed.";
  }

  return null; // valid — full structural check happens server-side
}

/* ── 5. API client ─────────────────────────────────────────────────────── */

/**
 * POST a conversion request to /convert and return the parsed JSON response.
 *
 * Centralising the fetch call means any future changes to the endpoint
 * (auth headers, base-URL config, retry logic) happen in one place.
 *
 * @param {"to_roman"|"to_int"} mode
 * @param {string} fieldName  — the form field key ("number" or "roman")
 * @param {string} value      — the raw input value
 * @returns {Promise<{ok: boolean, data: object}>}
 */
async function postConvert(mode, fieldName, value) {
  const body = new FormData();
  body.append("mode", mode);
  body.append(fieldName, value);

  const response = await fetch("/convert", { method: "POST", body });
  const data     = await response.json();

  // Normalise the response shape so callers don't inspect status codes.
  return { ok: response.ok && !data.error, data };
}

/* ── 6. Event handlers ─────────────────────────────────────────────────── */

/**
 * Switch the visible tab and its associated panel.
 *
 * Reads the target panel id from the clicked button's data-target attribute
 * so no hard-coded IDs live in the JS — adding a new tab only requires
 * updating the HTML.
 *
 * @param {HTMLButtonElement} btn — the tab button that was clicked.
 */
function switchTab(btn) {
  // Deactivate all tabs and hide all panels first.
  document.querySelectorAll(".tab").forEach(t => {
    t.classList.remove("active");
    t.setAttribute("aria-selected", "false");
  });
  document.querySelectorAll(".panel").forEach(p => {
    p.classList.remove("active");
  });

  // Activate the clicked tab and its corresponding panel.
  btn.classList.add("active");
  btn.setAttribute("aria-selected", "true");
  byId(btn.dataset.target).classList.add("active");
}

/**
 * Toggle the quick-reference table open/closed.
 *
 * @param {HTMLButtonElement} btn — the toggle button element.
 */
function toggleReference(btn) {
  const table = byId("ref-table");
  const isOpen = table.classList.toggle("open");
  btn.setAttribute("aria-expanded", String(isOpen));
  // Keep aria-hidden in sync so screen readers skip the table when closed.
  table.setAttribute("aria-hidden", String(!isOpen));
  // Update the indicator arrow to reflect the new state.
  btn.querySelector(".ref-arrow").textContent = isOpen ? "▲" : "▼";
}

/**
 * Handle form submission for both conversion modes.
 *
 * Flow:
 *   1. Run client-side validation — show error and abort if invalid.
 *   2. Disable the button and send the request.
 *   3. Display the result or an error from the server response.
 *   4. Re-enable the button in the finally block (always runs).
 *
 * The mode is read from the form's data-mode attribute, so a single
 * delegated submit listener can serve both forms.
 *
 * @param {SubmitEvent}            event
 * @param {"to_roman"|"to_int"}    mode
 */
async function handleSubmit(event, mode) {
  event.preventDefault();

  // Resolve the relevant elements for this mode.
  const isToRoman  = mode === "to_roman";
  const inputEl    = byId(isToRoman ? "input-number" : "input-roman");
  const resultBox  = byId(isToRoman ? "result-to-roman" : "result-to-int");
  const btn        = byId(isToRoman ? "btn-to-roman" : "btn-to-int");
  const fieldName  = isToRoman ? "number" : "roman";
  const rawValue   = inputEl.value.trim();

  // Client-side validation — fast path before network round trip.
  const clientError = isToRoman
    ? validateIntegerInput(rawValue)
    : validateRomanInput(rawValue);

  if (clientError) {
    showError(resultBox, clientError);
    inputEl.classList.add("invalid");
    inputEl.focus();
    return;
  }

  // Optimistic UI: disable button to prevent duplicate submissions.
  btn.disabled    = true;
  btn.textContent = "Converting…";

  try {
    const { ok, data } = await postConvert(mode, fieldName, rawValue);

    if (!ok) {
      showError(resultBox, data.error || "An unexpected error occurred.");
      inputEl.classList.add("invalid");
    } else {
      showSuccess(resultBox, data.result, mode);
      inputEl.classList.remove("invalid");
    }
  } catch {
    // Network failure or JSON parse error.
    showError(resultBox, "Network error. Please try again.");
  } finally {
    // Always restore the button regardless of outcome.
    btn.disabled    = false;
    btn.textContent = "Convert";
  }
}

/* ── 7. Initialisation ─────────────────────────────────────────────────── */

/**
 * Wire up all event listeners once the DOM is fully parsed.
 *
 * All bindings live here because the Content-Security-Policy header
 * (script-src 'self') forbids inline onclick / onsubmit attributes —
 * inline handlers are silently blocked by the browser. Centralising the
 * wiring also keeps the markup pure structure.
 *
 * Wires up:
 *   - Tab buttons               → switchTab
 *   - Both conversion forms     → handleSubmit (mode from data-mode)
 *   - Quick-reference toggle    → toggleReference
 *   - Input "clear on edit"     → hides stale result the moment the user
 *                                 starts typing again
 */
document.addEventListener("DOMContentLoaded", () => {
  // Tab buttons — delegated by class so adding a tab needs no JS change.
  document.querySelectorAll(".tab").forEach(tab => {
    tab.addEventListener("click", () => switchTab(tab));
  });

  // Both conversion forms — mode is read from the form's data-mode attr.
  document.querySelectorAll("form[data-mode]").forEach(form => {
    form.addEventListener("submit", event => {
      handleSubmit(event, form.dataset.mode);
    });
  });

  // Quick-reference open/close toggle.
  const refToggle = byId("reference-toggle");
  if (refToggle) {
    refToggle.addEventListener("click", () => toggleReference(refToggle));
  }

  // Clear-on-edit: stale result vanishes the moment the user edits the input.
  const pairs = [
    { inputId: "input-number", resultId: "result-to-roman" },
    { inputId: "input-roman",  resultId: "result-to-int"   },
  ];

  pairs.forEach(({ inputId, resultId }) => {
    const input  = byId(inputId);
    const result = byId(resultId);

    input.addEventListener("input", () => {
      input.classList.remove("invalid");
      clearResult(result);
    });
  });
});
