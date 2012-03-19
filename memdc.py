#!/usr/local/bin/python
# -*- coding: utf-8 -*-
'''memdc
custom MemoryDC
Copyright(C) 2012 idobatter, All Rights Reserved.
'''

import ctypes
from wx.lib.colourchooser.canvas import BitmapBuffer
import wx

class MemDC(object):
  def __init__(self, dc, bg):
    self.ddc = dc
    self.bm = wx.EmptyBitmap(*dc.GetSize())
    self.dc = wx.MemoryDC(self.bm)
    self.bg = bg
    self.dc.SetBackground(wx.Brush(bg))
    self.dc.Clear()

  def flush(self, ddc=None):
    w, h = self.dc.GetSize()
    (ddc if ddc else self.ddc).Blit(0, 0, w, h, self.dc, 0, 0)

  def bm2bb(self, bm):
    w, h = bm.GetSize()
    bb = BitmapBuffer(w, h, self.bg)
    bb.DrawBitmap(bm, 0, 0, useMask=False)
    return bb

  def gclip(self, w, h, srcx, srcy, grey=True):
    '''returns buffer Greyscale (N bytes) or RGB (3 * N bytes)'''
    bb = BitmapBuffer(w, h, self.bg)
    bb.Blit(0, 0, w, h, self.dc, srcx, srcy)
    im = bb.GetBitmap().ConvertToImage()
    buf = (im.ConvertToGreyscale() if grey else im).GetData()
    return ''.join(buf[i * 3] for i in xrange(len(buf) / 3)) if grey else buf

  def gblit(self, dstx, dsty, w, h, src, srcx, srcy, grey=True):
    '''convert to Greyscale and Blit'''
    bm = src if isinstance(src, wx.Bitmap) else src.GetBitmap()
    if grey: bm = bm.ConvertToImage().ConvertToGreyscale().ConvertToBitmap()
    else: bm = bm.ConvertToImage().ConvertToBitmap() # Don't delete this line
    if w is None or h is None: w, h = bm.GetSize()
    bdc = wx.BufferedDC(self.dc, wx.NullBitmap, wx.BUFFER_CLIENT_AREA)
    bdc.Blit(dstx, dsty, w, h, self.bm2bb(bm), srcx, srcy)

  def gcapture(self, dstx, dsty, w, h, shwnd, srcx, srcy, grey=True):
    hdc = ctypes.windll.user32.GetDC(shwnd)
    # cdc = ctypes.windll.gdi32.CreateCompatibleDC(hdc)
    # cbmp = ctypes.windll.gdi32.CreateCompatibleBitmap(hdc, w, h)
    # ctypes.windll.gdi32.SelectObject(cdc, cbmp)
    bb = BitmapBuffer(w, h, self.bg)
    ctypes.windll.gdi32.BitBlt(bb.GetHDC(), dstx, dsty, w, h,
      hdc, srcx, srcy, 0xCC0020) # SRCCOPY
    # bb.GetBitmap().SaveFile(u'test.png', wx.BITMAP_TYPE_PNG)
    self.gblit(dstx, dsty, w, h, bb, srcx, srcy, grey)
    # ctypes.windll.gdi32.DeleteObject(cbmp)
    # ctypes.windll.gdi32.DeleteObject(cdc)
    ctypes.windll.user32.ReleaseDC(shwnd, hdc)

if __name__ == '__main__':
  app = wx.App(False) # Don't delete this line
  mdc = MemDC(wx.ScreenDC(), wx.Colour(0, 0, 0)) # root window: ScreenDC
  mdc.gcapture(0, 0, 320, 240, 0, 0, 0, grey=False) # root window: shwnd=0
  mdc.bm.SaveFile(u'colour.png', wx.BITMAP_TYPE_PNG)
  mdc.gblit(0, 0, 320, 240, mdc.bm, 0, 0, grey=True)
  mdc.bm.SaveFile(u'grey.png', wx.BITMAP_TYPE_PNG)
