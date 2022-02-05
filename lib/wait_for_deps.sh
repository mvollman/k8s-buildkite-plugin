#!/bin/bash

while [ $retv -ne 0 ]; do
  mysqladmin -h $DB_HOST -u$DB_USERNAME -p$DB_PASSWORD ping
  retv=$?
  sleep 5
done
