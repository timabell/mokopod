from distutils.core import setup
setup (name = "podpooch",
	version = ##version##,  #version set by gen-src-archive.sh
	package_dir = {'': 'src'},
	scripts = ['src/podpooch'],
	packages = ["podpoochlib"],
	url = "http://wiki.openmoko.org/wiki/PodPooch",
	author = "Tim Abell et al",
	author_email = "tim@timwise.co.uk",
	maintainer = "Tim Abell",
	maintainer_email = "tim@timwise.co.uk",
	data_files=[('share/pixmaps', ['podpooch.png']),
		('share/applications', ['podpooch.desktop'])
		]
	)

