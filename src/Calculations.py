import PromptUser
import UtilityFunctions

dict_of_Prices = {6: "1", 5: "2", 4: "5", 3: "10", 2: "20", 1: "30", 0: "50"}


def tickets_sold_for_each_price(open_Tickets, close_Tickets):
    
    arry_tickets_sold_for_each_price = []
    #Length of tickets should be same at each index for both open and close -- check this later
    for price_index in range(7): #Six input for 50, 30, 20, 10, 5, 2, 1 tickets, Loop through all the prices
        arry_of_tickets_sold_at_price = []
        #For each price iterate through open or close list to calculate subtraction, length of open or close should be same so it does not matter which one is being iterated.
        for i,open_ticket_num in enumerate(open_Tickets[price_index]):
            close_ticket_num = close_Tickets[price_index][i]
            #Subtract number from open with number from close to get how many tickets were sold
            #Work with nil 
            if open_ticket_num != "-" and close_ticket_num != "-":
                if open_ticket_num >= close_ticket_num:
                    ticket_sold = open_ticket_num - close_ticket_num
                else:
                    #Prompt user for help and store user's answer into ticket_sold
                    at_spot = find_final_table_spot_for_index(i, price_index, open_Tickets)
                    ticket_sold_string = PromptUser.promptUser_forHelp(at_spot, dict_of_Prices.get(price_index), open_ticket_num, close_ticket_num)
                    if UtilityFunctions._string_is_numerical(ticket_sold_string):                     
                        ticket_sold = int(ticket_sold_string)
                    else:
                        #TODO: Prompt user again.
                        print("Value conversion error!")
            elif open_ticket_num == "-" and close_ticket_num == "-":
                ticket_sold = 0
            elif open_ticket_num == "-":
                    #Prompt user for help and store user's answer into ticket_sold
                    at_spot = find_final_table_spot_for_index(i, price_index, open_Tickets)
                    ticket_sold_string = PromptUser.promptUser_forHelp(at_spot, dict_of_Prices.get(price_index), open_ticket_num, close_ticket_num)
                    if UtilityFunctions._string_is_numerical(ticket_sold_string):                   
                        ticket_sold = int(ticket_sold_string)
                    else:
                        #TODO: Prompt user again
                        print("Value conversion error!")
                    ticket_sold = int(ticket_sold_string)
            elif close_ticket_num == "-": 
                ticket_sold = open_ticket_num + 1
            arry_of_tickets_sold_at_price.append(ticket_sold)
        arry_tickets_sold_for_each_price.append(arry_of_tickets_sold_at_price)
    return arry_tickets_sold_for_each_price



def calc_total_at_each_price(tickets_at_price):
    toreturn = []
    #Loop through all the prices
    for i ,price in enumerate(tickets_at_price): # Value of price is no longer needed.
        priceTotal = 0 
        #Loop thorugh each price and add all the sold tickets
        for v in tickets_at_price[i]:
            priceTotal += v
        toreturn.append(priceTotal)
    return toreturn

def getMoneyValue_from_tickets_sold(ticketSold_at_each_price):
    toreturn = []
    #Loop through each price 
    #[1, 2, 3, 4, 5, 6, 7]
    for (i,v) in enumerate(ticketSold_at_each_price): #i = index, v = value
        money_at_price = v * int(dict_of_Prices[i])
        toreturn.append(money_at_price)
    return toreturn

def getTotal_instant_sell(money_at_each_price):
    sellTotal = 0
    #Loop thorugh each price and add all the sold tickets
    for v in money_at_each_price:
        sellTotal += v
    return sellTotal

def find_final_table_spot_for_index(index, price_index, open_arry):
    """
    Find the final spot that the given index will have in the table output. 
    The final spot in table depends on the price that the given index is in. For example,
    if index is in the $50 price range then just adding 1 to the index will give the final spot. However, if index is in $30 
    range then get the size of $50 array and then add to it the index + 1 to get final spot. 
    """
    
    row = 0
    for i in range(price_index + 1):#price_index + 1 is price_index that includes the exclusion by range
        if i == 0:
            final_spot = index + 1
            continue
        previous_price_length = len(open_arry[i-1])
        row = row + previous_price_length
    final_spot = final_spot + row 

    return final_spot   
    

