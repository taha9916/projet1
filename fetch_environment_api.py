import requests
import pandas as pd

def fetch_openweathermap(lat, lon, api_key):
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=metric&lang=fr"
    r = requests.get(url)
    r.raise_for_status()
    data = r.json()
    res = {
        'Température': data['main']['temp'],
        'Humidité': data['main']['humidity'],
        'Pression': data['main']['pressure'],
        'Vent': data['wind']['speed'],
        'Ciel': data['weather'][0]['description'],
    }
    return res

def fetch_aqicn(lat, lon, token):
    url = f"https://api.waqi.info/feed/geo:{lat};{lon}/?token={token}"
    r = requests.get(url)
    r.raise_for_status()
    data = r.json()
    if data['status'] != 'ok':
        return {}
    iaqi = data['data'].get('iaqi', {})
    res = {}
    for k, v in iaqi.items():
        res[k] = v.get('v')
    return res

def get_environmental_data(lat, lon):
    owm_key = "4d6683b49a192822ceb510d6f65844f1"
    aqicn_key = "2a29806f-7f37-41aa-9c33-f95a22963b73"
    meteo = fetch_openweathermap(lat, lon, owm_key)
    air = fetch_aqicn(lat, lon, aqicn_key)
    # Fusionner et structurer pour SLRI (exemple simplifié)
    df = pd.DataFrame([
        {
            'Paramètre': 'Température',
            'Milieu': 'Air',
            'Intervalle acceptable/MIN': None,
            'Intervalle acceptable/MAX': None,
            'Valeur mesurée de milieux initial': meteo.get('Température'),
            'Rejet de PHASE CONSTRUCTION': None,
            'Valeure Mesure+rejet': meteo.get('Température'),
            'Unité': '°C',
            'Justification/Calcul': 'Valeur OpenWeatherMap',
        },
        {
            'Paramètre': 'PM2.5',
            'Milieu': 'Air',
            'Intervalle acceptable/MIN': None,
            'Intervalle acceptable/MAX': None,
            'Valeur mesurée de milieux initial': air.get('pm25'),
            'Rejet de PHASE CONSTRUCTION': None,
            'Valeure Mesure+rejet': air.get('pm25'),
            'Unité': 'µg/m3',
            'Justification/Calcul': 'Valeur AQICN',
        },
        # ... Ajouter d'autres paramètres selon les données disponibles
    ])
    return df
