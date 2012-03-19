#!/usr/local/bin/python
# -*- coding: utf-8 -*-
'''cwm
Cruise apps using Window Messages
Copyright(C) 2012 idobatter, All Rights Reserved.
'''

import ctypes

class PostWinMsg(object):
  def __init__(self, hwnd, wait=0, fg=False):
    self.hwnd = hwnd
    self.wait = wait
    if fg: self.foreground()

  @classmethod
  def target(cls, wname, cname=None, chwnd=None, phwnd=None):
    return ctypes.windll.user32.FindWindowExW(
      phwnd if phwnd else 0, chwnd if chwnd else 0,
      ctypes.c_wchar_p(cname) if cname else 0,
      ctypes.c_wchar_p(wname) if wname else 0)

  def getclassname(self, l):
    buf = ctypes.c_wchar_p(u' ' * (l + 1))
    ctypes.windll.user32.GetClassNameW(self.hwnd, buf, l + 1)
    return buf.value

  def foreground(self):
    ctypes.windll.user32.SetForegroundWindow(self.hwnd)

  def topmost(self, flg=True):
    ctypes.windll.user32.SetWindowPos(self.hwnd,
      -1 if flg else -2, # HWND_TOPMOST or HWND_NOTOPMOST
      0, 0, 0, 0, 3) # SWP_NOSIZE | SWP_NOMOVE

  def sleep(self, ms):
    ctypes.windll.kernel32.Sleep(ms)

  def isalnum(self, c):
    return (0x30 <= c <= 0x39) or (0x41 <= c <= 0x5A) or (0x61 <= c <= 0x7A)

  def wm(self, msg, wp, lp):
    if self.wait: self.sleep(self.wait)
    ctypes.windll.user32.PostMessageW(self.hwnd, msg, wp, lp)

  def syskeyd(self, vk):
    self.wm(260, vk, 1 << 29) # WM_SYSKEYDOWN lparam = Alt down

  def syskeyu(self, vk):
    self.wm(261, vk, 6 << 29) # WM_SYSKEYUP lparam = Alt up

  def syskeydu(self, vk):
    self.wm(260, vk, 1 << 29) # WM_SYSKEYDOWN lparam + Alt
    if self.isalnum(vk): self.wm(262, vk, 7 << 29) # WM_SYSCHAR lparam + Alt
    self.wm(261, vk, 7 << 29) # WM_SYSKEYUP lparam + Alt

  def altkeys(self, s):
    self.syskeyd(18) # Alt down
    for c in s: self.syskeydu(ord(c))
    self.syskeyu(18) # Alt up

  def keydu(self, vk):
    self.wm(256, vk, 0) # WM_KEYDOWN
    if self.isalnum(vk): self.wm(258, vk, 0) # WM_CHAR
    self.wm(257, vk, 0) # WM_KEYUP

  def keys(self, s):
    for c in s: self.keydu(ord(c))

  def mouseclk(self, b, x, y, dbl=False):
    lp = x + y * 2 ** 16
    wp = 1 if b == 0 else 2 if b == 1 else 16
    o = 3 * b
    self.wm(513 + o, wp, lp) # WM_LBUTTONDOWN
    self.wm(514 + o, wp, lp) # WM_LBUTTONUP
    if dbl: self.wm(515 + o, wp, lp) # WM_LBUTTONDBLCLK

if __name__ == '__main__':
  target = PostWinMsg.target(u'無題 - メモ帳')
  pwm = PostWinMsg(target, wait=1000, fg=True)
  pwm.keys('xyz abc')
  pwm.altkeys('FS')
