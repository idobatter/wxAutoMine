#!/usr/local/bin/python
# -*- coding: utf-8 -*-
'''AutoMineDict
Copyright(C) 2012 idobatter, All Rights Reserved.
pattern (same as maptbl code)
 f: not opened
 o: opened any number or wall
 n(1-8): opened and number
 9: flagged

m = mirror mode (0: なし, 1: 線非対称(縦線｜), 2: 線非対称(斜線＼))
 -> 1 or 2 どちらの線非対称でも 4 種 rotate 全て持てば 1 or 2 の区別は無くなる
r = rotate angle (0: 0, 1: 90, 2: 180, 3: 270)
lop = delta points list to be opened
lmk = delta points list to be marked
※pattern (と mirror / rotate 処理) は今のところ 3 x 3 専用だが
delta points の範囲は 3 x 3 以上に離れた場所 (1-3-1) のときなどにも使える
ただし枠外に出るケースに注意
※現状は検索を高速化するため mirror した pattern も持っているが
pattern のサイズが大きくなると組み合わせが増えるので注意
 -> amd.add() で mirror ありのときは amd.add() 内で自動生成
'''

DATAFILE = u'AutoMineDict.txt'

class AutoMineDict(object):
  def __init__(self):
    self.flush()

  def flush(self):
    self.d = [None, {}, {}, {}, {}, {}, {}, {}, {}]

  def reload(self, fn=DATAFILE):
    self.flush()
    f = open(fn, 'rb')
    c, sw, sh, m, dw, dh, p, q = 0, 0, 0, 0, 0, 0, [], []
    for l in f.readlines():
      if l[0] == '#' or len(l.rstrip()) == 0: continue
      if l[0] == 'p':
        d, sw, sh, m, dw, dh, e = map(
          lambda x: int(x) if x.isdigit() else x, l.split(',', 6))
        c, o, p, q = 0, (dw - 1) / 2, [], []
        continue
      p.append(l[1:1 + dw])
      q.append(l[7:7 + dw])
      c += 1
      if c < dh: continue
      ptn = ''.join(p[1 + n][1:1 + sw] for n in xrange(sh))
      lop, lmk = [], []
      for y in xrange(dh):
        for x in xrange(dw):
          r = q[y][x]
          if r == 'o': lop.append((x - o, y - o))
          elif r == 'm': lmk.append((x - o, y - o))
      self.add(ptn, m, lop, lmk)
    f.close()

  def add(self, ptn, m, lop, lmk):
    '''mirror ありのときは自動生成'''
    n = int(ptn[4])
    for i in xrange(2 if m else 1):
      if i:
        ptn = self.ptnmirror(ptn, m)
        lop = [self.pmirror(p, m) for p in lop]
        lmk = [self.pmirror(p, m) for p in lmk]
      for r in xrange(4):
        k = self.ptnrrotate(ptn, r)
        if self.d[n].has_key(k): print 'key conflicts: [%s]\a' % k # with beep
        self.d[n][k] = [ptn, m, r,
          [self.prrotate(p, r) for p in lop],
          [self.prrotate(p, r) for p in lmk]]

  def match(self, ptn):
    '''ptn must be a string length 9'''
    n = int(ptn[4]) # center is always a number 1-8, bat arounds may be 'f09?'
    for k in self.d[n].keys():
      for i, c in enumerate(k):
        if c == '-': continue
        elif c == 'o':
          if not ptn[i].isdigit() or int(ptn[i]) == 9: break
        elif c == 'f':
          if ptn[i] != '9' and ptn[i] != 'f': break
        else:
          if c != ptn[i]: break
      else: return k, self.d[n][k]
    else: return None, None

  @classmethod
  def ptnmirror(cls, ptn, m=0):
    '''mirror'''
    l = list(ptn)
    if m == 1: l = [l[n] for n in (2, 1, 0, 5, 4, 3, 8, 7, 6)]
    if m == 2: l = [l[n] for n in (0, 3, 6, 1, 4, 7, 2, 5, 8)]
    return ''.join(l)

  @classmethod
  def pmirror(cls, p, m=0):
    '''reverse mirror'''
    x, y = p[0], p[1]
    if m == 1: return (-x, y)
    if m == 2: return (y, x)
    return (x, y)

  @classmethod
  def ptnrrotate(cls, ptn, r=1):
    '''rotate right'''
    l = list(ptn)
    for i in xrange(r): l = [l[n] for n in (6, 3, 0, 7, 4, 1, 8, 5, 2)]
    return ''.join(l)

  @classmethod
  def prrotate(cls, p, r=1):
    '''rotate right'''
    x, y = p[0], p[1]
    for i in xrange(r): x, y = -y, x
    return (x, y)

  @classmethod
  def plrotate(cls, p, r=1):
    '''rotate left'''
    x, y = p[0], p[1]
    for i in xrange(r): x, y = y, -x
    return (x, y)

if __name__ == '__main__':
  amd = AutoMineDict()
  amd.reload()
  ptn = '123456789'
  print 'mirror'
  print amd.ptnmirror(ptn, m=1),
  print amd.ptnmirror(amd.ptnmirror(ptn, m=1), m=1),
  print amd.ptnmirror(ptn, m=2),
  print amd.ptnmirror(amd.ptnmirror(ptn, m=2), m=2)
  print 'rrotate'
  print amd.ptnrrotate(ptn),
  print amd.ptnrrotate(ptn, r=2),
  print amd.ptnrrotate(ptn, r=3),
  print amd.ptnrrotate(ptn, r=4),
  print amd.ptnrrotate(ptn, r=5)
  print '----'
  for n, d in enumerate(amd.d):
    if not n: continue
    for ptn in d.keys():
      print n, ptn, d[ptn]
      m = d[ptn][1]
      if m: print 'reverse mirror',
      print n, amd.ptnmirror(ptn, m=m), \
        [amd.pmirror(p, m=m) for p in d[ptn][3]], \
        [amd.pmirror(p, m=m) for p in d[ptn][4]]
      print '----'
  print 'match'
  print amd.match('o2fo2fo9f')
  print amd.match('52f52f59f')
  print amd.match('f1of4offf')
  print amd.match('f16f46fff')
