import wx

TOOL_SELECT = 10
TOOL_BRUSH = 20
TOOL_MOVE = 30
TOOL_ZOOM_RESET = 40
TOOL_ZOOM_IN = 50
TOOL_ZOOM_OUT = 60
TOOL_GRID = 70

class ITool(object):
	def __init__(self, canvas):
		self._canvas = canvas
		
	def onMouseEnter(self):
		return False
	def onMouseExit(self):
		return False
	def onMouseMove(self, x, y):
		return False
	def onLeftDown(self, x, y):
		return False
	def onLeftUp(self, x, y):
		return False
	def onRightDown(self, x, y):
		return False
	def onRightUp(self, x, y):
		return False
	def onKeyUp(self, key):
		return False
	def onKeyDown(self, key):
		return False
	def onActivated(self):
		pass
	def draw(self, gc, x, y):
		pass	
	
def getMapPoint(canvas, x, y, snapToGrid=True):
	doc = wx.GetApp().doc
	pt = [x, y]
	if (snapToGrid and (doc.grid is not None) and 
	    (doc.grid.enabled) and (doc.grid.snapEnabled)):
		gridW = doc.grid.w * canvas.getScale()
		gridH = doc.grid.h * canvas.getScale()			
		offsetX, offsetY = canvas.getOffset()		
		modX = offsetX % gridW
		modY = offsetY % gridH
		
		pt[0] += (gridW/2) - modX
		pt[1] += (gridH/2) - modY
		
		pt = doc.grid.snap(pt[0], pt[1], canvas.getScale())
						
		pt[0] += modX
		pt[1] += modY
	return pt

class BrushTool(ITool):
	def __init__(self, canvas):
		super(BrushTool, self).__init__(canvas)
		
		self._brush = None
		self._hasMouse = False
		self._lastBrushPt = (0, 0)
		
		wx.GetApp().doc.addEventListener('onBrushChanged', self.onBrushChanged)
		
	def onBrushChanged(self, brush):
		self._brush = brush
		wx.GetApp().mainWindow.Refresh()
		
	def onMouseEnter(self):
		self._hasMouse = True
		return True

	def onMouseExit(self):
		self._hasMouse = False
		return True
		
	def onMouseMove(self, x, y):
		self._hasMouse = True
		
		doc = wx.GetApp().doc
		ptBrush = getMapPoint(self._canvas, x, y)
							
		if ((self._brush is not None) and (ptBrush != self._lastBrushPt)):
			self._lastBrushPt = ptBrush
			return True
		
		return False
		
	def onLeftUp(self, x, y):
		if ((self._brush is not None) and (self._lastBrushPt is not None)):
			mapCoords = self._canvas.toMapCoord(*self._lastBrushPt)
			wx.GetApp().doc.strokeBrush(*mapCoords)
			return True
		return False
		
	def onRightUp(self, x, y):
		if (self._brush is not None):
			if (wx.GetApp().mainWindow.randomizeBrushes):
				wx.GetApp().mainWindow.randomizeBrush(wx.GetApp().doc)
			else:
				self._brush.rotate()
			return True
		return False

	def draw(self, gc, x, y):
		if (not self._hasMouse):
			return
		
		doc = wx.GetApp().doc
		if ((self._brush is not None) and (self._lastBrushPt is not None)):
			gc.PushState()
			gc.Translate(*self._lastBrushPt)
			scale = self._canvas.getScale()
			gc.Scale(scale, scale)
			color = wx.Colour(255, 255, 255, 128)
			gc.SetBrush(wx.Brush(color))
			gc.SetPen(wx.Pen(color))
			self._brush.draw(gc, 0, 0)
			gc.PopState()

class MoveTool(ITool):
	def __init__(self, canvas):
		super(MoveTool, self).__init__(canvas)
		self._lastMouse = None
		self.enabled = False
		
	def onLeftDown(self, x, y):
		self.setEnabled(True)
		return False

	def onLeftUp(self, x, y):
		self.setEnabled(False)
		return False
		
	def setEnabled(self, enabled):
		self.enabled = enabled
		self._lastMouse = None
		
	def onMouseMove(self, x, y):
		needsRefresh = False
		if ((self.enabled) and (self._lastMouse is not None)):
			self._canvas.offset(x - self._lastMouse[0], 
			                    y - self._lastMouse[1])
			needsRefresh = True		
		self._lastMouse = (x, y)
		return needsRefresh	
	
