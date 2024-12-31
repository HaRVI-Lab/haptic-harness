from PyQt5.QtCore import ws
from numpy import test
import numpy as np
from .Generator import Generator
import ezdxf
import os

doc = ezdxf.new(dxfversion="AC1015")
msp = doc.modelspace()
test_generator = Generator("/Users/kr/Downloads")

results1 = test_generator.genCenter(msp)
results2 = test_generator.genCenter2(msp)
if results1 == results2:
    print("genCenter is good")

results1 = np.array(test_generator.genTyvekTileFlap())
results2 = np.array(test_generator.genTyvekTileFlap2())
if (results1 == results2).all():
    print("genTyvekTileFlap is good")

results1 = test_generator.generateTyvekTile()
results2 = test_generator.generateTyvekTile2()
if results1 == results2:
    print("generateTyvekTile is good")

verts1, lines1 = test_generator.genOuterPolygon(msp, [], [])
verts2, lines2 = test_generator.genOuterPolygon2(msp, [], [])
verts1 = np.array(verts1)
verts2 = np.array(verts2)
if (verts1 == verts2).all() and lines1 == lines2:
    print("genOuterPolygon is good")
