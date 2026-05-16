"""
app.py — Flask application entry point.

Responsibilities limited to:
  - Creating and configuring the Flask app instance
  - Registering the security-header middleware
  - Defining HTTP routes (thin controllers: parse → validate → convert → respond)

Conversion logic lives in converter.py.
Validation logic lives in validator.py.
Neither of those modules imports Flask, keeping them independently testable.
"""

from flask import Flask, render_template, request, jsonify

from converter import int_to_roman, roman_to_int
from validator import validate_integer_input, validate_roman_input

app = Flask(__name__)


# ---------------------------------------------------------------------------
# Security middleware
# ---------------------------------------------------------------------------

@app.after_request
def set_security_headers(response):
    """Attach security-related HTTP headers to every outgoing response.

    Applied as an after_request hook so the headers are added uniformly
    regardless of which route produced the response, including error pages.

    Headers set:
      - X-Content-Type-Options: prevents MIME-type sniffing attacks.
      - X-Frame-Options: blocks the page from being embedded in an iframe
        (clickjacking protection).
      - X-XSS-Protection: legacy XSS filter for older browsers.
      - Referrer-Policy: limits referrer leakage on cross-origin requests.
      - Content-Security-Policy: whitelists allowed sources for scripts,
        styles, and fonts; blocks inline execution except where marked safe.
    """
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src https://fonts.gstatic.com; "
        "script-src 'self';"  # external static/app.js is served by 'self'
    )
    return response


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    """Serve the single-page converter UI."""
    return render_template("index.html")


@app.route("/convert", methods=["POST"])
def convert():
    """Handle a conversion request from the frontend.

    Accepts a POST form with:
      - mode:   "to_roman" | "to_int"
      - number: raw integer string  (required when mode == "to_roman")
      - roman:  raw Roman numeral   (required when mode == "to_int")

    Returns a JSON object:
      On success: {"result": str, "input": str, "mode": str}
      On failure: {"error": str}  with an appropriate 4xx status code.

    The route itself performs no validation or conversion — it delegates
    entirely to validator.py and converter.py, then shapes the response.
    """
    mode = request.form.get("mode", "").strip()

    if mode == "to_roman":
        raw = request.form.get("number", "").strip()
        number, err = validate_integer_input(raw)
        if err:
            return jsonify({"error": err}), 400
        return jsonify({
            "result": int_to_roman(number),
            "input":  str(number),
            "mode":   mode,
        })

    elif mode == "to_int":
        raw = request.form.get("roman", "").strip()
        roman, err = validate_roman_input(raw)
        if err:
            return jsonify({"error": err}), 400
        return jsonify({
            "result": str(roman_to_int(roman)),
            "input":  roman,
            "mode":   mode,
        })

    else:
        # Reached only if a client sends an unsupported mode value directly.
        return jsonify({"error": "Invalid conversion mode."}), 400


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # debug=False in all environments; never expose the Werkzeug debugger
    # to end users on a public-facing deployment.
    app.run(host="0.0.0.0", port=5000, debug=False)
