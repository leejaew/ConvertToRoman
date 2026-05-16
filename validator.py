"""
validator.py — Input validation for Roman numeral conversion requests.

Keeping validation separate from both the HTTP layer (app.py) and the
conversion logic (converter.py) means:
  - Rules live in exactly one place; changing the valid range or regex
    requires editing only this file.
  - Route handlers stay thin: parse → validate → convert → respond.
  - Validation can be unit-tested without a running Flask server.

Return convention:
  Each function returns a (value, error) tuple.
  On success:  (parsed_value, None)
  On failure:  (None, human-readable error string)
"""

import re

# ---------------------------------------------------------------------------
# Constants — single source of truth for all validation rules.
# ---------------------------------------------------------------------------

INT_MIN: int = 1
INT_MAX: int = 3999

# Maximum accepted length for a Roman numeral string before any processing.
# The longest valid Roman numeral is "MMMCCCXXXIII" (13 chars), so 15 gives
# a small buffer while still blocking obviously oversized input early.
ROMAN_MAX_LENGTH: int = 15

# Digits-only pattern used to reject floats, negatives, or other non-integer
# strings before we attempt int() conversion.
_DIGITS_ONLY: re.Pattern = re.compile(r"^\d+$")

# Structural Roman numeral validator.
# This regex enforces correct ordering and repetition rules, e.g.:
#   - "IIII" is rejected (I may not repeat more than three times)
#   - "VV"   is rejected (V may not repeat)
#   - "IIX"  is rejected (not a valid subtractive pair)
# Source pattern follows the standard grammar for numbers 1–3999.
_VALID_ROMAN: re.Pattern = re.compile(
    r"^M{0,3}(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})$",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Public validation functions
# ---------------------------------------------------------------------------

def validate_integer_input(raw: str) -> tuple[int | None, str | None]:
    """Validate and parse a raw string as a convertible integer.

    Checks in order:
      1. Non-empty
      2. Digits only (rejects floats, negatives, leading/trailing spaces
         should be stripped by the caller before passing)
      3. Within the representable Roman numeral range [INT_MIN, INT_MAX]

    Args:
        raw: The stripped string value received from the form field.

    Returns:
        (parsed_int, None) on success.
        (None, error_message) on the first failed check.
    """
    if not raw:
        return None, "Please enter a number."

    # Reject anything that isn't a plain non-negative integer string.
    # This catches floats ("3.5"), negatives ("-1"), and whitespace.
    if not _DIGITS_ONLY.match(raw):
        return None, "Only positive integers are allowed."

    number = int(raw)

    if number < INT_MIN or number > INT_MAX:
        return None, f"Number must be between {INT_MIN} and {INT_MAX}."

    return number, None


def validate_roman_input(raw: str) -> tuple[str | None, str | None]:
    """Validate a raw string as a well-formed Roman numeral.

    Checks in order:
      1. Non-empty
      2. Length within ROMAN_MAX_LENGTH (cheap early rejection)
      3. Structural validity via the full Roman numeral regex

    The regex check also implicitly ensures only valid Roman characters are
    present, so a separate character-set check is not needed.

    Args:
        raw: The stripped string value received from the form field.

    Returns:
        (uppercased_roman, None) on success.
        (None, error_message) on the first failed check.
    """
    if not raw:
        return None, "Please enter a Roman numeral."

    # Cheap length gate before running the regex.
    if len(raw) > ROMAN_MAX_LENGTH:
        return None, "Input is too long."

    normalised = raw.upper()

    # Full structural check: catches invalid characters, wrong ordering,
    # and illegal repetitions in a single pass.
    if not _VALID_ROMAN.fullmatch(normalised):
        return None, "Invalid Roman numeral. Use M, D, C, L, X, V, I with correct ordering."

    return normalised, None
