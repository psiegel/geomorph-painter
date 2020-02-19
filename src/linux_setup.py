from cx_Freeze import setup, Executable
import os
import sys
import shutil

sys.argv.append('build')

includes = ['encodings.utf_8', 'encodings.ascii',]
packages = ['lxml._elementpath', 'gzip']

executable = Executable(script='geomorph.py',
                        copyDependentFiles=True,
                        )


setup(name='Geomorph Painter',
      version='1.0',
      description='A program for painting Geomorphs.',
      author='Paul Siegel',
      executables=[executable],
      options={'build_exe': {'packages': packages, 
                             'includes': includes,
                             'optimize': 2,
                             'compressed': True,
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

deletedirs('../dist/linux')
if not os.path.isdir('../dist/linux'):
	os.makedirs('../dist/linux')
for root, dirs, files in os.walk('build', False):
	for dir in dirs:
		if (dir.startswith('exe')):
			os.rename('build/%s/' % dir, '../dist/linux')
shutil.copy('../images/icon.ico', '../dist/linux')
os.removedirs('build')

