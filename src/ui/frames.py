import random
import wx
import wx.lib.agw.aui as aui

from ui import images
from ui import tools
from ui.brushes import BrushPanel, BrushDirPanel
from ui.canvas import CanvasPanel
			
class MainFrame(wx.Frame):	
	def __init__(self, *args, **kwargs):	
		super(MainFrame, self).__init__(*args, **kwargs)
		self._createPanes()
		self._createMenu()
		self._createToolbar()

		self._curToolId = None
		self._tools = {tools.TOOL_SELECT: tools.SelectTool(self._canvas),
		               tools.TOOL_BRUSH: tools.BrushTool(self._canvas),
		               tools.TOOL_MOVE: tools.MoveTool(self._canvas)}
		self.setTool(tools.TOOL_BRUSH)
		
		self.SetIcon(images.App.GetIcon())
		
		self.randomizeBrushes = False
		wx.GetApp().doc.addEventListener('onMapChanged', self._onMapChanged)

	def getToolId(self):
		return self._curToolId
		
	def setTool(self, toolId, toggleUI=True):
		self._curToolId = toolId
		if (toggleUI):
			self._toolbar.ToggleTool(self._curToolId, True)
		self._canvas.setTool(self._tools[self._curToolId])		
		
	def _createPanes(self):
		self._mgr = aui.AuiManager()
		self._mgr.SetManagedWindow(self)

		# Main Panel
		self._canvas = CanvasPanel(self, -1)
		self._mgr.AddPane(self._canvas, 
		                  aui.AuiPaneInfo().Name("canvas_panel").
		                  CenterPane())
		
		# Brush Panels
		self._brushes = BrushPanel(self, -1, wx.Point(0, 0), wx.Size(200, 90))
		self._mgr.AddPane(self._brushes, 
						  aui.AuiPaneInfo().Name("brush_panel").Caption("Brushes").
                          Right().Layer(1).Position(1).CloseButton(True).MaximizeButton(True))		                  
		
		self._brushDirSelector = BrushDirPanel(self, -1, wx.Point(0, 0), wx.Size(200, 300))
		self._mgr.AddPane(self._brushDirSelector, 
						  aui.AuiPaneInfo().Name("brushdir_panel").Caption("Brush Library").
                          Right().Layer(1).Position(1).CloseButton(True).MaximizeButton(True))		                  
		
		self._mgr.Update()

		self.Bind(wx.EVT_CLOSE, self.onClose)
		
	def _createMenu(self):
		menuBar = wx.MenuBar()
		
		# File Menu
		fileMenu = wx.Menu()
		fileMenu.Append(101, "New Canvas\tCTRL+N", "Create a new canvas to draw on.")
		self.Bind(wx.EVT_MENU, self.onNewCanvas, id=101)
		fileMenu.Append(102, "Open Canvas\tCTRL+O", "Open an existing canvas xml file.")
		self.Bind(wx.EVT_MENU, self.onOpenCanvas, id=102)
		fileMenu.Append(103, "Save Canvas\tCTRL+S", "Save canvas data to xml file.")
		self.Bind(wx.EVT_MENU, self.onSaveCanvas, id=103)
		fileMenu.Append(104, "Save Canvas As...\tCTRL+A", "Save canvas data to new xml file.")
		self.Bind(wx.EVT_MENU, self.onSaveCanvasAs, id=104)
		fileMenu.Append(105, "Export Canvas\tCTRL+E", "Export canvas to an image file (bmp, jpg, png, etc.).")
		self.Bind(wx.EVT_MENU, self.onExportCanvas, id=105)
		menuBar.Append(fileMenu, "File")
		
		# Tools Menu
		toolsMenu = wx.Menu()
		toolsMenu.AppendCheckItem(201, "Randomize Brushes\tCTRL+R")
		self.Bind(wx.EVT_MENU, self.onRandomizeBrushes, id=201)
		self.Bind(wx.EVT_UPDATE_UI, self.updateRandomizeBrushes, id=201)
		menuBar.Append(toolsMenu, "Tools")
		
		# View Menu
		viewMenu = wx.Menu()
		viewMenu.AppendCheckItem(301, "Brush Library")
		self.Bind(wx.EVT_MENU, self.onViewBrushLibrary, id=301)
		self.Bind(wx.EVT_UPDATE_UI, self.updateViewBrushLibrary, id=301)
		viewMenu.AppendCheckItem(302, "Brushes")
		self.Bind(wx.EVT_MENU, self.onViewBrushes, id=302)
		self.Bind(wx.EVT_UPDATE_UI, self.updateViewBrushes, id=302)
		menuBar.Append(viewMenu, "Windows")				
		self.SetMenuBar(menuBar)

		self.CreateStatusBar()
		self.CenterOnScreen()

	def _createToolbar(self):
		self._toolbar = self.CreateToolBar(wx.TB_HORIZONTAL | wx.NO_BORDER | wx.TB_FLAT)

		tsize = (24, 24)
		
		self._toolbar.AddRadioTool(tools.TOOL_SELECT, "Select", images.Select.GetBitmap(), shortHelp="Select", 
		                           longHelp="Select and modify placed geomorphs.")
		self.Bind(wx.EVT_TOOL, self.onSetTool, id=tools.TOOL_SELECT)
		
		self._toolbar.AddRadioTool(tools.TOOL_BRUSH, "Paint", images.Brush.GetBitmap(), shortHelp="Paint", 
		                           longHelp="Place new geomorphs onto the canvas.")
		self.Bind(wx.EVT_TOOL, self.onSetTool, id=tools.TOOL_BRUSH)
		
		self._toolbar.AddRadioTool(tools.TOOL_MOVE, "Move", images.Move.GetBitmap(), shortHelp="Move", 
		                           longHelp="Move the canvas about.")
		self.Bind(wx.EVT_TOOL, self.onSetTool, id=tools.TOOL_MOVE)
		
		self._toolbar.AddSeparator()
		
		self._toolbar.AddTool(tools.TOOL_ZOOM_RESET, "Reset Zoom", images.ZoomReset.GetBitmap(), 
							  shortHelp="Reset Zoom")
		self.Bind(wx.EVT_TOOL, self.onZoomReset, id=tools.TOOL_ZOOM_RESET)
		
		self._toolbar.AddTool(tools.TOOL_ZOOM_IN, "Zoom In", images.ZoomIn.GetBitmap(),
		                      shortHelp="Zoom in the canvas view.")
		self.Bind(wx.EVT_TOOL, self.onZoomIn, id=tools.TOOL_ZOOM_IN)
		
		self._toolbar.AddTool(tools.TOOL_ZOOM_OUT, "Zoom Out", images.ZoomOut.GetBitmap(),
		                      shortHelp="Zoom out the canvas view.")
		self.Bind(wx.EVT_TOOL, self.onZoomOut, id=tools.TOOL_ZOOM_OUT)
		
		self._toolbar.AddSeparator()
		
		self._toolbar.AddTool(tools.TOOL_GRID, "Grid Settings", images.Grid.GetBitmap(),
		                      shortHelp="Change settings for overlaying a grid on the canvas.")
		self.Bind(wx.EVT_TOOL, self.onSetGrid, id=tools.TOOL_GRID)
		
		self._toolbar.Realize()

	def onNewCanvas(self, event):
		wx.GetApp().doc.new()
	
	def onOpenCanvas(self, event):
		wx.GetApp().doc.load()
		
	def onSaveCanvas(self, event):
		wx.GetApp().doc.save()
		
	def onSaveCanvasAs(self, event):
		wx.GetApp().doc.saveAs()
		
	def onExportCanvas(self, event):
		wx.GetApp().doc.export()
		
	def onSetTool(self, event):
		self.setTool(event.GetId(), False)
		
	def onZoomIn(self, event):
		self._canvas.modifyScale(0.1)

	def onZoomOut(self, event):
		self._canvas.modifyScale(-0.1)
	
	def onZoomReset(self, event):
		self._canvas.setScale(1.0)
		
	def onSetGrid(self, event):
		doc = wx.GetApp().doc
		dlg = GridOptionsDialog(self, -1, "Grid Settings")
		dlg.initFromGrid(doc.grid)
		if (dlg.ShowModal() == wx.ID_OK):
			dlg.populateGrid(doc.grid)
			doc.onGridChanged(doc.grid)
		dlg.Destroy()
		
	def onViewBrushLibrary(self, event):
		self._mgr.GetPane(self._brushDirSelector).Show(event.IsChecked())
		self._mgr.Update()
	
	def onViewBrushes(self, event):
		self._mgr.GetPane(self._brushes).Show(event.IsChecked())
		self._mgr.Update()
		
	def updateViewBrushLibrary(self, event):
		event.Check(self._mgr.GetPane(self._brushDirSelector).IsShown())
		
	def updateViewBrushes(self, event):
		event.Check(self._mgr.GetPane(self._brushes).IsShown())
		
	def onRandomizeBrushes(self, event):
		self.randomizeBrushes = event.IsChecked()
	
	def updateRandomizeBrushes(self, event):
		event.Check(self.randomizeBrushes)
		
	def _onMapChanged(self, doc, needsRepaint):
		if (self.randomizeBrushes):
			self.randomizeBrush(doc)
				
	def randomizeBrush(self, doc):
		brush = doc.setBrush(self._brushes.getRandomBrush())
		for i in xrange(random.randint(0, 3)):
			brush.rotate()

	def onClose(self, event):
		self._mgr.UnInit()
		event.Skip()
		
		
