#!/bin/bash -e

for i in $(seq 1 10); do
  if apt-get update && apt-get install -y "$@"; then
    exit 0
  fi
  echo "retry apt"
  sleep 5
done

echo "apt failed"
exit 1
