import http.client

conn = http.client.HTTPSConnection("v3.football.api-sports.io")

headers = {
    'x-apisports-key': "76c113ca9ce35931c0ee5e0db56b7c42"
    }

conn.request("GET", "/teams?id=33", headers=headers)

res = conn.getresponse()
data = res.read()
print(data)
