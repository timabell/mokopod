# bitbake recipie for podpooch
# http://wiki.openmoko.org/wiki/Application_Development_Crash_Course#Filling_the_Files

DESCRIPTION = "A podcast downloader/player"
AUTHOR = "Tim Abell et al"
HOMEPAGE = "http://wiki.openmoko.org/wiki/PodPooch"
SECTION = "x11/applications"
PRIORITY = "optional"
LICENSE = "GPLv3"
SRC_URI = "file:///home/tim/projects/openmoko/mokopod.git/dist/podpooch-0.2.0.6.tar.gz"
#SRC_URI = "http://waitdownload.github.com/timabell-mokopod-5da239b.tar.gz"
#src_uri is 302 redirect for "http://github.com/timabell/mokopod/tarball/0.2.0.3", (try with wget), bitbake can't cope with redirects it seems
DEPENDS = "python"
inherit autotools

PV = "0.2.0.6"
FILES_${PN} += "${datadir}/podpooch.desktop  ${datadir}/src ${datadir}/podpooch.png"
FILES_${PN} += "${libdir}"

# http://svn.nslu2-linux.org/svnroot/slugos/releases/slugos-3.10-beta/openembedded/packages/rdiff-backup/rdiff-backup.inc

#
# Without this the python interpreter path points to the staging area.
#
do_compile() {
	BUILD_SYS=${BUILD_SYS} HOST_SYS=${HOST_SYS} \
	  ${bindir}/python setup.py build --executable=${bindir}/python || \
	  oefatal "python setup.py build execution failed."
}

#
# The default do_install sets install-data to ${D}/${datadir} which
# ends up with documentation in /usr/share/share/... instead of
# /usr/share/... Modify the install data directory here to get it
# into the correct place.
#
do_install() {
	BUILD_SYS=${BUILD_SYS} HOST_SYS=${HOST_SYS} \
	  ${bindir}/python setup.py install --prefix=${D}/${prefix} --install-data=${D}/${prefix} || \
	  oefatal "python setup.py install execution failed."
}

