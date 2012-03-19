#!/usr/local/bin/python
# -*- coding: utf-8 -*-
'''wxAutoMine
Copyright(C) 2012 idobatter, All Rights Reserved.
SoftwareDesign 2012-03 記事が動機 (Win7 / Python 2.5 / wxPython 2.8 で動作確認)
敢えて pywinauto SendKeys PIL 等は使用せず標準機能 (ctypes) と wx のみで動作
キー送信(F2:開始)とマウスクリック(左右中央)と画面キャプチャから各セル種の判定

※改善予定場所とバグ
OS (というか機種依存) の色設定によっては正常に動作しない場合がある
 -> TrueColor 32bit なら正常動作 / HighColor 16bit だと誤動作
 -> capture 画像の色が参照画像 (wxAutoMine.png) と一致しないため
 -> CHKBMP の再出力で改善するが完全一致でないと誤動作 (白黒 2 値化してみる？)
真の推論モード(未開場所の共有数に基く仮定と矛盾の利用)は今のところ無し
 -> 最初の数箇所は適当に開く
 -> 数字と Box 数(未開) が一致しているとき右クリックで Box に旗を立てる
 -> 別 Cell に移動して旗の数が数字と一致していたら残りの Box (未開) を全て開く
 -> 繰り返し(ただしこのやり方だと推論が無いので終了しないケースが多い)
 -> 数字と開封状態のパターン辞書を用意して擬似推論(公理定理系を構築)すると速い
  -> 11- 12? 122 121 129 229 131 14- 等 (1221 など 2Cell に跨る物は未対応)
 -> 終盤は左上に出てくる残り爆弾数も推論に利用可能(未対応)
 -> それでも判別不能のケースがあるので無限ループにしない判定が必要
  -> 知識不足/煮詰まったとき [じっくり考える 助言を待つ 適当に開く]
今のところレベルは上級者または上級者と同サイズで爆弾数増減のケースのみ対応
上級者サイズ以外の場合のサイズ判定をしたい
Alt-G-E を送信して上級者を強制選択しているが lparam が中途半端？で稀に誤動作
Windows XP だと HWND_TOPMOST が必須？ Graphic Accelerator の問題？
target を HWND_TOPMOST にしている間は BalloonTip が一回しか表示されない
TARGETWCLASS が日本語版にしか対応していない (というか何故クラス名が日本語)
target (winmine.exe) を立ち上げる機能があると便利
思考モードで旗を立てるとき既に立っている場所を右クリックすると ? になるので注意

※最高記録
いまのところ上級者モードで 54 秒が最高 (SoftwareDesign の画像だと 37 秒)
wxAutoMine.py 2 つ同時起動だと 33 秒記録達成出来た !!!
 -> 片方は動作速度をずらす / 最初に開く数を減らす / 序盤以外はリトライしない
もっと高速化する場合
 -> multi thread にすると速くなりそう
 -> INTERVAL を 50ms 以下にする (逆に reentry block に掛かって遅くなる場合あり)
  -> あるいは EVT_PAINT は無視してクリックに徹する (wxPython 使わない)
 -> updatepaint の描画中表示そのものを無くす (ほとんど変わらないかも)
  -> memdc.py 中の BitBlt / gblit を最適化 (効率良くなれば高速化可能)
  -> Grayscale (ConvertoToGreyscale) しない方が良いかもしれない (byte 3 倍注意)
  -> capture 後全体を updatemap しているが gray 化を未開地だけに絞れば速くなる
 -> 辞書を増やす (特に開ける場所が多く判明する pattern を増やす)
 -> 「真の推論」と「辞書方式」のどちらが速いか検証必要
'''

from cwm import PostWinMsg
from memdc import MemDC
import AutoMineDict as AMD
import BalloonTipDict as BTD
import wx
import main_icon

