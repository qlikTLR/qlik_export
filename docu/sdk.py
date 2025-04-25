
#only a test how it works with the sdk to get the Master Items

from qlik_sdk import Apps, AuthType, Config


qli_tenat_url = "https://qlikinternal.us.qlikcloud.com"
api_key = "eyJhbGciOiJFUzM4NCIsImtpZCI6IjE4Yzg4NDhhLTkyMTUtNDRjOC1iMzAxLWI4NzE5MjYzY2Y0MyIsInR5cCI6IkpXVCJ9.eyJzdWJUeXBlIjoidXNlciIsInRlbmFudElkIjoiSnF2NXVVUGh5a29JV09zNHh1WkRWV3FHRHQwa2hfNWIiLCJqdGkiOiIxOGM4ODQ4YS05MjE1LTQ0YzgtYjMwMS1iODcxOTI2M2NmNDMiLCJhdWQiOiJxbGlrLmFwaSIsImlzcyI6InFsaWsuYXBpL2FwaS1rZXlzIiwic3ViIjoiODFJVlBTMklzZWR4X2d3QTB3RGFvajhfRk5kS0xoeVEifQ.zBfAZVIN4RtUPFe5yVJ9jYEUrHmDmMIcIrJ8h4m87iZSb2HTuu5Lb2fgt6hEdnoEwvsRmM6D8P8UIR-ZO-Bxug6v556_QQBZRBbbd29_q5zkBgtjn80yWnMYjwd_707s"
 
app_id = "37e72b96-b3f2-445b-89a8-d79c90c965f3"
 
# open connection
apps = Apps(Config(host = qli_tenat_url, auth_type = AuthType.APIKey, api_key = api_key))
 
# app is fetched from the REST /v1/apps/{app_id}
app = apps.get(appId = app_id)
 
# opens a websocket connection against the Engine API and gets the app layout
with app.open():
    app_info = app.get_all_infos()
 
    for app_object in app_info:
        match app_object.qType:
            case "dimension":
                master_item = app.get_dimension(app_object.qId).get_dimension()
                if master_item.qGrouping == 'N':
                    print(master_item)
            case "measure":
                master_item = app.get_measure(app_object.qId).get_measure()
                print(master_item)
 
    app.close()
 