#!/usr/bin/python

#
# TODO:
# 1. Clean up for distribution.
#
import wx

import ui
import doc

class GeomorphApp(wx.App):
	def OnInit(self):
		self.doc = doc.MapDocument()
		
		self.mainWindow = ui.MainFrame(None, -1, "Geomorph Painter", pos=(0, 0), size=(800, 600))
		self.doc.new()
		self.mainWindow.Show(True)
		
		return True	
	
if __name__ == '__main__':
	app = GeomorphApp(0)
	app.MainLoop()