APPTITLE = u'wxAutoMine'
TARGETWCLASS = u'マインスイーパ'
INTERVAL = 30 # msec
CLPW, CLPH = 8, 4
ADJW, ADJH = 7, 8
OFFSETW, OFFSETH = 20, 64
CELLW, CELLH = 16, 16
LEVELHW, LEVELHH = 30, 16 # 今のところ上級者サイズ固定(爆弾数は増減可能)
PANELHW, PANELHH = (OFFSETW + CELLW * LEVELHW), (OFFSETH + CELLH * LEVELHH)
GENERATE_CHKBMP = None
# GENERATE_CHKBMP = u'chkbmp.txt' # to generate CHKBMP strings
CHKBMP = [
  'ffffffffffffffffffc0c0c0c0c0c0c0ffc0c0c0c0c0c0c0ffc0c0c0c0c0c0c0', # f box
  'c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0', # 0 none
  'c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c01dc0c0c0c0c0c01d1d', # 1
  'c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c04b4b4b4b4bc0c04b4b4b4b4b4b', # 2
  'c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c04c4c4c4c4c4cc0c04c4c4c4c4c4c', # 3
  'c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c00f0f0fc0c0c0c0c00f0f0fc0', # 4
  'c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0262626262626c0c0262626262626', # 5
  'c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c05a5a5a5a5ac0c05a5a5a5a5a5a', # 6
  'c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0000000000000c0c0000000000000', # 7
  'c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c08080808080c0c0808080808080', # 8
  'ffffffffffffffffffc0c0c0c0c0c0c0ffc0c0c0c0c04c4cffc0c0c04c4c4c4c', # 9 flag
  'c0c0c0c0c0c0c0c0c0c0c0c0c0c0c000c0c0c0c0c0c0c000c0c0c000c0000000', # a bomb
  '4c4c4c4c4c4c4c4c4c4c4c4c4c4c4c004c4c4c4c4c4c4c004c4c4c004c000000', # b crash
  'ffffffffffffffffffc0c0c0c0c0c0c0ffc0c0c0c0000000ffc0c0c00000c0c0', # c '?'
  'e2e2e2e2e2e2e2e2e2e2e2e2e2e2e2e20000000000000000000000e200000000', # d good
  'e2e2e2e2e2e2e2e2e200e2e2e200e20000e2e2e2e2e200e2e200e2e2e200e200'] # e miss

