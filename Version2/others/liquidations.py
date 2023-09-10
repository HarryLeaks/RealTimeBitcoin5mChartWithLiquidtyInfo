import requests
import json

url1 = "https://open-api.coinglass.com/public/v2/liquidation_ex?time_type=h1&symbol=all"
url4 = "https://open-api.coinglass.com/public/v2/liquidation_ex?time_type=h4&symbol=all"
url12 = "https://open-api.coinglass.com/public/v2/liquidation_ex?time_type=h12&symbol=all"
url24 = "https://open-api.coinglass.com/public/v2/liquidation_ex?time_type=h24&symbol=all"

def getLiquitations(url):
    headers = {
        "accept": "application/json",
        "coinglassSecret": "8bc3f71a794b4d81b23d059bd0d12ec7"
    }

    response = requests.get(url, headers=headers)

    data = json.loads(response.text)

    for entry in data['data']:
        if entry['exchangeName'] == 'All':
            longVolUsd = entry['longVolUsd']
            shortVolUsd = entry['shortVolUsd']
            break

    return longVolUsd, shortVolUsd

getLiquitations(url1)
getLiquitations(url4)
getLiquitations(url12)
getLiquitations(url24)