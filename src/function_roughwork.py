print("40401746360243005080000000076".__len__())
print("35600949981000515070000000091".__len__())

def get_game_num(input):
     """
     From "input": 35600949981000515070000000091
     game number is: 356
     """
     game_num = input[0:3]
     return game_num
 
def get_book_id(input): 
    """
     From "input": 35600949981000515070000000091
     book id is: 0094998
     shown book id is: 094998
     There is a different shown book id because in "input" the number have an zero because the shown book id starts. This 
     looks important so I am keeping the zero for book id but will not display this extra zero to the user.
     """
    book_id = input[3:10]
    return book_id
    
    
def get_ticket_num(input):
     """
     From "input": 35600949981000515070000000091
     ticket number is: 100
     """
     tick_num = input[10:13]
     return tick_num
 
    
def get_ticket_price(input):
    """
     From "input": 35600949981000515070000000091
     ticket price is: 05
     """
    ticket_price = input[13:15]
    return ticket_price

def get_book_amount(input):
    """
     From "input": 35600949981000515070000000091
     book amount is: 150
     """
    book_amount = input[15:18]
    return book_amount
    



 
"TicketName, ActivationID"