class GridOptionsDialog(wx.Dialog):
	def __init__(self, *args, **kwargs):
		super(GridOptionsDialog, self).__init__(*args, **kwargs)
		self.__layoutUI()
		
	def __layoutUI(self):
		sizer = wx.BoxSizer(wx.VERTICAL)

		# Enable/disable
		line = wx.BoxSizer(wx.HORIZONTAL)
		
		self.enabledCtrl = wx.CheckBox(self, -1, "Display Grid")
		line.Add(self.enabledCtrl, 1, wx.ALL|wx.EXPAND, 5)

		self.snapCtrl = wx.CheckBox(self, -1, "Snap to Grid")
		line.Add(self.snapCtrl, 1, wx.ALL|wx.EXPAND, 5)
		
		self.aboveCtrl = wx.CheckBox(self, -1, "Render Above Map")
		line.Add(self.aboveCtrl, 1, wx.ALL|wx.EXPAND, 5)
		
		sizer.Add(line, 0, wx.ALL|wx.GROW|wx.ALIGN_CENTER_VERTICAL, 5)
		
		# Width and height
		line = wx.BoxSizer(wx.HORIZONTAL)
		
		line.Add(wx.StaticText(self, -1, "Width:"), 0, wx.ALL|wx.ALIGN_CENTER, 5)
		self.widthCtrl = wx.SpinCtrl(self, -1)
		line.Add(self.widthCtrl, 1, wx.ALL|wx.ALIGN_CENTER, 5)
		
		line.Add(wx.StaticText(self, -1, "Height:"), 0, wx.ALL|wx.ALIGN_CENTER, 5)
		self.heightCtrl = wx.SpinCtrl(self, -1)
		line.Add(self.heightCtrl, 1, wx.ALL|wx.ALIGN_CENTER, 5)
		
		sizer.Add(line, 0, wx.ALL|wx.GROW|wx.ALIGN_CENTER_VERTICAL, 5)
		
		# x/y offsets
		line = wx.BoxSizer(wx.HORIZONTAL)
		
		line.Add(wx.StaticText(self, -1, "X Offset:"), 0, wx.ALL|wx.ALIGN_CENTER, 5)
		self.xOffCtrl = wx.SpinCtrl(self, -1)
		line.Add(self.xOffCtrl, 1, wx.ALL|wx.ALIGN_CENTER, 5)
		
		line.Add(wx.StaticText(self, -1, "Y Offset:"), 0, wx.ALL|wx.ALIGN_CENTER, 5)
		self.yOffCtrl = wx.SpinCtrl(self, -1)
		line.Add(self.yOffCtrl, 1, wx.ALL|wx.ALIGN_CENTER, 5)
		
		sizer.Add(line, 0, wx.ALL|wx.GROW|wx.ALIGN_CENTER_VERTICAL, 5)
		
		# color and line width
		line = wx.BoxSizer(wx.HORIZONTAL)
		
		line.Add(wx.StaticText(self, -1, "Line Color:"), 0, wx.ALL|wx.ALIGN_CENTER, 5)
		self.colorCtrl = wx.Button(self, -1)
		self.colorCtrl.SetBackgroundColour(wx.BLACK)
		self.Bind(wx.EVT_BUTTON, self.onColorSelect, self.colorCtrl)
		line.Add(self.colorCtrl, 1, wx.ALL|wx.ALIGN_CENTER, 5)
		
		line.Add(wx.StaticText(self, -1, "Line Width:"), 0, wx.ALL|wx.ALIGN_CENTER, 5)
		self.lineWidthCtrl = wx.SpinCtrl(self, -1)
		line.Add(self.lineWidthCtrl, 1, wx.ALL|wx.ALIGN_CENTER, 5)
		
		sizer.Add(line, 0, wx.ALL|wx.GROW|wx.ALIGN_CENTER_VERTICAL, 5)
		
		# OK/Cancel
		btnsizer = wx.StdDialogButtonSizer()
		
		btn = wx.Button(self, wx.ID_OK)
		btn.SetDefault()
		btnsizer.AddButton(btn)
		
		btn = wx.Button(self, wx.ID_CANCEL)
		btnsizer.AddButton(btn)
		btnsizer.Realize()
		
		sizer.Add(btnsizer, 0, wx.ALL|wx.EXPAND, 5)
		
		self.SetSizer(sizer)
		sizer.Fit(self)
		
	def onColorSelect(self, event):
		dlg = wx.ColourDialog(self)
		dlg.GetColourData().SetChooseFull(True)
		if (dlg.ShowModal() == wx.ID_OK):
			self.colorCtrl.SetBackgroundColour(dlg.GetColourData().GetColour())
		dlg.Destroy()
		
	def initFromGrid(self, grid):
		self.xoff = grid.x
		self.yoff = grid.y
		self.width = grid.w
		self.height = grid.h
		self.enabled = grid.enabled
		self.color = grid.color
		self.lineWidth = grid.lineWidth
		self.snap = grid.snapEnabled
		self.renderAbove = grid.renderAbove
		
	def populateGrid(self, grid):
		grid.x = self.xoff
		grid.y = self.yoff
		grid.w = self.width
		grid.h = self.height
		grid.enabled = self.enabled
		grid.color = self.color
		grid.lineWidth = self.lineWidth
		grid.snapEnabled = self.snap
		grid.renderAbove = self.renderAbove
		
	enabled = property(lambda self: self.enabledCtrl.GetValue(), lambda self, x: self.enabledCtrl.SetValue(x))
	width = property(lambda self: self.widthCtrl.GetValue(), lambda self, x: self.widthCtrl.SetValue(x))
	height = property(lambda self: self.heightCtrl.GetValue(), lambda self, x: self.heightCtrl.SetValue(x))
	xoff = property(lambda self: self.xOffCtrl.GetValue(), lambda self, x: self.xOffCtrl.SetValue(x))
	yoff = property(lambda self: self.yOffCtrl.GetValue(), lambda self, x: self.yOffCtrl.SetValue(x))
	color = property(lambda self: self.colorCtrl.GetBackgroundColour(), lambda self, x: self.colorCtrl.SetBackgroundColour(x))
	lineWidth = property(lambda self: self.lineWidthCtrl.GetValue(), lambda self, x: self.lineWidthCtrl.SetValue(x))
	snap = property(lambda self: self.snapCtrl.GetValue(), lambda self, x: self.snapCtrl.SetValue(x))
	renderAbove = property(lambda self: self.aboveCtrl.GetValue(), lambda self, x: self.aboveCtrl.SetValue(x))
