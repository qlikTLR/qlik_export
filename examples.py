# Wrapper Examples

import asyncio
import json
import os
from qlik_wrapper import QlikWrapper
from terminal_helper import TerminalHelper
from dotenv import load_dotenv

load_dotenv()

# Define Config Vars
API_KEY = os.getenv("API_KEY")
APP_ID = "37e72b96-b3f2-445b-89a8-d79c90c965f3"
#APP_ID = "66a6bb41-1426-4117-946b-6d4401fc36e3"
QLIK_TENANT = "qlikinternal.us.qlikcloud.com"
SPACE_ID = "609448f56d3d560001283b3c"
testUser = "YnN5jjuwGn9aQSOqm6C9BMx_Z4Kx_d9d"

async def export_masteritems():

    # Init the the Wrapper
    qlik = QlikWrapper(QLIK_TENANT, API_KEY)
   
    apps = await qlik.get_app_list()
    TerminalHelper.print_array(apps, f"   📁 {len(apps)} Apps found")

    space_name = await qlik.get_space_name(SPACE_ID)  # Simple get an Space Name
    apps_in_space = await qlik.get_app_list(SPACE_ID)
    TerminalHelper.print_array(apps_in_space, f"   📁 Apps in Space '{space_name}' with ID '{SPACE_ID}' ({len(apps_in_space)})")

    # Connect to an App
    await qlik.connect(APP_ID)

    # Simple Call to get only the App Name
    app_name = await qlik.get_app_name(APP_ID) 
    print(f"   Appname: '{app_name}'")

    # Gets Detailed App Infos what needs 3 different API Calls normaly
    app_info = await qlik.get_app_info(APP_ID) 
    TerminalHelper.print_single_array(app_info, 'App Infos','   ')


    # G
    # ----- Get Regular JSON Response for Dimension -------
    #dims = await qlik.get_dimension_list() 
    #print("📦 Dimensions:", dims)
    #dimension_id = "zBFt"
    #dimension_data = await qlik.get_dimension(dimension_id)
    #print(json.dumps(dimension_data, indent=2))
    #meas = await qlik.get_measure_list()
    #print("📐 Measures:", meas)
    #measure = await qlik.getMeasure(id)
    #variables = await qlik.get_variable_list()
    #print(json.dumps(variables, indent=2))
    # ----- END Get Regular JSON Response -------
    
    # Get a detailed List as Array (combine getList and Loop GetDim)
    dimensions = await qlik.get_dimension_list_detailed()
    TerminalHelper.print_bullet_from_array(dimensions, ["Title", "Description", "Tags", "Field Definitions", "Field Labels", "Type"])
  
    measures = await qlik.get_measure_list_detailed()
    TerminalHelper.print_bullet_from_array(measures,["Title", "Tags", "Expression", "Label", "Description"])
   
    await qlik.close()

if __name__ == "__main__":
    asyncio.run(export_masteritems())
