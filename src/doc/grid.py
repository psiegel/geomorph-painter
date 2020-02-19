from lxml import etree
import wx

class Grid(object):
	def __init__(self, w, h, x=0, y=0, lineWidth=1, color=wx.BLACK):
		self.x = x
		self.y = y
		self.w = w
		self.h = h
		self.lineWidth = lineWidth
		self.color = color
		self.enabled = False
		self.snapEnabled = False
		self.renderAbove = True

	def _createGridPath(self, gc):
		path = gc.CreatePath()
		path.MoveToPoint(0, self.h)
		path.AddLineToPoint(self.w, self.h)
		path.AddLineToPoint(self.w, 0)
		return path

	def draw(self, gc, w, h):
		gc.PushState()
		
		path = self._createGridPath(gc)
		gc.SetPen(wx.Pen(self.color, self.lineWidth))

		startX = self.x
		while (startX > 0):
			startX -= self.w
		startY = self.y
		while (startY > 0):
			startY -= self.h
		gc.Translate(startX, startY)

		x = startX
		y = startY
		gc.PushState() 
		while x < w:
			gc.PushState()
			while y < h:
				gc.StrokePath(path)
				gc.Translate(0, self.h)
				y += self.h
			gc.PopState()
			gc.Translate(self.w, 0)
			x += self.w
			y = startY
		gc.PopState()     
		
		gc.PopState()

	def snap(self, x, y, scale):
		w = self.w * scale
		h = self.h * scale
		return [int(x / w) * w, int(y / h) * h]
	
	def toNode(self):
		gridNode = etree.Element('grid',
		                         x = '%d' % self.x,
		                         y = '%d' % self.y,
		                         w = '%d' % self.w,
		                         h = '%d' % self.h,
		                         lineWidth = '%d' % self.lineWidth,
		                         color = self.color.GetAsString(),
		                         enabled = 'true' if self.enabled else 'false',
		                         snap = 'true' if self.snapEnabled else 'false')
		return gridNode
			
	def fromNode(self, gridNode):
		self.x = int(gridNode.get('x'))
		self.y = int(gridNode.get('y'))
		self.w = int(gridNode.get('w'))
		self.h = int(gridNode.get('h'))
		self.lineWidth = int(gridNode.get('lineWidth'))
		self.color.Set(gridNode.get('color'))
		self.enabled = (gridNode.get('enabled') == 'true')
		self.snapEnabled = (gridNode.get('enabled') == 'true')
