import os
import UtilityFunctions

#TODO: Save file with date and time

class SaveToCloseNumFile:
    def __init__(self, arrayToSave):
        self.arrayToSave = arrayToSave
    
    def _save_close_nums_(self):
        file = open("Previous_Day_Close_Nums", "w")
        close_num_str = ""
        for closeNumPrice in self.arrayToSave:
            for closeNum in closeNumPrice:
                close_num_str +=  f"{closeNum} "
            close_num_str += "\n"
        file.write(close_num_str)
        print("Close Numbers saved sucessfully")
        file.close()
    
class ReadCloseNumFile:
    def _is_file_(fileName = "Previous_Day_Close_Nums"):
        path = f"./{fileName}"
        file_exist = os.path.isfile(path)
        if file_exist:
            return True
        else:
            return False
    
    def get_file_content():
        if ReadCloseNumFile._is_file_():
           close_nums_file = open("Previous_Day_Close_Nums", "r")
           previous_day_close_nums = close_nums_file.read()
           return previous_day_close_nums
        else:
            return None
    
    def get_file_content_converted_to_array():
        close_nums = ReadCloseNumFile.get_file_content()
        if close_nums is None:
            return None
        else:
            #Is close_nums formatted correctly
            return UtilityFunctions.file_string_arry_to_int_arry(UtilityFunctions.file_string_to_array(close_nums))






