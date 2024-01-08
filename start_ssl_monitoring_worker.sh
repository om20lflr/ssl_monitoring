#!/bin/bash

app_name="ssl_monitoring_worker"
log_dir="/var/log/cp_argus/${app_name}"
log_path="${log_dir}/${app_name}_worker.log"

echo -e "Restarting ${app_name} App"
ps ax | grep "celery" | grep -E "${app_name}_worker" |grep -Ev grep | awk '{print $1}' | xargs kill -9
sleep 3
echo -e "Log path: ${log_path}"
nohup /app/venv/bin/celery -A ${app_name}_worker worker -Q ${app_name}Queue -l debug > ${log_path} 2> ${log_path} &
echo "Restarted Successfully."

