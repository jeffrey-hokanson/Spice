#!/usr/bin/env python
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

""" A one dimensional viewer 
"""

import wx
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


class OneFrame(wx.Frame):

    def __init__(self, *args, **kwargs):
        wx.Frame.__init__(self, *args, **kwargs)
        
        # Storage of data
        self._flowdata = []
        
        # Default Variables
        self._channel = 0
        self._index = 0


        


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

        ######################################################################## 
        # Finalize setup
        ######################################################################## 
        
        self.SetSizer(sizer)


class OneControl():
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
        print combo_xtransform.GetBestSize()
        combo_xtransform.SetSize(combo_xtransform.GetBestSize())
        sizer_xtransform.Add(combo_xtransform, 0, wx.ALL|wx.ALIGN_CENTER)

        pane.SetSizer(sizer_xtransform)
        

class OnePlot(wx.Panel):
    """ A panel for one dimensional plotting
    """
    def __init__(self, *args, **kwargs):
        wx.Panel.__init__(self, *args, **kwargs)


        # Get the background colour
        bg_color = self.GetBackgroundColour()
        # wxPython uses (0,255) RGB colors, matplotlib (0,1) RGB colors
        bg_color = [bg_color[0]/255. ,  bg_color[1]/255., bg_color[2]/255.]
        self.figure = Figure(facecolor = bg_color)

        self.ax = self.figure.add_subplot(111)
        self.canvas = FigureCanvas(self, -1, self.figure)
        
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.canvas, 1, wx.LEFT | wx.TOP | wx.GROW)
        self.SetSizer(self.sizer)
        self.Fit()

        # TODO: Temp. testing code
        t = np.linspace(0, 1, 100)
        x = np.sin(10*t)
        self.ax.plot(t, x)

class App(wx.App):
    """ Stand alone version of the one dimensional view
    """
    def OnInit(self):
        self.frame = OneFrame(parent=None, title="Histogram", size=(640,480)) 

        # Read in files from command line
        if len(sys.argv) != 1:
            for arg in sys.argv[1:]:
                print arg
                filename = os.path.join(os.getcwd(),arg)
                if os.path.isfile(filename):
                    self.frame.load_file(filename)


        self.frame.Show()
        return True


def main():
    global _app
    _app = App()
    _app.MainLoop()


if __name__ == "__main__":
    main()
