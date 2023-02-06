import arcgis
import concurrent.futures
from arcgis.gis import GIS
from arcgis.gis.admin import PortalAdminManager
import datetime as _dt
from typing import Any

def handler(event, context):
    message = 'Hello from AWS Lambda using ArcGIS API for Python ' + arcgis.__version__ + '!'
    if event.get('action', 'hello_world') == 'hello_world':
        return message
    if event.get('action') == 'echo':
        return event

    gis:GIS = get_gis(event)
    logs_by_server = get_logs(gis)
    return logs_by_server

def get_gis(event):
    return GIS(url=event.get('url'), username=event.get('username'), password=event.get('password'))

def get_logs(gis):
    admin:PortalAdminManager = gis.admin
    servers:dict[str, list[str,Any]] = {admin.url: []}
    days_back:int
    ref:dict[str, Any] = {admin.url: admin.logs}
    start:_dt.datetime = _dt.datetime.now()
    jobs = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as tp:
        # gather the portal logs
        #
        days_back = admin.logs.settings.get("maxLogFileAge", 90)
        for d in range(days_back):
            future = tp.submit(admin.logs.query, 
                            **{"start_time" : start - _dt.timedelta(days=d), 
                                "end_time" : start - _dt.timedelta(days=d + 1)}
                            )
            jobs[future] = {
                            "server" : admin.url, 
                            'start_time' : start - _dt.timedelta(days=d), 
                            'end_time' : start - _dt.timedelta(days=d + 1)
                        }   
        # gather the server logs
        #
        for server in admin.servers.list():
            servers[server.url] = []
            ref[server.url] = server
            days_back = server.logs.settings.get("maxLogFileAge", 90)
            for d in range(days_back):
                future = tp.submit(server.logs.query, 
                                **{"start_time" : start - _dt.timedelta(days=d), 
                                    "end_time" : start - _dt.timedelta(days=d + 1)}
                                )
                jobs[future] = {
                                "server" : server.url, 
                                'start_time' : start - _dt.timedelta(days=d), 
                                'end_time' : start - _dt.timedelta(days=d + 1)
                            }   
        #  Push the log entries into the servers. 
        #
        for job in concurrent.futures.as_completed(jobs):
            try:
                records = job.result()
                servers[jobs[job]['server']].extend(records.get("logMessages", []))
            except:
                # retry the operation on 504 timeout
                params = jobs[job]
                server_url = params.pop('server')
                servers[server_url].extend(ref[server_url].logs.query(**params))
        return servers