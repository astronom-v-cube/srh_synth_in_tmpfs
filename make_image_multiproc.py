import os
import logging
import concurrent.futures
from synthesis_utils import GlobaMultiSynth
from tqdm import tqdm
import itertools
import os
from tqdm import tqdm
from threading import Lock

###### Для заполнения ######
observation_range = '1224'
path_to_calib_tables = '/home/dmitry/Documents/calib_tables/2024/20240514 - 1224 - 02-02-49.json'
directory_of_data = '/home/dmitry/14may/1224/data'
directory_of_result = '/mnt/astro/14maytetette'
all_tasks_file = "all_tasks.json"
done_tasks_file = "done_tasks.json"
flags_freq = [12960, 13720, 14480, 15240, 16760, 17520, 18280, 19040, 19800, 20560, 21320, 22080, 23400]#[12960, 13720, 23000]
number_of_clean_iter = 200000

frequencies = list(range(16))
scans = list(range(20))
num_threads = 10
######                ######

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
        print(f"Error processing {task}: {e}")
        return task, False

def main(files, frequencies, scans, num_threads, all_tasks_file, done_tasks_file):
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

    with tqdm(total=len(list(all_tasks)), desc="Progress", bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} tasks") as pbar:
        pbar.update(len(list(done_tasks)))

        with concurrent.futures.ProcessPoolExecutor(max_workers=num_threads) as executor:
            future_to_task = {executor.submit(task_wrapper, task): task for task in remaining_tasks}
            for future in concurrent.futures.as_completed(future_to_task):
                task, success = future.result()
                if success:
                    done_tasks.add(task)
                    with lock:
                        synthesizer.save_progress(all_tasks_file, done_tasks_file, all_tasks, list(done_tasks))
                    pbar.update(1)

    synthesizer.remove_progress(all_tasks_file, done_tasks_file)

if __name__ == "__main__":
    main(files, frequencies, scans, num_threads, all_tasks_file, done_tasks_file)



