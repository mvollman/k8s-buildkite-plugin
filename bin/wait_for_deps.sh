#!/bin/bash

basedir="$(dirname $0)"

not_ready_count="$(${basedir}/kubectl get pod -o json $POD_NAME \
	| ${basedir}/jq -r '.status.containerStatuses[] | select(.ready != true) | .name' \
	| grep -v ^step$ \
	| wc -l)"

while [ $not_ready_count -gt 0 ]; do
  echo "Containers not ready $not_ready_count"
  sleep 5
  not_ready_count="$(${basedir}/kubectl get pod -o json $POD_NAME \
	| ${basedir}/jq -r '.status.containerStatuses[] | select(.ready != true) | .name' \
	| grep -v ^step$ \
	| wc -l)"
done

echo "Containers ready!  Waiting 10s before starting command"
sleep 10

#retv=1

#while [ $retv -ne 0 ]; do
  #mysqladmin -h $DB_HOST -u$DB_USERNAME -p$DB_PASSWORD ping
  #retv=$?
  #sleep 5
#done
