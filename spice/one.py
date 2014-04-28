#!/usr/bin/env python
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

""" A one dimensional viewer 
"""

import wx
import wx.gizmos as gizmos
import os
import sys

from wx.lib.pubsub import pub

import numpy as np
import matplotlib
matplotlib.interactive(True)
matplotlib.use('WXAgg')
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.backends.backend_wxagg import NavigationToolbar2Wx
from matplotlib.figure import Figure
import wx.lib.agw.foldpanelbar as fpb

from flowdata import FlowData as FlowData
from flowdata import FlowAnalysis as FlowAnalysis

class OneFrame(wx.Frame):

    def __init__(self, *args, **kwargs):
        wx.Frame.__init__(self, *args, **kwargs)
        
        # Storage of data
        self.fa = FlowAnalysis()
        
        # Default Variables: these are not to be written to,
        # as the memory is shared throughout the program
        self._channel = 0
        self._sample = [0]

        ######################################################################## 
        # Create the toolbar on the main window
        ######################################################################## 

        # Create wxIDs
        tb_back_ID = wx.NewId()
        tb_forward_ID = wx.NewId()
        tb_tag_list_ID = wx.NewId()
        tb_save_ID = wx.NewId()
        tb_export_ID = wx.NewId()
        tb_load_ID = wx.NewId()

        # Toolbar
        self.toolbar = self.CreateToolBar(wx.TB_HORIZONTAL | wx.NO_BORDER | wx.TB_FLAT)
        tb_size = (24,24)
        self.toolbar.SetToolBitmapSize(tb_size)
        tb_back =  wx.ArtProvider.GetBitmap(wx.ART_GO_BACK, wx.ART_TOOLBAR, tb_size)
        tb_forward =  wx.ArtProvider.GetBitmap(wx.ART_GO_FORWARD, wx.ART_TOOLBAR, tb_size)
        tb_save = wx.ArtProvider.GetBitmap(wx.ART_FILE_SAVE, wx.ART_TOOLBAR, tb_size)
        tb_load = wx.ArtProvider.GetBitmap(wx.ART_FILE_OPEN, wx.ART_TOOLBAR, tb_size)

        # List of Tags
        self.tag_list = wx.ComboBox(self.toolbar, tb_tag_list_ID, size = (300,-1), style = wx.CB_DROPDOWN | wx.CB_READONLY)

        self.toolbar.AddLabelTool(tb_load_ID, "Load", tb_load, shortHelp = "Load FCS", longHelp = "")
        self.toolbar.AddLabelTool(tb_save_ID, "Export Plot", tb_save, shortHelp = "Export Plot to PNG, JPG, etc", longHelp = "")
        self.toolbar.AddStretchableSpace()
        self.toolbar.AddControl(self.tag_list)
        self.toolbar.AddStretchableSpace()
        self.toolbar.AddLabelTool(tb_back_ID, "Back", tb_back, shortHelp = "Go Back One Tag")
        self.toolbar.AddLabelTool(tb_forward_ID, "Forward", tb_forward, shortHelp = "Go Forward One Tag")

        self.toolbar.Realize()
        
        ######################################################################## 
        # Create Status Bar
        ######################################################################## 
        self.statusbar = self.CreateStatusBar()

        ######################################################################## 
        # Generate the Plot window
        ######################################################################## 
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.figure = OnePlot(self)
        sizer.Add(self.figure, 5, wx.EXPAND)

        ######################################################################## 
        # Controls
        ######################################################################## 
       
        self.cp = cp = wx.CollapsiblePane(self, label="Plotting Controls", style=wx.CP_DEFAULT_STYLE)

        # Test code
        self.control = OneControl(cp.GetPane(), self.figure)

        sizer.Add(self.cp, 0, wx.EXPAND)

        self.cp2 = cp2 = wx.CollapsiblePane(self, label="Gating Tree", style=wx.CP_DEFAULT_STYLE)
        
        self.tree = TreeData(cp2.GetPane(), self)

        sizer.Add(self.cp2, 0, wx.EXPAND)
        ######################################################################## 
        # Bind Events
        ######################################################################## 

        self.Bind(wx.EVT_TOOL, self.load_dialog, id = tb_load_ID) 
        self.Bind(wx.EVT_TOOL, self.plus_channel, id = tb_forward_ID)
        self.Bind(wx.EVT_TOOL, self.minus_channel, id = tb_back_ID)
        self.Bind(wx.EVT_COMBOBOX, self.on_tag_list, id = tb_tag_list_ID)
        self.Bind(wx.EVT_CHAR_HOOK, self.on_key)
        ######################################################################## 
        # Finalize setup
        ######################################################################## 
        
        self.SetSizer(sizer)

    def load(self, filename):
        self.fa.load(filename)
        self.tree.update()
        self.index = len(self.fa)-1
        self.update_tag_list()

    def load_dialog(self, event):
        dlg = wx.FileDialog(self, "Choose an FCS file", os.getcwd(), "", "*.fcs", wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            self.load(path) 
        dlg.Destroy()
        
    @property
    def channel(self):
        return self._channel
    @property
    def sample(self):
        return self._sample


    def plus_channel(self, event = None):
        self._channel = (self._channel + 1) % self.fa[self.sample[0]].nparameters
        self.set_channel()
    
    def minus_channel(self, event = None):
        self._channel = (self._channel - 1) % self.fa[self.sample[0]].nparameters
        self.set_channel()

    def set_channel(self, channel = None):
        if channel is None:
            channel = self._channel
        self._channel = channel
        
        self.tag_list.SetSelection(self.channel)
        self.figure.plot()

    def update_tag_list(self):
        self.tag_list.Clear()
        fd = self.fa[self.sample[0]]
        tags = fd.tags
        markers = fd.markers

        labels = []
        for j in range(fd.nparameters):
            labels.append(tags[j] + ' :: ' + markers[j])

        self.tag_list.AppendItems(labels)
        self.tag_list.SetSelection(0)

    def on_tag_list(self, event):
        self.set_channel(self.tag_list.GetSelection())

    def on_key(self, event):
        if event.GetKeyCode() == wx.WXK_LEFT:
            self.minus_channel()
        if event.GetKeyCode() == wx.WXK_RIGHT:
            self.plus_channel()

class OneControl:
    """ A panel containing widgets for controlling the appearance of OnePlot
    """
    def __init__(self, pane, figure):
        self.pane = pane
        self.figure = figure
        sizer_xtransform = wx.BoxSizer(wx.HORIZONTAL)
        
        text_xtransform = wx.StaticText(pane, -1, "X Transform")
        text_xtransform.SetSize(text_xtransform.GetBestSize())
        sizer_xtransform.Add(text_xtransform, 0, wx.ALL|wx.ALIGN_CENTER)

        combo_xtransform_ID = wx.NewId()

        combo_xtransform = wx.ComboBox(pane, combo_xtransform_ID, style = wx.CB_DROPDOWN | wx.CB_READONLY)
        combo_xtransform.AppendItems(['Linear', 'Log', 'Biexponential', 'Arcsinh'])
        combo_xtransform.SetSize(combo_xtransform.GetBestSize())
        sizer_xtransform.Add(combo_xtransform, 0, wx.ALL|wx.ALIGN_CENTER)

        pane.SetSizer(sizer_xtransform)
       

class TreeData():
    """ A tree for showing gates/masks and multiple file sets
    """
    def __init__(self, pane, parent):
        self.pane = pane
        self.parent = parent
        self.fa = parent.fa
        pane.SetDoubleBuffered(True)
        sizer = wx.BoxSizer(wx.VERTICAL)

        self.tree = gizmos.TreeListCtrl(pane, -1, style = wx.TR_DEFAULT_STYLE|wx.TR_FULL_ROW_HIGHLIGHT|
                        wx.TR_HIDE_ROOT)
        
        self.tree.AddColumn("File name")
        self.tree.AddColumn("Site")
        self.tree.AddColumn("Time")
        
        self.root = self.tree.AddRoot("The Root Item")
        sizer.Add(self.tree, 1, wx.EXPAND)

        pane.SetSizer(sizer)


    def update(self):
        """ Update the list of loaded files"""
        self.tree.DeleteAllItems()
        self.root = self.tree.AddRoot("Invisible Root")
        self.children = []
        for fd in self.fa:
            child = self.tree.AppendItem(self.root, fd.filename)
            self.children.append(child)


class OnePlot(wx.Panel):
    """ A pane for one dimensional plotting.
        This class initilizes a set of controls that appear inside OneFrame
        and then 
    """
    def __init__(self, parent, *args, **kwargs):
        wx.Panel.__init__(self, parent, *args, **kwargs)

        # Setup default parameters
        self.parent = parent

        # Get the background colour
        bg_color = self.GetBackgroundColour()
        # wxPython uses (0,255) RGB colors, matplotlib (0,1) RGB colors
        bg_color = [bg_color[0]/255. ,  bg_color[1]/255., bg_color[2]/255.]
        self.figure = Figure(facecolor = bg_color)

        self.ax = self.figure.add_subplot(111)
        self.canvas = FigureCanvas(self, -1, self.figure)    
        self.Bind(wx.EVT_SIZE, self._size)


    def _size(self, event):
        self.canvas.SetSize(self.GetSize())
        self.figure.tight_layout(pad=2)
    
    def plot(self):
        sample = self.parent.sample
        channel = self.parent.channel
        fa = self.parent.fa
        self.ax.cla()
        # TODO: import more control properties here
        for j in sample:
            (xgrid, den) = fa[j].histogram(channel)
            self.ax.plot(xgrid,den)
        
        self.figure.tight_layout(pad=2)
        self.canvas.draw()


class App(wx.App):
    """ Stand alone version of the one dimensional view
    """
    def OnInit(self):
        self.frame = OneFrame(parent=None, title="Histogram", size=(640,480)) 

        # Read in files from command line
        if len(sys.argv) != 1:
            for arg in sys.argv[1:]:
                filename = os.path.join(os.getcwd(),arg)
                if os.path.isfile(filename):
                    self.frame.load(filename)


        self.frame.SetDoubleBuffered(True)
        self.frame.Show()
        return True


def main():
    global _app
    _app = App()
    _app.MainLoop()


if __name__ == "__main__":
    main()
