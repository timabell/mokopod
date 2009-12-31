# bitbake recipie for podpooch
# http://wiki.openmoko.org/wiki/Application_Development_Crash_Course#Filling_the_Files

DESCRIPTION = "A podcast downloader/player"
AUTHOR = "Tim Abell et al"
HOMEPAGE = "http://wiki.openmoko.org/wiki/PodPooch"
SECTION = "x11/applications"
PRIORITY = "optional"
LICENSE = "GPLv3"

SRC_URI = "http://download.github.com/timabell-mokopod-0023788.tar.gz"
#SRC_URI is the 302 redirect target for "http://github.com/timabell/mokopod/tarball/0.2.0.4", (try with wget), bitbake can't cope with redirects it seems
DEPENDS = "python"
inherit distutils

FILES_${PN} += "${datadir} ${libdir}"

