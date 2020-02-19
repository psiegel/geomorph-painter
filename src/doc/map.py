import base64
import os
import sys
import wx
from lxml import etree

from doc.grid import Grid
from util.events import EventProducer, event

class MapDocument(EventProducer):
	def __init__(self):
		super(MapDocument, self).__init__()
		self._brushDir = None
		self._brush = None
		self._strokes = []
		self._dirty = False
		self._lastSavePath = None
		self.selectedStroke = None
		self.grid = None
		
	def setBrush(self, imgPath):
		self._brush = Brush(imgPath)
		self.onBrushChanged(self._brush)
		return self._brush

	def strokeBrush(self, x, y):
		if (self._brush is not None):
			self._strokes.append(self._brush.createStroke(x, y))
		self.markDirty()

	def buildImage(self, includeGrid=False, useWhiteMask=True):
		x, y, w, h = self._getBoundingRect()
		if ((w < 1) or (h < 1)):
			return (x, y, None)
		
		if ((x != 0) or (y != 0)):
			w -= x
			h -= y
			for stroke in self._strokes:
				stroke.x -= x
				stroke.y -= y
		
		bmp = wx.Bitmap.FromRGBA(int(w), int(h), 255, 255, 255, 255)
		
		dc = wx.MemoryDC()
		dc.SelectObject(bmp)
		gc = wx.GraphicsContext.Create(dc)
		
		if (includeGrid and self.grid.enabled and not self.grid.renderAbove):
			self.grid.draw(gc, w, h)
		
		for stroke in self._strokes:
			stroke.draw(gc)
		
		if (includeGrid and self.grid.enabled and self.grid.renderAbove):
			self.grid.draw(gc, w, h)
			
		if (useWhiteMask and ImageCache.getInstance().getWhiteMask()):
			img = bmp.ConvertToImage()
			ImageCache.getInstance().setImageAlpha(img)
			bmp = img.ConvertToBitmap()
								
		return (x, y, bmp)
	
	def selectStroke(self, x, y):
		self.selectedStroke = self.findStroke(x, y)
		if (self.selectedStroke is not None):
			self._strokes.remove(self.selectedStroke)
		return self.selectedStroke
				
	def deleteSelectedStroke(self):
		if (self.selectedStroke is not None):
			self.deleteStroke(self.selectedStroke)
		
	def replaceSelectedStroke(self):
		if (self.selectedStroke is not None):
			self._strokes.append(self.selectedStroke)
			self.selectedStroke = None
			self.markDirty()

	def deleteStroke(self, stroke):
		if (self.selectedStroke == stroke):
			self.selectedStroke = None
		if (stroke in self._strokes):
			self._strokes.remove(stroke)
		self.markDirty()
						
	def findStroke(self, x, y):
		for stroke in self._strokes:
			if (stroke.isInside(x, y)):
				return stroke
		return None
		
	def markDirty(self, needsPaint=True):
		self._dirty = True
		self.onMapChanged(self, needsPaint)
		
	def clearDirty(self):
		self._dirty = False
		
	def new(self):
		if (self.checkForSave() == wx.ID_CANCEL):
			return

		self._strokes = []
		self.grid = Grid(27, 27, 0, 0)
		self.clearDirty()
		
		self.onNewMap(self)
		self.onGridChanged(self.grid)
		
	def load(self):
		if (self.checkForSave() == wx.ID_CANCEL):
			return
		
		defaultFile = ''
		if (self._lastSavePath is not None):
			defaultFile = self._lastSavePath
		dlg = wx.FileDialog(wx.GetApp().mainWindow,
		                    message="Choose a file",
		                    defaultDir=os.getcwd(), 
		                    defaultFile=defaultFile,
		                    wildcard="Xml file (*.xml)|*.xml|All files (*.*)|*.*",
		                    style=wx.FD_OPEN | wx.FD_CHANGE_DIR)
		if (dlg.ShowModal() == wx.ID_OK):
			path = dlg.GetPath()
			inFile = open(path, 'r')
			node = etree.parse(inFile)
			self.fromNode(node.getroot())
			self._lastSavePath = path
		dlg.Destroy()
			
	def checkForSave(self):
		retVal = wx.YES
		if (self._dirty):
			dlg = wx.MessageDialog(wx.GetApp().mainWindow, 
			                       'Recent changes have not been saved.  Save now?',
			                       'Save Canvas?',
			                       wx.YES_NO | wx.CANCEL | wx.ICON_WARNING)
			retVal = dlg.ShowModal()
			if (retVal == wx.YES):
				self.save()
			dlg.Destroy()
		return retVal
		
	def save(self):
		if (self._lastSavePath is None):
			self.saveAs()
		else:
			self._doSave(self._lastSavePath)
		
	def saveAs(self):
		defaultFile = ''
		if (self._lastSavePath is not None):
			defaultFile = self._lastSavePath
		dlg = wx.FileDialog(wx.GetApp().mainWindow,
		                    message="Save canvas as ...", 
		                    defaultDir=os.getcwd(), 
		                    defaultFile=defaultFile, 
		                    wildcard="Xml file (*.xml)|*.xml|All files (*.*)|*.*",
		                    style=wx.FD_SAVE)
		if dlg.ShowModal() == wx.ID_OK:
			self._doSave(dlg.GetPath())
		dlg.Destroy()
	
	def _doSave(self, path):
		node = self.toNode()
		strNode = etree.tostring(node, pretty_print=True)
		outFile = open(path, 'w')
		outFile.write(strNode)
		self.clearDirty()
		self._lastSavePath = path
		
	def export(self):
		dlg = wx.FileDialog(wx.GetApp().mainWindow,
		                    message="Export canvas to ....",
		                    defaultDir=os.getcwd(), 
		                    wildcard="Png file (*.png)|*.png|All files (*.*)|*.*",
		                    style=wx.FD_SAVE)
		if dlg.ShowModal() == wx.ID_OK:
			path = dlg.GetPath()
			x, y, bmp = self.buildImage(True, False)
			bmp.SaveFile(path, wx.BITMAP_TYPE_PNG)
		dlg.Destroy()
	
	def toNode(self):
		rootNode = etree.Element('map')
		if (self._brushDir is not None):
			rootNode.set('brushDir', self._brushDir)
			
		# grid
		rootNode.append(self.grid.toNode())
		
		# strokes
		strokeRoot = etree.Element('strokes')
		for stroke in self._strokes:
			strokeRoot.append(stroke.toNode())
		rootNode.append(strokeRoot)

		# image data
		rootNode.append(ImageCache.getInstance().toNode())
		
		return rootNode
			
	def fromNode(self, rootNode):
		self.setBrushDir(rootNode.get('brushDir'))

		# image data
		imagesNode = rootNode.find('images')
		if (imagesNode is not None):
			ImageCache.getInstance().fromNode(imagesNode)
			
		# strokes
		self._strokes = []
		strokesNode = rootNode.find('strokes')
		if (strokesNode is not None):
			for strokeNode in strokesNode:
				if (strokeNode.tag == 'stroke'):
					self._strokes.append(BrushStroke.fromNode(strokeNode))
					
		# grid
		gridNode = rootNode.find('grid')
		if (gridNode is not None):
			self.grid.fromNode(gridNode)
				
		self.onNewMap(self)
		self.onGridChanged(self.grid)

	def _getBoundingRect(self):
		x = 0
		y = 0
		w = 0
		h = 0

		if len(self._strokes) > 0:
			x = sys.maxint
			y = sys.maxint
			for stroke in self._strokes:
				sx, sy, sw, sh = stroke.getRect()
				x = min(x, sx)
				y = min(y, sy)
				w = max(w, sx + sw)
				h = max(h, sy + sh)

		if ((self.grid is not None) and (self.grid.enabled)):
			xMod = x % self.grid.w
			x -= xMod
			w += xMod
			w += w % self.grid.w
			
			yMod = y % self.grid.h
			y -= yMod
			h += yMod
			h += h % self.grid.h			
		
		return (x, y, w, h)
	
	def setBrushDir(self, brushDir):
		self._brushDir = brushDir
		self.onBrushDirChanged(self._brushDir)
		
	@event
	def onBrushDirChanged(self, brushDir):
		pass

	@event 
	def onBrushChanged(self, brush):
		pass

	@event
	def onMapChanged(self, doc, needsPaint):
		pass
	
	@event
	def onNewMap(self, doc):
		pass
	
	@event
	def onGridChanged(self, grid):
		pass


