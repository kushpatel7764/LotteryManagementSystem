import UtilityFunctions
import PromptUser
import Calculations
import TableOutput_Management
import Manage_SaveToFile


#TODO: consider making a ticket class (low priority)

#TODO: go to previous price
#TODO: Get scanner working 
    #TODO: When user prompted for help, give vaild GameNumber as well
    #TODO: Excel Output
#TODO: Save to open from previous day's close
class MainProgram:

    """Ask for inputs like $50, $30, $20, $10, $5, $2, $1 in open and closed. Total 12 inputs"""
    
    open_Tickets = []
    close_Tickets = []
    listOfPrices = ["50", "30", "20", "10", "5", "2", "1"] 

    def setup_user_input():
        #Set open_Tickets from previous day's close nums
        previous_day_close_nums_arry = Manage_SaveToFile.ReadCloseNumFile.get_file_content_converted_to_array()
        if previous_day_close_nums_arry is None:
            print("Previous day's closing numbers are not found and so please enter today's open nubmers.")
        else:
            MainProgram.open_Tickets = previous_day_close_nums_arry

        #Get userinput and place in open and close arrays
        atPrice = 0
        time = "OPEN"
        while atPrice < 7:
            if len(MainProgram.open_Tickets) >= 7:
                time = "CLOSE"
            #Get open ticket numbers from user in string.
            userInput = PromptUser.ask_user_tickets(MainProgram.listOfPrices[atPrice], time)
            #Two types of userInput:
            #1: keyboard -> "10 20 30 40 5 2"
            #2: Scanner -> "40401746360243005080000000076\n"

            # convert to arry of int
            temp_int_arry = UtilityFunctions.string_arry_to_int_arry(userInput)

            #Place result in proper array 
            if len(MainProgram.open_Tickets) < 7:
                MainProgram.open_Tickets.append(temp_int_arry)
                atPrice += 1
                if atPrice >= 7:
                    atPrice = 0
            else: 
                MainProgram.close_Tickets.append(temp_int_arry)
                atPrice += 1
    
    def main():
        #Print Welcome Message
        print("-------------\nWelcome to Lottery Counter!\n-------------")
        print("\nEnter Tickets:")
        print("[Seperate out each ticket using space (ex. 20 21 22 23...) and place \"-\" for empty box or no ticket]\n")

        #HERE try to get info for open

        MainProgram.setup_user_input()
        

        #Calculate array of tickets sold for each price and store the array at the index of price. 
        tickets_at_price = Calculations.tickets_sold_for_each_price(MainProgram.open_Tickets, MainProgram.close_Tickets) #Sell
        #Add up all values in each array in ticket_at_price to get the total number of tickets sold at each price
        total_at_each_price = Calculations.calc_total_at_each_price(tickets_at_price) 
        #Multiply total number of tickets sold at each price to get the amount of money made at each price
        money_at_each_price = Calculations.getMoneyValue_from_tickets_sold(total_at_each_price)
        #Total every thing to get final total for the amount of money made from selling instant tickets
        total_instant_sell = Calculations.getTotal_instant_sell(money_at_each_price)



        #Convert open_Tickets, close_Tickets, sell to string
        open = []
        close = []
        sell = []
        for price in range(7):
            #convert open_Tickets
            open.append(UtilityFunctions.int_arry_to_string_arry(MainProgram.open_Tickets[price]))
            #convert close_Tickets
            close.append(UtilityFunctions.int_arry_to_string_arry(MainProgram.close_Tickets[price]))
            #convert total_at_each_price - sell_arry
            sell.append(UtilityFunctions.int_arry_to_string_arry(tickets_at_price[price]))
        
        
        table = TableOutput_Management.TableOutput(open, close, sell, total_instant_sell)
        table.Terminal_Output()

        #Ask user about the close numbers 
        save_close = input("Are all the close numbers set correctly? (Y/N) ")

        if save_close.lower() == "n":
            #TODO: allow the user to edit open and close numbers 
            return
        else:
            #save the close numbers
            print("Saving Closing numbers now...")
            closeFile = Manage_SaveToFile.SaveToCloseNumFile(MainProgram.close_Tickets)
            closeFile._save_close_nums_()
            print("Creating a Excel output file now...")
            excelFile = TableOutput_Management.ExcelOutput(open, close, sell, total_instant_sell)
            excelFile.Exel_Output()

        

        
    
  
MainProgram.main()
    
