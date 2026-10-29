from flask import Flask, render_template, request, jsonify
import requests

app = Flask(__name__, template_folder='../templates', static_folder='../static')

# API Geocoding Open-Meteo untuk mencari koordinat berdasarkan nama kota
GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
# API Forecast Open-Meteo
WEATHER_URL = "https://api.open-meteo.com/v1/forecast"

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/cuaca', methods=['GET'])
def get_cuaca():
    kota = request.args.get('kota', 'Semarang')
    
    try:
        # 1. Cari Koordinat Kota
        geo_res = requests.get(GEOCODING_URL, params={'name': kota, 'count': 1, 'language': 'id', 'format': 'json'}).json()
        
        if not geo_res.get('results'):
            return jsonify({'error': f'Kota "{kota}" tidak ditemukan.'}), 404
            
        location = geo_res['results'][0]
        lat = location['latitude']
        lon = location['longitude']
        nama_lokasi = f"{location['name']}, {location.get('admin1', '')} {location.get('country', '')}".strip()

        # 2. Ambil Data Cuaca dari Open-Meteo
        weather_params = {
            'latitude': lat,
            'longitude': lon,
            'current': 'temperature_2m,relative_humidity_2m,apparent_temperature,weather_code,wind_speed_10m',
            'daily': 'weather_code,temperature_2m_max,temperature_2m_min',
            'timezone': 'auto'
        }
        w_res = requests.get(WEATHER_URL, params=weather_params).json()

        # 3. Format Data untuk Dikirim ke Front-End
        result = {
            'lokasi': nama_lokasi,
            'saat_ini': {
                'suhu': round(w_res['current']['temperature_2m']),
                'terasa_seperti': round(w_res['current']['apparent_temperature']),
                'kelembapan': w_res['current']['relative_humidity_2m'],
                'kecepatan_angin': w_res['current']['wind_speed_10m'],
                'kode_cuaca': w_res['current']['weather_code']
            },
            'harian': []
        }

        # Format prakiraan 5 hari ke depan
        daily = w_res['daily']
        for i in range(min(5, len(daily['time']))):
            result['harian'].append({
                'tanggal': daily['time'][i],
                'temp_max': round(daily['temperature_2m_max'][i]),
                'temp_min': round(daily['temperature_2m_min'][i]),
                'kode_cuaca': daily['weather_code'][i]
            })

        return jsonify(result)

    except Exception as e:
        return jsonify({'error': 'Gagal mengambil data cuaca.', 'detail': str(e)}), 500

# Wajib ada untuk penanganan eksekusi Vercel
if __name__ == '__main__':
    app.run(debug=True)