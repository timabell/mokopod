# bitbake recipie for podpooch
# http://wiki.openmoko.org/wiki/Application_Development_Crash_Course#Filling_the_Files

DESCRIPTION = "A podcast downloader/player"
AUTHOR = "Tim Abell et al"
HOMEPAGE = "http://wiki.openmoko.org/wiki/PodPooch"
SECTION = "x11/applications"
PRIORITY = "optional"
LICENSE = "GPLv3"
#SRC_URI = "file:///home/tim/projects/openmoko/mokopod.git/dist/podpooch-0.2.0.4.tar.gz"
SRC_URI = "http://waitdownload.github.com/timabell-mokopod-5da239b.tar.gz"
#src_uri is 302 redirect for "http://github.com/timabell/mokopod/tarball/0.2.0.3", (try with wget), bitbake can't cope with redirects it seems
DEPENDS = "python"
inherit autotools

S = "${WORKDIR}"
PV = "0.2.0.4"
FILES_${PN} += "${datadir}/podpooch.desktop  ${datadir}/src ${datadir}/podpooch.png"

