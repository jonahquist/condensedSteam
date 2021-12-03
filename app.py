from flask import Flask
from flask import current_app as app
from flask import render_template
import urllib.parse, urllib.request, urllib.error, json
from config import api_key

app = Flask(__name__)

@app.route("/")
def home():
    """home page"""
    return render_template(
        'home.html'
    )
    
    
def pretty(obj):
    return json.dumps(obj, sort_keys=True, indent=2)

def safeget(url):
    try:
        return urllib.request.urlopen(url)
    except urllib.error.URLError as e:
        if hasattr(e, "code"):
            print(e.code)
    return None

def STEAM_REST(service, request, version, **kwargs):
    url = f"http://api.steampowered.com/{service}/{request}/{version}/"
    dataDict = kwargs
    dataDict["format"] = "json"
    url = url + "?" + urllib.parse.urlencode(dataDict)
    return json.loads(safeget(url).read())

class User:
    
    def __init__(self, steamid: str):
        playerSummary = STEAM_REST("ISteamUser", "GetPlayerSummaries", "v0002", key=api_key, steamids = steamid)
        friendList = STEAM_REST("ISteamUser", "GetFriendList", "v0002", key=api_key, steamids = steamid)
        

    def requestPlayerSummary(self, steamid):
         pass
     
jsonfile = STEAM_REST("ISteamUser", "GetPlayerSummaries", "v0002", key = api_key, steamids = "76561197960435530")
print(pretty(jsonfile))

