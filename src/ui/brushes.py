import os
import random
import wx

from doc.map import ImageCache

IMG_SIZE = 128

class BrushDirPanel(wx.Panel):
	def __init__(self, *args, **kwargs):
		super(BrushDirPanel, self).__init__(*args, **kwargs)
		self._changingDir = False
		
		self._layoutUI()
		self.onBrushDirChanged(os.path.abspath(__file__))
		wx.GetApp().doc.addEventListener('onBrushDirChanged', self.onBrushDirChanged)
		self.GetParent().Bind(wx.EVT_CLOSE, self.onClosing)

	def onClosing(self, event):
		# This prevents a crash bug in win32, where for some reason this event is
		# firing after self.dirCtrl has already been destroyed.
		self.dirCtrl.GetTreeCtrl().Bind(wx.EVT_TREE_SEL_CHANGED, None)
		event.Skip()
	
	def _layoutUI(self):
		sizer = wx.BoxSizer(wx.VERTICAL)
		
		sizer.Add(wx.StaticText(self, -1, "Brush Library:"), 0, wx.ALL|wx.EXPAND)
		
		self.dirCtrl = wx.GenericDirCtrl(self, -1, style=wx.DIRCTRL_DIR_ONLY)
		self.dirCtrl.GetTreeCtrl().Bind(wx.EVT_TREE_SEL_CHANGED, self.onBrushDirSelected)
		sizer.Add(self.dirCtrl, 1, wx.ALL|wx.EXPAND)
		
		whiteMask = wx.CheckBox(self, -1, "Use White as Alpha")
		whiteMask.SetValue(True)
		self.Bind(wx.EVT_CHECKBOX, self.onWhiteMaskChanged, whiteMask)
		sizer.Add(whiteMask, 0, wx.ALL|wx.EXPAND)
		
		sizer.Add(wx.StaticLine(self), 0, wx.ALL|wx.EXPAND, 5)
        
		self.SetSizer(sizer)
		
	def onBrushDirSelected(self, event):
		self._changingDir = True
		self._setBrushDir(self.dirCtrl.GetPath())
		self._changingDir = False
		
	def onBrushDirChanged(self, brushDir):
		if (not self._changingDir):
			self.dirCtrl.SetPath(brushDir)
			self.dirCtrl.ExpandPath(brushDir)
		
	def onWhiteMaskChanged(self, event):
		ImageCache.getInstance().setWhiteMask(event.IsChecked())
		wx.GetApp().doc.markDirty()
		
	def _setBrushDir(self, brushDir):
		wx.GetApp().doc.setBrushDir(brushDir)



class BrushPanel(wx.Panel):
	def __init__(self, *args, **kwargs):
		super(BrushPanel, self).__init__(*args, **kwargs)
		self._layoutUI()
		wx.GetApp().doc.addEventListener('onBrushDirChanged', self.onBrushDirChanged)
		
	def _layoutUI(self):	
		sizer = wx.BoxSizer(wx.VERTICAL)
		
		sizer.Add(wx.StaticText(self, -1, "Brushes:"), 0, wx.ALL|wx.EXPAND)
		
		self.brushList = wx.ListCtrl(self, -1, style=wx.LC_ICON|wx.LC_SINGLE_SEL|wx.LC_ALIGN_TOP)
		self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.onBrushSelected, self.brushList)
		sizer.Add(self.brushList, 1, wx.ALL|wx.EXPAND)
		
		self.SetSizer(sizer)
		
	def _populateList(self, path):
		self.brushList.ClearAll()
		
		self.imageList = wx.ImageList(IMG_SIZE, IMG_SIZE)
		
		self.items = []
		for root, dirs, files in os.walk(path):
			names = [x for x in dirs]
			names.sort()
			for name in names:				
				if (name.startswith('.')):
					dirs.remove(name)
					
			for name in files:
				imgPath = "%s/%s" % (root, name)
				if (wx.Image.CanRead(imgPath)):
					img = wx.Image(imgPath)
					if (img.IsOk()):
						img = img.Scale(IMG_SIZE, IMG_SIZE)
						bmp = img.ConvertToBitmap()
						if ((bmp.GetWidth() != IMG_SIZE) or (bmp.GetHeight() != IMG_SIZE)):
							raise Exception("Houston, we have a problem.")
						imgIndex = self.imageList.Add(bmp)
						self.items.append((name.split('.')[0], imgIndex, imgPath))
						
		self.brushList.SetImageList(self.imageList, wx.IMAGE_LIST_NORMAL)
	
		for i in xrange(len(self.items)):
			name, imgIndex, imgPath = self.items[i]
			self.brushList.InsertItem(i, imgIndex)
			#self.brushList.InsertImageStringItem(i, name, imgIndex)
	
	def onBrushDirChanged(self, brushDir):
		self._populateList(brushDir)
	
	def onBrushSelected(self, event):
		wx.GetApp().doc.setBrush(self.items[event.Index][2])
		
	def getRandomBrush(self):
		return random.choice(self.items)[2]
	
