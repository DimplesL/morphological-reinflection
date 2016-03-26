"""Runs the script on all langs in parallel

Usage:
  run_all_langs.py [--cnn-mem MEM][--input=INPUT] [--feat-input=FEAT][--hidden=HIDDEN] [--epochs=EPOCHS] [--layers=LAYERS]
   [--optimization=OPTIMIZATION] [--pool=POOL] SRC_PATH RESULTS_PATH SIGMORPHON_PATH...

Arguments:
  SRC_PATH  source files directory path
  RESULTS_PATH  results file to be written
  SIGMORPHON_PATH   sigmorphon root containing data, src dirs

Options:
  -h --help                     show this help message and exit
  --cnn-mem MEM                 allocates MEM bytes for (py)cnn
  --input=INPUT                 input vector dimensions
  --feat-input=FEAT             feature input vector dimension
  --hidden=HIDDEN               hidden layer dimensions
  --epochs=EPOCHS               amount of training epochs
  --layers=LAYERS               amount of layers in lstm network
  --optimization=OPTIMIZATION   chosen optimization method ADAM/SGD/ADAGRAD/MOMENTUM
  --pool=POOL                   amount of processes in pool
"""

import os
import time
import datetime
import docopt
from multiprocessing import Pool


# default values
INPUT_DIM = 200
FEAT_INPUT_DIM = 20
HIDDEN_DIM = 200
EPOCHS = 1
LAYERS = 2
MAX_PREDICTION_LEN = 50
OPTIMIZATION = 'ADAM'
EARLY_STOPPING = True
MAX_PATIENCE = 100
REGULARIZATION = 0.0001
LEARNING_RATE = 0.001  # 0.1
POOL = 4


def main(src_dir, results_dir, sigmorphon_root_dir, input_dim, hidden_dim, epochs, layers,
         optimization, feat_input_dim, pool_size):
    # langs = ['russian', 'turkish', 'spanish', 'arabic', 'georgian', 'german', 'navajo', 'finnish']
    cnn_mem = 4096
    parallelize_training = True
    langs = ['russian', 'turkish', 'georgian', 'german', 'navajo', 'finnish']

    params = []
    print 'now training langs: ' + str(langs)
    for lang in langs:
        params.append([cnn_mem, epochs, feat_input_dim, hidden_dim, input_dim, lang, layers, optimization, results_dir,
                    sigmorphon_root_dir, src_dir])

    # train models for each lang in parallel or in loop
    if parallelize_training:
        pool = Pool(int(pool_size))
        print 'now training {0} langs in parallel'.format(len(langs))
        pool.map(train_language_wrapper, params)
    else:
        print 'now training {0} langs in loop'.format(len(langs))
        for p in params:
            train_language(*p)
    print 'finished training all models'

    train_language(cnn_mem, epochs, feat_input_dim, hidden_dim, input_dim, lang, layers, optimization, results_dir,
                    sigmorphon_root_dir, src_dir)

        # evaluate_baseline(lang, results_dir, sig_root)

def train_language_wrapper(params):
    train_language(*params)

def train_language(cnn_mem, epochs, feat_input_dim, hidden_dim, input_dim, lang, layers, optimization, results_dir,
                sigmorphon_root_dir, src_dir):
    start = time.time()
    os.chdir(src_dir)
    # os.system('python pycnn_factored_inflection.py --cnn-mem 4096 --input=150 --hidden=150 --epochs=300
    # --layers=2 \
    #           --optimization ADAM \
    #           {0}/data/{1}-task1-train \
    #           {0}/data/{1}-task1-dev \
    #           {3}/{1}_{2}_results.txt \
    #           {0}'.format(sig_root, lang, st, results_dir))
    os.system('python pycnn_joint_structured_inflection.py --cnn-mem 8096 --input={1} --hidden={2} \
                  --feat-input={3} --epochs={4} --layers={5} --optimization {6} \
                  {7}/data/{8}-task1-train \
                  {7}/data/{8}-task1-dev \
                  {9}/joint_structured_{8}_results.txt \
                  {7}'.format(cnn_mem, input_dim, hidden_dim, feat_input_dim, epochs, layers, optimization,
                              sigmorphon_root_dir, lang, results_dir))
    end = time.time()
    print 'finished ' + lang + ' in ' + str(ms_to_timestring(end - start))


def ms_to_timestring(ms):
    return str(datetime.timedelta(ms))


def evaluate_baseline(lang, results_dir, sig_root):
    os.chdir(sig_root + '/src/baseline')

    # run baseline system
    os.system('./baseline.py --task=1 --language={0} \
        --path={1}/data/ > {2}/baseline_{0}_task1_predictions.txt'.format(lang, sig_root, results_dir))
    os.chdir(sig_root + '/src')

    # eval baseline system
    os.system('python evalm.py --gold ../data/{0}-task1-dev --guesses \
        {1}/baseline_{0}_task1_predictions.txt'.format(lang, results_dir))


if __name__ == '__main__':
    arguments = docopt.docopt(__doc__)

    ts = time.time()
    st = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d_%H:%M:%S')

    # default values
    if arguments['SRC_PATH']:
        src_dir = arguments['SRC_PATH']
    else:
        src_dir = '/Users/roeeaharoni/GitHub/morphological-reinflection/src/'
    if arguments['RESULTS_PATH']:
        results_dir = arguments['RESULTS_PATH']
    else:
        results_dir = '/Users/roeeaharoni/Dropbox/phd/research/morphology/inflection_generation/results/'
    if arguments['SIGMORPHON_PATH']:
        sigmorphon_root_dir = arguments['SIGMORPHON_PATH'][0]
    else:
        sigmorphon_root_dir = '/Users/roeeaharoni/research_data/sigmorphon2016-master/'
    if arguments['--input']:
        input_dim = int(arguments['--input'])
    else:
        input_dim = INPUT_DIM
    if arguments['--hidden']:
        hidden_dim = int(arguments['--hidden'])
    else:
        hidden_dim = HIDDEN_DIM
    if arguments['--feat-input']:
        feat_input_dim = int(arguments['--feat-input'])
    else:
        feat_input_dim = FEAT_INPUT_DIM
    if arguments['--epochs']:
        epochs = int(arguments['--epochs'])
    else:
        epochs = EPOCHS
    if arguments['--layers']:
        layers = int(arguments['--layers'])
    else:
        layers = LAYERS
    if arguments['--optimization']:
        optimization = arguments['--optimization']
    else:
        optimization = OPTIMIZATION
    if arguments['--pool']:
        pool_size = arguments['--pool']
    else:
        pool_size = POOL

    print arguments

    main(src_dir, results_dir, sigmorphon_root_dir, input_dim, hidden_dim, epochs, layers,
         optimization, feat_input_dim, pool_size)
