import arcgis

def handler(event, context):
    return 'Hello from AWS Lambda using ArcGIS API for Python ' + arcgis.__version__ + '!'   