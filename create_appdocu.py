# pip install aiohttp asyncio dotenv websockets 
from classes.qlik_wrapper import QlikWrapper
from dotenv import load_dotenv # type: ignore
import os  
import asyncio
from classes.terminal_helper import TerminalHelper
from classes.file_writer_helper import FileWriterHelper
load_dotenv()

# Define Config Vars
API_KEY = os.getenv("API_KEY")
#APP_ID = "37e72b96-b3f2-445b-89a8-d79c90c965f3"
QLIK_TENANT = "qlikinternal.us.qlikcloud.com"

async def create_docu():
    qlik = QlikWrapper(QLIK_TENANT, API_KEY)
    # Connect to an App
    await qlik.connect(APP_ID)

    APP_ID = input('Please enter App Id:')

    app_name = await qlik.get_app_name(APP_ID) 
    writer = FileWriterHelper(f"exports/{app_name}-documentation.txt")
    
    # Gets Detailed App Infos what needs 3 different API Calls normaly
    app_info = await qlik.get_app_info(APP_ID) 
    TerminalHelper.print_single_array(app_info, 'App Infos','   ')
    writer.print_single_array(app_info, 'App Infos','   ')

    # Get a detailed List as Array (combine getList and Loop GetDim)
    dimensions = await qlik.get_dimension_list_detailed()
    writer.write_title('   ------- Master Measures ---------')
    writer.print_bullet_from_array(dimensions, ["ID","Title", "Description", "Tags", "Field Definitions", "Field Labels", "Type"])

    measures = await qlik.get_measure_list_detailed()
    writer.write_title('   ------- Master Dimensions ---------')
    writer.print_bullet_from_array(measures,["ID","Title", "Tags", "Expression", "Label", "Description"])

    variables = await qlik.get_var_list_detailed()
    writer.write_title('   ------- Variables ---------')
    writer.print_bullet_from_array(variables,["ID","Title", "Value", "Tags"])
   
    await qlik.close()

if __name__ == "__main__":
    asyncio.run(create_docu())
