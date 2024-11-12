import re
import matplotlib.pyplot as plt
from datetime import datetime

# Чтение файла
log_file_path = '/home/dmitry/synth_log.log'  # Укажите путь к вашему файлу
with open(log_file_path, 'r') as file:
    log_data = file.readlines()

# Регулярное выражение для поиска времени выполнения
time_pattern = re.compile(r'Time for .*? on freq \d+ scan \d+: (\d+)')

# Списки для хранения времени выполнения и меток времени
execution_times = []
timestamps = []

# Парсинг данных
for line in log_data:
    match = time_pattern.search(line)
    if match:
        execution_time = int(match.group(1))
        execution_times.append(execution_time)

        # Извлечение временной метки
        timestamp_str = line.split(' - ')[0]
        timestamp = datetime.strptime(timestamp_str, '%d-%b-%y %H:%M:%S')
        timestamps.append(timestamp)

# Построение графика
plt.figure(figsize=(10, 5))
# plt.plot(timestamps, execution_times, marker='o')
plt.scatter(timestamps, execution_times)
plt.title('Время выполнения')
plt.xlabel('Время')
plt.ylabel('Время выполнения (секунды)')
plt.xticks(rotation=45)
plt.grid()
plt.tight_layout()
plt.show()
