#!/bin/bash
release=$1
if [ $release == "" ]; then
	release="master"
fi
git archive --prefix podpooch_$release/ $release | gzip > podpooch_$release.tgz
echo "archive podpooch_$release.tgz created. contents:"
tar -tzf podpooch_$release.tgz
