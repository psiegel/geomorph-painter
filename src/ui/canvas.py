import wx

from ui import tools

class CanvasPanel(wx.Panel):
	def __init__(self, *args, **kwargs):
		super(CanvasPanel, self).__init__(*args, **kwargs)
		self.SetBackgroundStyle(wx.BG_STYLE_CUSTOM)
		self.SetDoubleBuffered(True)

		self._offset = [0, 0]
		self._mapBmp = None
		self._grid = None
		self._buffer = None
		self._scale = 1.0
		
		self._mouse = (0, 0)
		self._axisLock = (False, False)
		self._tool = None
		self._savedToolId = None
		
		self.Bind(wx.EVT_SIZE, self.onSize)
		self.Bind(wx.EVT_PAINT, self.onPaint)
		self.Bind(wx.EVT_ENTER_WINDOW, self.onMouseEnter)
		self.Bind(wx.EVT_LEAVE_WINDOW, self.onMouseExit)
		self.Bind(wx.EVT_MOTION, self.onMouseMove)
		self.Bind(wx.EVT_LEFT_DOWN, self.onLeftDown)
		self.Bind(wx.EVT_LEFT_UP, self.onLeftUp)
		self.Bind(wx.EVT_RIGHT_DOWN, self.onRightDown)
		self.Bind(wx.EVT_RIGHT_UP, self.onRightUp)
		self.Bind(wx.EVT_MIDDLE_DOWN, self.onMiddleDown)
		self.Bind(wx.EVT_MIDDLE_UP, self.onMiddleUp)
		self.Bind(wx.EVT_MOUSEWHEEL, self.onWheel)
		self.Bind(wx.EVT_KEY_DOWN, self.onKeyDown)
		self.Bind(wx.EVT_KEY_UP, self.onKeyUp)
		
		wx.GetApp().doc.addEventListener('onMapChanged', self.onMapChanged)
		wx.GetApp().doc.addEventListener('onNewMap', self.onNewMap)
		wx.GetApp().doc.addEventListener('onGridChanged', self.onGridChanged)
		
	def reset(self):
		self._offset = [0, 0]
		self._scale = 1.0
		self._mapBmp = None
		
	def offset(self, x, y):
		self._offset[0] += x
		self._offset[1] += y
		
	def getOffset(self):
		return self._offset
		
	def setTool(self, tool):
		self._tool = tool
		
	def onMapChanged(self, doc, needsPaint):
		if (needsPaint):
			xOff, yOff, self._mapBmp = doc.buildImage()
			if (self._mapBmp is not None):
				self.offset(xOff * self._scale, yOff * self._scale)
			self.Refresh()
			
	def onNewMap(self, doc):
		self.reset()
		xOff, yOff, self._mapBmp = doc.buildImage()
		self.Refresh()		
			
	def onGridChanged(self, grid):
		self._grid = grid
		self.Refresh()
		
	def onSize(self, event):
		w, h = self.GetClientSize()
		self._buffer = wx.Bitmap(w, h)
		self.Refresh()
		
	def onPaint(self, event):
		dc = wx.BufferedPaintDC(self, self._buffer)
		try:
			gc = wx.GraphicsContext.Create(dc)
		except NotImplementedError:
			dc.DrawText("This build of wxPython does not support the wx.GraphicsContext "
						"family of classes.", 25, 25)
			return	

		gc.PushState()									
		self._draw(gc)
		gc.PopState()
		
	def onMouseEnter(self, event):
		if (self._tool is not None):
			if (self._tool.onMouseEnter()):
				self.Refresh()
		
	def onMouseExit(self, event):
		if (self._tool is not None):
			if (self._tool.onMouseExit()):
				self.Refresh()
	
	def onMouseMove(self,event):
		self._axisLock = (event.ShiftDown(), event.ControlDown())

		mousePos = event.GetPosition()
		if (not self._axisLock[0] and not self._axisLock[1]):
			self._mouse = mousePos
		elif (self._axisLock[0]):
			self._mouse = (self._mouse[0], mousePos[1])
		elif (self._axisLock[1]):
			self._mouse = (mousePos[0], self._mouse[1])
			
		if (self._tool is not None):
			if (self._tool.onMouseMove(self._mouse[0], self._mouse[1])):
				self.Refresh()	
				
		event.Skip()
			
	def onLeftDown(self, event):
		if (self._tool is not None):
			if (self._tool.onLeftDown(self._mouse[0], self._mouse[1])):
				self.Refresh()
		event.Skip()

	def onLeftUp(self, event):
		if (self._tool is not None):
			if (self._tool.onLeftUp(self._mouse[0], self._mouse[1])):
				self.Refresh()
		event.Skip()
	
	def onRightDown(self, event):
		if (self._tool is not None):
			if (self._tool.onRightDown(self._mouse[0], self._mouse[1])):
				self.Refresh()
		event.Skip()
			
	def onRightUp(self, event):
		if (self._tool is not None):
			if (self._tool.onRightUp(self._mouse[0], self._mouse[1])):
				self.Refresh()
		event.Skip()
		
	def onWheel(self, event):
		if (event.WheelRotation > 0):
			self.modifyScale(0.1, self._mouse)
		else:
			self.modifyScale(-0.1, self._mouse)		

	def onKeyDown(self, event):
		if (self._tool is not None):
			if (self._tool.onKeyDown(event.GetKeyCode())):
				self.Refresh()
		event.Skip()

	def onKeyUp(self, event):
		if (self._tool is not None):
			if (self._tool.onKeyUp(event.GetKeyCode())):
				self.Refresh()
		event.Skip()
				
	def onMiddleDown(self, event):
		self._savedToolId = wx.GetApp().mainWindow.getToolId()
		wx.GetApp().mainWindow.setTool(tools.TOOL_MOVE)
		self._tool.setEnabled(True)
		event.Skip()
		
	def onMiddleUp(self, event):
		if (self._savedToolId is not None):
			self._tool.setEnabled(False)
			wx.GetApp().mainWindow.setTool(self._savedToolId)
			self.Refresh()
		self._savedToolId = None
		event.Skip()
		
	def setScale(self, scale, centerPt=None):
		if (centerPt is None):
			w, h = self.GetClientSize()
			centerPt = (w/2, h/2)
		self._offset[0] = centerPt[0] - (((centerPt[0] - self._offset[0]) / self._scale) * scale)
		self._offset[1] = centerPt[1] - (((centerPt[1] - self._offset[1]) / self._scale) * scale)
		self._scale = scale		

		# Refresh the tool's mouse location to allow it to update
		# based on the new scale.
		if (self._tool is not None):
			self._tool.onMouseMove(*self._mouse)
			
		self.Refresh()

	def modifyScale(self, increment, centerPt=None):
		self.setScale(self._scale + (self._scale * increment), centerPt)
		
	def getScale(self):
		return self._scale
		
	def toMapCoord(self, mouseX, mouseY):
		mouseX -= self._offset[0]
		mouseY -= self._offset[1]
		mouseX /= self._scale
		mouseY /= self._scale
		return (round(mouseX), round(mouseY))
			
	def _draw(self, gc):
		w, h = self.GetSize()		
		gc.SetBrush(wx.Brush("white"))
		gc.DrawRectangle(0, 0, w, h)
		
		if ((self._grid is not None) and self._grid.enabled and not self._grid.renderAbove):
			self._drawGrid(gc)
		self._drawMap(gc)
		if ((self._grid is not None) and self._grid.enabled and self._grid.renderAbove):
			self._drawGrid(gc)
		
		if (self._tool is not None):
			self._tool.draw(gc, self._mouse[0], self._mouse[1])
		
	def _drawMap(self, gc):		
		if (self._mapBmp is None):
			return
		
		gc.PushState()
		
		gc.Translate(*self._offset)
		gc.Scale(self._scale, self._scale)
		
		color = wx.Colour(255, 255, 255)
		gc.SetBrush(wx.Brush(color))
		
		w = self._mapBmp.GetWidth()
		h = self._mapBmp.GetHeight()
		gc.DrawBitmap(self._mapBmp, 0, 0, w, h)
		
		gc.PopState()
			
	def _drawGrid(self, gc):
		if ((self._grid is None) or (not self._grid.enabled)):
			return
			
		gc.PushState()
		
		gridW = self._grid.w * self._scale
		gridH = self._grid.h * self._scale

		x = (self._offset[0] % gridW) - gridW
		y = (self._offset[1] % gridH) - gridH
				
		gc.Translate(x, y)
		gc.Scale(self._scale, self._scale)
		
		w, h = self.GetClientSize()
		self._grid.draw(gc, 
		                (w / self._scale) + gridW, 
		                (h / self._scale) + gridH)
		
		gc.PopState()
			