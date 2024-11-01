import logging
from aiogram import F, Dispatcher
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.storage.memory import MemoryStorage
import requests
from aiogram.fsm.context import FSMContext
from config import API_TOKEN
from aiogram.filters import Command
from aiogram.filters.state import State, StatesGroup
from aiogram.filters import StateFilter
import asyncio
bot = Bot(API_TOKEN)

dp = Dispatcher(storage=MemoryStorage())
# OpenWeatherMap API URL
WEATHER_BASE_URL = "http://api.openweathermap.org/data/2.5"
API_KEY = '2743b4a0f99648c34789d9dcfb3ad81d'
# Команда /start
@dp.message(Command('start'))
async def send_welcome(message: types.Message):
    await message.answer(
        "Привет! Я WeatherBot. Я могу предоставить прогноз погоды для вашего маршрута.\n"
        "Используйте команду /weather для начала."
    )

# Команда /help
@dp.message(Command('help'))
async def send_help(message: types.Message):
    await message.reply(
        "Доступные команды:\n"
        "/start - Приветствие и объяснение функционала\n"
        "/help - Список доступных команд\n"
        "/weather - Получить прогноз погоды для маршрута\n"
    )

# Команда /weather
@dp.message(Command('weather'), StateFilter(None))
async def weather_command(message: types.Message, state: FSMContext):
    await message.reply("Введите начальную точку маршрута (широта, долгота):")
    
    await state.set_state(WeatherStates.START_LOCATION)

# Состояния для машины состояний


class WeatherStates(StatesGroup):
    START_LOCATION = State()
    END_LOCATION = State()
    FORECAST_INTERVAL = State()

# Обработка начальной точки маршрута
@dp.message(StateFilter(WeatherStates.START_LOCATION))
async def process_start_location(message: types.Message, state: FSMContext):
    await state.update_data(start_location=message.text)
    await message.reply("Введите конечную точку маршрута (широта, долгота):")
    await state.set_state(WeatherStates.END_LOCATION)

# Обработка конечной точки маршрута
@dp.message(StateFilter(WeatherStates.END_LOCATION))
async def process_end_location(message: types.Message, state: FSMContext):
    await state.update_data(end_location=message.text)
    buttons = [
        [
            InlineKeyboardButton(text="Прогноз на 3 дня", callback_data='3')
        ],[
            InlineKeyboardButton(text="Прогноз на неделю", callback_data='7')
        ]
    ]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.reply("Выберите временной интервал прогноза:", reply_markup=keyboard)
    await state.set_state(WeatherStates.FORECAST_INTERVAL)

# Обработка выбора временного интервала
@dp.callback_query(StateFilter(WeatherStates.FORECAST_INTERVAL))
async def process_forecast_interval(callback_query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    days = int(callback_query.data)
    await state.update_data(days=days)


    start_lat, start_lon = map(float, data['start_location'].split(','))
    end_lat, end_lon = map(float, data['end_location'].split(','))

    start_weather = fetch_weather_forecast(start_lat, start_lon, days)
    end_weather = fetch_weather_forecast(end_lat, end_lon, days)

    if not start_weather or not end_weather:
        await callback_query.message.answer("Ошибка: Невозможно получить данные прогноза!")
        await state.clear()
        return
    start_response = format_weather(start_weather) 
    start_response = start_response.split("\n\n")
    print(start_response)
    await callback_query.message.answer('Прогноз погоды для начальной точки')
    for resp in start_response:
        await callback_query.message.answer(resp)

    end_response = format_weather(end_weather) 
    end_response = end_response.split("\n\n")
    await callback_query.message.answer('Прогноз погоды для конечной точки')
    for resp in end_response:
        await callback_query.message.answer(resp)

    await state.clear()

# Функция для получения прогноза погоды
def fetch_weather_forecast(lat, lon, days=1):
    forecast_request_url = f"{WEATHER_BASE_URL}/forecast?lat={lat}&lon={lon}&cnt={days * 8}&appid={API_KEY}&units=metric"
    try:
        weather_response = requests.get(forecast_request_url)
        if weather_response.status_code != 200:
            return None
        return weather_response.json()
    except Exception:
        return None

# Функция для форматирования прогноза погоды
def format_weather(weather):
    forecast = ""
    for day in weather['list']:
        forecast += (
            f"Дата: {day['dt_txt']}\n"
            f"Мин. температура: {day['main']['temp_min']}°C\n"
            f"Макс. температура: {day['main']['temp_max']}°C\n"
            f"Скорость ветра: {day['wind']['speed']} м/с\n"
            f"Вероятность осадков: {day['pop'] * 100}%\n\n"
        )
    
    return forecast


async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())