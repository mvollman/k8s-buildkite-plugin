#!/usr/bin/python

import jinja2
import os
import yaml


pod_name = 'fake-pod-name'
build_number = '10'
environment = 'test'
job_name = 'fake-job-name'
pipeline = 'fake-pipeline'
queue = 'default'
namespace = 'buildkite'
args = []
command = 'sleep 10000'
env = []
node_name = os.getenv('NODE_NAME')
cpu_limits = '1'
memory_limits = '2g'
cpu_requests = '1'
memory_requests = '2g'
security_gid = 65356
security_uid = 65356
image = '932532311803.dkr.ecr.us-east-1.amazonaws.com/pipeline_libs:latest'
service_account = 'buildkite-agent'
volumes = [
        {
            'name': 'buildkite-builds-store',
            'hostpath': {
                'path': '/buildkite/builds'
            }
        },
        {
            'name': 'buildkite-agent-store',
            'hostpath': {
                'path': '/var/buildkite'
            }
        }
    ]

with open("pod.yaml.j2", 'r') as pod:
    pod_template = yaml.safe_load(
            jinja2.Template(
                pod.read()
            ).render(
                pod_name=pod_name,
                build_number=build_number,
                environment=environment,
                job_name=job_name,
                pipeline=pipeline,
                queue=queue,
                namespace=namespace,
                args=args,
                command=command,
                env=env,
                image=image,
                cpu_limits=cpu_limits,
                memory_limits=memory_limits,
                cpu_requests=cpu_requests,
                memory_requests=memory_requests,
                node_name=node_name,
                security_gid=security_gid,
                security_uid=security_uid,
                service_account=service_account,
                volumes=volumes
            )
    )

print(yaml.safe_dump(pod_template))
