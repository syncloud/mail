#!/bin/bash -xe

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
REDIS=${DIR}/../build/snap/redis

${REDIS}/bin/redis.sh --version
${REDIS}/bin/redis-cli.sh --version
