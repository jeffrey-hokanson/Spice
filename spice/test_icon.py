import wx
import wx.gizmos as gizmos

class Frame(wx.Frame):
	def __init__(self, *args, **kwargs):
		wx.Frame.__init__(self, *args, **kwargs)
        	self.tree = gizmos.TreeListCtrl(self, -1, style = wx.TR_DEFAULT_STYLE|wx.TR_FULL_ROW_HIGHLIGHT|
                	wx.TR_HIDE_ROOT)
		
        	isz = (16,16)
		img = wx.EmptyImage(1,1)
		img.SetRGB(0,0,128,128,128)
		img = img.Rescale(10,10)
        	self.img = wx.BitmapFromImage(img.Rescale(isz[0],isz[1]))
		
		self.il = il = wx.ImageList(isz[0], isz[1])
		self.idx = il.Add(self.img)
		self.tree.SetImageList(il)

        	self.tree.AddColumn("Empty Column")
		self.root = self.tree.AddRoot("Hello world")
		child = self.tree.AppendItem(self.root, "Grey Icon")
		self.tree.SetItemImage(child, self.idx)

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

