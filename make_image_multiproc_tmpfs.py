import os
import multiprocessing
# multiprocessing.log_to_stderr().setLevel('WARNING')
from multiprocessing import Process
import logging
import time
from fnmatch import fnmatch
import shutil
import re
from synthesis_utils import GlobaMultiSynth
from tqdm import tqdm

os.system('python -m casaconfig --update-all')

###### Для заполнения ######
observation_range = '1224'
path_to_calib_tables = '/home/dmitry/Documents/calib_tables/2024/20240514 - 1224 - 02-02-49.json'
directory_of_data = '/home/dmitry/14may/1224/data'
directory_of_result = '/mnt/astro/14may'
flags_freq = [12960, 13720, 23000]
number_of_clean_iter = 150000
######                ######

GlobaMultiSynth = GlobaMultiSynth()
GlobaMultiSynth.start_procedures()
GlobaMultiSynth.start_log('synth_log')

files = sorted(os.listdir(directory_of_data))
logging.info(f'Список файлов: {files}')

list_of_freqs = GlobaMultiSynth.indicate_observation_range(observation_range)
GlobaMultiSynth.create_places(directory_of_result, list_of_freqs, flags_freq)

def image_maker(file_of_data):
    """
    Мультипроцессинговая функция по созданию радиоизображений
    """
    import os
    N_THREADS = "1"
    os.environ['OMP_NUM_THREADS'] = N_THREADS
    os.environ['OPENBLAS_NUM_THREADS'] = N_THREADS
    os.environ['MKL_NUM_THREADS'] = N_THREADS
    os.environ['VECLIB_MAXIMUM_THREADS'] = N_THREADS
    os.environ['NUMEXPR_NUM_THREADS'] = N_THREADS

    from casatasks import casalog
    casalog.filter('SEVERE')

    import srhdata
    srhfile = srhdata.open(f'{directory_of_data}/{file_of_data}')

    for freq in tqdm(range(0, 16), desc='Freqs', position=1, leave=False):

        for scan in tqdm(range(0, 20), desc=f'Scans for freq {freq}', position=2, leave=False): #range(0, 20, 4):

            from tempfile import TemporaryDirectory
            tmpfs = TemporaryDirectory(prefix='srh_tmp_', suffix=f'_{file_of_data[9:-4]}')
            TMPFS_DIR = tmpfs.name
            logging.info(f'Working in {TMPFS_DIR}')
            os.chdir(TMPFS_DIR)

            start = time.time()

            if list_of_freqs[freq] in flags_freq:
                pass
            else:
                logging.info(f'{file_of_data} in process id: {os.getpid()}')

                srhfile.makeImage(
                    path = f'{TMPFS_DIR}',
                    calibtable = path_to_calib_tables,
                    remove_tables = True,
                    frequency = freq,
                    scan = scan,
                    average = 0,
                    RL = True,
                    clean_disk = False,
                    calibrate = False,
                    cdelt = 2.45,
                    naxis = 1024,
                    niter = number_of_clean_iter,
                    threshold = 500000,
                    stokes = 'RRLL',
                    deconvolver = 'multiscale',
                    scales=[0, 3, 6, 9, 12]
                )

            logging.info(f'Time for {file_of_data} on freq {freq} scan {scan}: {int(time.time() - start)}')

            for root, dirs, files in os.walk(TMPFS_DIR):
                for file_name in files:
                    if fnmatch(file_name, '*LCP*.fit') or fnmatch(file_name, '*RCP*.fit'):
                        logging.info(f'{file_name} - OK')

                        freqs_pattern = re.compile(r'(?<=[_.])\d{4,5}(?=[_.])')
                        freqqq = int(freqs_pattern.search(file_name).group())

                        shutil.copy(os.path.join(root, file_name), f'{directory_of_result}/{freqqq}/{file_name}')

            tmpfs.cleanup()

if __name__ == '__main__':

    summary_start = time.time()

    try:
        procs = []

        with tqdm(total=len(files), desc='Files', position=0) as pbar_files:

            for index, file in enumerate(files):
                proc = Process(target=image_maker, args=(file,))
                procs.append(proc)
                proc.start()

            for proc in procs:
                proc.join()

        logging.info(f'summary time: {int(time.time() - summary_start)}')

    except KeyboardInterrupt:
        print('Остановлено вручную')
