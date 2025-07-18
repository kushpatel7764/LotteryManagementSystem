from config_utils import load_config

class ScannedCodeManagement:
    def __init__(self, scanned_code):
        self.scanned_code = scanned_code
    
    def validate_scanned_code(self):
        pass
    
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

            tick_num = (int(self.get_book_amount()) - 1) if descending else 0
            
            
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
            
        
