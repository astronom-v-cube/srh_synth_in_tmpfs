import os
import psutil
import logging
import time
import json
import re
import shutil

class GlobaMultiSynth():

    def __init__(self, directory_of_data, directory_of_result, path_to_calib_tables, number_of_clean_iter) -> None:
        self.directory_of_data = directory_of_data
        self.directory_of_result = directory_of_result
        self.path_to_calib_tables = path_to_calib_tables
        self.number_of_clean_iter = number_of_clean_iter
        self.list_of_freqs_0306 = [2800, 3000, 3200, 3400, 3600, 3800, 4000, 4200, 4400, 4600, 4800, 5000, 5200, 5400, 5600, 5800]
        self.list_of_freqs_0612 = [6000, 6400, 6800, 7200, 7600, 8000, 8400, 8800, 9200, 9600, 10000, 10400, 10800, 11200, 11600, 12000]
        self.list_of_freqs_1224 = [12200, 12960, 13720, 14480, 15240, 16000, 16760, 17520, 18280, 19040, 19800, 20560, 21320, 22080, 23000, 23400]

    @staticmethod
    def start_log(name_file : str):
        """Инициализация ```.log``` файла
        Args:
            name_file (str): название файла без расширения
        """
        logging.basicConfig(filename = f'{name_file}.log',  filemode='a', level = logging.INFO, format = '%(asctime)s - %(levelname)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S', encoding = "UTF-8")
        # encoding = "UTF-8"

    @staticmethod
    def logprint(info_msg : str):
        """Вывод отладочной информации и в консоль, и в ```.log``` файл

        Args:
            info_msg (str): строка с отладочной информацией
        """
        print(info_msg)
        logging.info(info_msg)

    @staticmethod
    def start_procedures():
        import os
        N_THREADS = "1"
        os.environ['OMP_NUM_THREADS'] = N_THREADS
        os.environ['OPENBLAS_NUM_THREADS'] = N_THREADS
        os.environ['MKL_NUM_THREADS'] = N_THREADS
        os.environ['VECLIB_MAXIMUM_THREADS'] = N_THREADS
        os.environ['NUMEXPR_NUM_THREADS'] = N_THREADS

        from casatasks import casalog
        casalog.filter('SEVERE')

    def create_places(self, directory_of_result, list_of_freqs, flags_freq):
        try:
            os.makedirs(directory_of_result)
            print('folder of result is created successfully')
            for fq in list_of_freqs:
                if fq in flags_freq:
                    pass
                else:
                    os.makedirs(f'{directory_of_result}/{fq}')
            print('subfolders of result is created successfully')

        except FileExistsError:
            logging.info('folder of output exists')

        except Exception as err:
            print(err)

    def indicate_observation_range(self, observation_range):
        if observation_range == '0306':
            return self.list_of_freqs_0306
        elif observation_range == '0612':
            return self.list_of_freqs_0612
        elif observation_range == '1224':
            return self.list_of_freqs_1224

    def find_free_ram(self):
        memory_info = psutil.virtual_memory()
        free_ram = memory_info.available / (1024 ** 2)
        return free_ram

    def image_maker(self, file_of_data, frequency, scan_number):
        """
        Мультипроцессинговая функция по созданию радиоизображений
        """
        self.start_procedures()

        import srhdata
        srhfile = srhdata.open(f'{self.directory_of_data}/{file_of_data}')

        from tempfile import TemporaryDirectory
        tmpfs = TemporaryDirectory(prefix='srh_tmp_', suffix=f'_{file_of_data[9:-4]}')
        TMPFS_DIR = tmpfs.name
        logging.info(f'Working in {TMPFS_DIR}')
        os.chdir(TMPFS_DIR)

        start = time.time()
        logging.info(f'{file_of_data} in process')

        srhfile.makeImage(
            path = f'{TMPFS_DIR}',
            calibtable = self.path_to_calib_tables,
            remove_tables = True,
            frequency = frequency,
            scan = scan_number,
            average = 0,
            RL = True,
            clean_disk = False,
            calibrate = False,
            cdelt = 2.45,
            naxis = 1024,
            niter = self.number_of_clean_iter,
            threshold = 75000,
            stokes = 'RRLL',
            deconvolver = 'multiscale',
            scales=[0, 3]
        )

        logging.info(f'Time for {file_of_data} on freq {frequency} scan {scan_number}: {int(time.time() - start)}')

        for name in srhfile.out_filenames:
            filename = name.split('/')[-1]
            freqs_pattern = re.compile(r'(?<=[_.])\d{4,5}(?=[_.])')
            freqqq = int(freqs_pattern.search(name).group())
            shutil.copy(name, f'{self.directory_of_result}/{freqqq}/{filename}')
            logging.info(f'{filename} - OK')

        tmpfs.cleanup()

    def save_progress(self, all_tasks_file, done_tasks_file, all_tasks, done_tasks):
        try:
            with open(all_tasks_file, 'w') as f:
                json.dump(all_tasks, f, indent=4)
            with open(done_tasks_file, 'w') as f:
                json.dump(list(done_tasks), f, indent=4)
        except Exception as e:
            logging.error(f"Error saving progress: {e}")

    def load_progress(self, all_tasks_file, done_tasks_file):
        if os.path.exists(all_tasks_file) and os.path.exists(done_tasks_file):
            try:
                with open(all_tasks_file, 'r') as f:
                    all_tasks = json.load(f)
                with open(done_tasks_file, 'r') as f:
                    # Преобразуем список в множество кортежей, если элементы являются списками
                    done_tasks = {tuple(task) if isinstance(task, list) else task for task in json.load(f)}
                return all_tasks, done_tasks
            except (json.JSONDecodeError, FileNotFoundError) as e:
                logging.warning(f"Error loading progress: {e}")
                return [], set()
        else:
            return [], set()

    def remove_progress(self, all_tasks_file, done_tasks_file):
        os.remove(all_tasks_file)
        os.remove(done_tasks_file)
        logging.info('Files of progress removed')