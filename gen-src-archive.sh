#!/bin/bash
release=$1
if [ $release == "" ]; then
	release="master"
fi
git archive --prefix podpooch-$release/ $release | gzip > podpooch-$release.tgz
echo "archive podpooch-$release.tgz created. contents:"
tar -tzf podpooch-$release.tgz