class SelectTool(ITool):
	def __init__(self, canvas):
		super(SelectTool, self).__init__(canvas)

		self._selectedStroke = None
		self._dragOffset = None
		self._ptBrush = (0, 0)
		self._lastMouse = None
		self._dragging = False
		
		self._popupMenu = wx.Menu()

		rotCId = wx.NewId()
		self._popupMenu.Append(rotCId, "Rotate Clockwise")
		self._canvas.Bind(wx.EVT_MENU, self.onRotateClockwise, id=rotCId)
		
		rotCCId = wx.NewId()
		self._popupMenu.Append(rotCCId, "Rotate Counter-Clockwise")
		self._canvas.Bind(wx.EVT_MENU, self.onRotateCounterClockwise, id=rotCCId)
		
		delId = wx.NewId()
		self._popupMenu.Append(delId, "Delete")
		self._canvas.Bind(wx.EVT_MENU, self.onDelete, id=delId)
		
	def onLeftDown(self, x, y):		
		mapCoords = self._canvas.toMapCoord(x, y)
		self._selectedStroke = wx.GetApp().doc.selectStroke(*mapCoords)
		if (self._selectedStroke is not None):
			offset = self._canvas.getOffset()
			self._dragOffset = [offset[0] - x, offset[1] - y]
			
			self._dragOffset[0] += (self._selectedStroke.x + self._selectedStroke.w/2) * self._canvas.getScale()
			self._dragOffset[1] += (self._selectedStroke.y + self._selectedStroke.h/2) * self._canvas.getScale()

			self._ptBrush = getMapPoint(self._canvas, x + self._dragOffset[0], y + self._dragOffset[1], False)
			wx.GetApp().doc.markDirty()
			self._dragging = True
		return True
	
	def onLeftUp(self, x, y):
		if (self._selectedStroke is not None):
			if (self._dragging):
				mapCoords = self._canvas.toMapCoord(*self._ptBrush)
				self._selectedStroke.x = mapCoords[0] - self._selectedStroke.w/2
				self._selectedStroke.y = mapCoords[1] - self._selectedStroke.h/2
			wx.GetApp().doc.replaceSelectedStroke()
			self._dragging = False
		return False
		
	def onMouseMove(self, x, y):
		if (self._dragging):
			newX = x + self._dragOffset[0]
			newY = y + self._dragOffset[1]
			self._ptBrush = getMapPoint(self._canvas, newX, newY)
			self._dragging = True
		self._lastMouse = (x, y)
		return self._dragging

	def onRightUp(self, x, y):
		self._canvas.PopupMenu(self._popupMenu)

	def onKeyDown(self, key):
		if (self._selectedStroke is not None):
			if (key == wx.WXK_LEFT):
				self._selectedStroke.x -= 1
				wx.GetApp().doc.markDirty()
				return True
			elif (key == wx.WXK_RIGHT):
				self._selectedStroke.x += 1
				wx.GetApp().doc.markDirty()
				return True
			elif (key == wx.WXK_UP):
				self._selectedStroke.y -= 1
				wx.GetApp().doc.markDirty()
				return True
			elif (key == wx.WXK_DOWN):
				self._selectedStroke.y += 1
				wx.GetApp().doc.markDirty()
				return True
			elif (key == wx.WXK_DELETE):
				self._deleteStroke()
				return True
	
	def onRotateClockwise(self, event):
		if (self._selectedStroke is not None):
			self._selectedStroke.rotate(1)
			wx.GetApp().doc.markDirty()
	
	def onRotateCounterClockwise(self, event):
		if (self._selectedStroke is not None):
			self._selectedStroke.rotate(-1)
			wx.GetApp().doc.markDirty()
	
	def onDelete(self, event):
		self._deleteStroke()
		
	def _deleteStroke(self):
		if (self._selectedStroke is None):
			mapCoords = self._canvas.toMapCoord(*self._lastMouse)
			self._selectedStroke = wx.GetApp().doc.selectStroke(*mapCoords)
		if (self._selectedStroke is not None):
			wx.GetApp().doc.deleteStroke(self._selectedStroke)
			self._selectedStroke = None
		
	def onActivated(self):
		self._selectedStroke = None		
		
	def draw(self, gc, x, y):
		if (self._selectedStroke is not None):
			gc.PushState()			
			scale = self._canvas.getScale()
			if (self._dragging):
				gc.Translate(*self._ptBrush)
				gc.Scale(scale, scale)
			else:
				gc.Translate(*self._canvas.getOffset())
				gc.Scale(scale, scale)
				gc.Translate(self._selectedStroke.x, self._selectedStroke.y)
			color = wx.Colour(255, 255, 255, 128)
			gc.SetBrush(wx.Brush(color))
			if (self._dragging):
				gc.Translate(-self._selectedStroke.w/2, -self._selectedStroke.h/2)
				self._selectedStroke.drawTo(gc, 0, 0)
			gc.SetPen(wx.Pen(wx.Colour(0, 255, 0), 5))
			gc.SetBrush(wx.Brush(wx.Colour(0, 0, 0, 0)))
			gc.DrawRoundedRectangle(0, 0, self._selectedStroke.w, self._selectedStroke.h, 5)
			gc.PopState()
			