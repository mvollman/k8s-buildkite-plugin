#!/bin/bash

basedir="$(dirname $0)"

${basedir}/kubectl get pod $POD_NAME

echo "$POD_SPEC_JSON" | ${basedir}/jq .

retv=1

while [ $retv -ne 0 ]; do
  mysqladmin -h $DB_HOST -u$DB_USERNAME -p$DB_PASSWORD ping
  retv=$?
  sleep 5
done
