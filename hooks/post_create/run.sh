#!/bin/bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
echo "running post create hooks..."
for file in $DIR/*
do
  if [ $(basename $file) != 'run.sh' ]
  then
    exec $file
  fi
done
