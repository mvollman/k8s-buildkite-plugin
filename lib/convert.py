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
memory_requests = os.getenv('BUILDKITE_PLUGIN_K8S_RESOURCES_REQUEST_MEMORY', '2G')
cpu_limits = os.getenv('BUILDKITE_PLUGIN_K8S_RESOURCES_LIMIT_CPU', '1')
memory_limits = os.getenv('BUILDKITE_PLUGIN_K8S_RESOURCES_LIMIT_MEMORY', '2G')
security_gid = os.getenv('BUILDKITE_PLUGIN_K8S_GID', '0')
security_uid = os.getenv('BUILDKITE_PLUGIN_K8S_UID', '0')
image = os.environ['BUILDKITE_PLUGIN_K8S_IMAGE']
service_account = os.getenv('BUILDKITE_PLUGIN_K8S_SERVICE_ACCOUNT_NAME', 'default')
ttl_seconds_after_finished = os.getenv('BUILDKITE_PLUGIN_K8S_JOB_TTL_SECONDS_AFTER_FINISHED', '120')
#ttl_seconds_after_finished = 120
active_deadline_seconds = 600
backoff_limit = os.getenv('BUILDKITE_PLUGIN_K8S_JOB_BACKOFF_LIMIT', 1)
agent_name = os.getenv('BUILDKITE_AGENT_NAME', f'{job_name}-1')
#backoff_limit = 1
volume_mounts = [
        {
            'mountPath': f'/var/buildkite/{job_name}',
            'name': 'buildkite-agent-store'
        },
        {
            'mountPath': f'/buildkite/builds/{agent_name}',
            'name': 'buildkite-builds-store'
        }
]
volumes = [
        {
            'name': 'buildkite-builds-store',
            'hostPath': {
                'path': f'/buildkite/builds/{agent_name}'
            }
        },
        {
            'name': 'buildkite-agent-store',
            'hostPath': {
                'path': f'/var/buildkite/{job_name}'
            }
        }
    ]

pull_policy = 'IfNotPresent'
if os.getenv('BUILDKITE_PLUGIN_K8S_ALWAYS_PULL', 'false') == 'true':
    pull_policy = 'Always'

env_file = "/tmp/env_file"
env_file_handle = open(env_file, 'w')

# If requested, propagate a set of env vars as listed in a given env var to the
# container.
if 'BUILDKITE_PLUGIN_K8S_ENV_PROPAGATION_LIST' in os.environ:
   for env in os.environ['BUILDKITE_PLUGIN_K8S_ENV_PROPAGATION_LIST'].split():
       if env not in os.environ:
           print(f'Environment variable {env} requested in propagation-list and not defined in the agents environment')
           sys.exit(1)
       env_file_handle.write(f'{env}={os.getenv(env)}')
       envs.append({
           'name': env,
           'valueFrom': {
               'secretKeyRef': {
                   'key': env,
                   'name': job_name
               }
           }
        })

if 'BUILDKITE_PLUGIN_K8S_ENVIRONMENT' in os.environ:
   for env in os.environ['BUILDKITE_PLUGIN_K8S_ENVIRONMENT'].split():
       if '=' in env:
           key, value = env.split('=', maxsplit=1)
           env_file_handle.write(f'{key}={value}')
           envs.append({
              'name': key,
              'valueFrom': {
                   'secretKeyRef': {
                       'key': key,
                       'name': job_name
                    }
               }
           })
       else:
           if env not in os.environ:
               print(f'Environment variable {env} requested in environment and not defined in the agents environment')
               sys.exit(1)
           env_file_handle.write(f'{env}={os.getenv(env)}')
           envs.append({
               'name': env,
               'valueFrom': {
                   'secretKeyRef': {
                       'key': env,
                       'name': job_name
                    }
               }
            })

# Propagate all environment variables into the container if requested
if os.getenv('BUILDKITE_PLUGIN_K8S_PROPAGATE_ENVIRONMENT', 'false') == 'true':
    if 'BUILDKITE_ENV_FILE' in os.environ:
        with open(os.environ['BUILDKITE_ENV_FILE'], 'r') as env_file:
            for line in env_file:
                key, value = line.split('=', maxsplit=1)
                env_file_handle.write(f'{key}={value}')
                envs.append({
                   'name': key,
                   'valueFrom': {
                       'secretKeyRef': {
                           'key': key,
                           'name': job_name
                        }
                   }
                })
    else:
        print("🚨 Not propagating environment variables to container as $BUILDKITE_ENV_FILE is not set")

if os.getenv('BUILDKITE_PLUGIN_K8S_PROPAGATE_AWS_AUTH_TOKENS', 'false') != 'false':
    for aws_var in [
            'AWS_ACCESS_KEY_ID',
            'AWS_SECRET_ACCESS_KEY',
            'AWS_SESSION_TOKEN',
            'AWS_REGION',
            'AWS_DEFAULT_REGION',
            'AWS_ROLE_ARN',
            'AWS_STS_REGIONAL_ENDPOINTS',
            'AWS_CONTAINER_CREDENTIALS_FULL_URI',
            'AWS_CONTAINER_CREDENTIALS_RELATIVE_URI',
            'AWS_CONTAINER_AUTHORIZATION_TOKEN',
            'AWS_WEB_IDENTITY_TOKEN_FILE'
        ]:
        if aws_var in os.environ:
            env_file_handle.write(f'{aws_var}={os.environ[aws_var]}')
            envs.append({
                'name': aws_var,
                'valueFrom': {
                    'secretKeyRef': {
                        'key': aws_var,
                        'name': job_name
                    }
                }
            })

  # Pass EKS variables when the agent is running in EKS
  # https://docs.aws.amazon.com/eks/latest/userguide/iam-roles-for-service-accounts-minimum-sdk.html
  #if [[ -n "${AWS_WEB_IDENTITY_TOKEN_FILE:-}" ]] ; then
      #args+=( --env "AWS_WEB_IDENTITY_TOKEN_FILE" )
      # Add the token file as a volume
      #args+=( --volume "${AWS_WEB_IDENTITY_TOKEN_FILE}:${AWS_WEB_IDENTITY_TOKEN_FILE}" )
  #fi

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
                pull_policy=pull_policy,
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

env_file_handle.close()
print(yaml.safe_dump(job_template))
