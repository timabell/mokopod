#!/bin/sh

release=$1
if [ -z "$release" ]; then
	echo "version required"
	exit 1
fi


# Create dirs
mkdir -p opkgfolder/usr/bin
mkdir -p opkgfolder/usr/lib/site-python/podpoochlib/
mkdir -p opkgfolder/usr/share/applications/
mkdir -p opkgfolder/usr/share/pixmaps/


# Copy the script
cp src/podpooch opkgfolder/usr/bin/
cp podpooch_mplayer opkgfolder/usr/bin/

#Copy modules
cp src/podpoochlib/*.py opkgfolder/usr/lib/site-python/podpoochlib/

# Copy .desktop
cp podpooch.desktop opkgfolder/usr/share/applications/
cp podpooch.png opkgfolder/usr/share/pixmaps/

# Copy control
mkdir opkgfolder/CONTROL
cp control opkgfolder/CONTROL

#add version info
echo "Version: $release" >> opkgfolder/CONTROL/control

fakeroot ./ipkg-build opkgfolder


# Clean
rm -rf opkgfolder
