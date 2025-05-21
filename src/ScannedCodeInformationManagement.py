class ScannedCodeManagement:
    def __init__(self, scanned_code):
        self.scanned_code = scanned_code
    
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
        book id is: 0094998
        shown book id is: 094998
        There is a different shown book id because in "input" the number have an zero because the shown book id starts. This 
        looks important so I am keeping the zero for book id but will not display this extra zero to the user.
        """
        book_id = self.scanned_code[3:10]
        return book_id
        
        
    def get_ticket_num(self):
        """
        From "self.scanned_code": 35600949981000515070000000091
        ticket number is: 100
        """
        tick_num = self.scanned_code[10:13]
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
            
        
