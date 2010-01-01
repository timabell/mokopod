# bitbake recipie for podpooch
HOMEPAGE = "http://wiki.openmoko.org/wiki/PodPooch"
AUTHOR = "Tim Abell et al"
DESCRIPTION = "A podcast downloader/player"
LICENSE = "GPLv3"
SRC_URI = "http://www.timwise.co.uk/src/podpooch-0.2.0.4.tgz"
SECTION = "x11/applications"
PRIORITY = "optional"
DEPENDS = "python"
inherit distutils
FILES_${PN} += "${datadir} ${libdir}"

