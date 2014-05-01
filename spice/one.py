#!/usr/bin/env python
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

""" A one dimensional viewer 
"""

import os
import sys

import wx
import wx.gizmos as gizmos
from wx.lib.pubsub import pub
from wx.lib.agw.floatspin import FloatSpin as FloatSpin


import numpy as np
import matplotlib
matplotlib.interactive(True)
matplotlib.use('WXAgg')
import matplotlib.scale
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.backends.backend_wxagg import NavigationToolbar2Wx
from matplotlib.figure import Figure


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
        #self.Bind(wx.EVT_CHAR_HOOK, self.on_key)
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
        # TODO: This will need to call the saved variables
        # and update with current values

        self.figure.plot()
        self.control.channel = channel

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
        elif event.GetKeyCode() == wx.WXK_RIGHT:
            self.plus_channel()

        else:
            event.Skip()


# NB: We inherit from object so that getters/setters will work properly
class OneControl(object):
    """ A panel containing widgets for controlling the appearance of OnePlot
    """
    def __init__(self, pane, figure):
        self.pane = pane
        self.figure = figure
        self._channel = 0

        gbs = wx.GridBagSizer(5, 5)
        
        # Poll avalible scales from matplotlib
        self.scales = scales = matplotlib.scale.get_scale_names()
        self.kernels = kernels = FlowData().kernel_1D_list
        print kernels
        ########################################################################
        # X/Y Control Title Column
        ########################################################################
        text_scale = wx.StaticText(pane, -1, "Scale")
        text_scale_param = wx.StaticText(pane, -1, "Cofactor")
        text_min = wx.StaticText(pane, -1, "Min")
        text_max = wx.StaticText(pane, -1, "Max")

        flag = wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL
        gbs.Add(text_scale, (1,0), flag = flag)
        gbs.Add(text_scale_param, (2,0), flag = flag)
        gbs.Add(text_min, (3,0), flag = flag)
        gbs.Add(text_max, (4,0), flag = flag)

        ########################################################################
        # X Control Column
        ########################################################################
        text_x = wx.StaticText(pane, -1, "X Configuration")
        
        combo_xscale_ID = wx.NewId()
        combo_xscale = wx.ComboBox(pane, combo_xscale_ID, style = wx.CB_DROPDOWN | wx.CB_READONLY)
        combo_xscale.AppendItems(scales)
        combo_xscale.SetSize(combo_xscale.GetBestSize())

        spin_xcofactor_ID = wx.NewId()
        spin_xcofactor = FloatSpin(pane,spin_xcofactor_ID, value = 5, min_val = None, max_val = None) 
        spin_xcofactor.SetFormat("%g")
        spin_xmin_ID = wx.NewId()
        spin_xmin = FloatSpin(pane,spin_xmin_ID, value = -1, min_val = None, max_val = None) 
        spin_xmin.SetFormat("%g")
        spin_xmax_ID = wx.NewId()
        spin_xmax = FloatSpin(pane,spin_xmax_ID, value = 100, min_val = None, max_val = None) 
        spin_xmax.SetFormat("%g")

        flag = wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL
        gbs.Add(text_x, (0,1))
        gbs.Add(combo_xscale, (1,1), flag = flag)
        gbs.Add(spin_xcofactor, (2,1), flag = flag)
        gbs.Add(spin_xmin, (3,1), flag = flag)
        gbs.Add(spin_xmax, (4,1), flag = flag)

        self.combo_xscale = combo_xscale
        self.spin_xcofactor = spin_xcofactor
        self.spin_xmin = spin_xmin
        self.spin_xmax = spin_xmax
        ########################################################################
        # Y Control Column
        ########################################################################
        text_y = wx.StaticText(pane, -1, "Y Configuration")
        
        combo_yscale_ID = wx.NewId()
        combo_yscale = wx.ComboBox(pane, combo_yscale_ID, style = wx.CB_DROPDOWN | wx.CB_READONLY)
        combo_yscale.AppendItems(scales)
        combo_yscale.SetSize(combo_yscale.GetBestSize())
        self.combo_yscale = combo_yscale

        spin_ycofactor_ID = wx.NewId()
        spin_ycofactor = FloatSpin(pane,spin_ycofactor_ID, value = 5, min_val = None, max_val = None) 
        spin_ycofactor.SetFormat("%g")
        
        spin_ymin_ID = wx.NewId()
        spin_ymin = FloatSpin(pane,spin_ymin_ID, value = -1, min_val = None, max_val = None) 
        spin_ymin.SetFormat("%g")

        spin_ymax_ID = wx.NewId()
        spin_ymax = FloatSpin(pane,spin_ymax_ID, value = 100, min_val = None, max_val = None) 
        spin_ymax.SetFormat("%g")

        flag = wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL
        gbs.Add(text_y, (0,2))
        gbs.Add(combo_yscale, (1,2), flag = flag)
        gbs.Add(spin_ycofactor, (2,2), flag = flag)
        gbs.Add(spin_ymin, (3,2), flag = flag)
        gbs.Add(spin_ymax, (4,2), flag = flag)
        
        self.combo_yscale = combo_yscale
        self.spin_ycofactor = spin_ycofactor
        self.spin_ymin = spin_ymin
        self.spin_ymax = spin_ymax
        ########################################################################
        # Titles for Histogram/KDE Control
        ########################################################################
        text_kernel = wx.StaticText(pane, -1, "Kernel")
        text_width_mode = wx.StaticText(pane, -1, "Method")
        text_width = wx.StaticText(pane, -1, "Bandwidth")
        text_kde = wx.StaticText(pane, -1, "Kernel Configuration")

        gbs.Add(text_kde, (0,3), (1,2), flag = wx.ALIGN_CENTER)
        flag = wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL
        gbs.Add(text_kernel, (1,3), flag = flag)
        gbs.Add(text_width_mode, (2,3), flag = flag)
        gbs.Add(text_width, (3,3), flag = flag)

        ########################################################################
        # Histogram/KDE Control
        ########################################################################
        combo_kernel_ID = wx.NewId()
        combo_kernel = wx.ComboBox(pane, combo_kernel_ID, style = wx.CB_DROPDOWN | wx.CB_READONLY)
        combo_kernel.AppendItems(kernels)
        combo_kernel.SetSize(combo_kernel.GetBestSize())

        combo_width_ID = wx.NewId()
        combo_width = wx.ComboBox(pane, combo_width_ID, style = wx.CB_DROPDOWN | wx.CB_READONLY)
        # TODO: generalize these techniques, pull in external libraries
        combo_width.AppendItems(['manual', 'cross-validation', 'plugin'])

        spin_width_ID = wx.NewId()
        spin_width = FloatSpin(pane, spin_width_ID, value = 0.1, min_val = None, max_val = None) 
        spin_width.SetFormat('%g') 
        gbs.Add(combo_kernel, (1,4))
        gbs.Add(combo_width, (2,4))
        gbs.Add(spin_width, (3,4))

        self.spin_width = spin_width

        ########################################################################
        # Bind Events
        ########################################################################
        pane.Bind(wx.EVT_COMBOBOX, self.on_xscale, id = combo_xscale_ID)
        pane.Bind(wx.EVT_COMBOBOX, self.on_yscale, id = combo_yscale_ID)
        
        spin = []
        spin.append( (self.on_spin_xmin, spin_xmin) )
        spin.append( (self.on_spin_xmax, spin_xmax) )
        spin.append( (self.on_spin_ymin, spin_ymin) )
        spin.append( (self.on_spin_ymax, spin_ymax) )
        spin.append( (self.on_spin_width, spin_width) )
        for fn, ID in spin:
            pane.Bind(wx.EVT_SPINCTRL, fn, ID)
            pane.Bind(wx.EVT_TEXT, fn, ID)
        # Intialize
        pane.SetSizer(gbs)
        self.set_default()

    def set_default(self):
        self.xscale = 'linear'
        self.yscale = 'linear'

    @property
    def xscale(self):
        k = self.combo_xscale.GetSelection()
        return self.scales[k]

    @xscale.setter
    def xscale(self, value):
        """ Sets the xscale of the plot, takes a string input
        """
        try:
            k = self.scales.index(value)
        except:
            ValueError("{} is not a valid scale type".format(value))
        self.combo_xscale.SetSelection(k)
        self.figure.ax.set_xscale(value)
    
    @property
    def yscale(self):
        k = self.combo_yscale.GetSelection()
        return self.scales[k]
    
    @yscale.setter
    def yscale(self, value):
        """ Sets the xscale of the plot, takes a string input
        """
        try:
            k = self.scales.index(value)
        except:
            ValueError("{} is not a valid scale type".format(value))
        self.combo_yscale.SetSelection(k)
        self.figure.ax.set_yscale(value)

    @property
    def xmin(self):
        return self.spin_xmin.GetValue()

    @xmin.setter
    def xmin(self, value):
        self.spin_xmin.SetValue(value)
        self.figure.ax.set_xlim(left = value)
    
    @property
    def xmax(self):
        return self.spin_xmax.GetValue()

    @xmax.setter
    def xmax(self, value):
        self.spin_xmax.SetValue(value)
        self.figure.ax.set_xlim(right = value)
    
    @property
    def ymin(self):
        return self.spin_ymin.GetValue()

    @ymin.setter
    def ymin(self, value):
        self.spin_ymin.SetValue(value)
        self.figure.ax.set_ylim(bottom = value)

    @property
    def ymax(self):
        return self.spin_ymax.GetValue()

    @ymax.setter
    def ymax(self, value):
        self.spin_ymax.SetValue(value)
        self.figure.ax.set_ylim(top = value)
     
    @property
    def channel(self):
        return self._channel

    @channel.setter
    def channel(self, value = None):
        self._channel = value
        self.defaults()
        self.figure.draw()

    def defaults(self):
        """ Grab current range of plot"""
        self.xmin = self.figure.xmin
        self.xmax = self.figure.xmax
        self.ymin = self.figure.ymin
        self.ymax = self.figure.ymax
        self.xscale = self.xscale
        self.yscale = self.yscale

    @property
    def bandwidth(self):
        return self.spin_width.GetValue()
    
    @bandwidth.setter
    def bandwidth(self, value):
        self.spin_width.SetValue(value)
        self.figure.plot(bandwidth = value)

    def save(self):
        raise NotImplementedError
    
    def load(self):
        raise NotImplementedError
    
    def on_xscale(self, event = None):
        self.xscale = self.xscale
        self.figure.draw()
    
    def on_yscale(self, event = None):
        self.yscale = self.yscale
        self.figure.draw()

    def on_spin_xmin(self, event = None):
        self.xmin = self.xmin
        self.figure.draw()

    def on_spin_xmax(self, event = None):
        self.xmax = self.xmax
        self.figure.draw()

    def on_spin_ymin(self, event = None):
        self.ymin = self.ymin
        self.figure.draw()

    def on_spin_ymax(self, event = None):
        self.ymax = self.ymax
        self.figure.draw()

    def on_spin_width(self, event = None):
        self.bandwidth = self.bandwidth
        self.defaults()
        self.figure.draw()

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
    
    def plot(self, **kwargs):
        sample = self.parent.sample
        channel = self.parent.channel
        fa = self.parent.fa
        self.ax.cla()
        # TODO: import more control properties here
        self.xmax = -float('inf')
        self.xmin = float('inf')
        self.ymin = float('inf')
        self.ymax = -float('inf')

        for j in sample:
            (xgrid, den) = fa[j].kde1(channel, **kwargs)
            self.ax.plot(xgrid,den)
            self.xmin = min(self.xmin, np.amin(xgrid))
            self.xmax = max(self.xmax, np.amax(xgrid))
            self.ymin = min(self.ymin, np.amin(den))
            self.ymax = max(self.ymax, np.amax(den))
        
        self.figure.tight_layout(pad=2)
        self.canvas.draw()

    def draw(self):
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
