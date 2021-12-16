from flask import Flask
from flask import current_app as app
from flask import render_template, request
import urllib.parse, urllib.request, urllib.error, json
from config import steam_api_key, rawg_api_key
import datetime

TEMPLATES_AUTO_RELOAD = True
app = Flask(__name__)

@app.route("/")
def home():
    """home page"""
    app.logger.info("In home")
    return render_template(
        'home.html'
    )

@app.route("/steamid")
def steamid_response_handler():
    steamid = request.args.get('steamIDResponse')
    app.logger.info(steamid)
    try:
        user = MainUser(steamid)
        try:
            return render_template('condensed.html',
                steamid=steamid,
                user=user
                )
        except:
            app.logger.info("Failed to Load Condensed")
    except:
            return render_template('home.html',
                prompt="Oh no! Steam ID you input was invalid. Double Check that your profile is public!"
                )
    
if __name__ == "__main__":
    app.run(host="localhost", port=8080, debug=True)

def pretty(obj):
    return json.dumps(obj, sort_keys=True, indent=2)

def safeget(url):
    try:
        app.logger.info(url)
        return urllib.request.urlopen(url)
    except urllib.error.URLError as e:
        if hasattr(e, "code"):
            print(e.code)
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
        app.logger.info("Accessing Player Summary...")
        self.playerSummaryJSON = STEAM_REST("ISteamUser", "GetPlayerSummaries", "v0002", steamids = steamid)
        app.logger.info(self.playerSummaryJSON)
        
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
        
        timestamp = datetime.datetime.fromtimestamp(self.friendsince)
        self.frienddate = timestamp.strftime('%Y-%m-%d')

    def getFriendSince(self):
        return self.friendsince
    
    def __repr__(self):
        return f"{self.personaname} friends since {self.friendsince}"
    
class MainUser(User):
    
    def __init__(self, steamid: str):
        User.__init__(self, steamid = steamid)
        
        self.mainuser = True
        
        app.logger.info("Accessing Friends List...")
        self.friendListJSON = STEAM_REST("ISteamUser", "GetFriendList", "v0001", steamid = steamid, relationship = "friend")
        app.logger.info(self.friendListJSON)
        
        app.logger.info("Accessing Owned Games List...")
        self.ownedGamesJSON = STEAM_REST("IPlayerService", "GetOwnedGames", "v0001", steamid = steamid, include_appinfo = 1)
        app.logger.info(self.ownedGamesJSON)
        
        app.logger.info("Finished API Requests...")
        
        #GAMES CODE
        self.games = []
        for game in self.ownedGamesJSON["response"]["games"]:
            self.games.append(Game(game))
            
        #for i in range(20):
            #self.games.append(Game(self.ownedGamesJSON["response"]["games"][i]))
            
        #self.games = [Game[x] for x in self.ownedGamesJSON["response"]["games"]]
        self.game_count = self.ownedGamesJSON["response"]["game_count"]
        app.logger.info("!!Games Compiled!!")      
        self.rawgGames = []
        
        
        self.friends = []
        for user in self.friendListJSON["friendslist"]["friends"]:
            self.friends.append(FriendUser(user["steamid"], user["friend_since"]))
        #self.friends = [User[x] for x in self.friendListJSON["friendslist"]["friends"]]
        
        app.logger.info("success~")
    
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
        genres = sorted(genres.items(), key=lambda x: x[1], reverse=True)
        return genres
            
    def getNewFriends(self):
        newFriends = []
        for friend in self.friends:
            if (friend.friendsince > 1609488000):
                newFriends.append(friend)
        newFriends = sorted(newFriends, key=FriendUser.getFriendSince, reverse = True)
        return newFriends

class Game:
    
    def __init__(self, gameJson):
        self.appid = gameJson['appid']
        self.img_logo_url = f"http://media.steampowered.com/steamcommunity/public/images/apps/{self.appid}/{gameJson['img_logo_url']}.jpg"
        app.logger.info(f"{self.img_logo_url}!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!1")
        self.name = gameJson['name']
        self.playtime_forever = gameJson['playtime_forever']
        self.hours = int(self.playtime_forever / 60)
        if "playtime_2weeks" in gameJson:
            self.playtime_2weeks = gameJson['playtime_2weeks']
        else:
            self.playtime_2weeks = 0
         
    def __repr__(self):
        return f"{self.name}"         
            
    def getPlaytime(self):
        return self.playtime_forever
    

    
    def getGenres(self):
        if (self.checkRawg()):
            genres = []
            for genre in self.tentativerawg["genres"]:
                genres.append(genre['name'])
            return genres
        else:
            return []
    
    def getRawg(self):
        print(f"checking rawg...{self.name}")
        rest = RAWG_REST("games", search=self.name)
        print(f"rest complete for {self.name}")
        if (self.name == "tModLoader"):
            print(rest)
        if (rest['count'] != 0):
            self.tentativerawg = rest["results"][0]
            self.tentativerawg["confirmed"] = self.compareRawg()
        else:
            print(self.name)
            self.tentativerawg = {}
            self.tentativerawg['confirmed'] = False;
            
    def compareRawg(self):
        return (self.tentativerawg["name"] == self.name)
        
    def checkRawg(self):
        if (self.tentativerawg == None or self.tentativerawg['confirmed'] == False):
            return False
        else:
            return True
