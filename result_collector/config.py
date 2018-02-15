IMAGE = 'olantwin/ship-shield'
IMAGE_TAG = 

JOB_TEMPLATE = {
    'input': ['eos:/eos/experiment/ship/skygrid/importance_sampling'],
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
        '''python2 /code/compute_loss.py '''
        '''--tag {tag}''',
    },
    'required_outputs': {
        'output_uri': 'eos:/eos/experiment/ship/skygrid/importance_sampling',
    }
}
