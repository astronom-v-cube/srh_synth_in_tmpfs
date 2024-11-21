import os
import logging
import concurrent.futures
from synthesis_utils import GlobaMultiSynth
from tqdm import tqdm
import itertools
import os
from tqdm import tqdm
from threading import Lock
import sys

from config import *

synthesizer = GlobaMultiSynth(directory_of_data, directory_of_result, path_to_calib_tables, number_of_clean_iter)
synthesizer.start_log('synth_log')
synthesizer.start_procedures()
lock = Lock()

files = sorted(os.listdir(directory_of_data))
logging.info(f'Список файлов: {files}')

list_of_freqs = synthesizer.indicate_observation_range(observation_range)
synthesizer.create_places(directory_of_result, list_of_freqs, flags_freq)

def task_wrapper(task):
    file_name, frequency, scan_number = task
    try:
        synthesizer.image_maker(file_name, frequency, scan_number)
        return task, True
    except Exception as e:
        logging.info(f"Error processing {task}: {e}")
        return task, False

def main():
    synthesizer.remove_srh_directories()
    os.system('python -m casaconfig --update-all')

    all_tasks = [
        (file, freq, scan)
        for file, freq, scan in itertools.product(files, frequencies, scans)
        if list_of_freqs[freq] not in flags_freq
    ]

    saved_all_tasks, saved_done_tasks = synthesizer.load_progress(all_tasks_file, done_tasks_file)

    # Если сохранённый список задач совпадает с текущим, продолжаем с того места, где остановились
    if set(tuple(task) for task in saved_all_tasks) == set(tuple(task) for task in all_tasks):
        done_tasks = saved_done_tasks
    else:
        # Иначе начинаем заново и сохраняем прогресс
        done_tasks = set()

    remaining_tasks = [task for task in all_tasks if task not in done_tasks]

    try:
        with tqdm(total=len(list(all_tasks)), desc="Progress", bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} tasks") as pbar:
            pbar.update(len(list(done_tasks)))

            with concurrent.futures.ProcessPoolExecutor(max_workers=num_threads) as executor:
                try:
                    future_to_task = {executor.submit(task_wrapper, task): task for task in remaining_tasks}
                    for future in concurrent.futures.as_completed(future_to_task):
                        task, success = future.result()
                        if success:
                            done_tasks.add(task)
                            with lock:
                                synthesizer.save_progress(all_tasks_file, done_tasks_file, all_tasks, list(done_tasks))
                            pbar.update(1)

                except KeyboardInterrupt:
                        print("  <- Получен сигнал остановки. Завершаю уже запущенные процессы...")
                        for future in future_to_task:
                            future.cancel()
                        executor.shutdown(wait=True)
                        raise

    except KeyboardInterrupt:
        synthesizer.remove_srh_directories()
        print('Остановлено вручную. Процессы завершены. RAM очищена. Дамп задач сохранен')
        sys.exit()

    synthesizer.remove_progress(all_tasks_file, done_tasks_file)