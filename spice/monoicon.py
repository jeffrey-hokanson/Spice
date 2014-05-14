# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
import wx
class MonoIcon:
    """ Single colored icons.
        
        To use, 
        mi = MonoIcon(16, 16)
        widget = wx.<SOME WX WIDGET>
        widget.SetImageList(mi.GetImageList())

        Then when you add an icon execute
        setItemImage(widget, mi[25,16,23])

        WARNING: Python will deallocate memory for the structure unless you 
        keep it as a variable inside where-ever it is called, e.g., 
        self.mi = MonoIcon(16,16)
    """
    def __init__(self, sizex = 16, sizey = 16):
        self.sizex = sizex
        self.sizey = sizey
        self.il = wx.ImageList(sizex, sizey)
        self.keys = {}
    def __len__(self):
        return self.il.GetImageCount()

    def __getitem__(self, key):
        """ Provide a three color tuple (RGB) (0-255), returns an icon list 
        """
        if not len(key) == 3:
            raise ValueError
        for j in range(3):
            if not type(key[j]) is int:
                raise ValueError("Argument {} expected to be an int".format(j))
            if not ( 0 <= key[j] < 256 ):
                raise ValueError("Expect value of argument {} between 0 and 255 inclusive".format(j))

        if not key in self.keys:
            # Build icon
            img = wx.EmptyImage(1,1)
            img.SetRGB(0,0,key[0],key[1],key[2])
            img = wx.BitmapFromImage(img.Rescale(self.sizex,self.sizey))
            idx = self.il.Add(img)
            self.keys[key] = idx

        return self.keys[key]

    def GetImageList(self):
        return self.il 
