# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

import wx
import wx.gizmos as gizmos
from monoicon import MonoIcon
        
        
class Frame(wx.Frame):
    def __init__(self, *args, **kwargs):
        wx.Frame.__init__(self, *args, **kwargs)
        self.tree = gizmos.TreeListCtrl(self, -1, style = wx.TR_DEFAULT_STYLE|wx.TR_FULL_ROW_HIGHLIGHT|
                wx.TR_HIDE_ROOT)
        
        self.mi = mi = MonoIcon(16,16)
        self.tree.SetImageList(mi.GetImageList())
        mi[128,128,128]
        print len(mi)
        self.tree.AddColumn("Empty Column")
        self.root = self.tree.AddRoot("Hello world")
        child = self.tree.AppendItem(self.root, "Grey Icon")
        self.tree.SetItemImage(child, mi[128,128,128])
        
        child = self.tree.AppendItem(self.root, "Another color")
        self.tree.SetItemImage(child, mi[255,0,0])
	

class App(wx.App):
    def OnInit(self):
        self.frame = Frame(parent=None, title="Tree View", size=(640,480)) 
	self.frame.Show()
	return True

def main():
    global _app
    _app = App()
    _app.MainLoop()


if __name__ == "__main__":
    main()

