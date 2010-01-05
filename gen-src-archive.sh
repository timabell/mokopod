#!/bin/bash
release=$1
if [ "$release" == "" ]; then
	release="master"
	release=`git log -1 --pretty=format:%h $release`
	git archive --prefix podpooch-$release/ $release | gzip > podpooch-$release.tar.gz
else
	git archive --prefix podpooch-$release/ $release > podpooch-$release.tar
	mkdir fixup-tmp
	tar -C fixup-tmp -xf podpooch-$release.tar podpooch-$release/setup.py
	sed -i s/##version##/$release/ fixup-tmp/podpooch-$release/setup.py
	tar --delete -f podpooch-$release.tar podpooch-$release/setup.py
	tar -C fixup-tmp -uf podpooch-$release.tar podpooch-$release/setup.py
	rm -rf fixup-tmp
	gzip podpooch-$release.tar
	md5sum podpooch-$release.tar.gz > podpooch-$release.tar.gz.md5
fi
echo "archive podpooch-$release.tgz created. contents:"
tar -tzf podpooch-$release.tar.gz
