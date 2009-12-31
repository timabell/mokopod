from distutils.core import setup
setup (name = "podpooch",
	version = "0.2.0.5",
	package_dir = {'': 'src'},
	py_modules = ['podpooch'],
	packages = ["podpoochlib"],
	url = "http://wiki.openmoko.org/wiki/PodPooch",
	author = "Tim Abell et al",
	author_email = "tim@timwise.co.uk",
	maintainer = "Tim Abell",
	maintainer_email = "tim@timwise.co.uk",
	data_files=[('pixmaps', ['podpooch.png']),
		('applications', ['podpooch.desktop'])
		]
	)

