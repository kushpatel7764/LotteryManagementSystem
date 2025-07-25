import datetime
import generate_invoice
print("40401746360243005080000000076".__len__())
print("35600949981000515070000000091".__len__())
 
"TicketName, ActivationID"

# print(datetime.date.today().strftime("%d/%m/%Y"))
print(datetime.datetime.now(datetime.timezone.utc).time().strftime("%H:%M:%S"))

from config_utils import load_config
import game_number_lookup_table

def validate_scanned_code(game_num, ticket_price, book_amount):
    """
    Validates the scanned code:
    - Must be all digits
    - Must be exactly 29 characters
    - Checks that game number, ticket price, and book amount are within expected bounds
    """
    output = False
    lottery_lookup_table = game_number_lookup_table.get_lottery_net_lookup_table()
    distinct_prices = lottery_lookup_table["Price"].unique()
    cleaned_prices = [int(price.replace('$', '')) for price in distinct_prices] # because ticket_price is int
    for _, row in lottery_lookup_table.iterrows():
        # is valid game_number
        if row["Game No."] == game_num:
            rmv_dollar_sign = row["Price"].replace('$', '')
            # check if it is valid price for gm
            # to do this convert two ticket_price and rmv_dollar_sign price from the lottery website to int so easy comparision.
            # This way we can avoid the string comparison issue of "02" != "2"
            int_web_price = int(rmv_dollar_sign)
            if int_web_price == ticket_price:
                output = True
    
    if not (ticket_price in cleaned_prices):
            return False
    
    # book amount range {Price: min_book_amount}
    book_sizes = {
    1: 99, 2: 99, 5: 99,
    10: 49, 20: 49, 30: 49, 50: 49}
    
    if int(book_amount) < book_sizes[ticket_price]:
        return False
    
    return output
# 48100232220130220040000000055
# 49700077611480515060000000090

#print(validate_scanned_code("481", 2, "150"))
cleaned_prices = [1,2,5,10,20,30,50]

book_sizes = {x: 49 if x > 5 else 99 for x in cleaned_prices}
print(book_sizes)
