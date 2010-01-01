# bitbake recipie for podpooch
# http://wiki.openmoko.org/wiki/Application_Development_Crash_Course#Filling_the_Files

DESCRIPTION = "A podcast downloader/player"
AUTHOR = "Tim Abell et al"
HOMEPAGE = "http://wiki.openmoko.org/wiki/PodPooch"
SECTION = "x11/applications"
PRIORITY = "optional"
LICENSE = "GPLv3"

SRC_URI = "git://github.com/timabell/mokopod.git;protocol=http"
PV = "0.2.0+gitr${SRCPV}"
PR = "r0"
DEPENDS = "python"
inherit distutils

FILES_${PN} += "${datadir} ${libdir}"

