import json
import urllib.request
try:
    response = urllib.request.urlopen("http://localhost:5173")
    print(response.getcode())
except Exception as e:
    print(e)
