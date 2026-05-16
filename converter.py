"""
converter.py — Pure Roman numeral conversion logic.

This module is intentionally free of any framework dependency so it can be
imported, tested, or reused in isolation (CLI, API, background job, etc.)
without pulling in Flask or any HTTP context.
"""

# ---------------------------------------------------------------------------
# Lookup tables — defined once at module level, never rebuilt at call time.
# ---------------------------------------------------------------------------

# Ordered from largest to smallest so the greedy subtraction in int_to_roman
# works correctly in a single pass.
_INT_TO_ROMAN_TABLE: list[tuple[int, str]] = [
    (1000, "M"), (900, "CM"), (500, "D"), (400, "CD"),
    (100,  "C"), (90,  "XC"), (50,  "L"), (40,  "XL"),
    (10,   "X"), (9,   "IX"), (5,   "V"), (4,   "IV"),
    (1,    "I"),
]

# Single-character lookup used by the subtractive roman_to_int algorithm.
# Only the seven base symbols are needed; two-character combos (IV, IX, etc.)
# are resolved implicitly by the right-to-left traversal logic.
_ROMAN_CHAR_VALUES: dict[str, int] = {
    "M": 1000, "D": 500, "C": 100,
    "L": 50,   "X": 10,  "V": 5,
    "I": 1,
}


# ---------------------------------------------------------------------------
# Public conversion functions
# ---------------------------------------------------------------------------

def int_to_roman(number: int) -> str:
    """Convert a positive integer to its Roman numeral string representation.

    Uses a greedy subtraction approach: iterate the lookup table from largest
    to smallest value, appending the matching symbol and reducing the number
    until it reaches zero.

    Args:
        number: A positive integer in the range 1–3999. The caller is
                responsible for range validation before calling this function.

    Returns:
        The Roman numeral string, e.g. int_to_roman(2024) -> "MMXXIV".
    """
    result = ""
    for value, numeral in _INT_TO_ROMAN_TABLE:
        # While the remaining number can absorb this value, keep subtracting
        # and appending the corresponding symbol.
        while number >= value:
            result += numeral
            number -= value
    return result


def roman_to_int(roman: str) -> int:
    """Convert a Roman numeral string to its integer value.

    Uses a right-to-left subtractive algorithm: when a character's value is
    less than the value of the character to its right, it is subtracted rather
    than added. This handles all two-character combos (IV, IX, XL, etc.)
    without an explicit lookup table for each pair.

    Args:
        roman: An uppercase Roman numeral string that has already been
               validated by the caller. Behaviour is undefined for invalid
               input — always validate first.

    Returns:
        The integer value, e.g. roman_to_int("MMXXIV") -> 2024.
    """
    total = 0
    prev_value = 0  # tracks the value of the character to the right

    for char in reversed(roman.upper()):
        curr_value = _ROMAN_CHAR_VALUES[char]

        # Subtractive rule: if this symbol is smaller than the one after it
        # (e.g. 'I' before 'V' in "IV"), subtract instead of add.
        if curr_value < prev_value:
            total -= curr_value
        else:
            total += curr_value

        prev_value = curr_value

    return total
