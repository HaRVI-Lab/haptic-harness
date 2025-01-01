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
verts1 = np.array(verts1)

verts1, lines1 = test_generator.genMagnetHoles(msp, [], [])
verts2, lines2 = test_generator.genMagnetHoles2(msp, [], [])
verts1 = np.array(verts1)
verts2 = np.array(verts2)
# for i in range(len(verts1)):
#     if not (verts1[i] == verts2[i]).all():
#         print(verts1[i])
#         print(verts2[i])
#         print(i)
if np.isclose(verts1, verts2, atol=1e-8).all() and lines1 == lines2:
    print("genMagnetHoles is good")


mesh1 = test_generator.polygonalPrism(
    radius=test_generator.concentricPolygonRadius * 2,
    res=40,
    height=test_generator.magnetThickness + 2,
    origin=(0, 0, 0),
)
mesh2 = test_generator.polygonalPrism2(
    radius=test_generator.concentricPolygonRadius * 2,
    res=40,
    height=test_generator.magnetThickness + 2,
    origin=(0, 0, 0),
)
if mesh1 == mesh2:
    print("polygonalPrism is good")


verts1, faces1 = test_generator.generateMagneticConnectorHalf(np.array([0, 0, 0]))
verts1 = np.array(verts1)
verts2, faces2 = test_generator.generateMagneticConnectorHalf2(np.array([0, 0, 0]))
verts2 = np.array(verts2)

for i in range(len(verts1)):
    if not (verts1[i] == verts2[i]).all():
        print(verts1[i])
        print(verts2[i])
if (verts1 == verts2).all():
    print("generateMagneticConnectorHalf is good")
origin = np.array((0, 0, 0))
width = (
    test_generator.distanceBetweenMagnetClipAndSlot
    + test_generator.magnetRadius * 2
    + test_generator.magnetClipThickness * 3
)
height = (
    4 * test_generator.magnetClipThickness
    + 2 * test_generator.magnetRadius
    + test_generator.distanceBetweenMagnetsInClip
)
r = 2 * test_generator.magnetClipThickness + test_generator.magnetRadius
verts1, faces1 = test_generator.generateSlot(origin, width, height, r)
verts1 = np.array(verts1)
verts2, faces2 = test_generator.generateSlot2(origin, width, height, r)
verts2 = np.array(verts2)

for i in range(len(verts1)):
    if not (verts1[i] == verts2[i]).all():
        print(verts1[i])
        print(verts2[i])
if (verts1 == verts2).all():
    print("generateSlot is good")
