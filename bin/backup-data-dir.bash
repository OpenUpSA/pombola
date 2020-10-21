#!/bin/bash

set -euf -o pipefail

export AWS_SECRET_ACCESS_KEY=${DATA_DIR_BACKUP_AWS_SECRET_ACCESS_KEY}
export AWS_ACCESS_KEY_ID=${DATA_DIR_BACKUP_AWS_ACCESS_KEY_ID}
export AWS_DEFAULT_REGION=eu-west-1

BUCKET=peoples-assembly-data-dir-backups
TMP_FILENAME=pombola-data-dir-$(date "+%FT%H-%M-%S").tgz
TMP_PATH=/tmp/${TMP_FILENAME}

trap "rm -f ${TMP_PATH}" EXIT

tar --exclude=${PMG_API_CACHE_DIR} -czf ${TMP_PATH} ${POMBOLA_DATADIR}
aws s3 cp ${TMP_PATH} s3://${BUCKET}/${TMP_FILENAME}
