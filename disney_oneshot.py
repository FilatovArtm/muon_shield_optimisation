#!/usr/bin/env python3
import time
import json
import base64
import copy
import config
import disney_common as common

from disneylandClient import (
    new_client,
    Job,
    RequestWithId,
)

STATUS_IN_PROCESS = set([
    Job.PENDING,
    Job.PULLED,
    Job.RUNNING,
])
STATUS_FINAL = set([
    Job.COMPLETED,
    Job.FAILED,
])


def get_result(jobs):
    results = []
    for job in jobs:
        if job.status != Job.COMPLETED:
            raise Exception(
                "Incomplete job while calculating result: %d",
                job.id
            )

        var = [o for o in json.loads(job.output)
               if o.startswith("variable")][0]
        result = json.loads(var.split("=", 1)[1])
        if result['error']:
            raise Exception(result['error'])
        results.append(result)

    # Only one job per machine calculates the weight and the length
    # -> take first we find
    weight = float([r['weight'] for r in results if r['weight']][0])
    length = float([r['length'] for r in results if r['length']][0])
    if weight < 3e6:
        muons = sum(int(result['muons']) for result in results)
        muons_w = sum(float(result['muons_w']) for result in results)
    else:
        muons, muons_w = None, 0
    return weight, length, muons, muons_w


def CreateMetaData(point, tag, sampling, seed):
    metadata = copy.deepcopy(config.METADATA_TEMPLATE)
    metadata['user'].update([
        ('tag', tag),
        ('params', str(point)),
        ('seed', seed),
        ('sampling', sampling),
    ])
    return json.dumps(metadata)


def CreateJobInput(point, number):
    job = copy.deepcopy(config.JOB_TEMPLATE)
    job['descriptor']['container']['cmd'] = \
        job['descriptor']['container']['cmd'].format(
            params=base64.b64encode(str(point).encode('utf8')).decode('utf8'),
            sampling=37,
            seed=1,
            job_id=number+1
        )

    return json.dumps(job)


def WaitForCompleteness(jobs):
    uncompleted_jobs = jobs

    while True:
        time.sleep(3)
        uncompleted_jobs = [
            stub.GetJob(RequestWithId(id=job.id))
            for job in uncompleted_jobs
        ]
        print("[{}] Job :\n {}\n".format(time.time(), uncompleted_jobs[0]))

        uncompleted_jobs = [
            job for job in uncompleted_jobs
            if job.status not in STATUS_FINAL
        ]

        if not uncompleted_jobs:
            break

    jobs = [stub.GetJob(RequestWithId(id=job.id)) for job in jobs]

    if any(job.status == Job.FAILED for job in jobs):
        print("Job failed!")
        print(list(job for job in jobs if job.status == Job.FAILED))
        raise SystemExit(1)
    return jobs


def main():
    space = common.CreateDiscreteSpace()
    point = common.AddFixedParams(space.rvs()[0])

    jobs = [
        stub.CreateJob(Job(
            input=CreateJobInput(point, i),
            kind='docker',
            metadata=CreateMetaData(point, 'test_oneshot', sampling=37, seed=1)
        ))
        for i in range(16)
    ]

    print("Job", jobs[0])

    print("result:", get_result(WaitForCompleteness(jobs)))


if __name__ == '__main__':
    stub = new_client()
    main()
