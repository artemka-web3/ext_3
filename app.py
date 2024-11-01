from flask import Flask, request, render_template, redirect
import requests
from api import API_KEY
import os
import csv

app = Flask(__name__)

WEATHER_BASE_URL = "http://api.openweathermap.org/data/2.5"

def analyze_weather_conditions(min_temp, max_temp, wind_velocity, precipitation_chance):
    if min_temp < 0 or max_temp > 35:
        return "Температурные условия неблагоприятны!"
    if wind_velocity > 50:
        return "Слишком сильный ветер!"
    if precipitation_chance > 70:
        return "Высокая вероятность дождя!"
    return f"Минимальная температура: {min_temp}C\nМакс температура: {max_temp}С\nСкорость ветра: {wind_velocity} м/с\nПогодные условия удовлетворительные."

def fetch_weather_forecast(lat, lon, days=1):
    forecast_request_url = f"{WEATHER_BASE_URL}/forecast?lat={lat}&lon={lon}&cnt={days * 8}&appid={API_KEY}&units=metric"
    try:
        weather_response = requests.get(forecast_request_url)
        if weather_response.status_code != 200:
            return None
        return weather_response.json()
    except Exception:
        return None

@app.route('/')
def main_page():
    return render_template('index.html')

@app.route('/get-forecast', methods=['POST'])
def process_weather_request():
    start_lat = request.form['lat_st']
    start_lon = request.form['lon_st']
    end_lat = request.form['lat_end']
    end_lon = request.form['lon_end']
    intermediate_points = request.form.getlist('intermediate_points')
    days = int(request.form['days'])

    if not all([start_lat, start_lon, end_lat, end_lon]):
        return "Ошибка: Все координаты должны быть указаны!", 400

    locations = [(start_lat, start_lon, 'Start Location'), (end_lat, end_lon, 'End Location')]
    for point in intermediate_points:
        lat, lon = point.split(',')
        locations.append((lat.strip(), lon.strip(), 'Intermediate Location'))

    weather_data = []
    for lat, lon, loc_type in locations:
        weather = fetch_weather_forecast(lat, lon, days)
        if not weather:
            return f"Ошибка: Невозможно получить данные прогноза для {loc_type}!", 400
        weather_data.append((loc_type, weather))

    csv_file_path = '/Users/artemsidnev/Desktop/weather_extern/weather_monitoring/weather_data.csv'
    file_exists = os.path.isfile(csv_file_path)

    with open(csv_file_path, mode='a', newline='') as file:
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow(['Location', 'Day', 'Min Temp (C)', 'Max Temp (C)', 'Wind Speed (m/s)', 'Precipitation Chance (%)'])
        for loc_type, weather in weather_data:
            for day in weather['list']:
                writer.writerow([
                    loc_type,
                    day['dt_txt'],
                    day['main']['temp_min'],
                    day['main']['temp_max'],
                    day['wind']['speed'],
                    day['pop'] * 100  # Probability of precipitation
                ])

    html_content = '''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Weather Forecast</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                background-color: #f4f4f4;
                margin: 0;
                padding: 0;
                display: flex;
                flex-direction: column;
                align-items: center;
                padding: 20px;
            }
            h1 {
                color: #333;
            }
            table {
                width: 100%;
                max-width: 800px;
                border-collapse: collapse;
                margin: 20px 0;
                background: #fff;
                box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
            }
            th, td {
                padding: 12px;
                border: 1px solid #ddd;
                text-align: left;
            }
            th {
                background-color: #f2f2f2;
            }
            a {
                display: inline-block;
                margin-top: 20px;
                color: #007bff;
                text-decoration: none;
            }
            a:hover {
                text-decoration: underline;
            }
        </style>
    </head>
    <body>
        <h1>Weather Forecast</h1>
    '''

    for loc_type, weather in weather_data:
        html_content += f'<h2>{loc_type}</h2>'
        html_content += '''
        <table>
            <thead>
                <tr>
                    <th>Day</th>
                    <th>Min Temp (C)</th>
                    <th>Max Temp (C)</th>
                    <th>Wind Speed (m/s)</th>
                    <th>Precipitation Chance (%)</th>
                </tr>
            </thead>
            <tbody>
        '''
        for day in weather['list']:
            html_content += f'''
                <tr>
                    <td>{day['dt_txt']}</td>
                    <td>{day['main']['temp_min']}</td>
                    <td>{day['main']['temp_max']}</td>
                    <td>{day['wind']['speed']}</td>
                    <td>{day['pop'] * 100}</td>
                </tr>
            '''
        html_content += '''
            </tbody>
        </table>
        '''

    html_content += '''
        <a href="/">Вернуться</a>
        <br>
        <a href="/dash">Посмотреть графики</a>
    </body>
    </html>
    '''

    return html_content

@app.route('/dash')
def render_dash():
    return redirect('http://127.0.0.1:8050/')

if __name__ == '__main__':
    app.run(debug=True)