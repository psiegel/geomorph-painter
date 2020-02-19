import os
import sys
import shutil
from setuptools import setup

sys.argv.append('py2app')
sys.argv.append('-A')

includes = ['encodings.utf_8', 'encodings.ascii',]
packages = ['lxml._elementpath', 'gzip']

setup(name='Geomorph Painter',
      version='1.0',
      description='A program for painting Geomorphs.',
      author='Paul Siegel',
      app=['geomorph.py'],
      options={'py2app': {'argv_emulation': True,
       					  'packages': packages, 
	                      'includes': includes,
	                      'optimize': 2,
	                      'compressed': True,
	                      'iconfile': '../images/icon.icns',
	                     }
               },
      setup_requires=['py2app'],
      )

shutil.rmtree('../dist/osx')
if not os.path.isdir('../dist'):
	os.makedirs('../dist')
os.rename('dist', '../dist/osx')
shutil.rmtree('build')
