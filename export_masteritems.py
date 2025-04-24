# pip install aiohttp asyncio dotenv websockets 


from qlik_wrapper import QlikWrapper
from dotenv import load_dotenv

from terminal_helper import TerminalHelper
load_dotenv()

# Define Config Vars
API_KEY = os.getenv("API_KEY")
APP_ID = "37e72b96-b3f2-445b-89a8-d79c90c965f3"
QLIK_TENANT = "qlikinternal.us.qlikcloud.com"
SPACE_ID = "609448f56d3d560001283b3c"


async def export_masteritems():
    
    qlik = QlikWrapper(QLIK_TENANT, API_KEY)
    # Connect to an App
    await qlik.connect(APP_ID)

    # Gets Detailed App Infos what needs 3 different API Calls normaly
    app_info = await qlik.get_app_info(APP_ID) 
    TerminalHelper.print_single_array(app_info, 'App Infos','   ')

    # Get a detailed List as Array (combine getList and Loop GetDim)
    dimensions = await qlik.get_dimension_list_detailed()
    TerminalHelper.print_bullet_from_array(dimensions, ["Title", "Description", "Tags", "Field Definitions", "Field Labels", "Type"])
  
    measures = await qlik.get_measure_list_detailed()
    TerminalHelper.print_bullet_from_array(measures,["Title", "Tags", "Expression", "Label", "Description"])
   
    await qlik.close()

if __name__ == "__main__":
    asyncio.run(export_masteritems())
