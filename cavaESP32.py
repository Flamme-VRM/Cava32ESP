import numpy as np
import pyaudiowpatch as pyaudio
import serial
import struct
import sys
import time

# --- НАСТРОЙКИ ---
PORT = 'COM3'         # Твой COM-порт
BAUD = 1000000        # Скорость как в Arduino (важно!)
NUM_BARS = 10         # Количество столбиков
CHUNK = 1024          # Размер буфера
CHANNELS = 2          # Windows Loopback почти всегда Стерео
RATE = 48000          # Частота дискретизации

# 1. Сначала поставь None, запусти, найди ID устройства с пометкой [Loopback]
# 2. Впиши сюда этот ID (целое число)
DEVICE_INDEX = 13

# --- ИНИЦИАЛИЗАЦИЯ PYAUDIO ---
p = pyaudio.PyAudio()

# --- ПОИСК УСТРОЙСТВА (WASAPI LOOPBACK) ---
if DEVICE_INDEX is None:
    print("------------------------------------------------")
    print("Поиск устройств вывода (WASAPI Loopback)...")
    print("Ищи устройство с названием твоих динамиков/наушников.")
    print("------------------------------------------------")
    
    # Ищем Host API для WASAPI
    wasapi_info = None
    for i in range(p.get_host_api_count()):
        api = p.get_host_api_info_by_index(i)
        if "WASAPI" in api["name"]:
            wasapi_info = api
            break
            
    if wasapi_info:
        # Перебираем устройства только этого API
        for i in range(p.get_device_count()):
            dev = p.get_device_info_by_index(i)
            if dev["hostApi"] == wasapi_info["index"]:
                # Декодируем имя (исправление кириллицы)
                try:
                    name = dev['name'].encode('cp1251').decode('utf-8')
                except:
                    name = dev['name']
                
                # Показываем только устройства, которые могут быть входными (loopback тоже считается входом)
                if dev["maxInputChannels"] > 0:
                    print(f"ID {i}: {name} (Inputs: {dev['maxInputChannels']})")
    else:
        print("ОШИБКА: WASAPI не найден. Убедитесь, что вы на Windows.")

    print("------------------------------------------------")
    print(">>> Впиши ID нужного устройства в переменную 'DEVICE_INDEX' в коде!")
    p.terminate()
    sys.exit()

# --- ПОДКЛЮЧЕНИЕ К ARDUINO ---
try:
    ser = serial.Serial(PORT, BAUD, timeout=0.1)
    time.sleep(2) # Ждем перезагрузки Arduino
    print(f"Подключено к {PORT}")
except Exception as e:
    print(f"Ошибка COM-порта: {e}")
    sys.exit()

# --- ЗАПУСК ПОТОКА ---
try:
    stream = p.open(
        format=pyaudio.paInt16,
        channels=CHANNELS,
        rate=RATE,
        input=True,
        input_device_index=DEVICE_INDEX,
        frames_per_buffer=CHUNK
    )
    print("Визуализатор работает! Нажми Ctrl+C для выхода.")
except Exception as e:
    print(f"Ошибка открытия аудиопотока: {e}")
    print("Совет: Попробуй включить 'Стерео микшер' в настройках звука Windows или используй библиотеку 'pyaudiowpatch'.")
    ser.close()
    p.terminate()
    sys.exit()

# --- ОСНОВНОЙ ЦИКЛ ---
try:
    while True:
        # 1. Читаем данные
        try:
            raw_data = stream.read(CHUNK, exception_on_overflow=False)
        except:
            continue
            
        # 2. Конвертируем в массив чисел
        data_int = np.frombuffer(raw_data, dtype=np.int16)
        
        # 3. ПРЕОБРАЗОВАНИЕ СТЕРЕО В МОНО (Важно для Loopback!)
        # Берем каждый второй семпл (левый канал), чтобы уменьшить массив в 2 раза
        # Если этого не сделать, FFT будет "шуметь" из-за смешивания каналов
        data_mono = data_int[::2] 
        
        # 4. FFT (Преобразование Фурье)
        fft_data = np.abs(np.fft.rfft(data_mono))
        
        # Обрезаем высокие частоты (оставляем басы и середину, где больше всего "движения")
        # Для музыки обычно интересны первые 50-100 отсчетов при CHUNK=1024
        fft_data = fft_data[:150] 
        
        # 5. Разбиваем на 10 столбиков
        bands = np.array_split(fft_data, NUM_BARS)
        
        # 6. Считаем среднюю громкость для каждого столбика
        # Delimiter (делитель) 500 подобран для системного звука (он громче микрофона)
        # Если столбики слишком низкие -> уменьши 500 до 100 или 50
        # Если все забито до потолка -> увеличь 500 до 1000
        bar_data = [int(np.sum(band) / 500) for band in bands]
        
        # 7. Ограничиваем диапазон 0-255
        bar_data = [min(255, max(0, b)) for b in bar_data]
        
        # 8. Отправляем на Arduino
        # Формат: 'B' (байт заголовка) + 10 байт данных
        packet = struct.pack('B' + 'B' * NUM_BARS, ord('B'), *bar_data)
        ser.write(packet)

except KeyboardInterrupt:
    print("\nОстановка...")
    stream.stop_stream()
    stream.close()
    p.terminate()
    ser.close()