import datetime

def _string_is_numerical(in_string):
        """ 
        returns True if the incoming parameter can be converted to float (i.e. is a number)
        returns False otherwise - checks for TypeError and ValueError on incoming value
        """  

        try:
            float(in_string)
            return True
        except TypeError:
            return False
        except ValueError:
            return False
        
def string_arry_to_int_arry(str_arry):
        """
        This function requires that open_Tickets and close_Tickets be an array with an array of strings inside.
        string_arry_to_int_arry will given array of str to array of int. 
        """
        to_return = []
        for v in str_arry:
            if v.isdigit():
                to_return.append(int(v))
            elif v == "-":
                to_return.append(v)
            else:
                print("Invalid character detected. Quitting the program now...")
                exit(0)
        return to_return

def int_arry_to_string_arry(int_arry):
        to_return = []
        for digit in int_arry:
            to_return.append(str(digit))
        return to_return



def file_string_to_array(userInput):
    """
    Converts given str to array. 

    Requirement: the string to be converted should be seperated by space. Each element of the array will be determind by spacing. 
    Addtionally each row will be a array of its own 

    Example Input:
    1 2 3 4 5 
    2 3 4 5

    output:
    [["1", "2", "3", "4", "5"]["2", "3", "4", "5"]]

    """
    #strip() - will remove leading and trailing white spaces
    toreturn = []
    temp_string = userInput.strip()
    temp_string_price_arry = temp_string.split("\n")
    for close_num_price in temp_string_price_arry:
        stripped_close_num_price = close_num_price.strip()
        temp_array = stripped_close_num_price.split(" ")
        toreturn.append(temp_array)
    
    return toreturn 

def file_string_arry_to_int_arry(str_arry):
        """
        This function requires that open_Tickets and close_Tickets be an array with an array of strings inside.
        string_arry_to_int_arry will given array of str to array of int. 
        """
        to_return = []

        for arry in str_arry:
            for v in arry:
                temp_arry = []
                if v.isdigit():
                    temp_arry.append(int(v))
                elif v == "-":
                    temp_arry.append(v)
                else:
                    print("Invalid character detected. Quitting the program now...")
                    exit(0)
            to_return.append(temp_arry)
        return to_return


def is_input_from_scanner(input):
     if len(input) >= 29:
          return True
     else:
          return False
     
def get_ticket_num(input):
     """
     From scanner input: get ticket number
     """
     tick_num = input[10:13]
     return tick_num

def get_clean_date_string():
    """
    Returns a clean string representation of the current date and time, suitable for use in file naming.

    Example from Professor Matta:
    “2023-11-27_14_44_42_496754.txt”
    2023-11-27 is the year, month, and day the file was created
    14_44_42_496754 is the hour, minute, second, and microseconds at which the file was created

    Returns:
    - str: A clean string representation of the current date and time.
    """

    current_datestamp = datetime.date.today()
    current_datestamp.strftime("%Y-%m-%d")
    return str(current_datestamp)

print(get_clean_date_string())