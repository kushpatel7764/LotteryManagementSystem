from config_utils import load_config
import game_number_lookup_table

class ScannedCodeManagement:
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
        barcode = self.scanned_code
        if not barcode.isdigit() or len(barcode) != 29:
            return False
        
        game_num = self.get_game_num()
        ticket_price = self.get_ticket_price()
        book_amount = self.get_book_amount()

        lottery_lookup_table = game_number_lookup_table.get_lottery_net_lookup_table()
        # distinct_prices = lottery_lookup_table["Price"].unique()
        # cleaned_prices = [price.replace('$', '') for price in distinct_prices]
        for _, row in lottery_lookup_table.iterrows():
            # is valid game_number
            if row["Game No."] == game_num:
                # is valid price for gm
                if row["Price"] != ticket_price:
                    return False
            else:
                return False
        
        # book amount range {Price: min_book_amount}
        book_sizes = {
        "01": 99, "02": 99, "05": 99,
        "10": 49, "20": 49, "30": 49, "50": 49}
        
        if int(book_amount) < book_sizes[ticket_price]:
            return False
        
        return True
    
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
        
        if tick_num == "999" :
            config_file = load_config()
            descending = True if config_file["ticket_order"] == "descending" else False

            tick_num = str((int(self.get_book_amount()) - 1) if descending else 0)
            
            
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
        if ScannedCodeManagement.validate_scanned_code(self):  
            codes = {
                "game_number": self.get_game_num(),
                "book_id": self.get_book_id(),
                "ticket_number": self.get_ticket_num(),
                "ticket_price": self.get_ticket_price(),
                "book_amount": self.get_book_amount()
            }
            return codes
        else:
            return "INVALID BARCODE"