"""
Tests for ScannedCodeManagement — barcode parsing and validation.

This module was previously completely untested.  It covers:
- validate_scanned_code: length, digit, game, price, book-amount checks
- get_game_num / get_book_id / get_ticket_num / get_ticket_price / get_book_amount
- extract_all_scanned_code: full round-trip from raw barcode to dict
- Edge cases: ticket 999 (sold-out sentinel), boundary book amounts, invalid combos
"""

from unittest.mock import patch

import pandas as pd

from lottery_app.scanned_code_information_management import ScannedCodeManagement


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

# Reference barcode (29 digits):
#   356  0  094998  100  05  150  70000000091
#   gam  _  bookid  tkn  pr  amt  padding
VALID_BARCODE = "35600949981000515070000000091"
# breakdown: game=356, book=094998, ticket=100, price=05(->5), amount=150

assert len(VALID_BARCODE) == 29
assert VALID_BARCODE.isdigit()


def _make_lookup(game_no: str, price_str: str) -> pd.DataFrame:
    """Return a minimal DataFrame that mimics get_lottery_net_lookup_table()."""
    return pd.DataFrame([{"Game No.": game_no, "Price": price_str}])


def _patched_scm(barcode: str, game_no: str = "356", price_str: str = "$5"):
    """
    Build a ScannedCodeManagement with get_lottery_net_lookup_table mocked.
    """
    scm = ScannedCodeManagement(scanned_code=barcode, db_path=":memory:")
    return scm, _make_lookup(game_no, price_str)


# ---------------------------------------------------------------------------
# validate_scanned_code — length and digit checks
# ---------------------------------------------------------------------------


class TestValidateLengthAndDigits:
    """Tests for barcode length and digit validation."""

    def test_valid_barcode_returns_true(self):
        """A well-formed barcode for a known game + price validates successfully."""
        scm, df = _patched_scm(VALID_BARCODE)
        with patch(
            "lottery_app.scanned_code_information_management"
            ".game_number_lookup_table.get_lottery_net_lookup_table",
            return_value=df,
        ):
            assert scm.validate_scanned_code() is True

    def test_too_short_barcode_fails(self):
        """A barcode shorter than 29 characters is immediately invalid."""
        short = "3560094998100051507000000009"  # 28 chars
        assert len(short) == 28
        scm = ScannedCodeManagement(short, ":memory:")
        with patch(
            "lottery_app.scanned_code_information_management"
            ".game_number_lookup_table.get_lottery_net_lookup_table"
        ):
            assert scm.validate_scanned_code() is False

    def test_too_long_barcode_fails(self):
        """A barcode longer than 29 characters is immediately invalid."""
        long_bc = VALID_BARCODE + "0"  # 30 chars
        scm = ScannedCodeManagement(long_bc, ":memory:")
        with patch(
            "lottery_app.scanned_code_information_management"
            ".game_number_lookup_table.get_lottery_net_lookup_table"
        ):
            assert scm.validate_scanned_code() is False

    def test_empty_barcode_fails(self):
        """An empty string is not a valid barcode."""
        scm = ScannedCodeManagement("", ":memory:")
        with patch(
            "lottery_app.scanned_code_information_management"
            ".game_number_lookup_table.get_lottery_net_lookup_table"
        ):
            assert scm.validate_scanned_code() is False

    def test_letters_in_barcode_fail(self):
        """A barcode containing letters fails the all-digit check."""
        bad = "35600ABCDE1000515070000000091"
        assert len(bad) == 29
        scm = ScannedCodeManagement(bad, ":memory:")
        with patch(
            "lottery_app.scanned_code_information_management"
            ".game_number_lookup_table.get_lottery_net_lookup_table"
        ):
            assert scm.validate_scanned_code() is False

    def test_special_chars_in_barcode_fail(self):
        """Special characters cause immediate validation failure."""
        bad = "356!0949981000515070000000091"
        assert len(bad) == 29
        scm = ScannedCodeManagement(bad, ":memory:")
        with patch(
            "lottery_app.scanned_code_information_management"
            ".game_number_lookup_table.get_lottery_net_lookup_table"
        ):
            assert scm.validate_scanned_code() is False

    def test_spaces_in_barcode_fail(self):
        """Spaces are not digits and must fail validation."""
        bad = "356 0949981000515070000000091"
        assert len(bad) == 29
        scm = ScannedCodeManagement(bad, ":memory:")
        with patch(
            "lottery_app.scanned_code_information_management"
            ".game_number_lookup_table.get_lottery_net_lookup_table"
        ):
            assert scm.validate_scanned_code() is False


