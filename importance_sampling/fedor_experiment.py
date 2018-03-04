#!/usr/bin/env python3
from muon_shield_optimisation.disney_common import (AddFixedParams, CreateDiscreteSpace)
from optimization import CreateOptimizer
from utils import (WaitCompleteness)

import base64
import json
import copy

from disneylandClient import (Job)
from config import IMAGE_TAG
import disneylandClient

from muon_shield_optimisation.disney_oneshot import (
    CreateMetaData,
)

IMAGE = 'olantwin/ship-shield'
JOB_TEMPLATE_IMP_SAMPLING = {
    'input': ['eos:/eos/experiment/ship/skygrid/importance_sampling/cumloss.npy',
              'eos:/eos/experiment/ship/skygrid/importance_sampling/cumindeces.npy',
              'eos:/eos/experiment/ship/data/Mbias/'
              'pythia8_Geant4-withCharm_onlyMuons_4magTarget.root'],

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
        '''mkdir -p /output/previous_results;'''
        '''python2 /code/weighter/weighter.py '''
        '''--params {params} '''
        '''--results /output/result.json '''
        '''--hists /output/hists_{IMAGE_TAG}_'''
        '''{params}_{job_id}_{sampling}_{seed}.root --seed {seed} '''
        '''--share_muons {share} --tag {tag} --point_id {point_id} '''
        '''--sampling_seed 1' ''',
    },
    'required_outputs': {
        'output_uri': 'eos:/eos/experiment/ship/skygrid/importance_sampling',
        'file_contents': [{
            'file': 'result.json',
            'to_variable': 'result'
        }]
    }
}


def SubmitDockerJobs(stub, point, user_tag, sampling, seed, point_id, share, tag):
    return [
        stub.CreateJob(Job(
            input=CreateSimulationJobInput(point, sampling, seed, point_id, share, tag),
            kind='docker',
            metadata=CreateMetaData(point, user_tag, sampling=sampling, seed=seed)
        ))
        ]


def CreateSimulationJobInput(point, sampling, seed, point_id, share, tag):
    job = copy.deepcopy(JOB_TEMPLATE_IMP_SAMPLING)
    job['container']['cmd'] = \
        job['container']['cmd'].format(
            params=base64.b64encode(str(point).encode('utf8')).decode('utf8'),
            sampling=sampling,
            seed=seed,
            job_id=0,
            IMAGE_TAG=IMAGE_TAG,
            point_id=point_id,
            share=share,
            tag=tag
        )

    return json.dumps(job)


stub = disneylandClient.new_client()

if __name__ == '__main__':
    space = CreateDiscreteSpace()
    clf = CreateOptimizer(
        'random',
        space,
        random_state=1
    )

    points = clf.ask(
        n_points=1,
        strategy='cl_mean')
    points = [AddFixedParams(p) for p in points]
    for epoch in range(10):
        shield_jobs = []
        for j in range(100):
            shield_jobs.append(SubmitDockerJobs(
                stub,
                points[0],
                'fedor_sampling',
                sampling='IS',
                seed=j + epoch * 100,
                point_id=j + epoch * 100,
                share=0.01,
                tag="fedor")
            )
        shield_jobs = WaitCompleteness(stub, shield_jobs)
