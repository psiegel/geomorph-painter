from distutils.core import setup
import py2exe
import os
import sys
import time

sys.argv.append('py2exe')

includes = ['encodings.utf_8', 'encodings.ascii',]
packages = ['lxml._elementpath', 'inspect', 'gzip']

setup(windows=[{'script':'geomorph.py',
				'icon_resources':[(1,'../images/icon.ico')]
				}],
      options={'py2exe': {'packages': packages, 
                          'includes': includes,
                          'optimize': 2,
                          'compressed': True,
						  'dll_excludes': ['w9xpopen.exe'],
                          }
               },
      )

def deletedirs(dirname):
	for root, dirs, files in os.walk(dirname, False):
		for file in files:
			total_time = 0;
			file_name = root + os.path.sep + file
			while os.path.exists(file_name):
				try:
					os.chmod(file_name, 0666)
					os.unlink(file_name)
				except Exception, e:
					time.sleep(0.2)
					total_time += 0.2
					if (total_time >= 3):
						self.fail("Error - unable to delete file %s" % file)
				else:
					break					

		os.rmdir(root)

deletedirs('../dist/win32')
if not os.path.isdir('../dist'):
	os.makedirs('../dist')
os.rename('dist', '../dist/win32')
deletedirs('build')
deletedirs('dist')

