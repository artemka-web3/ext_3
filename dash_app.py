import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objs as go
import pandas as pd
import os

# Путь к CSV файлу
csv_file_path = '/Users/artemsidnev/Desktop/weather_extern/weather_monitoring/weather_data.csv'

# Проверка существования файла и создание пустого файла, если он не существует
if not os.path.isfile(csv_file_path):
    with open(csv_file_path, 'w') as file:
        file.write('Location,Day,Min Temp (C),Max Temp (C),Wind Speed (m/s),Precipitation Chance (%)\n')

# Загрузка данных из CSV файла
df = pd.read_csv(csv_file_path)

# Создание приложения Dash
app = dash.Dash(__name__)

app.layout = html.Div(children=[
    html.H1(children='Weather Data Visualization'),

    dcc.Dropdown(
        id='location-dropdown',
        options=[
            {'label': loc, 'value': loc} for loc in df['Location'].unique()
        ],
        value='Start Location'
    ),

    dcc.Dropdown(
        id='parameter-dropdown',
        options=[
            {'label': 'Min Temp (C)', 'value': 'Min Temp (C)'},
            {'label': 'Max Temp (C)', 'value': 'Max Temp (C)'},
            {'label': 'Wind Speed (m/s)', 'value': 'Wind Speed (m/s)'},
            {'label': 'Precipitation Chance (%)', 'value': 'Precipitation Chance (%)'}
        ],
        value='Min Temp (C)'
    ),

    dcc.Graph(
        id='weather-graph'
    )
])

@app.callback(
    Output('weather-graph', 'figure'),
    [Input('location-dropdown', 'value'),
     Input('parameter-dropdown', 'value')]
)
def update_graph(selected_location, selected_param):
    filtered_df = df[df['Location'] == selected_location]
    return {
        'data': [go.Scatter(
            x=filtered_df['Day'],
            y=filtered_df[selected_param],
            mode='lines+markers'
        )],
        'layout': go.Layout(
            title=f'{selected_param} for {selected_location}',
            xaxis={'title': 'Day'},
            yaxis={'title': selected_param}
        )
    }

if __name__ == '__main__':
    app.run_server(debug=True)