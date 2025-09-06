"""
Module for managing scanned lottery code information.

This module validates scanned barcodes, extracts relevant lottery ticket details,
and ensures they conform to expected formats and game rules.
"""
from pandas import DataFrame
from src import game_number_lookup_table
from src.utils.config import load_config



class ScannedCodeManagement:
    """
    Manages validation and extraction of scanned lottery barcode data.

    Attributes:
        scanned_code (str): The scanned barcode string.
        db_path (str): Path to the database.
    """
    def __init__(self, scanned_code, db_path):
        self.scanned_code = scanned_code
        self.db_path = db_path

    def validate_scanned_code(self):
        """
        Validates the scanned code:
        - Must be all digits
        - Must be exactly 29 characters
        - Checks that game number, ticket price, and book amount are within expected bounds
        """
        output = False
        barcode = self.scanned_code
        if not barcode.isdigit() or len(barcode) != 29:
            return False

        game_num = self.get_game_num()
        ticket_price = int(
            self.get_ticket_price()
        )  # Converting to int for easier comparison
        book_amount = self.get_book_amount()

        lottery_lookup_table: DataFrame = game_number_lookup_table.get_lottery_net_lookup_table()
        distinct_prices = lottery_lookup_table.get("Price").unique()
        cleaned_prices = [
            int(price.replace("$", "")) for price in distinct_prices
        ]  # because ticket_price is int
        for _, row in lottery_lookup_table.iterrows():
            # is valid game_number
            if row["Game No."] == game_num:
                rmv_dollar_sign = row["Price"].replace("$", "")
                # IS valid price for gm?
                # to check this convert both "2"'s from ticket_price and rmv_dollar_sign price
                # to int so a comparison can occur. This way we can avoid the string comparison
                # issue of "02" != "2"
                int_web_price = int(rmv_dollar_sign)
                if int_web_price == ticket_price:
                    output = True

        if ticket_price not in cleaned_prices:
            return False

        # book amount range {Price: min_book_amount}
        book_sizes = {x: 49 if x > 5 else 99 for x in cleaned_prices}
        # example output: {1: 99, 2: 99, 5: 99, 10: 49, 20: 49, 30: 49, 50: 49}

        min_book_amount = book_sizes[ticket_price]
        max_book_amount = 700

        if max_book_amount < int(book_amount) or int(
                book_amount) < min_book_amount:
            return False

        return output

    def get_game_num(self):
        """
        From "input": 35600949981000515070000000091
        game number is: 356
        """
        game_num = self.scanned_code[0:3]
        return game_num

    def get_book_id(self):
        """
        From "self.scanned_code": 35600949981000515070000000091
        book id is: 094998
        The zero between Gamenumber and BookID is being neglected.
        """
        book_id = self.scanned_code[4:10]
        return book_id

    def get_ticket_num(self):
        """
        From "self.scanned_code": 35600949981000515070000000091
        ticket number is: 100
        """
        tick_num = self.scanned_code[10:13]

        if tick_num == "999":
            config_file = load_config()
            descending = config_file["ticket_order"] == "descending"

            tick_num = str((int(self.get_book_amount()) - 1)
                           if descending else 0)

        return tick_num

    def get_ticket_price(self):
        """
        From "self.scanned_code": 35600949981000515070000000091
        ticket price is: 05
        """
        ticket_price = self.scanned_code[13:15]
        return ticket_price

    def get_book_amount(self):
        """
        From "self.scanned_code": 35600949981000515070000000091
        book amount is: 150
        """
        book_amount = self.scanned_code[15:18]
        return book_amount

    def extract_all_scanned_code(self):
        """
        Extracts all relevant data from the scanned barcode.

        Returns:
            dict | str: Dictionary of extracted values if valid,
                        otherwise "INVALID BARCODE".
        """
        if ScannedCodeManagement.validate_scanned_code(self):
            codes = {
                "game_number": self.get_game_num(),
                "book_id": self.get_book_id(),
                "ticket_number": self.get_ticket_num(),
                "ticket_price": self.get_ticket_price(),
                "book_amount": self.get_book_amount(),
            }
            return codes

        return "INVALID BARCODE"