# ---------------------------------------------------------------------------
# validate_scanned_code — game number and price validation
# ---------------------------------------------------------------------------


class TestValidateGameAndPrice:
    """Tests for game number and price validation."""

    def test_unknown_game_number_fails(self):
        """A game number not in the lookup table must fail validation."""
        scm, df = _patched_scm(VALID_BARCODE, game_no="999", price_str="$5")
        # VALID_BARCODE has game "356"; lookup only knows "999"
        with patch(
            "lottery_app.scanned_code_information_management"
            ".game_number_lookup_table.get_lottery_net_lookup_table",
            return_value=df,
        ):
            assert scm.validate_scanned_code() is False

    def test_price_mismatch_for_game_fails(self):
        """
        If the lookup says the game costs $10 but the barcode encodes $5,
        validation must fail.
        """
        # Build a barcode where price field = 05 (=$5)
        scm, df = _patched_scm(VALID_BARCODE, game_no="356", price_str="$10")
        with patch(
            "lottery_app.scanned_code_information_management"
            ".game_number_lookup_table.get_lottery_net_lookup_table",
            return_value=df,
        ):
            assert scm.validate_scanned_code() is False

    def test_price_not_in_cleaned_prices_fails(self):
        """
        Even if the game matches, the ticket price must be one of the distinct
        prices in the lookup table.
        """
        # Lookup only has $5; barcode encodes $7 (not a standard price)
        barcode = "35600949981000715070000000091"  # price=07
        assert len(barcode) == 29
        df = _make_lookup("356", "$5")
        scm = ScannedCodeManagement(barcode, ":memory:")
        with patch(
            "lottery_app.scanned_code_information_management"
            ".game_number_lookup_table.get_lottery_net_lookup_table",
            return_value=df,
        ):
            assert scm.validate_scanned_code() is False

    def test_multiple_games_correct_match(self):
        """
        A lookup table with multiple games; the barcode must match the right one.
        """
        df = pd.DataFrame([
            {"Game No.": "356", "Price": "$5"},
            {"Game No.": "100", "Price": "$10"},
        ])
        scm = ScannedCodeManagement(VALID_BARCODE, ":memory:")
        with patch(
            "lottery_app.scanned_code_information_management"
            ".game_number_lookup_table.get_lottery_net_lookup_table",
            return_value=df,
        ):
            assert scm.validate_scanned_code() is True


# ---------------------------------------------------------------------------
# validate_scanned_code — book amount bounds
# ---------------------------------------------------------------------------


