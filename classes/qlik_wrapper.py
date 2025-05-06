# QlikWrapper.py
# pip install aiohttp asyncio dotenv websockets openpyxl
# written by Thomas Lindackers
# owned by QlikTech 
# Version 1.0.0

import ssl
import json
from aiohttp import ClientSession, WSMsgType # type: ignore
from datetime import datetime

class QlikWrapper:
    """
    QlikWrapper is an asynchronous interface to interact with Qlik's WebSocket and REST APIs.

    Attributes:
        tenant (str): The Qlik Cloud tenant domain.
        api_key (str): API key used for authentication.
        session (aiohttp.ClientSession): HTTP session for REST calls.
        ws (aiohttp.ClientWebSocketResponse): WebSocket session for real-time API.
        app_id (str, optional): Qlik app ID for WebSocket operations.
        space_id (str, optional): Qlik space ID for context-specific queries.
    """
    def __init__(self, tenant, api_key):
        self.tenant = tenant
        self.api_key = api_key
        self.app_id = None
        self.space_id = None
        self.url = None
        self.rest_base = f"https://{tenant}"

        self.session = None
        self.ws = None
        self.msg_id = 0
        self.app_handle = None
        self.session = ClientSession()
        print(f"🟢 INIT: {self.tenant}\n")

    def format_us_datetime(self, dt_str):
        try:
            dt = datetime.strptime(dt_str, "%Y-%m-%dT%H:%M:%SZ")
            return dt.strftime("%B %d, %Y, %-I:%M %p")
        except Exception:
            return dt_str or "–"
        
    async def connect(self, app_id):
        """
        Establishes a WebSocket connection to a Qlik app.

        This method sets the app ID, constructs the WebSocket URL, 
        and initiates the connection using the provided API key.

        Args:
            app_id (str): The ID of the Qlik app to connect to.

        Raises:
            Exception: If the WebSocket connection fails.
        """
        self.app_id = app_id
        self.url = f"wss://{self.tenant}/app/{self.app_id}"
        headers = {"Authorization": "Bearer " + self.api_key}
        ssl_context = ssl.create_default_context()

        try:
            print(f"\n🟢 Connecting to WebSocket: {self.url}")
            self.ws = await self.session.ws_connect(self.url, ssl=ssl_context, headers=headers)
            print("   ✅ Connection established!")
            await self._open_doc()
        except Exception as e:
            print(f"   ❗ Failed to connect to WebSocket: {e}")

    async def _open_doc(self):
        """
        Opens the specified Qlik app via WebSocket.

        This method sends an 'OpenDoc' command using the current app ID 
        and retrieves the handle for further interactions with the app.

        If the opening fails or returns an error, it logs the error message.

        Raises:
            Exception: If the request fails due to connection or protocol errors.
        """
        try:
            print(f"\n🟢 Opening Qlik app with id {self.app_id}")
            await self._send("OpenDoc", params={"qDocName": self.app_id})
            response = await self._receive()

            if "error" in response:
                error_message = response["error"].get("message", "Unknown error")
                print(f"   ❗ Failed to open document: {error_message}")
                return

            self.app_handle = response["result"]["qReturn"]["qHandle"]
            print("   ✅ opened successfully!\n")

        except Exception as e:
            print(f"   ❗ Exception while opening document: {e}")

    async def _send(self, method, handle=-1, params=None):
        """
        Sends a JSON-RPC message over the WebSocket connection to Qlik.

        Args:
            method (str): The JSON-RPC method to be called (e.g., "OpenDoc", "GetLayout").
            handle (int): The object handle for the request. Default is -1 (global handle).
            params (dict, optional): Parameters to pass with the method call.

        Returns:
            int: The message ID used for this request.

        Logs an error message if sending the message fails.
        """
        self.msg_id += 1
        msg = {
            "jsonrpc": "2.0",
            "id": self.msg_id,
            "method": method,
            "handle": handle,
            "params": params or {}
        }

        try:
            await self.ws.send_str(json.dumps(msg))
        except Exception as e:
            print(f"❗ Error sending message '{method}': {e}")

        return self.msg_id

    async def _receive(self):
        """
        Waits for and processes incoming messages from the WebSocket connection.

        This method listens for incoming WebSocket messages and processes them. It handles
        both successful responses (with 'result') and errors (with 'error') from Qlik's engine.

        Returns:
            dict: The data received from Qlik in the response, either containing 'result' or 'error'.

        Logs error messages if receiving messages fails or if Qlik sends an error.

        Notes:
            This method continues to listen until a valid response (or error) is received.
        """
        try:
            while True:
                msg = await self.ws.receive()

                if msg.type == WSMsgType.TEXT:
                    data = json.loads(msg.data)

                    if 'error' in data:
                        error_message = data['error'].get("message", "Unknown error")
                        print(f"❗ Error received from Qlik Engine: {error_message}")

                    if 'result' in data or 'error' in data:
                        return data

                elif msg.type == WSMsgType.ERROR:
                    print("❗ WebSocket error while receiving message.")
                    break

        except Exception as e:
            print(f"❗ Exception while receiving message: {e}")

    async def _get_layout(self, definition):
        """
        Creates a session object and retrieves the layout of the Qlik app object.

        This method sends a "CreateSessionObject" request to Qlik to create a session object 
        based on the provided definition. Then, it sends a "GetLayout" request to retrieve 
        the layout details for the created object.

        Args:
            definition (dict): The properties (qProp) for the session object to be created.

        Returns:
            dict or None: The layout response from Qlik, or None if an error occurs during 
                        the process (either creating the session object or retrieving the layout).

        Logs error messages if any issue arises during the creation of the session object 
        or retrieving the layout from Qlik.

        Notes:
            This method relies on the creation of a session object, which is used to retrieve
            the layout of the app object in Qlik.
        """
        try:
            await self._send("CreateSessionObject", handle=self.app_handle, params={"qProp": definition})
            obj_response = await self._receive()

            if 'error' in obj_response:
                print("❗ Error during CreateSessionObject.")
                return None

            handle = obj_response['result']['qReturn']['qHandle']
            await self._send("GetLayout", handle=handle)
            layout_response = await self._receive()

            if 'error' in layout_response:
                print("❗ Error during GetLayout.")
                return None

            return layout_response

        except Exception as e:
            print(f"❗ Exception in _get_layout: {e}")
            return None

    async def get_dimension_list(self):
        """
        Retrieves a list of all master dimensions in the currently opened Qlik app.

        This method constructs a session object definition for `DimensionList`, sends it 
        to the Qlik Engine, and fetches the layout to extract the list of dimensions.

        Returns:
            list: A list of dictionaries containing metadata for each dimension, including
                title, tags, and the field definitions.

        Notes:
            This method relies on an active WebSocket connection and a successfully opened app.
            If no dimensions are found or an error occurs, an empty list is returned.
        """
        definition = {
            "qInfo": {"qType": "DimensionList"},
            "qDimensionListDef": {
                "qType": "dimension",
                "qData": {
                    "title": "/qMetaDef/title",
                    "tags": "/qMetaDef/tags",
                    "definition": "/qDim/qFieldDefs"
                }
            }
        }
        layout = await self._get_layout(definition)
        return layout.get("result", {}).get("qLayout", {}).get("qDimensionList", {}).get("qItems", [])

    async def get_measure_list(self):
        """
        Retrieves a list of all master measures in the currently opened Qlik app.

        This method creates a session object definition for `MeasureList`, sends it to the 
        Qlik Engine, and retrieves the layout to extract the list of measures.

        Returns:
            list: A list of dictionaries, each representing a master measure with details
                such as title, tags, and expression definition.

        Notes:
            This function assumes a WebSocket connection is already established and an app is open.
            If no measures are found or an error occurs, an empty list is returned.
        """
        definition = {
            "qInfo": {"qType": "MeasureList"},
            "qMeasureListDef": {
                "qType": "measure",
                "qData": {
                    "title": "/qMetaDef/title",
                    "tags": "/qMetaDef/tags",
                    "definition": "/qMeasure/qDef"
                }
            }
        }
        layout = await self._get_layout(definition)
        return layout.get("result", {}).get("qLayout", {}).get("qMeasureList", {}).get("qItems", [])
    

    async def get_var_list(self):
        """
        Retrieves a list of all variables in the currently opened Qlik app.

        This method creates a session object definition for `VariableList`, sends it to the 
        Qlik Engine, and retrieves the layout to extract the list of variables.

        Returns:
            list: A list of dictionaries, each representing a variable with details
                such as name, definition, tags, and ID.

        Notes:
            This function assumes a WebSocket connection is already established and an app is open.
            If no variables are found or an error occurs, an empty list is returned.
        """
        definition = {
            "qInfo": {"qType": "VariableList"},
            "qVariableListDef": {
                "qType": "variable",
                "qData": {
                    "tags": "/tags",
                    "title": "/title",
                    "definition": "/definition"
                }
            }
        }

        layout = await self._get_layout(definition)
        return layout.get("result", {}).get("qLayout", {}).get("qVariableList", {}).get("qItems", [])


    async def get_measure(self, measure_id):
        """
        Retrieves the full layout information of a specific master measure in the opened Qlik app.

        This method uses the Qlik Engine API to:
        1. Call 'GetMeasure' with the given measure ID to obtain a handle.
        2. Use the handle to call 'GetLayout' and retrieve detailed metadata about the measure.

        Args:
            measure_id (str): The unique ID of the master measure to retrieve.

        Returns:
            dict: The layout information of the master measure, including its definition, labels, and metadata.
        """
        try:
            await self._send("GetMeasure", handle=self.app_handle, params={"qId": measure_id})
            response = await self._receive()
            
            if 'error' in response:
                print(f"❗ Error getting measure (ID: {measure_id}): {response['error']}")
                return {} 

            measure_handle = response["result"]["qReturn"]["qHandle"]
            
            await self._send("GetLayout", handle=measure_handle)
            layout_response = await self._receive()
            
            if 'error' in layout_response:
                print(f"❗ Error getting measure layout (ID: {measure_id}): {layout_response['error']}")
                return {} 

            return layout_response["result"]["qLayout"]
        
        except Exception as e:
            print(f"❗ Unexpected error while retrieving measure (ID: {measure_id}): {e}")
            return {}  

    async def get_dimension(self, dimension_id):
        """
        Retrieves the full layout information of a specific master dimension in the opened Qlik app.

        This method performs the following:
        1. Sends a 'GetDimension' request using the provided dimension ID to retrieve its handle.
        2. Uses the handle to request the layout of the dimension using 'GetLayout'.

        Args:
            dimension_id (str): The unique ID of the master dimension to retrieve.

        Returns:
            dict: The layout data of the master dimension, including field definitions, labels, and metadata.
        """
        try:
            await self._send("GetDimension", handle=self.app_handle, params={"qId": dimension_id})
            response = await self._receive()
            
            if 'error' in response:
                print(f"❗ Error getting dimension (ID: {dimension_id}): {response['error']}")
                return {}  

            dimension_handle = response["result"]["qReturn"]["qHandle"]
         
            await self._send("GetLayout", handle=dimension_handle)
            layout_response = await self._receive()
            
            if 'error' in layout_response:
                print(f"❗ Error getting dimension layout (ID: {dimension_id}): {layout_response['error']}")
                return {} 

            return layout_response["result"]["qLayout"]
        
        except Exception as e:
            print(f"❗ Unexpected error while retrieving dimension (ID: {dimension_id}): {e}")
            return {}  

    async def get_variable_list(self):
        """
        Retrieves a list of all master variables defined in the currently opened Qlik app.

        This method sends a `CreateSessionObject` request with a `VariableList` definition to the Qlik Engine,
        then retrieves and returns the variable metadata via the layout.

        Returns:
            list: A list of dictionaries, each representing a master variable with title, tags, and definition.

        Notes:
            - Requires an active WebSocket connection and an opened app.
            - Returned variable items include metadata like title, tags, and the actual variable definition.
        """
        definition = {
            "qInfo": {"qType": "VariableList"},
            "qVariableListDef": {
                "qType": "variable",
                "qData": {
                    "title": "/qMetaDef/title",
                    "tags": "/qMetaDef/tags",
                    "definition": "/qDefinition"
                }
            }
        }
        layout = await self._get_layout(definition)
        return layout.get("result", {}).get("qLayout", {}).get("qVariableList", {}).get("qItems", [])

    async def get_dimension_list_detailed(self):
        """
        Retrieves detailed information about dimensions including their names,
        description, field definitions, labels, tags, and whether they are single or multi-valued.

        Returns:
            list: A list of lists, each containing:
                [title, description, tags, field definitions, field labels, type]
        """
        dimensions = await self.get_dimension_list()
        detailed_dimensions = []

        for dim in dimensions:
            dim_id = dim.get("qInfo", {}).get("qId")
            dim_title = dim.get("qMeta", {}).get("title", "❗ No Title")

            if dim_id:
                try:
                    layout = await self.get_dimension(dim_id)

                    description = layout.get("qDim", {}).get("descriptionExpression", "")
                    tags = ", ".join(layout.get("qMeta", {}).get("tags", ""))
                    field_defs = layout.get("qDim", {}).get("qFieldDefs", "")
                    field_labels = layout.get("qDim", {}).get("qLabelExpression", "")
                    grouping = layout.get("qDim", {}).get("qGrouping", "N")
                    dim_type = "multi" if grouping == "M" else "single"

                    detailed_dimensions.append([
                        dim_id,
                        dim_title,
                        description,
                        tags,
                        field_defs,
                        field_labels,
                        dim_type
                    ])
                except Exception as e:
                    print(f"❗ Failed to get layout for dimension '{dim_title}' (ID: {dim_id}): {e}")
            else:
                print(f"❗ Skipping dimension without qId: {dim}")

        return detailed_dimensions

    async def get_measure_list_detailed(self):
        """
        Retrieves detailed information about measures including their titles, tags,
        expressions, labels, and description.

        Returns:
            list: A list where each element is a list with measure details:
                [title, tags, expression, label, description]
        """
        measures = await self.get_measure_list()
        detailed_measures = []

        for measure in measures:
            measure_id = measure.get("qInfo", {}).get("qId")
            measure_title = measure.get("qMeta", {}).get("title", "❗ No Title")

            if measure_id:
                try:
                    layout = await self.get_measure(measure_id)
                    detailed_measures.append([
                        measure_id,
                        measure_title,  # title
                        ", ".join(layout.get("qMeta", {}).get("tags", "")),
                        layout.get("qMeasure", {}).get("qDef", ""),  # expression
                        layout.get("qMeasure", {}).get("qLabelExpression", ""),  # label
                        layout.get("qMeasure", {}).get("descriptionExpression", "")  # description
                    ])
                except Exception as e:
                    print(f"❗ Failed to get layout for measure '{measure_title}' (ID: {measure_id}): {e}")
            else:
                print(f"❗ Skipping measure without qId: {measure}")

        return detailed_measures

    async def get_var_list_detailed(self):
        """
        Returns variable data prepared for terminal output.

        Returns:
            list: A list of lists, where each inner list contains:
                [ID, Title (qName), Value (qDefinition), Tags]
        """
        raw_vars = await self.get_var_list()
        return [
            [
                item.get("qInfo", {}).get("qId", ""),
                item.get("qName", ""),
                item.get("qDefinition", ""),
                ", ".join(item.get("qMeta", {}).get("tags", ""))
            ]
            for item in raw_vars
        ]
    
    async def get_masteritems_detailed(self, include_variables=True, columns=None):
        """
        Retrieves detailed information about dimensions, measures, and optionally variables,
        combining them into a single list with the specified columns.

        You can control which columns to include by passing a list of column names
        as the 'columns' parameter. If 'columns' is None, all columns will be included by default.

        Parameters:
            columns (list, optional): A list of column names to include in the output. 
                                    Available options are ["ID", "Title", "Description", "Value", "Tags", "Type", "ItemType"].
                                    If None, all columns will be shown by default.
            include_variables (bool, optional): A flag to control whether variables should be included. 
                                                Defaults to True (includes variables).

        Returns:
            list: A list of lists, each containing the requested columns.
        """
        # Default columns if none are provided
        all_columns = ["ID", "Title", "Label", "Description", "Expression", "Tags", "Type", "ItemType"]
        if columns is None:
            columns = all_columns

        # Getting the detailed lists
        dimensions = await self.get_dimension_list_detailed()
        measures = await self.get_measure_list_detailed()
        variables = await self.get_var_list_detailed() if include_variables else []

        # Combine the data from dimensions, measures, and variables
        combined_data = []

        # Process Dimensions
        for dim in dimensions:
            row = []
            if "ID" in columns:
                row.append(dim[0]) 
            if "Title" in columns:
                row.append(dim[1])  
            if "Label" in columns:
                row.append(dim[5])  
            if "Description" in columns:
                description = dim[2] if dim[2] else ""  
                row.append(description)
            if "Expression" in columns:
                row.append(dim[4])  
            if "Tags" in columns:
                row.append(dim[3])  
            if "Type" in columns:
                row.append(dim[6])  # Type (multi or single)
            if "ItemType" in columns:
                row.append("Dimension")
            combined_data.append(row)

        # Process Measures
        for measure in measures:
            row = []
            if "ID" in columns:
                row.append(measure[0])
            if "Title" in columns:
                row.append(measure[1])
            if "Label" in columns:
                row.append(dim[4])  
            if "Description" in columns:
                description = measure[5] if measure[5] else ""  
                row.append(description)
            if "Expression" in columns:
                row.append(measure[3])  
            if "Tags" in columns:
                row.append(measure[2]) 
            if "Type" in columns:
                row.append(" ") 
            if "ItemType" in columns:
                row.append("Measure")
            combined_data.append(row)

        # Process Variables if include_variables is True
        if include_variables:
            for variable in variables:
                row = []
                if "ID" in columns:
                    row.append(variable[0])  
                if "Title" in columns:
                    row.append(variable[1]) 
                if "Label" in columns:
                    row.append("")   
                if "Description" in columns:
                    row.append(" ") 
                if "Expression" in columns:
                    row.append(variable[2])  
                if "Tags" in columns:
                    row.append(variable[3])  
                if "Type" in columns:
                    row.append(" ")  
                if "ItemType" in columns:
                    row.append("Variable")
                combined_data.append(row)

        return combined_data

    
    async def close(self):
        """
        Closes the WebSocket and HTTP session connections to the Qlik server.

        This method ensures that both the WebSocket (`self.ws`) and the `aiohttp` client session (`self.session`)
        are cleanly closed. It also logs a confirmation message or an error if the process fails.

        Notes:
            - Should be called at the end of the script or when the connection to Qlik is no longer needed.
            - Safe to call even if the connections are already closed.
        """
        try:
            if self.ws:
                await self.ws.close()
            if self.session:
                await self.session.close()
            print("🔴 Connection closed successfully.")
        except Exception as e:
            print(f"❗ Error while closing the connection: {e}")

    
    # REST API Calls

    async def get_space_name(self, space_id):
        """
        Retrieves the name of a Qlik Cloud space based on its space ID.

        Args:
            space_id (str): The unique identifier of the Qlik Cloud space.

        Returns:
            str or None: The name of the space if found, or a fallback message like 
            "❗ No name found" if not. Returns None if an exception occurs.

        Notes:
            - Uses the Qlik REST API endpoint `/api/v1/spaces/{space_id}`.
            - Requires a valid API key for authentication.
        """
        url = f"{self.rest_base}/api/v1/spaces/{space_id}"
        headers = {"Authorization": "Bearer " + self.api_key}
        try:
            async with self.session.get(url, headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get("name", "❗ No name found")
                else:
                    print(f"❗ Failed to fetch space name (Status: {resp.status})")
        except Exception as e:
            print(f"❗ Error retrieving space name: {e}")
        return None

    async def get_app_name(self, app_id):
        """
        Retrieves the name of a Qlik app using its unique app ID.

        Args:
            app_id (str): The unique identifier of the Qlik app.

        Returns:
            str or None: The name of the app if available, or "❗ No name found" if not.
            Returns None if an exception occurs or the request fails.

        Notes:
            - This method uses the Qlik REST API endpoint `/api/v1/apps/{app_id}`.
            - A valid API key is required for authentication.
        """
        url = f"{self.rest_base}/api/v1/apps/{app_id}"
        headers = {"Authorization": "Bearer " + self.api_key}
        try:
            async with self.session.get(url, headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get("name", "❗ No name found")
                else:
                    print(f"❗ Failed to fetch app name (Status: {resp.status})")
        except Exception as e:
            print(f"❗ Error retrieving app name: {e}")
        return None

    async def get_app_list(self, space_id=None):
        """
        Retrieves a list of Qlik apps, optionally filtered by space ID.

        Args:
            space_id (str, optional): The ID of the space to filter apps by. 
                                    If not provided, all apps will be listed.

        Returns:
            list[dict]: A list of dictionaries containing app names and IDs.
                        Each entry has the form: {"name": ..., "id": ...}

        Raises:
            Exception: If the REST API request fails with a non-200 status code.

        Notes:
            - Uses `/api/v1/items` if `space_id` is provided (resourceType=app).
            - Uses `/api/v1/apps` if no `space_id` is given.
            - Requires a valid API key for authorization.
        """
        if space_id:
            rest_url = f"{self.rest_base}/api/v1/items"
            params = {
                "resourceType": "app",
                "spaceId": space_id
            }
        else:
            rest_url = f"{self.rest_base}/api/v1/apps"
            params = {}

        headers = {
            "Authorization": "Bearer " + self.api_key,
            "Content-Type": "application/json"
        }

        async with self.session.get(rest_url, headers=headers, params=params, ssl=False) as response:
            if response.status != 200:
                raise Exception(f"Error fetching app list: {response.status}")
            data = await response.json()

            app_list = []

            for item in data.get("data", []):
                if space_id:
                    app_list.append({
                        "name": item.get("name", "❗ No Name"),
                        "id": item.get("resourceId", item.get("id", "Undefiend"))
                    })
                else:
                    app_list.append({
                        "name": item.get("attributes", {}).get("name", "❗ No Name"),
                        "id": item.get("attributes", {}).get("id", "Undefiend")
                    })

            return app_list

    async def get_user_list(self, limit=100):
    
        url = f"https://{self.tenant}/api/v1/users?limit={limit}"
        headers = {
            "Authorization": "Bearer " + self.api_key,
            "Content-Type": "application/json"
        }

        async with self.session.get(url, headers=headers, ssl=ssl.create_default_context()) as response:
            if response.status == 200:
                result = await response.json()
                return result.get("data", [])
            else:
                print(f"❗ Error fetching user list: {response.status}")
                return []
            
    async def get_user(self, user_id):
     
        url = f"https://{self.tenant}/api/v1/users/{user_id}"
        headers = {
            "Authorization": "Bearer " + self.api_key,
            "Content-Type": "application/json"
        }

        async with self.session.get(url, headers=headers, ssl=ssl.create_default_context()) as response:
            if response.status == 200:
                return await response.json()
            else:
                print(f"❗ Error get User '{user_id}': {response.status}")
                return {}
            
    async def get_glossaries_list(self, limit=100):
    
        url = f"https://{self.tenant}/api/v1/glossaries?limit={limit}"
        headers = {
            "Authorization": "Bearer " + self.api_key,
            "Content-Type": "application/json"
        }

        async with self.session.get(url, headers=headers, ssl=ssl.create_default_context()) as response:
            if response.status == 200:
                data = await response.json()
                return data.get("data", [])
            else:
                print(f"❗ Error fetching glossaries list: {response.status}")
                return []

    async def get_glossary(self, glossary_id):
        """
        Retrieves detailed information about a glossary from Qlik by its unique glossary ID.

        Parameters:
            glossary_id (str): The unique identifier of the glossary.

        Returns:
            dict: A dictionary containing the glossary's metadata if the request is successful.
                  An empty dictionary is returned if the request fails.

        Notes:
            - The method accesses the REST API endpoint /api/v1/glossaries/{glossary_id}.
            - On error, a message is printed to the console and an empty dictionary is returned.
        """
        url = f"https://{self.tenant}/api/v1/glossaries/{glossary_id}"
        headers = {
            "Authorization": "Bearer " + self.api_key,
            "Content-Type": "application/json"
        }

        async with self.session.get(url, headers=headers, ssl=ssl.create_default_context()) as response:
            if response.status == 200:
                return await response.json()
            else:
                print(f"❗ Error fetching glossary '{glossary_id}': {response.status}")
                return {}
            
    async def get_term(self, term_id):
        """
        Retrieves detailed information about a glossary term in Qlik by its unique term ID.

        Parameters:
            term_id (str): The unique identifier of the glossary term.

        Returns:
            dict: A dictionary containing the term's metadata if the request is successful.
                  An empty dictionary is returned if the request fails.

        Notes:
            - On success, the full JSON response with term details is returned.
            - On failure, an error message is printed and an empty dictionary is returned.
        """
        url = f"https://{self.tenant}/api/v1/terms/{term_id}"
        headers = {
            "Authorization": "Bearer " + self.api_key,
            "Content-Type": "application/json"
        }

        async with self.session.get(url, headers=headers, ssl=ssl.create_default_context()) as response:
            if response.status == 200:
                return await response.json()
            else:
                print(f"❗ Error fetching term '{term_id}': {response.status}")
                return {}

    async def get_space_name(self, space_id):
        """
        Retrieves the name of a Qlik space based on its unique space ID.

        Parameters:
            space_id (str): The unique identifier of the Qlik space.

        Returns:
            str or None: The name of the space if found, otherwise a warning string or None if an error occurs.

        Notes:
            - If the request is successful but the space has no name, a default warning is returned.
            - If the request fails or an exception occurs, an error is printed and None is returned.
        """
        url = f"{self.rest_base}/api/v1/spaces/{space_id}"
        headers = {"Authorization": "Bearer " + self.api_key}
        try:
            async with self.session.get(url, headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get("name", "❗ No name found")
                else:
                    print(f"❗ Failed to fetch space name (Status: {resp.status})")
        except Exception as e:
            print(f"❗ Error retrieving space name: {e}")
        return None

    async def get_app_name(self, app_id):
        """
        Retrieves the name of a Qlik app based on its unique app ID.

        Parameters:
            app_id (str): The unique identifier of the Qlik app.

        Returns:
            str or None: The name of the app if found, otherwise a warning string or None if an error occurs.

        Notes:
            - If no app is found with the given ID, a warning is printed.
            - In case of a failed request or exception, an error message is printed and None is returned.
        """
        url = f"{self.rest_base}/api/v1/items?resourceType=app&resourceId={app_id}"
        headers = {"Authorization": "Bearer " + self.api_key}
        try:
            async with self.session.get(url, headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    items = data.get("data", [])
                    if items:
                        return items[0].get("name", "❗ No name found")
                    else:
                        print("❗ No app found for the given ID.")
                else:
                    print(f"❗ Failed to fetch app name (Status: {resp.status})")
        except Exception as e:
            print(f"❗ Error retrieving app name: {e}")
        return None
    

    async def get_app_info(self, app_id):
        """
        Retrieves metadata for a Qlik app, including name, description, owner, timestamps,
        and reload execution details.

        Parameters:
            app_id (str): The unique ID of the Qlik app.

        Returns:
            dict: A dictionary with app metadata and reload execution times.
        """
        url = f"{self.rest_base}/api/v1/items?resourceType=app&resourceId={app_id}"
        headers = {"Authorization": "Bearer " + self.api_key}
        try:
            async with self.session.get(url, headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    items = data.get("data", [])
                    if items:
                        item = items[0]
                        app_info = {
                            "name": item.get("name", "❗ No name"),
                            "description": item.get("description", "–"),
                            "created": self.format_us_datetime(item.get("createdAt")) or "❗ No created date",
                            "updated": self.format_us_datetime(item.get("updatedAt")) or "❗ No updated date"
                        }

                        # Owner
                        owner_id = item.get("ownerId")
                        if owner_id:
                            owner_info = await self.get_user(owner_id)
                            app_info["owner"] = owner_info.get("name", "❗ No owner name")
                        else:
                            app_info["owner"] = "❗ No owner ID"

                        # Schritt 2 – reload task Info (REST statt JSON API)
                        reload_url = f"{self.rest_base}/api/v1/reload-tasks?appId={app_id}"
                        async with self.session.get(reload_url, headers=headers) as reload_resp:
                            if reload_resp.status == 200:
                                reload_data = await reload_resp.json()
                                tasks = reload_data.get("data", [])
                                if tasks:
                                    task = tasks[0]
                                    app_info["lastExecutionTime"] = self.format_us_datetime(task.get("lastExecutionTime", ""))
                                    app_info["nextExecutionTime"] = self.format_us_datetime(task.get("nextExecutionTime", ""))
                                else:
                                    app_info["lastExecutionTime"] = "❗ No task data"
                                    app_info["nextExecutionTime"] = "❗ No task data"
                            else:
                                app_info["lastExecutionResult"] = f"❗ Error (Status {reload_resp.status})"
                                app_info["lastExecutionTime"] = "❗ Error fetching reload time"
                                app_info["nextExecutionTime"] = "❗ Error fetching reload time"

                        return app_info
                    else:
                        print("❗ No app found for the given ID.")
                else:
                    print(f"❗ Failed to fetch app info (Status: {resp.status})")
        except Exception as e:
            print(f"❗ Error retrieving app info: {e}")
        return None