class Brush(object):
	ROT_NONE = 0
	ROT_90 = 1
	ROT_180 = 2
	ROT_270 = 3

	def __init__(self, imgPath):
		self.imgPath = imgPath
		self.rot = Brush.ROT_NONE
		self._bmp = None

	def _createBmp(self):
		img = wx.Image(self.imgPath)
		for i in xrange(self.rot):
			img = img.Rotate90()
		alphaBytes = chr(128) * (img.GetWidth() * img.GetHeight())
		img.SetAlphaBuffer(alphaBytes)
		return img.ConvertToBitmap()

	def rotate(self, direction=1):
		self.rot += direction
		if (self.rot > Brush.ROT_270):
			self.rot = Brush.ROT_NONE
		if (self.rot < Brush.ROT_NONE):
			self.rot = Brush.ROT_270
		self._bmp = None

	def draw(self, gc, x, y):
		if (self._bmp is None):
			self._bmp = self._createBmp()
		w = self._bmp.GetWidth()
		h = self._bmp.GetHeight()
		gc.DrawBitmap(self._bmp, x - (w/2), y - (h/2), w, h)

	def createStroke(self, x, y):
		stroke = BrushStroke(self.imgPath, x, y, self.rot)
		stroke.x -= stroke.w / 2
		stroke.y -= stroke.h / 2
		return stroke