class TestValidateBookAmount:
    """
    Ticket price determines minimum book size:
      - price <= $5  → min 99
      - price > $5   → min 49
    Maximum is always 700.
    """

    def _barcode_with_amount(self, amount_str: str) -> str:
        """
        Build a 29-digit barcode where book_amount = amount_str (3 digits).
        Uses game=356, price=05 ($5), book=094998.
        """
        # Format: 356 0 094998 100 05 AMT PADDING
        # Indices: 0-2  3  4-9  10-12 13-14 15-17 18-28
        padding = "0" * (29 - 3 - 1 - 6 - 3 - 2 - 3)
        barcode = f"35600949981000 5{amount_str}{padding}"
        barcode = barcode.replace(" ", "0")
        return barcode

    def _validate_with_amount(self, amount_str: str) -> bool:
        df = _make_lookup("356", "$5")
        # Barcode layout (29 chars):
        #   gam(3) + sep(1) + book(6) + ticket(3) + price(2) + amount(3) + pad(11)
        # "356" + "0" + "094998" + "100" + "05" + amount + "00000000000"
        barcode = f"3560094998100{5:02d}{amount_str}00000000000"
        assert len(barcode) == 29, f"len={len(barcode)}"
        scm = ScannedCodeManagement(barcode, ":memory:")
        with patch(
            "lottery_app.scanned_code_information_management"
            ".game_number_lookup_table.get_lottery_net_lookup_table",
            return_value=df,
        ):
            return scm.validate_scanned_code()

    def test_minimum_book_amount_for_low_price(self):
        """For $5 tickets (price ≤ 5) the minimum book amount is 99."""
        assert self._validate_with_amount("099") is True

    def test_below_minimum_book_amount_fails(self):
        """A book amount below 99 (for $5 tickets) must fail."""
        assert self._validate_with_amount("098") is False

    def test_maximum_book_amount_700(self):
        """A book amount of exactly 700 must pass."""
        assert self._validate_with_amount("700") is True

    def test_above_maximum_book_amount_fails(self):
        """A book amount above 700 must fail."""
        assert self._validate_with_amount("701") is False

    def test_minimum_for_high_price_ticket(self):
        """For tickets costing > $5, the minimum book amount is 49."""
        df = pd.DataFrame([
            {"Game No.": "100", "Price": "$10"},
            {"Game No.": "356", "Price": "$5"},
        ])
        # game=100, price=10, amount=049
        # gam(3)+sep(1)+book(6)+ticket(3)+price(2)+amount(3)+pad(11) = 29
        barcode = "1000094998100" + "10" + "049" + "00000000000"
        assert len(barcode) == 29
        scm = ScannedCodeManagement(barcode, ":memory:")
        with patch(
            "lottery_app.scanned_code_information_management"
            ".game_number_lookup_table.get_lottery_net_lookup_table",
            return_value=df,
        ):
            assert scm.validate_scanned_code() is True

    def test_below_minimum_for_high_price_ticket_fails(self):
        """A book amount of 48 for a > $5 ticket must fail."""
        df = pd.DataFrame([
            {"Game No.": "100", "Price": "$10"},
            {"Game No.": "356", "Price": "$5"},
        ])
        barcode = "1000094998100" + "10" + "048" + "00000000000"
        assert len(barcode) == 29
        scm = ScannedCodeManagement(barcode, ":memory:")
        with patch(
            "lottery_app.scanned_code_information_management"
            ".game_number_lookup_table.get_lottery_net_lookup_table",
            return_value=df,
        ):
            assert scm.validate_scanned_code() is False


# ---------------------------------------------------------------------------
# Field extraction methods
# ---------------------------------------------------------------------------


class TestFieldExtraction:
    """Unit tests for each slice-based extraction method."""

    def _scm(self):
        return ScannedCodeManagement(VALID_BARCODE, ":memory:")

    def test_get_game_num(self):
        """game_num is the first 3 characters."""
        assert self._scm().get_game_num() == "356"

    def test_get_book_id(self):
        """book_id is characters 4–9 (skipping position 3)."""
        assert self._scm().get_book_id() == "094998"

    def test_get_ticket_num_normal(self):
        """Normal ticket number is characters 10–12."""
        assert self._scm().get_ticket_num() == "100"

    def test_get_ticket_price(self):
        """Ticket price is characters 13–14."""
        assert self._scm().get_ticket_price() == "05"

    def test_get_book_amount(self):
        """Book amount is characters 15–17."""
        assert self._scm().get_book_amount() == "150"

    def test_ticket_num_999_sentinel_ascending(self):
        """
        Ticket number 999 is a sentinel meaning 'first ticket'.
        In ascending mode the real ticket number is 0.
        """
        # Build barcode with ticket field = 999
        # gam(3)+sep(1)+book(6)+ticket(3)+price(2)+amount(3)+pad(11) = 29
        barcode = "3560094998999" + "05" + "150" + "00000000000"
        assert len(barcode) == 29
        scm = ScannedCodeManagement(barcode, ":memory:")
        with patch(
            "lottery_app.scanned_code_information_management.load_config",
            return_value={"ticket_order": "ascending"},
        ):
            assert scm.get_ticket_num() == "0"

    def test_ticket_num_999_sentinel_descending(self):
        """
        In descending mode, ticket 999 maps to book_amount - 1.
        For amount=150, the result should be '149'.
        """
        barcode = "3560094998999" + "05" + "150" + "00000000000"
        assert len(barcode) == 29
        scm = ScannedCodeManagement(barcode, ":memory:")
        with patch(
            "lottery_app.scanned_code_information_management.load_config",
            return_value={"ticket_order": "descending"},
        ):
            assert scm.get_ticket_num() == "149"

    def test_all_zeros_barcode_fields(self):
        """A valid all-zero barcode's fields can be extracted without error."""
        barcode = "0" * 29
        scm = ScannedCodeManagement(barcode, ":memory:")
        assert scm.get_game_num() == "000"
        assert scm.get_book_id() == "000000"
        assert scm.get_book_amount() == "000"


