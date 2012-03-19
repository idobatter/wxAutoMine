#!/usr/local/bin/python
# -*- coding: utf-8 -*-
'''BalloonTipDict
Copyright(C) 2012 idobatter, All Rights Reserved.
'''

import BalloonTip as BT
import wx

class BalloonTipDict(object):
  def __init__(self, iconbmp=None):
    '''must be called after wx.App created'''
    self.d = {}
    self.iconbmp = iconbmp
    self.setup()

  def add(self, key, sdelay, edelay, title, msg, shape, tipstyle,
    blncol=None, titlecol=None, msgcol=None,
    blnfont=None, titlefont=None, msgfont=None):
    bln = BT.BalloonTip(topicon=None,
      toptitle=title, message=msg, shape=shape, tipstyle=tipstyle)
    if blncol: bln.SetBalloonColour(blncol)
    if blnfont: bln.SetBalloonFont(blnfont)
    if titlecol: bln.SetTitleColour(titlecol)
    if titlefont: bln.SetTitleFont(titlefont)
    if msgcol: bln.SetMessageColour(msgcol)
    if msgfont: bln.SetMessageFont(msgfont)
    bln.SetStartDelay(sdelay)
    bln.SetEndDelay(edelay)
    self.d[key] = bln

  def get(self, frm, key, iconbmp=None):
    bln = self.d[key]
    bln.SetTarget(getattr(frm, key))
    bln.SetBalloonIcon(iconbmp if iconbmp else self.iconbmp)
    return bln

  def setup(self):
    self.add('clock', 200, 10000, u'動作速度について',
      u'''設定は一旦 Pause ボタンを押してから Resume すると有効になります。''',
      BT.BT_ROUNDED, BT.BT_LEAVE)

    self.add('timestrunc', 200, 60000, u'行動遷移について',
      u'''開ける場所もマークする場所も見つからないとき
推論を打ち切り次に行動を起こすまでの時間(動作速度 clock × 回数)を設定します。

「適当に開く」(タイムトライアル)モードを選択したときは
ここを最小値「2」にした方が良いかも知れません。
さらに失敗時の自動リトライを「序盤」「序盤以外」両方を選択すると良いでしょう。

「助言を待つ」(人間がクリックを手伝う)モードを選択したときは
ここを最大値「200」にして Pause される前に盤面をクリックする時間を稼げます。
さらに失敗時の自動リトライは「序盤」のみを選択すると良いでしょう。''',
      BT.BT_ROUNDED, BT.BT_LEAVE,
      wx.Colour(192, 240, 192), wx.Colour(64, 128, 64), wx.Colour(32, 64, 32))

    self.add('stmisscont', 200, 60000, u'自動リトライについて',
      u'''序盤や終盤はどうしても運任せの部分があります。

「適当に開く」(タイムトライアル)モードを選択したときは
行動遷移までの時間を最小値「2」に設定し
失敗時の自動リトライを「序盤」「序盤以外」両方を選択すると良いでしょう。''',
      BT.BT_ROUNDED, BT.BT_LEAVE,
      wx.Colour(192, 240, 240), wx.Colour(64, 128, 128), wx.Colour(32, 64, 64))

if __name__ == '__main__':
  pass # no test code
