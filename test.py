import requests

response = requests.get('https://game.gtimg.cn/images/lol/act/img/tft/js/hex.js')

print(response.json())