class MyFrame(wx.Frame):
  def __init__(self, *args, **kwargs):
    super(MyFrame, self).__init__(title=APPTITLE,
      size=(800, 600), pos=(520, 240), *args, **kwargs)
    self.SetIcon(main_icon.getIcon()) # img2py -i main_icon.ico main_icon.py
    hsz = wx.BoxSizer(wx.HORIZONTAL)
    vpnl = wx.Panel(self, -1)
    vpnl.SetBackgroundColour(wx.Colour(240, 192, 32))
    vsz00 = wx.BoxSizer(wx.VERTICAL)
    self.clock = wx.StaticText(vpnl, -1, u'動作速度 clock %dms' % INTERVAL)
    vsz00.Add(self.clock, 0, wx.EXPAND)
    self.clockslider = wx.Slider(vpnl, wx.NewId(), INTERVAL, 1, 500)
    vsz00.Add(self.clockslider, 0, wx.EXPAND)
    self.timesfirst = wx.StaticText(vpnl, -1, u'最初に開く場所 7ヶ所')
    vsz00.Add(self.timesfirst, 0, wx.EXPAND)
    self.timesfirstslider = wx.Slider(vpnl, wx.NewId(), 7, 1, 20)
    vsz00.Add(self.timesfirstslider, 0, wx.EXPAND)
    self.timestrunc = wx.StaticText(vpnl, -1, u'下の行動に遷移するまで 2')
    vsz00.Add(self.timestrunc, 0, wx.EXPAND)
    self.timestruncslider = wx.Slider(vpnl, wx.NewId(), 2, 2, 200)
    vsz00.Add(self.timestruncslider, 0, wx.EXPAND)
    self.choices = [u'じっくり考える', u'助言を待つ', u'適当に開く']
    self.suggestion = wx.RadioBox(vpnl, wx.NewId(), u'知識不足/煮詰まったとき',
      choices=self.choices, majorDimension=3, style=wx.RA_SPECIFY_COLS)
    self.suggestion.EnableItem(0, False)
    self.suggestion.SetSelection(2)
    vsz00.Add(self.suggestion, 0, wx.EXPAND)
    hsz0 = wx.BoxSizer(wx.HORIZONTAL)
    self.stmisscont = wx.StaticText(vpnl, -1, u'失敗時の自動リトライ')
    hsz0.Add(self.stmisscont, 1, wx.EXPAND)
    self.misscont1 = wx.CheckBox(vpnl, wx.NewId(), u'序盤')
    self.misscont1.SetValue(True)
    hsz0.Add(self.misscont1, 0, wx.EXPAND)
    self.misscont2 = wx.CheckBox(vpnl, wx.NewId(), u'序盤以外')
    self.misscont2.SetValue(True)
    hsz0.Add(self.misscont2, 0, wx.EXPAND)
    vsz00.Add(hsz0, 0, wx.EXPAND)
    self.btnpause = wx.Button(vpnl, wx.NewId(), u'Pause')
    vsz00.Add(self.btnpause, 0, wx.EXPAND)
    hsz00 = wx.BoxSizer(wx.HORIZONTAL)
    self.showinfer = wx.CheckBox(vpnl, wx.NewId(), u'推論状態表示')
    self.showinfer.SetValue(False)
    hsz00.Add(self.showinfer, 1, wx.EXPAND)
    self.showdict = wx.CheckBox(vpnl, wx.NewId(), u'辞書検出表示')
    self.showdict.SetValue(True)
    hsz00.Add(self.showdict, 1, wx.EXPAND)
    self.showmap = wx.CheckBox(vpnl, wx.NewId(), u'内部状態表示')
    self.showmap.SetValue(False)
    hsz00.Add(self.showmap, 1, wx.EXPAND)
    vsz00.Add(hsz00, 0, wx.EXPAND)
    self.txt = wx.TextCtrl(vpnl, style=wx.TE_MULTILINE)
    vsz00.Add(self.txt, 3, wx.EXPAND)
    self.ptn = wx.TextCtrl(vpnl, style=wx.TE_MULTILINE)
    vsz00.Add(self.ptn, 3, wx.EXPAND)
    self.msg = wx.TextCtrl(vpnl, style=wx.TE_MULTILINE)
    vsz00.Add(self.msg, 2, wx.EXPAND)
    vpnl.SetSizer(vsz00)
    hsz.Add(vpnl, 1 if GENERATE_CHKBMP else 4, wx.EXPAND)
    vsz01 = wx.BoxSizer(wx.VERTICAL)
    self.map = wx.TextCtrl(self, style=wx.TE_MULTILINE)
    self.map.SetFont(wx.Font(8, wx.TELETYPE, wx.NORMAL, wx.NORMAL)) # wx.MODERN
    vsz01.Add(self.map, 4, wx.EXPAND)
    self.cap = wx.Panel(self, size=(PANELHW, PANELHH))
    vsz01.Add(self.cap, 5, wx.EXPAND)
    hsz.Add(vsz01, 3 if GENERATE_CHKBMP else 7, wx.EXPAND)
    self.SetSizer(hsz)
    self.btd = BTD.BalloonTipDict(main_icon.getBitmap())
    self.blnclock = self.btd.get(self, 'clock')
    self.blntimestrunc = self.btd.get(self, 'timestrunc')
    self.blnstmisscont = self.btd.get(self, 'stmisscont')
    wx.CallAfter(self.setup)

  def setup(self):
    self.amd = AMD.AutoMineDict()
    self.x, self.y = 0, 0
    self.gcount, self.count, self.phase, self.roll = 0, 0, 0, []
    self.fixed = [False] * (LEVELHW * LEVELHH)
    self.ldelta = [(-1, -1), (0, -1), (1, -1),
      (-1, 0), (1, 0), (-1, 1), (0, 1), (1, 1)]
    self.mdc = MemDC(wx.ClientDC(self.cap), wx.Colour(0, 0, 0))
    self.chkbmp = {}
    self.loadrefimg()
    self.maptbl = [0xff] * (LEVELHW * LEVELHH)
    self.target, self.pwm = None, None
    self.tick1 = False
    self.timer1 = wx.Timer(self, wx.NewId())
    self.Bind(wx.EVT_TIMER, self.onTick, self.timer1)
    self.Bind(wx.EVT_SLIDER, self.onClockSlider, self.clockslider)
    self.Bind(wx.EVT_SLIDER, self.onTimesFirstSlider, self.timesfirstslider)
    self.Bind(wx.EVT_SLIDER, self.onTimesTruncSlider, self.timestruncslider)
    self.Bind(wx.EVT_RADIOBOX, self.onSuggestion, self.suggestion)
    self.Bind(wx.EVT_CHECKBOX, self.onMisscont, self.misscont1)
    self.Bind(wx.EVT_CHECKBOX, self.onMisscont, self.misscont2)
    self.Bind(wx.EVT_CHECKBOX, self.onShowinfer, self.showinfer)
    self.Bind(wx.EVT_CHECKBOX, self.onShowdict, self.showdict)
    self.Bind(wx.EVT_CHECKBOX, self.onShowmap, self.showmap)
    self.Bind(wx.EVT_BUTTON, self.onPause, self.btnpause)
    self.Bind(wx.EVT_PAINT, self.OnPaint)
    self.Bind(wx.EVT_CLOSE, self.OnClose)
    self.onPause(None)

  def loadrefimg(self):
    if GENERATE_CHKBMP:
      bm = wx.Bitmap(u'%s.png' % APPTITLE)
      self.mdc.gblit(PANELHW, OFFSETH, None, None, bm, 0, 0)
      fp = open(GENERATE_CHKBMP, 'wb')
      for i in xrange(14):
        buf = self.mdc.gclip(CLPW, CLPH, PANELHW + 1, OFFSETH + CELLH * i + 1)
        fp.write('%s\n' % buf.encode('hex'))
      for i in xrange(2):
        buf = self.mdc.gclip(CLPW, CLPH,
          PANELHW + 32 + 18 * i, OFFSETH + CELLH * 15 - 4)
        fp.write('%s\n' % buf.encode('hex'))
      fp.close()
    for i, h in enumerate(CHKBMP):
      self.chkbmp[h.decode('hex')] = i - 1 if i > 0 else 0xff

  def maptxt(self, buf, w, dlm=None, fmt=None):
    s = []
    for y in xrange(len(buf) / w):
      for x in xrange(w):
        if x and dlm: s.append(dlm)
        s.append((fmt if fmt else '%02x') % buf[y * w + x])
      s.append('\n')
    return ''.join(s)

  def updatemap(self):
    for y in xrange(LEVELHH):
      for x in xrange(LEVELHW):
        k = self.mdc.gclip(CLPW, CLPH,
          OFFSETW - ADJW + CELLW * x, OFFSETH - ADJH + CELLH * y)
        self.maptbl[y * LEVELHW + x] = self.chkbmp[k] & 0x0f if \
          self.chkbmp.has_key(k) else 0xee

  def updatepaint(self, dc):
    self.map.Clear()
    if self.showmap.GetValue():
      self.mdc.flush()
      self.map.WriteText(self.maptxt(self.maptbl, LEVELHW, ' ', '%x'))
    else:
      bdc = wx.BufferedDC(dc)
      bdc.Clear()
      bdc.DrawText(u'描画休止中(少しだけ高速化)', 80, 40)

  def isover(self):
    k = self.mdc.gclip(CLPW, CLPH, OFFSETW + CELLW * 14 + 5, 23)
    if not self.chkbmp.has_key(k): return 0
    return self.chkbmp[k] - 12 if self.chkbmp[k] else 0

  def num(self, x, y):
    if x < 0 or y < 0: return None
    if x >= LEVELHW or y >= LEVELHH: return None
    return self.maptbl[y * LEVELHW + x]

  def countaround(self, x, y):
    '''return count of flagged cell, opened cell, closed cell, r, l(=ptn)'''
    f, o, c, r, l = 0, 0, 0, set(), []
    for dx, dy in self.ldelta:
      n = self.num(x + dx, y + dy)
      if n is None:
        l.append(0)
        continue
      l.append(n)
      if n == 9: f += 1
      if 0 <= n <= 8: o += 1
      if n == 0x0f or n == 0x0c or n == 9:
        c += 1
        if n != 9: r.add((x + dx, y + dy)) # 二重 click 防止
    l[4:4] = [self.num(x, y)]
    return f, o, c, r, ''.join(hex(b)[-1] for b in l)

  def loginfer(self, s):
    if self.showinfer.GetValue(): self.txt.AppendText(s)

  def guess(self):
    import random
    self.loginfer(u'guess...')
    for _ in xrange(100): # block endress loop 効率悪 直接未開地を探す方が速い
      self.x = random.randint(0, LEVELHW - 1)
      self.y = random.randint(0, LEVELHH - 1)
      if self.num(self.x, self.y) == 0x0f: break
    self.loginfer(u'[%d, %d]' % (self.x, self.y))
    return [], set(((self.x, self.y),)), set() # always to be opened

  def infer(self):
    self.count += 1 # 手数
    if self.count <= self.timesfirstslider.GetValue(): return self.guess()
    if self.count - self.gcount <= 1: return self.guess() # 1 回だけ適当に開く
    self.loginfer(u'infer(%d, %d)...' % (self.x, self.y))
    roll = []
    while True: # 必ず最後は roll で break するので無限ループにはならない
      x, y = self.x, self.y
      self.x += 1
      if self.x >= LEVELHW: self.x, self.y = 0, self.y + 1
      if self.y >= LEVELHH: self.y = 0
      if not self.fixed[y * LEVELHW + x]:
        n = self.num(x, y)
        if 1 <= n <= 8:
          self.loginfer(u'%d[%d, %d]' % (n, x, y))
          roll.append((x, y))
          f, o, c, r, l = self.countaround(x, y)
          k, m = self.amd.match(l)
          lop, lmk = set(), set()
          if k:
            if self.showdict.GetValue():
              self.ptn.AppendText(u'%d[%d, %d]p[%s]q[%s]\n' % (n, x, y, l, k))
              self.ptn.AppendText(u'k[%s]m%dr%d\n' % (m[0], m[1], m[2]))
              self.ptn.AppendText(u'o%s\nm%s\n' % (repr(m[3]), repr(m[4])))
            for p in m[3]: # lop
              px, py = x + p[0], y + p[1]
              b = self.num(px, py)
              if b == 0x0f or b == 0x0c: lop.add((px, py)) # 二重 click 防止
            for p in m[4]: # lmk
              px, py = x + p[0], y + p[1]
              b = self.num(px, py)
              if b != 9: lmk.add((px, py)) # 二重 click 防止
          if len(r) == 0: self.fixed[y * LEVELHW + x] = True
          if f == n: return roll, lop.union(r), lmk # to be opened
          if c == n: return roll, lop, lmk.union(r) # to be marked
          # 戻った先でも lop lmk check しているが ここは roll 検出のため必要
          if k and (len(lop) or len(lmk)): return roll, lop, lmk
      if self.x == 0 and self.y == 0: break
    return roll, set(), set()

  def click(self, b, x, y):
    if x < 0 or y < 0: return 0
    if x >= LEVELHW or y >= LEVELHH: return 0
    self.loginfer(u'%c(%d, %d)' % ('m' if b else 'o', x, y))
    self.pwm.mouseclk(b, OFFSETW + CELLW * x, OFFSETH + CELLH * y) # btn L / R
    return 1

  def onTick(self, ev):
    if self.timer1.GetId() != ev.GetId(): return
    if self.tick1: return
    self.tick1 = True
    while True: # 除外処理系を break & 最後に break で脱出 (indent 減らすため)
      if self.target is None:
        self.msg.AppendText(u'Searching %s ...' % TARGETWCLASS)
        self.target = PostWinMsg.target(TARGETWCLASS, TARGETWCLASS)
        if self.target == 0:
          self.msg.AppendText(u'may not be running.\n')
          self.target = None
          break
        self.msg.AppendText(u'is found.\n')
        self.pwm = PostWinMsg(self.target, wait=0, fg=False)
        # self.msg.AppendText(self.pwm.getclassname(len(TARGETWCLASS)))
        self.pwm.topmost()
        self.pwm.altkeys('GE') # Alt-G-E select high level
        self.pwm.keydu(113) # VK_F2 restart
        self.pwm.sleep(INTERVAL * 4)
        self.txt.Clear()
        self.ptn.Clear()
        self.amd.reload()
        self.x, self.y = 0, 0
        self.gcount, self.count, self.phase, self.roll = 0, 0, 0, []
        self.fixed = [False] * (LEVELHW * LEVELHH)
        break
      self.mdc.gcapture(0, 0, PANELHW, PANELHH, self.target, 0, 0)
      self.updatemap()
      self.updatepaint(wx.ClientDC(self.cap))
      o = self.isover()
      if o == 1:
        self.msg.AppendText(u'completed\n')
        self.onPause(None)
        self.target = None
        # self.pwm.wm(18, 0, 0) # WM_QUIT
        break
      elif o == 2:
        self.msg.AppendText(u'missed never give up\n')
        if self.count <= self.timesfirstslider.GetValue() \
        and self.misscont1.GetValue(): # 序盤(規定手数内)の失敗続行
          self.pwm.topmost(False)
        elif self.count > self.timesfirstslider.GetValue() \
        and self.misscont2.GetValue(): # 序盤以外の失敗続行
          self.pwm.topmost(False)
        else: self.onPause(None)
        self.target = None
        break
      roll, lop, lmk = self.infer()
      if len(lop) or len(lmk):
        c = 0
        for x, y in lop: c += self.click(0, x, y) # open many boxes
        for x, y in lmk: c += self.click(1, x, y) # block '?' from double click
        if c: self.pwm.sleep(INTERVAL) # redraw (block reentry self.tick1)
      else:
        self.loginfer(u'roll\n')
        if roll == self.roll: self.phase += 1
        if self.phase >= self.timestruncslider.GetValue(): # 行動遷移
          if self.suggestion.GetSelection() == 1:
            self.msg.AppendText(u'I want your suggestion, and resume it.\n')
            self.onPause(None)
          else: self.gcount = self.count
          self.phase = 0
      self.roll = roll
      break
    self.tick1 = False

  def onClockSlider(self, ev):
    self.clock.SetLabel(u'動作速度 clock %dms' % (self.clockslider.GetValue()))

  def onTimesFirstSlider(self, ev):
    self.timesfirst.SetLabel(u'最初に開く場所 %dヶ所' % (
      self.timesfirstslider.GetValue()))

  def onTimesTruncSlider(self, ev):
    self.timestrunc.SetLabel(u'下の行動に遷移するまで %d' % (
      self.timestruncslider.GetValue()))

  def onSuggestion(self, ev):
    self.msg.AppendText(u'suggestion=%d\n' % self.suggestion.GetSelection())

  def onMisscont(self, ev):
    self.msg.AppendText(u'misscont%d=%d\n' % (
      1 if ev.GetId() == self.misscont1.GetId() else 2,
      ev.GetEventObject().GetValue()))

  def onShowinfer(self, ev):
    self.msg.AppendText(u'showinfer=%d\n' % self.showinfer.GetValue())

  def onShowdict(self, ev):
    self.msg.AppendText(u'showdict=%d\n' % self.showdict.GetValue())

  def onShowmap(self, ev):
    self.msg.AppendText(u'showmap=%d\n' % self.showmap.GetValue())

  def onPause(self, ev):
    if self.timer1.IsRunning():
      self.msg.AppendText(u'pause...\n')
      self.btnpause.SetLabel(u'Resume')
      self.timer1.Stop()
      if self.pwm: self.pwm.topmost(False) # after stop timer
    else:
      self.msg.AppendText(u'running...\n')
      self.btnpause.SetLabel(u'Pause')
      if self.pwm: self.pwm.topmost(True) # before start timer
      self.timer1.Start(
        milliseconds=self.clockslider.GetValue(), oneShot=False)

  def OnPaint(self, ev):
    dc = wx.PaintDC(self) # Don't delete this line
    wx.CallAfter(self.updatepaint, wx.ClientDC(self.cap))

  def OnClose(self, ev):
    if self.timer1.IsRunning(): self.timer1.Stop()
    if self.pwm: self.pwm.topmost(False)
    self.Destroy()

class MyApp(wx.App):
  def OnInit(self):
    self.frm = MyFrame(None, wx.NewId())
    self.SetTopWindow(self.frm)
    self.frm.Show()
    return True

if __name__ == '__main__':
  app = MyApp()
  app.MainLoop()
