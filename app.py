from flask import Flask
from flask import current_app as app
from flask import render_template
import urllib.parse, urllib.request, urllib.error, json
from config import steam_api_key, rawg_api_key

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
        print("AHHH it didnt work")
    return None

def STEAM_REST(service, request, version, **kwargs):
    url = f"http://api.steampowered.com/{service}/{request}/{version}/"
    dataDict = kwargs
    dataDict["format"] = "json"
    dataDict["key"] = steam_api_key
    url = url + "?" + urllib.parse.urlencode(dataDict)
    return json.loads(safeget(url).read())

def RAWG_REST(*args, **kwargs):
    url = "https://api.rawg.io/api"
    for arg in args: # ["games"]
        url += f"/{arg}" # https://api.rawg.io/api/games
    dataDict = kwargs # {"search" : "Halo", "ordering" : "name"}
    dataDict["key"] = rawg_api_key
    url = url + "?" + urllib.parse.urlencode(dataDict) # https://api.
    return json.loads(safeget(url).read())

class User:
    
    def __init__(self, steamid: str):
        self.playerSummaryJSON = STEAM_REST("ISteamUser", "GetPlayerSummaries", "v0002", steamids = steamid)
        
        self.steamid=steamid
        self.mainuser = False
        
        self.personaname=self.playerSummaryJSON["response"]["players"][0]["personaname"]
        self.avatar=self.playerSummaryJSON["response"]["players"][0]["avatar"]
        
    def __str__(self):
        return ""

class FriendUser(User):
    
    def __init__(self, steamid: str, friendsince):
        User.__init__(self, steamid = steamid)
        
        self.friendsince = friendsince

    def __repr__(self):
        return f"{self.personaname} friends since {self.friendsince}"
    
class MainUser(User):
    
    def __init__(self, steamid: str):
        User.__init__(self, steamid = steamid)
        
        self.mainuser = True
        
        self.friendListJSON = STEAM_REST("ISteamUser", "GetFriendList", "v0001", steamid = steamid, relationship = "friend")
        self.ownedGamesJSON = STEAM_REST("IPlayerService", "GetOwnedGames", "v0001", steamid = steamid, include_appinfo = True)
        
        self.games = []
        #for game in self.ownedGamesJSON["response"]["games"]:
            #self.games.append(Game(game))
            
        for i in range(20):
            self.games.append(Game(self.ownedGamesJSON["response"]["games"][i]))
            
        #self.games = [Game[x] for x in self.ownedGamesJSON["response"]["games"]]
        self.game_count = self.ownedGamesJSON["response"]["game_count"]
        
        self.friends = []
        for user in self.friendListJSON["friendslist"]["friends"]:
            self.friends.append(FriendUser(user["steamid"], user["friend_since"]))
        #self.friends = [User[x] for x in self.friendListJSON["friendslist"]["friends"]]
        
        self.rawgGames = []

    def getMostPlayed(self):
        mostPlayed = []
        mostPlayed = sorted(self.games, key=Game.getPlaytime, reverse=True)
        for i in range(10):
            mostPlayed[i].getRawg()
            self.rawgGames.append(mostPlayed[i])
        return mostPlayed

    def getMostGenres(self):
        genres = {}
        for game in self.games:
            if (game not in self.rawgGames):
                game.getRawg()
                self.rawgGames.append(game)
            for genre in game.getGenres():
                genres[genre] = genres.get(genre, 0) + 1
        return genres
            
    def getNewFriends(self):
        newFriends = []
        for friend in self.friends:
            if (friend.friendsince > 1609488000):
                newFriends.append(friend)
        return newFriends

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
            
    def getPlaytime(self):
        return self.playtime_forever
    
    def __repr__(self):
        return f"{self.name}"
    
    def getGenres(self):
        if (self.checkRawg()):
            genres = []
            for genre in self.tentativerawg["genres"]:
                genres.append(genre['name'])
            return genres
        else:
            return []
    
    def getRawg(self):
        self.tentativerawg = RAWG_REST("games", search=self.name)["results"][0]
        self.tentativerawg["confirmed"] = self.compareRawg()
        print("checking rawg...")
    
    def compareRawg(self):
        return (self.tentativerawg["name"] == self.name)
    
    def checkRawg(self):
        if (self.tentativerawg == None or self.tentativerawg["confirmed"] == False):
            return False
        else:
            return True



gamer = MainUser("76561197960434622")
#mostPlayed = gamer.getMostPlayed()
#for i in range(5):
    #print(f"{mostPlayed[i].name} {mostPlayed[i].playtime_forever}")

print(gamer.getNewFriends())
"""gamer = MainUser("76561197960434622")

print("----Steam----")

falsecount = 0
truecount = 0

for game in gamer.games:
    boolin = True
    rawg = RAWG_REST("games", search=game.name)["results"][0]["name"]
    if (game.name == rawg):
        boolin = True
        truecount += 1 
    else:
        boolin = False
        falsecount += 1
    print(f"{boolin} - STEAM: {game.name} - RAWG: {rawg}")

print(falsecount)
print(truecount)

for i in range(5):
    name = gamer.games[i].name
    search = RAWG_REST("games", search=name)
    print(search["results"][0]["name"])
#rawgtest = RAWG_REST("games", search="Halo", ordering="name")
#print(pretty(rawgtest))
"""