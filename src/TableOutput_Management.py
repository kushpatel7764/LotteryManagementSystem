"""
    TableOutput class provides methods to handle different types of outputs (terminal, text, Excel) for 
    filtered meteorite data.

    Attributes:
    - outputTypeChosen (str): Represents the user's choice for the type of output.
    - sortedList (list): the sorted list of meteorite objects.
"""

import xlwt
import UtilityFunctions
from colorama import Fore
from Calculations import dict_of_Prices



class TableOutput:
    def __init__(self,  open, close, sell, instantTotal):
        """
        Initializes a TableOutput object.
        """
        self.row_Number = 1 # The number of the row in the terminal table output
        self.open = open
        self.close = close
        self.sell = sell   
        self.instantTotal = instantTotal
        self.price = 0


    def fortmated_Table(self, tableString = ""):

        print("\n")
        tableString = tableString + TableOutput.Create_Terminal_Row_Label() + "\n"
        tableString = tableString + TableOutput.Draw_Terminal_Table_Sepration_Line(50) + "\n"
        for price in range(7):
            #For each price create a label
            self.price = dict_of_Prices[price]
            
            #Create row of data for each price
            for row, value in enumerate(self.open[price]):
                tableString = tableString + TableOutput.Create_Terminal_Data_Row(self, price, row) + "\n" 
            tableString = tableString + TableOutput.Draw_Terminal_Table_Sepration_Line(50) + "\n"
        return tableString

    def Draw_Terminal_Table_Sepration_Line(lineLength, line = ""):
        """
        Draws a separation line for the terminal table.

        Parameters:
        - lineLength (int): The length of the separation line.
        - line (str): A string to accumulate the separation line.

        Returns:
        - The separation line string.
        """

        for i in range(lineLength):
            if (i == (lineLength-1)):
                line = line + "=\n"
                break
            line = line + "="
        return line

    def Create_Terminal_Row_Label():
        """
        Creates the label row for the terminal table.

        Returns:
        - A formatted string of row labels.
        """

        labels = ["#","PRICE" ,"OPEN", "CLOSE", "SELL"]
        return TableOutput.setup_Terminal_Row(labels)
        
    
    def Create_Terminal_Data_Row(self, price, lineNum):
        """
        Creates a data row for the terminal table.

        Parameters:
        - lineNum (int): The line number of the row.
        - sortedObj: An object containing data to be displayed.

        Returns:
        - A formatted string of data for a single row.
        """

        toReturn = ""
        lineInfo = [str(self.row_Number), dict_of_Prices[price],self.open[price][lineNum], self.close[price][lineNum], self.sell[price][lineNum]] #+1 is added to convert from index to number
        self.row_Number += 1
        toReturn = TableOutput.setup_Terminal_Row(lineInfo, toReturn)
        return toReturn
    
    def setup_Terminal_Row(lineInfo, toAppendReturn = ""):
        """
        Sets up a row for the terminal table given information about what to put in the row.

        Parameters:
        - lineInfo (list): List of data to be displayed in a row.
        - toAppendReturn (str): A string to accumulate the formatted row.
s
        Returns:
        - The formatted row string.
        """

        for column, line in enumerate(lineInfo):
            if column == 0:
                toAppendReturn = toAppendReturn + f'{line:^5}' 
                continue
            elif column > 1 and column < 8:
                toAppendReturn = toAppendReturn + f'{line:>10}'
                continue
            toAppendReturn = toAppendReturn + f'{line:>10}' 
        return toAppendReturn

    def Terminal_Output(self):
        """
        Prints the formatted table for the terminal.
        """

        print(TableOutput.fortmated_Table(self))
        print(f"Instant Ticket Sell: {self.instantTotal}")

class ExcelOutput:
    colum_addtion_per_table = {"50":0,"30":0,"20":0,"10":6, "5":6, "2":12, "1":12}
    def __init__(self,  open, close, sell, instantTotal):
        """
        Initializes a TableOutput object.
        """
        self.row_Number = 0 # The number of the row in the terminal table output
        self.ticket_row_count = 1
        self.open = open
        self.close = close
        self.sell = sell   
        self.instantTotal = instantTotal
        self.price = 0


    def Exel_Output(self):
        """
        Generates an Excel file containing the Lottery data. 
        """
        workbook = xlwt.Workbook()
        sheet = workbook.add_sheet('Lottery Data')

        #Top of the sheet


        for table in range(7):
            #For each price create a label
            self.price = dict_of_Prices[table]

            #set row and col for different tables
            if table == 3:
                self.row_Number  = 0
            elif table == 5:
                self.row_Number = 0
            

            ExcelOutput.Excel_Write_Label(self, sheet, self.price)
            ExcelOutput.Excel_Write_Data(self, sheet, table)

            #Add a row gab between tables
            self.row_Number += 1

        # Save the workbook to a file
        fileName = UtilityFunctions.get_clean_date_string() + ".xls"
        workbook.save(fileName)
        print(f"\nExcel file \"{fileName}\" created successfully.\n")

    def Excel_Write_Label(self, sheet, price):
        """
        Writes labels to the Excel sheet.

        Parameters:
        - sheet: An Excel sheet object.
        """

        labels = [f"${price}","Game #" ,"OPEN", "CLOSE", "SELL"]
        for col, label in enumerate(labels):
            #set column for different tables
            col = col + ExcelOutput.colum_addtion_per_table[price]
            sheet.write(self.row_Number, col, label)
        #Go to next row
        self.row_Number += 1
    
    def Excel_Write_Data(self, sheet, table):
        """
        Writes data to the Excel sheet. The first loop picks a row and the second loop sets a columbs at a row from the first loop. 

        Parameters:
        - sheet: An Excel sheet object.
        """        

        for lineNum, table_at_price in enumerate(self.open[table]): 
            data = [str(self.ticket_row_count), "-",self.open[table][lineNum], self.close[table][lineNum], self.sell[table][lineNum]] #+1 is added to convert from index to number
            for col, value in enumerate(data):
                #set column for different tables
                price = str(self.price)
                col = col + ExcelOutput.colum_addtion_per_table[price]
                sheet.write(self.row_Number, col, value)
            #Go to next row
            self.row_Number += 1
            #update ticket spot number
            self.ticket_row_count += 1

   
   

    