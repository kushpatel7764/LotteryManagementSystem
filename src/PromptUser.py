import UserExit
import UtilityFunctions

def ask_user_tickets(price, time):
        userInput = []
        row_num = 1
        keepGoing = True
        # Asking for user input for open tickets
        print(f"Time: {time}") #time is only "open" and "close"
        print(f"Enter ticket numbers of each ${price} ticket: ")
        while keepGoing:
            row_val  = input(f"{row_num}. ")
            #check for exit 
            if UserExit.isExit(row_val) == True:
                exit(0)
            #check for scanner input
            #if used pressed enter
            if row_val == "":
                 keepGoing = False
            else: 
                #check for scanner input
                if UtilityFunctions.is_input_from_scanner(row_val):
                     row_val = UtilityFunctions.get_ticket_num(row_val)
                userInput.append(row_val)
                row_num += 1
        #return userinput
        return userInput

def promptUser_forHelp(index, price, open_tick_num, close_tick_num):
    return input(f"Please help me calulate tickets sold for slot {index}, ${price}: {open_tick_num} - {close_tick_num} = ")

