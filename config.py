# Configuration file for the optimisation. Only static global variables.
#
# For testing whether the config is sane, please add tests to `test_config.py`


def StripFreeParams(point):
    fixed_params = []
    for low, high in FIXED_RANGES:
        fixed_params += point[low:high]
    return fixed_params


DEFAULT_POINT = [
    70.0,
    170.0,
    255.,
    255.,
    255.,
    255.,
    255.,
    255.,
    40.0,
    40.0,
    150.0,
    150.0,
    2.0,
    2.0,
    80.0,
    80.0,
    150.0,
    150.0,
    2.0,
    2.0,
    40.0,
    40.0,
    150.0,
    150.0,
    2.0,
    2.0,
    40.0,
    40.0,
    150.0,
    150.0,
    2.0,
    2.0,
    40.0,
    40.0,
    150.0,
    150.0,
    2.0,
    2.0,
    40.0,
    40.0,
    150.0,
    150.0,
    2.0,
    2.0,
    40.0,
    40.0,
    150.0,
    150.0,
    2.0,
    2.0,
    40.0,
    40.0,
    150.0,
    150.0,
    2.0,
    2.0,
]
FIXED_RANGES = [(0, 8), (9, 56)]
FIXED_PARAMS = StripFreeParams(DEFAULT_POINT)
IMAGE = 'olantwin/ship-shield'
IMAGE_TAG = '20171129_T1'  # '20171128_T4' for T4
RESULTS_TEMPLATE = {
    'error': 'Some',
    'weight': None,
    'length': None,
    'muons': None,
    'muons_w': None,
    'args': None,
    'status': None,
}
JOB_TEMPLATE = {
    'descriptor': {
        'input': [],
        'container': {
            'workdir':
            '',
            'name':
            '{}:{}'.format(IMAGE, IMAGE_TAG),
            'volumes': [
                '/home/sashab1/ship-shield:/shield',
                '/home/sashab1/ship/shared:/shared'
            ],
            'cpu_needed':
            1,
            'max_memoryMB':
            1024,
            'min_memoryMB':
            512,
            'run_id':
            'near_run3',
            'cmd':
            '''/bin/bash -l -c 'source /opt/FairShipRun/config.sh; '''
            '''python2 /code/slave.py '''
            '''--params {params} '''
            '''-f /shield/worker_files/sampling_{sampling}/'''
            '''muons_{job_id}_16.root '''
            '''--results /output/result.json '''
            '''--hists /output/hists.root --seed {seed}' ''',
        },
        'required_outputs': {
            'output_uri': 'host:/srv/local/skygrid-local-storage/$JOB_ID',
            'file_contents': [{
                'file': 'result.json',
                'to_variable': 'result'
            }]
        }
    }
}
METADATA_TEMPLATE = {
    'user': {
        'tag': '',
        'sampling': 37,
        'seed': 1,
        'image_tag': IMAGE_TAG,
        'params': []
    },
    'disney': {}
}
