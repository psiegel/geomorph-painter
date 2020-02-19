"""
This is a way to save the startup time when running img2py on lots of
files.
"""

import sys
from wx.tools import img2py


command_lines = [
    "   -F -n Brush brush.png ../src/ui/images.py",
    "-a -F -n Select select.png ../src/ui/images.py",
    "-a -F -n Move move.png ../src/ui/images.py",
    "-a -F -n ZoomReset zoomreset.png ../src/ui/images.py",
    "-a -F -n ZoomIn zoomin.png ../src/ui/images.py",
    "-a -F -n ZoomOut zoomout.png ../src/ui/images.py",
    "-a -F -n Grid grid.png ../src/ui/images.py",
    "-a -F -i -n App icon.ico ../src/ui/images.py",
    ]


if __name__ == "__main__":
    for line in command_lines:
        args = line.split()
        img2py.main(args)

