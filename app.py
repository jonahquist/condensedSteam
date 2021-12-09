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
        self.playerSummaryJSON = STEAM_REST("ISteamUser", "GetPlayerSummaries", "v0002", key=api_key, steamids = steamid)
        
        self.steamid=steamid
        self.mainuser = False
        
        self.personaname=self.playerSummaryJSON["response"]["players"][0]["personaname"]
        self.avatar=self.playerSummaryJSON["response"]["players"][0]["avatar"]
        
    def __str__(self):
        return ""

class MainUser(User):
    
    def __init__(self, steamid: str):
        super.__init__(self, steamid)
        
        self.mainuser = True
        
        self.friendListJSON = STEAM_REST("ISteamUser", "GetFriendList", "v0001", key=api_key, steamid = steamid, relationship = "friend")
        self.ownedGamesJSON = STEAM_REST("IPlayerService", "GetOwnedGames", "v0001", key=api_key, steamid = steamid, include_appinfo = True)
         
        self.games = [Game[x] for x in self.ownedGamesJSON["response"]["games"]]
        self.game_count = self.ownedGamesJSON["response"]["game_count"]
        
        self.friends = [User[x] for x in self.friendListJSON["friendslist"]["friends"]]



class Game:
    
    def __init__(self, gameJson):
        self.appid = gameJson['appid']
        self.img_logo_url = gameJson['img_logo_url']
        self.name = gameJson['name']
        self.playtime_forever = gameJson['playtime_forever']
        if "playtime_2weeks" in gameJson:
            self.playtime_2weeks = gameJson['playtime_2weeks']
        else:
            self.playtime_2weeks = 0
           
        
        
     
jsonfile = STEAM_REST("ISteamUser", "GetFriendList", "v0001", key=api_key, steamid = "76561197960435530", relationship = "friend")
print(pretty(jsonfile))
