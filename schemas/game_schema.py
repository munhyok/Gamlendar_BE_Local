

def game_serializer(game) -> dict:
    return {
        'id':str(game["_id"]),
        'timestamp':game["timestamp"],
        'path':game["path"],
        'gindie':game["gindie"],
        'name':game["name"],
        'autokwd':game["autokwd"],
        'company':game["company"],
        'yearmonth':game["yearmonth"],
        'date':game["date"],
        'description':game["description"],
        'platform':game["platform"],
        'gameurl':game["gameurl"],
        'imageurl':game["imageurl"],
        'yturl':game["yturl"],
        'screenshots':game["screenshots"],
        
        'adult':game["adult"]
    }
    
def games_serializer(games) -> list:
    return [game_serializer(game) for game in games]