class BrushStroke(object):
	def __init__(self, imgPath, x, y, rot):
		self.imgPath = imgPath
		self.rot = rot
		self.x = x
		self.y = y
		
		self._bmp = ImageCache.getInstance().getImage(self.imgPath, self.rot)
		self.w = self._bmp.GetWidth()
		self.h = self._bmp.GetHeight()
		
	def __del__(self):
		ImageCache.getInstance().releaseImage(self.imgPath, self.rot)

	def draw(self, gc):
		self.drawTo(gc, self.x, self.y)
		
	def drawTo(self, gc, x, y):
		gc.DrawBitmap(self._bmp, x, y, self.w, self.h)

	def getRect(self):
		return (self.x, self.y, self.w, self.h)	
	
	def isInside(self, x, y):
		return ( (x >= self.x) and 
		         (y >= self.y) and
		         (x < (self.x + self. w)) and 
		         (y < (self.y + self.h)) )
	
	def rotate(self, direction=1):
		ImageCache.getInstance().releaseImage(self.imgPath, self.rot)
		self.rot += direction
		if (self.rot > Brush.ROT_270):
			self.rot = Brush.ROT_NONE
		if (self.rot < Brush.ROT_NONE):
			self.rot = Brush.ROT_270
		self._bmp = ImageCache.getInstance().getImage(self.imgPath, self.rot)
	
	def toNode(self):
		node = etree.Element("stroke")
		node.set('imgPath', self.imgPath)
		node.set('x', '%d' % self.x)
		node.set('y', '%d' % self.y)
		node.set('rot', str(self.rot))
		return node
	
	@staticmethod
	def fromNode(node):
		imgPath = node.get('imgPath')
		x = int(node.get('x'))
		y = int(node.get('y'))
		rot = int(node.get('rot'))
		return BrushStroke(imgPath, x, y, rot)


class ImageCache(object):
	__instance = None

	@staticmethod
	def getInstance():
		if ImageCache.__instance is None:
			ImageCache.__instance = ImageCache()
		return ImageCache.__instance

	def __init__(self):
		self._cache = {}
		self._bmpCache = {}
		self._whiteMask = True
		
	def setWhiteMask(self, whiteMask):
		if (self._whiteMask != whiteMask):
			self._whiteMask = whiteMask
			self._bmpCache.clear()
			for key, val in self._cache.iteritems():
				if (self._whiteMask):
					self.setImageAlpha(val[0])
				else:
					self.clearImageAlpha(val[0])
					
	def getWhiteMask(self):
		return self._whiteMask

	def getImage(self, imgPath, rot):
		key = "%s_%s" % (imgPath, rot)
		if (not self._cache.has_key(key)):
			self._cache[key] = [self._loadImage(imgPath, rot), 1]
		else:
			self._cache[key][1] += 1
		if (not self._bmpCache.has_key(key)):
			self._bmpCache[key] = self._cache[key][0].ConvertToBitmap()						
		return self._bmpCache[key]
	
	def releaseImage(self, imgPath, rot):
		key = "%s_%s" % (imgPath, rot)
		if (key in self._cache):
			self._cache[key][1] -= 1
			if (self._cache[key][1] == 0):
				del self._cache[key]
				
	def toNode(self):
		node = etree.Element("images")
		if (self._whiteMask):
			node.set('whiteMask', 'true')
		for key, val in self._cache.iteritems():
			img, count = val
			subNode = etree.Element("image")
			subNode.set('path', key)
			subNode.set('w', '%s' % img.GetWidth())
			subNode.set('h', '%s' % img.GetHeight())
			subNode.text = base64.b64encode(img.GetData())
			node.append(subNode)
		return node
	
	def fromNode(self, node):
		self.setWhiteMask(node.get('whiteMask') == 'true')
		for subNode in node:
			path = subNode.get('path')
			if (path not in self._cache):
				w = int(subNode.get('w'))
				h = int(subNode.get('h'))
				img = wx.Image(w, h)
				img.SetData(base64.b64decode(subNode.text))
				if (self._whiteMask):
					self.setImageAlpha(img)
				else:
					self.clearImageAlpha(img)
				self._cache[path] = [img, 0]

	def _loadImage(self, imgPath, rot):
		img = wx.Image(imgPath)
		for i in xrange(rot):
			img = img.Rotate90()
		if (self._whiteMask):
			self.setImageAlpha(img)
		return img
	
	def setImageAlpha(self, img):
		data = img.GetData()
		alpha = ''
		for i in xrange(len(data) / 3):
			alpha += chr(255 - ((data[i*3] + data[i*3+1] + data[i*3+2]) / 3))
		img.SetAlpha(alpha)
		
	def clearImageAlpha(self, img):
		data = img.GetData()
		alpha = chr(255) * (len(data) / 3)
		img.SetAlpha(alpha)
	
