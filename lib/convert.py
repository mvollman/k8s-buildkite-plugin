#!/usr/bin/python

import jinja2
import os
import sys
import yaml

script_directory = os.path.dirname(os.path.abspath(sys.argv[0]))

build_number = os.environ['BUILDKITE_BUILD_NUMBER']
build_id = os.environ['BUILDKITE_BUILD_ID']
job_id = os.environ['BUILDKITE_JOB_ID']
pipeline = os.environ['BUILDKITE_PIPELINE_SLUG']
branch = os.environ['BUILDKITE_BRANCH']
namespace = os.getenv('BUILDKITE_PLUGIN_K8S_NAMESPACE', 'default')
#full_pod_name = f'k8splug-{pipeline[:32]}-{job_id}'
#pod_name = full_pod_name[:63].lower()
job_name = sys.argv[1]
args = [os.environ['BUILDKITE_COMMAND']]
command = ['/bin/sh', '-c']
envs = []
node_name = os.getenv('NODE_NAME')
cpu_requests = os.getenv('BUILDKITE_PLUGIN_K8S_RESOURCES_REQUEST_CPU', '1')
memory_requests = os.getenv('BUILDKITE_PLUGIN_K8S_RESOURCES_REQUEST_MEMORY', '2g')
cpu_limits = os.getenv('BUILDKITE_PLUGIN_K8S_RESOURCES_LIMIT_CPU', '1')
memory_limits = os.getenv('BUILDKITE_PLUGIN_K8S_RESOURCES_LIMIT_MEMORY', '2g')
security_gid = os.getenv('BUILDKITE_PLUGIN_K8S_GID', '0')
security_uid = os.getenv('BUILDKITE_PLUGIN_K8S_UID', '0')
image = os.environ['BUILDKITE_PLUGIN_K8S_IMAGE']
service_account = os.getenv('BUILDKITE_PLUGIN_K8S_SERVICE_ACCOUNT_NAME', 'default')
ttl_seconds_after_finished = os.getenv('BUILDKITE_PLUGIN_K8S_JOB_TTL_SECONDS_AFTER_FINISHED', '120')
#ttl_seconds_after_finished = 120
active_deadline_seconds = 600
backoff_limit = os.getenv('BUILDKITE_PLUGIN_K8S_JOB_BACKOFF_LIMIT', 1)
#backoff_limit = 1
volume_mounts = [
        {
            'mountPath': f'/var/buildkite/{job_name}',
            'name': 'buildkite-agent-store'
        },
        {
            'mountPath': f'/buildkite/builds/{job_name}-1',
            'name': 'buildkite-builds-store'
        }
]
volumes = [
        {
            'name': 'buildkite-builds-store',
            'hostPath': {
                'path': f'/buildkite/builds/{job_name}-1'
            }
        },
        {
            'name': 'buildkite-agent-store',
            'hostPath': {
                'path': f'/var/buildkite/{job_name}'
            }
        }
    ]

with open(f"{script_directory}/job.yaml.j2", 'r') as job:
    job_template = yaml.safe_load(
            jinja2.Template(
                job.read()
            ).render(
                job_name=job_name,
                build_number=build_number,
                job_id=job_id,
                pipeline=pipeline,
                branch=branch,
                namespace=namespace,
                args=args,
                command=command,
                envs=envs,
                image=image,
                cpu_limits=cpu_limits,
                memory_limits=memory_limits,
                cpu_requests=cpu_requests,
                memory_requests=memory_requests,
                node_name=node_name,
                security_gid=security_gid,
                security_uid=security_uid,
                service_account=service_account,
                ttl_seconds_after_finished=ttl_seconds_after_finished,
                backoff_limit=backoff_limit,
                active_deadline_seconds=active_deadline_seconds,
                volume_mounts=volume_mounts,
                volumes=volumes
            )
    )

print(yaml.safe_dump(job_template))
