import requests

download_url = 'http://127.0.0.1:5000/api/download'
data = {'filename': 'engineer.txt'}
response = requests.post(download_url, json=data)

if response.status_code == 200:
    with open(f"{data['filename']}", 'wb') as file:
        file.write(response.content)
else:
    print(response.json())