# ---------------------------------------------------------------------------
# extract_all_scanned_code — full round trip
# ---------------------------------------------------------------------------


class TestExtractAllScannedCode:
    """Tests for full barcode extraction round-trip."""

    def test_valid_barcode_returns_dict(self):
        """A valid barcode returns a dict with all five expected keys."""
        scm, df = _patched_scm(VALID_BARCODE)
        with patch(
            "lottery_app.scanned_code_information_management"
            ".game_number_lookup_table.get_lottery_net_lookup_table",
            return_value=df,
        ):
            result = scm.extract_all_scanned_code()

        assert isinstance(result, dict)
        assert set(result.keys()) == {
            "game_number",
            "book_id",
            "ticket_number",
            "ticket_price",
            "book_amount",
        }

    def test_valid_barcode_values_correct(self):
        """The extracted values match the known barcode."""
        scm, df = _patched_scm(VALID_BARCODE)
        with patch(
            "lottery_app.scanned_code_information_management"
            ".game_number_lookup_table.get_lottery_net_lookup_table",
            return_value=df,
        ):
            result = scm.extract_all_scanned_code()

        assert result["game_number"] == "356"
        assert result["book_id"] == "094998"
        assert result["ticket_number"] == "100"
        assert result["ticket_price"] == "05"
        assert result["book_amount"] == "150"

    def test_invalid_barcode_returns_sentinel_string(self):
        """An invalid barcode returns the string 'INVALID BARCODE'."""
        scm = ScannedCodeManagement("TOOSHORT", ":memory:")
        with patch(
            "lottery_app.scanned_code_information_management"
            ".game_number_lookup_table.get_lottery_net_lookup_table",
            return_value=_make_lookup("356", "$5"),
        ):
            result = scm.extract_all_scanned_code()

        assert result == "INVALID BARCODE"

    def test_invalid_game_returns_sentinel(self):
        """An otherwise-valid barcode with a wrong game number returns INVALID BARCODE."""
        scm, df = _patched_scm(VALID_BARCODE, game_no="999", price_str="$5")
        with patch(
            "lottery_app.scanned_code_information_management"
            ".game_number_lookup_table.get_lottery_net_lookup_table",
            return_value=df,
        ):
            result = scm.extract_all_scanned_code()

        assert result == "INVALID BARCODE"

    def test_extract_idempotent(self):
        """Calling extract_all_scanned_code twice returns the same result."""
        scm, df = _patched_scm(VALID_BARCODE)
        with patch(
            "lottery_app.scanned_code_information_management"
            ".game_number_lookup_table.get_lottery_net_lookup_table",
            return_value=df,
        ):
            r1 = scm.extract_all_scanned_code()
            r2 = scm.extract_all_scanned_code()

        assert r1 == r2

    def test_inject_sql_in_barcode_fails_length_check(self):
        """
        A barcode containing SQL injection characters fails the digit/length
        check before any database interaction.
        """
        # Non-digit characters fail isdigit() immediately regardless of length
        sql_payload = "' OR 1=1 -- padding_to_maybe_29_chars_xxx"
        scm = ScannedCodeManagement(sql_payload, ":memory:")
        with patch(
            "lottery_app.scanned_code_information_management"
            ".game_number_lookup_table.get_lottery_net_lookup_table",
            return_value=_make_lookup("356", "$5"),
        ):
            result = scm.extract_all_scanned_code()
        assert result == "INVALID BARCODE"

    def test_all_nines_barcode(self):
        """A 29-digit barcode of all 9s undergoes full validation without crashing."""
        barcode = "9" * 29
        scm = ScannedCodeManagement(barcode, ":memory:")
        # Game "999", price 99 — unlikely to be valid, but must not crash
        df = _make_lookup("999", "$99")
        with patch(
            "lottery_app.scanned_code_information_management"
            ".game_number_lookup_table.get_lottery_net_lookup_table",
            return_value=df,
        ):
            result = scm.extract_all_scanned_code()
        # Result is either a dict (valid) or the sentinel (invalid)
        assert result == "INVALID BARCODE" or isinstance(result, dict)
