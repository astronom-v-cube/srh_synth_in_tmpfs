import os
import multiprocessing
import psutil
import logging
import time

class GlobaMultiSynth():

    def __init__(self) -> None:
        self.list_of_freqs_0306 = [2800, 3000, 3200, 3400, 3600, 3800, 4000, 4200, 4400, 4600, 4800, 5000, 5200, 5400, 5600, 5800]
        self.list_of_freqs_0612 = [6000, 6400, 6800, 7200, 7600, 8000, 8400, 8800, 9200, 9600, 10000, 10400, 10800, 11200, 11600, 12000]
        self.list_of_freqs_1224 = [12200, 12960, 13720, 14480, 15240, 16000, 16760, 17520, 18280, 19040, 19800, 20560, 21320, 22080, 23000, 23400]

    @staticmethod
    def start_log(name_file : str):
        """Инициализация ```.log``` файла
        Args:
            name_file (str): название файла
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

    def transform_timestamp(self, timestamp: str):
        """Трансформация имени файла в имя маски
        Args:
            timestamp (str): имя файла
        """
        return f"{timestamp[:4]}-{timestamp[4:6]}-{timestamp[6:8]}T{timestamp[9:11]}:{timestamp[11:13]}:{timestamp[13:15]}"

    def start_procedures(self):
        # на случай выполнения на ssd чтобы кэш не копился
        # os.system("tracker3 daemon -k")
        # os.system("tracker3 daemon --list-miners-running")

        multiprocessing.log_to_stderr()
        logger = multiprocessing.get_logger()
        logger.setLevel(logging.INFO)

    def finish_procedures(self, directory_of_result, list_of_freqs):
        # os.system("tracker3 daemon -s")
        os.system("rm -rf casa*.log")
        for fq in list_of_freqs:
            os.system(f"rm -rf {directory_of_result}/{fq}/*_mask")

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







    # def image_maker(self, file_of_data, freq, list_of_freqs, flags_freq, path_to_calib_tables, directory_of_data, directory_of_result, number_of_clean_iter, threshold):
    #     """
    #     Мультипроцессинговая функция по созданию радиоизображений для конкретной частоты
    #     """

    #     import os
    #     N_THREADS="1"
    #     os.environ['OMP_NUM_THREADS'] = N_THREADS
    #     os.environ['OPENBLAS_NUM_THREADS'] = N_THREADS
    #     os.environ['MKL_NUM_THREADS'] = N_THREADS
    #     os.environ['VECLIB_MAXIMUM_THREADS'] = N_THREADS
    #     os.environ['NUMEXPR_NUM_THREADS'] = N_THREADS

    #     from casatasks import casalog
    #     casalog.filter('SEVERE')
    #     import srhdata

    #     srhfile = srhdata.open(f'{directory_of_data}/{file_of_data}')

    #     for scan in range(0, 20):
    #         start = time.time()

    #         if list_of_freqs[freq] in flags_freq:
    #             pass

    #         else:
    #             proc_id = os.getpid()
    #             print(f'{file_of_data} in process id: {proc_id}, frequency: {freq}')
    #             srhfile.makeImage(
    #                 path = f'./{directory_of_result}/{list_of_freqs[freq]}',
    #                 calibtable = path_to_calib_tables,
    #                 remove_tables = True,
    #                 frequency = freq,
    #                 scan = scan,
    #                 average = 0,
    #                 RL = True,
    #                 clean_disk = True,
    #                 calibrate = False,
    #                 cdelt = 2.45,
    #                 naxis = 1024,
    #                 niter = number_of_clean_iter,
    #                 threshold = threshold,
    #                 stokes = 'RRLL'
    #             )

    #         finish = time.time()
    #         res = finish - start
    #         print('Время работы: ', int(res))