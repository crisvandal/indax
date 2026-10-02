#!/usr/bin/env python3
"""Sync Cris Vandal artist data from Spotify Web API into spotify.json."""
import base64,json,os,urllib.parse,urllib.request
from datetime import datetime,timezone
ARTIST_ID="3lTEF7QXEyJuCA2uGytIK2"; MARKET=os.getenv("SPOTIFY_MARKET","US"); LIMIT=12
def request(url,headers=None,data=None,method=None):
    req=urllib.request.Request(url,headers=headers or {},data=data,method=method)
    with urllib.request.urlopen(req,timeout=30) as res:return json.loads(res.read().decode())
def token():
    cid=os.getenv("SPOTIFY_CLIENT_ID"); secret=os.getenv("SPOTIFY_CLIENT_SECRET")
    if not cid or not secret:raise SystemExit("SPOTIFY_CLIENT_ID / SPOTIFY_CLIENT_SECRET are not set")
    auth=base64.b64encode(f"{cid}:{secret}".encode()).decode()
    body=urllib.parse.urlencode({"grant_type":"client_credentials"}).encode()
    return request("https://accounts.spotify.com/api/token",{"Authorization":f"Basic {auth}","Content-Type":"application/x-www-form-urlencoded"},body,"POST")["access_token"]
def main():
    h={"Authorization":f"Bearer {token()}"}
    artist=request(f"https://api.spotify.com/v1/artists/{ARTIST_ID}",h)
    albums=request("https://api.spotify.com/v1/artists/"+ARTIST_ID+"/albums?"+urllib.parse.urlencode({"include_groups":"album,single,compilation","market":MARKET,"limit":LIMIT}),h)["items"]
    tracks=request("https://api.spotify.com/v1/artists/"+ARTIST_ID+"/top-tracks?"+urllib.parse.urlencode({"market":MARKET}),h)["tracks"]
    seen=set(); releases=[]
    for a in albums:
        if a["id"] in seen:continue
        seen.add(a["id"]); releases.append({"id":a["id"],"name":a["name"],"type":a["album_type"],"release_date":a["release_date"],"total_tracks":a["total_tracks"],"image":(a.get("images") or [{}])[0].get("url"),"url":a["external_urls"]["spotify"]})
    out={"artist":{"id":artist["id"],"name":artist["name"],"url":artist["external_urls"]["spotify"],"followers":artist["followers"]["total"],"genres":artist.get("genres",[]),"image":(artist.get("images") or [{}])[0].get("url")},"releases":releases,"top_tracks":[{"id":t["id"],"name":t["name"],"album":t["album"]["name"],"image":(t["album"].get("images") or [{}])[0].get("url"),"url":t["external_urls"]["spotify"],"duration_ms":t["duration_ms"]} for t in tracks],"updated_at":datetime.now(timezone.utc).isoformat()}
    with open("spotify.json","w",encoding="utf-8") as f:json.dump(out,f,ensure_ascii=False,indent=2);f.write("\n")
    print(f"Synced {len(releases)} releases and {len(tracks)} top tracks")
if __name__=="__main__":main()
