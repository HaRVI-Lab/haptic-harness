from logging import currentframe
from PyQt5.QtCore import ws
from ezdxf.layouts import base
from ezdxf.math.bulge import angle
import numpy as np
from numpy._core.defchararray import lower
import pyvista as pv
import ezdxf
import numpy as np
from time import perf_counter
from PyQt5.QtCore import QRunnable, pyqtSignal, QObject
from vtkbool.vtkBool import vtkPolyDataBooleanFilter


class Signals(QObject):
    progress = pyqtSignal(int)
    finished = pyqtSignal()


class WorkerWrapper(QRunnable):
    def __init__(self, worker):
        super().__init__()
        self.worker = worker

    def run(self):
        self.worker.run()


class Generator(QRunnable):
    def __init__(self, userDir):
        super().__init__()
        self.userDir = userDir
        self.concentricPolygonRadius = 30
        self.tactorRadius = 10
        self.numSides = 6
        self.slotWidth = 30
        self.slotHeight = 1.5
        self.slotBorderRadius = 10
        self.magnetRadius = 5
        self.magnetThickness = 1
        self.magnetRingRadius = 20
        self.numMangetsInRing = 6
        self.magnetClipThickness = 1.5
        self.magnetClipRingThickness = 1.5
        self.distanceBetweenMagnetsInClip = (
            2 * (self.magnetRadius + self.magnetClipRingThickness) + 4
        )
        self.distanceBetweenMagnetClipAndPolygonEdge = 3
        self.distanceBetweenMagnetClipAndSlot = 3
        self.foamThickness = 1

        self.mountRadius = 13
        self.mountHeight = 10
        self.mountShellThickness = 2
        self.mountBottomAngleOpening = np.pi / 3
        self.mountTopAngleOpening = np.pi / 4
        self.brim = 3

        self.tyvek_tile = self.generateTyvekTile()
        self.foam = self.generateFoam()
        self.magnet_ring = self.generateMagnetRing()
        self.base = self.generateBase()
        self.bottom_clip = self.generateBottomClip()
        self.top_clip = self.generateTopClip()
        self.mount = self.generateMount()

        self.generatedObjects = [
            self.tyvek_tile,
            self.foam,
            self.magnet_ring,
            self.base,
            self.bottom_clip,
            self.top_clip,
            self.mount,
        ]

        # Shared signal for progress bar
        self.signals = Signals()

    def run(self):
        self.regen()
        self.generatedObjects = [
            self.tyvek_tile,
            self.foam,
            self.magnet_ring,
            self.base,
            self.bottom_clip,
            self.top_clip,
            self.mount,
        ]
        self.signals.finished.emit()

    def regen(self):
        time1 = perf_counter()
        self.signals.progress.emit(1)
        self.tyvek_tile = self.generateTyvekTile()
        self.signals.progress.emit(2)
        self.foam = self.generateFoam()
        self.signals.progress.emit(3)
        self.magnet_ring = self.generateMagnetRing()
        self.signals.progress.emit(4)
        self.base = self.generateBase()
        self.signals.progress.emit(5)
        self.bottom_clip = self.generateBottomClip()
        self.signals.progress.emit(6)
        self.top_clip = self.generateTopClip()
        self.signals.progress.emit(7)
        self.mount = self.generateMount()
        self.signals.progress.emit(8)
        print(perf_counter() - time1)

    def validate(self):
        messages = []
        tolerance = 1

        if self.numSides < 2 or self.numSides > 8:
            messages.append("numSides must be between 2 and 8 inclusive")

        for attr, val in vars(self).items():
            if attr != "userDir" and (val <= 0 or val == None):
                messages.append(f"{attr} must be some positive non-zero value")

        if self.tactorRadius >= self.concentricPolygonRadius:
            messages.append(
                "The tactorRadius is too large for the concentricPolygonRadius"
            )
        if self.mountRadius > self.magnetRingRadius - self.magnetRadius - tolerance:
            messages.append(
                "The mountRadius is too large for the magnetRingRadius and magnetRadius"
            )
        if self.mountBottomAngleOpening >= 3 * np.pi / 2:
            messages.append("the mountBottomAngleOpening must be less than 3 * PI / 2")
        if self.mountTopAngleOpening > 3 * np.pi / 2:
            messages.append("the mountTopAngleOpening must be less than 3 * PI / 2")
        if self.distanceBetweenMagnetsInClip < 2 * self.magnetRadius + tolerance:
            messages.append(
                "The distanceBetweenMagnetsInClip and magnetRadius are incompatible; try increasing distanceBetweenMagnetClipAndSlot decreasing magnetRadius"
            )
        maxTactorRadius = self.tactorRadius / (np.cos(np.pi / self.numSides))
        if maxTactorRadius + tolerance > self.magnetRingRadius - self.magnetRadius:
            messages.append(
                "The tactorRadius, magnetRadius, and magnetRingRadius are incompatible"
            )
        if (
            self.concentricPolygonRadius
            < self.magnetRingRadius + self.magnetRadius + tolerance
        ):
            messages.append(
                "The concentricPolygonRadius, magnetRadius, and magnetRingRadius are incompatible"
            )
        concentricPolygonEdge = (
            2 * self.concentricPolygonRadius * np.tan(np.pi / self.numSides)
        )
        if self.slotWidth + 2 * tolerance > concentricPolygonEdge:
            messages.append(
                "The slotWidth is too large for the concentricPolygonRadius and numSides"
            )

        if (
            concentricPolygonEdge
            < 2 * self.magnetRadius + 2 * tolerance + self.distanceBetweenMagnetsInClip
        ):
            messages.append("The polygon's edge is too short for the magnetRadius")

        if self.distanceBetweenMagnetsInClip < tolerance:
            messages.append(
                f"The distanceBetweenMagnetsInClip is less than the minimum tolerance, {tolerance}"
            )
        if self.distanceBetweenMagnetClipAndSlot < tolerance:
            messages.append(
                f"The distanceBetweenMagnetClipAndSlot is less than the minimum tolerance, {tolerance}"
            )
        if self.distanceBetweenMagnetClipAndPolygonEdge < tolerance:
            messages.append(
                f"The distanceBetweenMagnetClipAndPolygonEdge is less than the minimum tolerance, {tolerance}"
            )

        x = (concentricPolygonEdge - self.slotWidth) / 2
        y = (
            self.distanceBetweenMagnetClipAndPolygonEdge
            + 2 * (self.magnetRadius + self.magnetClipRingThickness)
            + self.distanceBetweenMagnetClipAndSlot
            + self.slotHeight / 2
        )
        beta = np.arctan(x / y)
        hypo = x / np.sin(beta)
        phi = (np.pi * (self.numSides - 2)) / self.numSides
        theta = (np.pi - phi) / 2
        dist = np.sin(beta + theta) * hypo
        if 2 * dist < 2 * self.slotBorderRadius + tolerance:
            messages.append(
                f"The edges of the flaps are intersecting; try decreasing slotWidth, increasing concentricPolygonRadius, decreasing slotBorderRadius, or decreasing numSides"
            )

        return messages

    def booleanOp(self, obj1, obj2, opType):
        if not obj1.is_manifold and not obj2.is_manifold:
            raise Exception("Both meshes must be manifold before a boolean operation")
        boolean = vtkPolyDataBooleanFilter()
        boolean.SetInputData(0, obj1)
        boolean.SetInputData(1, obj2)
        if opType == "difference":
            boolean.SetOperModeToDifference()
        elif opType == "union":
            boolean.SetOperModeToUnion()
        else:
            raise Exception("Operation type must be specified")
        boolean.Update()
        result = (
            pv.wrap(boolean.GetOutput())
            .triangulate()
            .clean()
            .compute_normals(consistent_normals=True, auto_orient_normals=True)
        )
        if not result.is_manifold:
            raise Exception("The resulting mesh is not manifold")
        return result

    def customSetAttr(self, attrName, val):
        if val == "":
            setattr(self, attrName, None)
        else:
            if attrName == "numSides" or attrName == "numMangetsInRing":
                setattr(self, attrName, int(val))
            else:
                setattr(self, attrName, float(val))

    def genCenter(self, msp):
        vertices = []
        pyVistaLines = [(2, i, (i + 1) % 6) for i in range(6)]
        thetas = np.arange(6) * 2 * np.pi / 6
        x_vals = self.tactorRadius * np.cos(thetas)
        y_vals = self.tactorRadius * np.sin(thetas)
        z_vals = np.zeros(6)
        vertices = np.column_stack((x_vals, y_vals, z_vals)).tolist()
        for i in range(6):
            msp.add_line(vertices[i], vertices[(i + 1) % 6])
        return (vertices, pyVistaLines)

    def genTyvekTileFlap(self):
        theta = np.pi * 2 / self.numSides

        lines = []
        # polygon side
        polygonSideHalf = self.concentricPolygonRadius * np.tan(theta / 2)
        lines.append(
            (
                [polygonSideHalf, self.concentricPolygonRadius],
                [-1 * polygonSideHalf, self.concentricPolygonRadius],
            )
        )

        # magnet clip holes
        resolution = 30
        yOffset = (
            self.distanceBetweenMagnetClipAndPolygonEdge
            + self.concentricPolygonRadius
            + self.magnetRadius
            + self.magnetClipRingThickness
        )
        step = 2 * np.pi / resolution
        angles = np.arange(resolution) * step
        r = self.magnetRadius + self.magnetClipRingThickness
        base_x_vals = r * np.cos(angles)
        y_vals = r * np.sin(angles) + yOffset
        offset = self.distanceBetweenMagnetsInClip / 2
        for j in range(2):
            x_vals = base_x_vals + offset * (-1) ** j
            v1 = np.column_stack((x_vals, y_vals))
            v2 = np.column_stack((np.roll(x_vals, -1), np.roll(y_vals, -1)))
            lines.extend(zip(v1, v2))

        # slot
        yOffset = (
            self.distanceBetweenMagnetClipAndPolygonEdge
            + self.concentricPolygonRadius
            + 2 * (self.magnetRadius + self.magnetClipRingThickness)
            + self.distanceBetweenMagnetClipAndSlot
        )
        lines.append(([-self.slotWidth / 2, yOffset], [self.slotWidth / 2, yOffset]))
        lines.append(
            (
                [self.slotWidth / 2, yOffset],
                [self.slotWidth / 2, yOffset + self.slotHeight],
            )
        )
        lines.append(
            (
                [self.slotWidth / 2, yOffset + self.slotHeight],
                [-self.slotWidth / 2, yOffset + self.slotHeight],
            )
        )
        lines.append(
            (
                [-self.slotWidth / 2, yOffset + self.slotHeight],
                [-self.slotWidth / 2, yOffset],
            )
        )

        # outer border
        if polygonSideHalf <= self.slotWidth / 2 + self.slotBorderRadius:
            initTheta = np.arccos(
                (polygonSideHalf - self.slotWidth / 2) / self.slotBorderRadius
            )
            resolution = 10
            yOffset = (
                self.distanceBetweenMagnetClipAndPolygonEdge
                + self.concentricPolygonRadius
                + 2 * (self.magnetRadius + self.magnetClipRingThickness)
                + self.distanceBetweenMagnetClipAndSlot
                + self.slotHeight / 2
            )
            stock = np.arange(resolution)
            stock1 = np.arange(1, resolution + 1)
            cur_thetas = (np.pi / 2 + initTheta) / resolution * stock - initTheta
            next_thetas = (np.pi / 2 + initTheta) / resolution * stock1 - initTheta
            base_x_vals_v1 = (
                np.cos(cur_thetas) * self.slotBorderRadius + self.slotWidth / 2
            )
            base_x_vals_v2 = (
                np.cos(next_thetas) * self.slotBorderRadius + self.slotWidth / 2
            )
            y_vals_v1 = self.slotBorderRadius * np.sin(cur_thetas) + yOffset
            y_vals_v2 = self.slotBorderRadius * np.sin(next_thetas) + yOffset
            init_val_x_vals = [
                np.array(
                    [
                        self.slotBorderRadius * np.cos(-initTheta) + self.slotWidth / 2,
                        self.slotBorderRadius * np.sin(-initTheta) + yOffset,
                    ]
                ),
                np.array(
                    [
                        -1
                        * (
                            self.slotBorderRadius * np.cos(-initTheta)
                            + self.slotWidth / 2
                        ),
                        self.slotBorderRadius * np.sin(-initTheta) + yOffset,
                    ]
                ),
            ]
            signs = np.array([1, -1])
            for j in range(2):
                lines.append(
                    (
                        [signs[j] * polygonSideHalf, self.concentricPolygonRadius],
                        init_val_x_vals[j],
                    )
                )
                x_vals_v1 = base_x_vals_v1 * signs[j]
                x_vals_v2 = base_x_vals_v2 * signs[j]
                v1 = np.column_stack((x_vals_v1, y_vals_v1))
                v2 = np.column_stack((x_vals_v2, y_vals_v2))
                lines.extend(zip(v1, v2))
            lines.append(
                (
                    [self.slotWidth / 2, self.slotBorderRadius + yOffset],
                    [-self.slotWidth / 2, self.slotBorderRadius + yOffset],
                )
            )
        else:
            yOffset = (
                self.distanceBetweenMagnetClipAndPolygonEdge
                + self.concentricPolygonRadius
                + 2 * (self.magnetRadius + self.magnetClipRingThickness)
                + self.distanceBetweenMagnetClipAndSlot
                + self.slotHeight
                + self.slotBorderRadius
            )
            lines.append(([polygonSideHalf, yOffset], [-polygonSideHalf, yOffset]))
            lines.append(
                (
                    [polygonSideHalf, self.concentricPolygonRadius],
                    [polygonSideHalf, yOffset],
                )
            )
            lines.append(
                (
                    [-polygonSideHalf, self.concentricPolygonRadius],
                    [-polygonSideHalf, yOffset],
                )
            )
        return lines

    def generateTyvekTile(self):
        doc = ezdxf.new(dxfversion="AC1015")
        msp = doc.modelspace()
        pvVerts, pvLines = self.genCenter(msp)
        lines = np.array(self.genTyvekTileFlap()).reshape(-1, 2).T
        new_len = lines.shape[1]
        zeros = np.zeros(new_len).reshape((-1, 1))
        for i in range(self.numSides):
            offset = len(pvVerts)
            theta = 2 * np.pi / self.numSides * i
            lines_copy = lines.copy()
            rotationalMatrix = np.matrix(
                np.array(
                    [[np.cos(theta), np.sin(theta)], [-np.sin(theta), np.cos(theta)]]
                )
            )
            product = rotationalMatrix * lines_copy
            new_verts = product.T
            verts_3d = np.concatenate((new_verts, zeros), axis=1).tolist()
            new_lines = [(2, k, k + 1) for k in range(offset, new_len + offset, 2)]
            pvVerts.extend(verts_3d)
            pvLines.extend(new_lines)
            for k in range(0, new_len, 2):
                msp.add_line(new_verts[k].tolist()[0], new_verts[k + 1].tolist()[0])
        doc.saveas(f"{self.userDir}/tyvekTile.dxf")

        mesh = pv.PolyData()
        mesh.points = pvVerts
        mesh.lines = pvLines
        return mesh

    def genOuterPolygon(self, msp, pvVerts, pvLines):
        theta = 2 * np.pi / self.numSides
        polygonSideHalf = self.concentricPolygonRadius * np.tan(theta / 2)
        ogPair = (
            [polygonSideHalf, self.concentricPolygonRadius],
            [-1 * polygonSideHalf, self.concentricPolygonRadius],
        )
        for i in range(self.numSides):
            theta = 2 * np.pi / self.numSides * i
            rotationalMatrix = np.matrix(
                [[np.cos(theta), np.sin(theta)], [-np.sin(theta), np.cos(theta)]]
            )
            v1 = rotationalMatrix * np.array(ogPair[0]).reshape((-1, 1))
            v2 = rotationalMatrix * np.array(ogPair[1]).reshape((-1, 1))
            offset = len(pvVerts)
            pvVerts.append((v1[0].item(), v1[1].item(), 0))
            pvVerts.append((v2[0].item(), v2[1].item(), 0))
            pvLines.append((2, offset, offset + 1))
            msp.add_line(v1, v2)

        return (pvVerts, pvLines)

    def generateFoam(self):
        doc = ezdxf.new(dxfversion="AC1015")
        msp = doc.modelspace()
        pvVerts, pvLines = self.genCenter(msp)
        pvVerts, pvLines = self.genOuterPolygon(msp, pvVerts, pvLines)
        doc.saveas(f"{self.userDir}/foamPiece.dxf")

        mesh = pv.PolyData()
        mesh.points = pvVerts
        mesh.lines = pvLines
        return mesh

    def genMagnetHoles(self, msp, pvVerts, pvLines):
        resolution = 30
        for i in range(self.numMangetsInRing):
            theta = 2 * np.pi / self.numMangetsInRing * i
            offset = len(pvVerts)
            stock = np.arange(resolution)
            thetas = 2 * np.pi / resolution * stock
            x_vals_v1 = (
                self.magnetRadius * np.cos(thetas)
                + np.cos(theta) * self.magnetRingRadius
            )
            y_vals_v1 = (
                self.magnetRadius * np.sin(thetas)
                + np.sin(theta) * self.magnetRingRadius
            )
            v1 = np.column_stack((x_vals_v1, y_vals_v1))
            x_vals_v2 = (
                self.magnetRadius * np.cos(np.roll(thetas, -1))
                + np.cos(theta) * self.magnetRingRadius
            )
            y_vals_v2 = (
                self.magnetRadius * np.sin(np.roll(thetas, -1))
                + np.sin(theta) * self.magnetRingRadius
            )
            v2 = np.column_stack((x_vals_v2, y_vals_v2))
            combined = np.column_stack((v1, v2)).reshape(-1, 2)
            verts_3d = np.column_stack((combined, np.zeros(resolution * 2)))
            for j in range(resolution):
                msp.add_line(verts_3d[2 * j], verts_3d[2 * j + 1])
            newLines = [
                (2, j, j + 1) for j in range(offset, offset + 2 * resolution, 2)
            ]
            pvLines.extend(newLines)
            pvVerts.extend(verts_3d)
        return (pvVerts, pvLines)

    def generateMagnetRing(self):
        doc = ezdxf.new(dxfversion="AC1015")
        msp = doc.modelspace()
        pvVerts, pvLines = self.genCenter(msp)
        pvVerts, pvLines = self.genOuterPolygon(msp, pvVerts, pvLines)
        pvVerts, pvLines = self.genMagnetHoles(msp, pvVerts, pvLines)
        doc.saveas(f"{self.userDir}/magnetRing.dxf")

        mesh = pv.PolyData()
        mesh.points = pvVerts
        mesh.lines = pvLines
        return mesh

    def polygonalPrism(self, radius, res, height, origin):
        totalFaces = []

        thetas = np.linspace(0, 2 * np.pi, res, endpoint=False)
        z_bottom = -height / 2 + origin[2]
        z_top = height / 2 + origin[2]
        x = radius * np.cos(thetas) + origin[0]
        y = radius * np.sin(thetas) + origin[1]
        z_bottom_array = np.full(res, z_bottom)
        z_top_array = np.full(res, z_top)
        bottom_vertices = np.column_stack((x, y, z_bottom_array))
        top_vertices = np.column_stack((x, y, z_top_array))
        totalVerts = np.vstack((bottom_vertices, top_vertices)).tolist()

        for i in range(res):
            totalFaces.append((3, i, (i + 1) % res, i + res))
            totalFaces.append((3, i + res, (i + 1) % res + res, (i + 1) % res))
        totalVerts.append((origin[0], origin[1], -height / 2 + origin[2]))
        totalVerts.append((origin[0], origin[1], height / 2 + origin[2]))
        for i in range(res):
            totalFaces.append((3, i, len(totalVerts) - 2, (i + 1) % res))
            totalFaces.append((3, i + res, len(totalVerts) - 1, (i + 1) % res + res))
        mesh = pv.PolyData(totalVerts, totalFaces)
        return mesh

    def polygonalPrismSlanted(self, radiusBottom, radiusTop, res, height, origin):
        totalVerts = []
        totalFaces = []
        thetaInterval = 2 * np.pi / res
        for i in range(res):
            totalVerts.append(
                (
                    radiusBottom * np.cos(thetaInterval * i) + origin[0],
                    radiusBottom * np.sin(thetaInterval * i) + origin[1],
                    -height / 2 + origin[2],
                )
            )
        for i in range(res):
            totalVerts.append(
                (
                    radiusTop * np.cos(thetaInterval * i) + origin[0],
                    radiusTop * np.sin(thetaInterval * i) + origin[1],
                    height / 2 + origin[2],
                )
            )
        for i in range(res):
            totalFaces.append((3, i, (i + 1) % res, i + res))
            totalFaces.append((3, i + res, (i + 1) % res + res, (i + 1) % res))
        totalVerts.append((origin[0], origin[1], -height / 2 + origin[2]))
        totalVerts.append((origin[0], origin[1], height / 2 + origin[2]))
        for i in range(res):
            totalFaces.append((3, i, len(totalVerts) - 2, (i + 1) % res))
            totalFaces.append((3, i + res, len(totalVerts) - 1, (i + 1) % res + res))
        mesh = pv.PolyData(totalVerts, totalFaces)
        return mesh

    def generateBase(self):
        prismHeight = 10
        polygon_theta = 2 * np.pi / self.numSides
        polygon_edge_half = self.concentricPolygonRadius * np.tan(polygon_theta / 2)
        incentric_radius = polygon_edge_half / np.sin(polygon_theta / 2)
        prism = self.polygonalPrismSlanted(
            radiusBottom=self.tactorRadius,
            radiusTop=self.tactorRadius * 0.8,
            res=6,
            height=prismHeight,
            origin=(0, 0, self.magnetThickness / 2 + 1 + prismHeight / 2),
        )
        base = (
            self.polygonalPrism(
                radius=incentric_radius + 10,
                res=40,
                height=self.magnetThickness + 2,
                origin=(0, 0, 0),
            )
            .subdivide(nsub=2)
            .compute_normals()
        )
        for i in range(self.numMangetsInRing):
            theta = 2 * np.pi / self.numMangetsInRing * i
            ogPoint = (
                self.magnetRingRadius * np.cos(theta),
                self.magnetRingRadius * np.sin(theta),
                1,
            )
            magnetHole = (
                self.polygonalPrism(
                    radius=self.magnetRadius,
                    res=30,
                    height=self.magnetThickness,
                    origin=ogPoint,
                )
                .subdivide(nsub=1)
                .compute_normals()
            )

            base = self.booleanOp(base, magnetHole, "difference")
        bottomBase = self.booleanOp(base, prism, "union")
        # Add foam recess
        outerBase = (
            self.polygonalPrism(
                radius=incentric_radius + 10,
                res=40,
                height=self.foamThickness,
                origin=(0, 0, self.magnetThickness / 2 + 1 + self.foamThickness / 2),
            )
            .subdivide(nsub=2)
            .compute_normals()
        )
        foamCavity = (
            self.polygonalPrism(
                radius=incentric_radius,
                res=self.numSides,
                height=self.foamThickness,
                origin=(0, 0, self.magnetThickness / 2 + 1 + self.foamThickness / 2),
            )
            .subdivide(nsub=2)
            .compute_normals()
        )
        outerBaseWithHole = self.booleanOp(outerBase, foamCavity, "difference")
        finalMesh = self.booleanOp(outerBaseWithHole, bottomBase, "union")
        finalMesh.save(f"{self.userDir}/base.stl")
        return finalMesh

    def generateMagneticConnectorHalf(self, origin: np.array):
        resolution = 30
        vertices = []
        r = self.magnetRadius + self.magnetClipRingThickness
        stock = np.arange(resolution)
        thetas = np.pi / resolution * stock - np.pi / 2
        x_vals = r * np.cos(thetas) + self.distanceBetweenMagnetsInClip / 2 + origin[0]
        y_vals = r * np.sin(thetas) + origin[1]
        z_vals = np.full(resolution, origin[2])
        thetas_1 = np.pi / 2 - np.pi / resolution * stock
        x_vals_1 = (
            -r * np.cos(thetas_1) - self.distanceBetweenMagnetsInClip / 2 + origin[0]
        )
        y_vals_1 = r * np.sin(thetas_1) + origin[1]

        vertices.extend(np.column_stack((x_vals, y_vals, z_vals)).tolist())
        vertices.extend(np.column_stack((x_vals_1, y_vals_1, z_vals)).tolist())
        vertices.append(origin)

        faces = [
            (3, len(vertices) - 1, i, (i + 1) % (2 * resolution))
            for i in range(2 * resolution)
        ]
        return vertices, faces

    def generateBottomMagnetConnector(self, origin: np.array):

        bottomVerts, bottomFaces = self.generateMagneticConnectorHalf(origin)
        topHalfOrigin = np.array(
            (origin[0], origin[1], origin[2] + self.magnetClipThickness)
        )
        topVerts, topFaces = self.generateMagneticConnectorHalf(topHalfOrigin)
        totalVerts = []
        totalFaces = []
        totalVerts.extend(bottomVerts)
        totalVerts.extend(topVerts)
        totalFaces.extend(bottomFaces)
        offset = len(bottomVerts)
        for i, face in enumerate(topFaces):
            topFaces[i] = (3, face[1] + offset, face[2] + offset, face[3] + offset)
        totalFaces.extend(topFaces)
        offset = len(bottomVerts)
        loopAround = len(bottomVerts) - 1
        for i in range(len(bottomVerts) - 1):
            totalFaces.append((3, i, i + offset, (i + 1) % loopAround + offset))
            totalFaces.append(
                (3, (i + 1) % loopAround + offset, (i + 1) % loopAround, i)
            )
        mesh = pv.PolyData(totalVerts, totalFaces)
        return mesh

    def generateBottomClip(self):
        origin = np.array((0, 0, 0))
        base = (
            self.generateBottomMagnetConnector(origin)
            .compute_normals(consistent_normals=True, auto_orient_normals=True)
            .subdivide(nsub=2)
        )
        for i in range(2):
            magnetOrigin = np.array(
                (
                    origin[0]
                    - self.distanceBetweenMagnetsInClip / 2
                    + i * self.distanceBetweenMagnetsInClip,
                    origin[1],
                    origin[2] + self.magnetClipThickness + self.magnetThickness / 2,
                )
            )
            magnet = (
                self.polygonalPrism(
                    radius=self.magnetRadius,
                    res=30,
                    height=self.magnetThickness,
                    origin=magnetOrigin,
                )
                .subdivide(nsub=1)
                .compute_normals()
            )
            outerMagnet = (
                self.polygonalPrism(
                    radius=self.magnetRadius + self.magnetClipRingThickness,
                    res=30,
                    height=self.magnetThickness,
                    origin=magnetOrigin,
                )
                .subdivide(nsub=1)
                .compute_normals()
            )

            magnetHolder = self.booleanOp(outerMagnet, magnet, "difference")
            base = self.booleanOp(base, magnetHolder, "union")
        base.save(f"{self.userDir}/bottomClip.stl")
        return base

    def generateSlot(self, origin: np.array, width, height, r):
        resolution = 30
        vertices = []
        lower_bound = int(resolution / 2)
        thetas = np.pi / resolution * np.arange(lower_bound) - np.pi / 2
        vertices.extend(
            np.column_stack(
                (
                    r * np.cos(thetas) + height / 2 + origin[0],
                    r * np.sin(thetas) + origin[1] - self.magnetClipRingThickness * 2,
                    np.full(lower_bound, origin[2]),
                )
            ).tolist()
        )
        thetas = np.pi / resolution * np.arange(lower_bound, resolution) - np.pi / 2
        vertices.extend(
            np.column_stack(
                (
                    r * np.cos(thetas) + height / 2 + origin[0],
                    r * np.sin(thetas) + origin[1] + width,
                    np.full(resolution - lower_bound, origin[2]),
                )
            ).tolist()
        )

        lower_bound = int(resolution / 2)
        thetas = np.pi / 2 - np.pi / resolution * np.arange(lower_bound)
        vertices.extend(
            np.column_stack(
                (
                    -r * np.cos(thetas) - height / 2 + origin[0],
                    r * np.sin(thetas) + origin[1] + width,
                    np.full(lower_bound, origin[2]),
                )
            ).tolist()
        )
        thetas = np.pi / 2 - np.pi / resolution * np.arange(lower_bound, resolution)
        vertices.extend(
            np.column_stack(
                (
                    -r * np.cos(thetas) - height / 2 + origin[0],
                    r * np.sin(thetas) + origin[1] - self.magnetClipRingThickness * 2,
                    np.full(resolution - lower_bound, origin[2]),
                )
            ).tolist()
        )
        vertices.append(origin)
        faces = [
            (3, len(vertices) - 1, i, (i + 1) % (2 * resolution))
            for i in range(2 * resolution)
        ]
        return vertices, faces

    def generateMount(self):
        base = self.genMountBlank(40).subdivide(nsub=2).compute_normals()
        tol = 2
        anglePoint = np.array(
            (
                np.cos(self.mountBottomAngleOpening / 2),
                np.sin(self.mountBottomAngleOpening / 2),
                self.magnetThickness / 2,
            )
        )
        anglePoint1 = np.array(
            (
                np.cos(-self.mountBottomAngleOpening / 2),
                np.sin(-self.mountBottomAngleOpening / 2),
                self.magnetThickness / 2,
            )
        )
        anglePointMag = np.linalg.norm(anglePoint)
        for i in range(self.numMangetsInRing):
            theta = 2 * np.pi / self.numMangetsInRing * i
            if theta < self.mountBottomAngleOpening / 2 or theta > (
                2 * np.pi - (self.mountBottomAngleOpening / 2)
            ):
                continue
            magOg = (
                self.magnetRingRadius * np.cos(theta),
                self.magnetRingRadius * np.sin(theta),
                self.magnetThickness / 2,
            )
            if theta < np.pi:
                proj = np.dot(magOg, anglePoint) / anglePointMag
                projPoint = proj * anglePoint / anglePointMag
                dist = np.linalg.norm(magOg - projPoint)
            else:
                proj = np.dot(magOg, anglePoint1) / anglePointMag
                projPoint = proj * anglePoint1 / anglePointMag
                dist = np.linalg.norm(magOg - projPoint)
            if (dist - self.magnetRadius) < tol:
                continue
            magnetHole = (
                self.polygonalPrism(
                    radius=self.magnetRadius,
                    res=30,
                    height=self.magnetThickness,
                    origin=magOg,
                )
                .subdivide(nsub=1)
                .compute_normals()
            )
            base = self.booleanOp(base, magnetHole, "difference")
        return base

    def genMountBlank(self, res):
        thetas = np.arange(res) * 2 * np.pi / res
        innerCircle = np.column_stack(
            (
                np.cos(thetas) * self.mountRadius,
                np.sin(thetas) * self.mountRadius,
                np.full(res, 0),
            )
        )
        outerCircle = np.column_stack(
            (
                np.cos(thetas) * (self.mountRadius + self.mountShellThickness),
                np.sin(thetas) * (self.mountRadius + self.mountShellThickness),
                np.full(res, 0),
            )
        )
        brimCircle = np.column_stack(
            (
                np.cos(thetas)
                * (self.magnetRingRadius + self.brim + self.magnetRadius),
                np.sin(thetas)
                * (self.magnetRingRadius + self.brim + self.magnetRadius),
                np.full(res, 0),
            )
        )
        outerCircleOffset = np.column_stack(
            (
                np.cos(thetas) * (self.mountRadius + self.mountShellThickness),
                np.sin(thetas) * (self.mountRadius + self.mountShellThickness),
                np.full(res, self.magnetThickness + self.mountShellThickness),
            )
        )
        brimCircleOffset = np.column_stack(
            (
                np.cos(thetas)
                * (self.magnetRingRadius + self.brim + self.magnetRadius),
                np.sin(thetas)
                * (self.magnetRingRadius + self.brim + self.magnetRadius),
                np.full(res, self.magnetThickness + self.mountShellThickness),
            )
        )
        innerCircleOffset = np.column_stack(
            (
                np.cos(thetas) * self.mountRadius,
                np.sin(thetas) * self.mountRadius,
                np.full(res, self.magnetThickness + self.mountShellThickness),
            )
        )
        topInnerCircle = np.column_stack(
            (
                np.cos(thetas) * self.mountRadius,
                np.sin(thetas) * self.mountRadius,
                np.full(res, self.mountHeight + self.mountShellThickness),
            )
        )
        topOuterCircle = np.column_stack(
            (
                np.cos(thetas) * (self.mountRadius + self.mountShellThickness),
                np.sin(thetas) * (self.mountRadius + self.mountShellThickness),
                np.full(res, self.mountHeight + self.mountShellThickness),
            )
        )
        topInnerCircleBottom = np.column_stack(
            (
                np.cos(thetas) * self.mountRadius,
                np.sin(thetas) * self.mountRadius,
                np.full(res, self.mountHeight),
            )
        )
        bottomCenter = np.array((0, 0, self.mountHeight))
        topCenter = np.array((0, 0, self.mountHeight + self.mountShellThickness))
        verts = np.vstack(
            (
                outerCircle,
                brimCircle,
                outerCircleOffset,
                brimCircleOffset,
                innerCircle,
                innerCircleOffset,
                topOuterCircle,
                topInnerCircle,
                topInnerCircleBottom,
                bottomCenter,
                topCenter,
            )
        )
        totalFaces = []

        startIndex = int(
            np.ceil((self.mountBottomAngleOpening / 2) / (2 * np.pi / res))
        )
        endIndex = res - startIndex

        brimIdxOffset = res * 2
        brimEdgeOffset = res
        innerCircleOffset = res * 4
        offsetTopBrim = res * 2
        offsetTopOuter = res * 6
        offsetTopInnerBottom = res * 8
        offsetInnerCircleOffset = res * 5
        offsetTopInner = res * 7

        # brim
        if self.mountBottomAngleOpening != 0:
            for i in range(startIndex, endIndex):
                # bottom of brim
                totalFaces.append((3, i, (i + 1) % res, i + res))
                totalFaces.append((3, i + res, (i + 1) % res + res, (i + 1) % res))

                # top of brim
                totalFaces.append(
                    (
                        3,
                        i + brimIdxOffset,
                        (i + 1) % res + brimIdxOffset,
                        i + res + brimIdxOffset,
                    )
                )
                totalFaces.append(
                    (
                        3,
                        i + res + brimIdxOffset,
                        (i + 1) % res + res + brimIdxOffset,
                        (i + 1) % res + brimIdxOffset,
                    )
                )

                # inner bottom ring
                totalFaces.append((3, i, i + 1, i + innerCircleOffset))
                totalFaces.append(
                    (3, i + innerCircleOffset, i + 1 + innerCircleOffset, i + 1)
                )

                # brim outer edge
                totalFaces.append(
                    (
                        3,
                        i + brimEdgeOffset,
                        (i + 1) % res + brimEdgeOffset,
                        i + brimIdxOffset + brimEdgeOffset,
                    )
                )
                totalFaces.append(
                    (
                        3,
                        i + brimIdxOffset + brimEdgeOffset,
                        i + 1 + brimIdxOffset + brimEdgeOffset,
                        i + 1 + brimEdgeOffset,
                    )
                )

                # brim inner edge
                totalFaces.append(
                    (
                        3,
                        i + innerCircleOffset,
                        i + 1 + innerCircleOffset,
                        i + innerCircleOffset + res,
                    )
                )
                totalFaces.append(
                    (
                        3,
                        i + innerCircleOffset + res,
                        i + 1 + innerCircleOffset + res,
                        i + 1 + innerCircleOffset,
                    )
                )

            totalFaces.append((3, startIndex, startIndex + res, startIndex + res * 2))
            totalFaces.append(
                (3, startIndex + res * 2, startIndex + res * 3, startIndex + res)
            )
            totalFaces.append((3, endIndex, endIndex + res, endIndex + res * 2))
            totalFaces.append(
                (3, endIndex + res * 2, endIndex + res * 3, endIndex + res)
            )

            totalFaces.append(
                (3, startIndex, startIndex + res * 2, startIndex + innerCircleOffset)
            )
            totalFaces.append(
                (
                    3,
                    startIndex + innerCircleOffset,
                    startIndex + innerCircleOffset + res,
                    startIndex + res * 2,
                )
            )
            totalFaces.append(
                (3, endIndex, endIndex + res * 2, endIndex + innerCircleOffset)
            )
            totalFaces.append(
                (
                    3,
                    endIndex + innerCircleOffset,
                    endIndex + innerCircleOffset + res,
                    endIndex + res * 2,
                )
            )

            # top ring of brim
            for i in range(startIndex):
                totalFaces.append(
                    (
                        3,
                        i + offsetTopBrim,
                        (i + 1) % res + offsetTopBrim,
                        i + res * 3 + offsetTopBrim,
                    )
                )
                totalFaces.append(
                    (
                        3,
                        i + res * 3 + offsetTopBrim,
                        (i + 1) % res + res * 3 + offsetTopBrim,
                        (i + 1) % res + offsetTopBrim,
                    )
                )
            for i in range(endIndex, res):
                totalFaces.append(
                    (
                        3,
                        i + offsetTopBrim,
                        (i + 1) % res + offsetTopBrim,
                        i + res * 3 + offsetTopBrim,
                    )
                )
                totalFaces.append(
                    (
                        3,
                        i + res * 3 + offsetTopBrim,
                        (i + 1) % res + res * 3 + offsetTopBrim,
                        (i + 1) % res + offsetTopBrim,
                    )
                )
        else:
            for i in range(res):
                # bottom of brim
                totalFaces.append((3, i, (i + 1) % res, i + res))
                totalFaces.append((3, i + res, (i + 1) % res + res, (i + 1) % res))

                # top of brim
                totalFaces.append(
                    (
                        3,
                        i + brimIdxOffset,
                        (i + 1) % res + brimIdxOffset,
                        i + res + brimIdxOffset,
                    )
                )
                totalFaces.append(
                    (
                        3,
                        i + res + brimIdxOffset,
                        (i + 1) % res + res + brimIdxOffset,
                        (i + 1) % res + brimIdxOffset,
                    )
                )

                # inner bottom ring
                totalFaces.append((3, i, (i + 1) % res, i + innerCircleOffset))
                totalFaces.append(
                    (
                        3,
                        i + innerCircleOffset,
                        (i + 1) % res + innerCircleOffset,
                        (i + 1) % res,
                    )
                )

                # brim outer edge
                totalFaces.append(
                    (
                        3,
                        i + brimEdgeOffset,
                        (i + 1) % res + brimEdgeOffset,
                        i + brimIdxOffset + brimEdgeOffset,
                    )
                )
                totalFaces.append(
                    (
                        3,
                        i + brimIdxOffset + brimEdgeOffset,
                        (i + 1) % res + brimIdxOffset + brimEdgeOffset,
                        (i + 1) % res + brimEdgeOffset,
                    )
                )

                # brim inner edge
                totalFaces.append(
                    (
                        3,
                        i + innerCircleOffset,
                        (i + 1) % res + innerCircleOffset,
                        i + innerCircleOffset + res,
                    )
                )
                totalFaces.append(
                    (
                        3,
                        i + innerCircleOffset + res,
                        (i + 1) % res + innerCircleOffset + res,
                        (i + 1) % res + innerCircleOffset,
                    )
                )

        # top cylindrical portion
        for i in range(res):
            # outer wall
            totalFaces.append(
                (
                    3,
                    i + offsetTopBrim,
                    (i + 1) % res + offsetTopBrim,
                    i + offsetTopOuter,
                )
            )
            totalFaces.append(
                (
                    3,
                    i + offsetTopOuter,
                    (i + 1) % res + offsetTopOuter,
                    (i + 1) % res + offsetTopBrim,
                )
            )

            # inner wall
            totalFaces.append(
                (
                    3,
                    i + offsetInnerCircleOffset,
                    (i + 1) % res + offsetInnerCircleOffset,
                    i + offsetTopInnerBottom,
                )
            )
            totalFaces.append(
                (
                    3,
                    i + offsetTopInnerBottom,
                    (i + 1) % res + offsetTopInnerBottom,
                    (i + 1) % res + offsetInnerCircleOffset,
                )
            )

            # top outer room
            totalFaces.append(
                (
                    3,
                    i + offsetTopOuter,
                    (i + 1) % res + offsetTopOuter,
                    i + offsetTopInner,
                )
            )
            totalFaces.append(
                (
                    3,
                    i + offsetTopInner,
                    (i + 1) % res + offsetTopInner,
                    (i + 1) % res + offsetTopOuter,
                )
            )

        startIndex = int(np.ceil((self.mountTopAngleOpening / 2) / (2 * np.pi / res)))
        endIndex = res - startIndex
        offsetBottomCenter = len(verts) - 2
        offsetTopCenter = len(verts) - 1
        if self.mountTopAngleOpening != 0:
            for i in range(startIndex, endIndex):
                # bottom face
                totalFaces.append(
                    (
                        3,
                        i + offsetTopInnerBottom,
                        (i + 1) % res + offsetTopInnerBottom,
                        offsetBottomCenter,
                    )
                )
                # top face
                totalFaces.append(
                    (
                        3,
                        i + offsetTopInner,
                        (i + 1) % res + offsetTopInner,
                        offsetTopCenter,
                    )
                )

            for i in range(startIndex):
                totalFaces.append(
                    (
                        3,
                        i + offsetTopInnerBottom,
                        (i + 1) % res + offsetTopInnerBottom,
                        i + offsetTopInner,
                    )
                )
                totalFaces.append(
                    (
                        3,
                        i + offsetTopInner,
                        (i + 1) % res + offsetTopInner,
                        (i + 1) % res + offsetTopInnerBottom,
                    )
                )
            for i in range(endIndex, res):
                totalFaces.append(
                    (
                        3,
                        i + offsetTopInnerBottom,
                        (i + 1) % res + offsetTopInnerBottom,
                        i + offsetTopInner,
                    )
                )
                totalFaces.append(
                    (
                        3,
                        i + offsetTopInner,
                        (i + 1) % res + offsetTopInner,
                        (i + 1) % res + offsetTopInnerBottom,
                    )
                )

            totalFaces.append(
                (
                    3,
                    offsetBottomCenter,
                    startIndex + offsetTopInnerBottom,
                    startIndex + offsetTopInner,
                )
            )
            totalFaces.append(
                (3, startIndex + offsetTopInner, offsetTopCenter, offsetBottomCenter)
            )

            totalFaces.append(
                (
                    3,
                    offsetBottomCenter,
                    endIndex + offsetTopInnerBottom,
                    endIndex + offsetTopInner,
                )
            )
            totalFaces.append(
                (3, endIndex + offsetTopInner, offsetTopCenter, offsetBottomCenter)
            )
        else:
            for i in range(res):
                # bottom face
                totalFaces.append(
                    (
                        3,
                        i + offsetTopInnerBottom,
                        (i + 1) % res + offsetTopInnerBottom,
                        offsetBottomCenter,
                    )
                )
                # top face
                totalFaces.append(
                    (
                        3,
                        i + offsetTopInner,
                        (i + 1) % res + offsetTopInner,
                        offsetTopCenter,
                    )
                )

        mesh = pv.PolyData(verts, totalFaces)
        return mesh

    def generateTopClip(self):
        # the origin centers at the mid point of the line connecting the two magnets
        origin = np.array((0, 0, 0))
        width = (
            self.distanceBetweenMagnetClipAndSlot
            + self.magnetRadius * 2
            + self.magnetClipRingThickness * 3
        )
        height = (
            4 * self.magnetClipRingThickness
            + 2 * self.magnetRadius
            + self.distanceBetweenMagnetsInClip
        )
        r = 2 * self.magnetClipRingThickness + self.magnetRadius

        bottomVerts, bottomFaces = self.generateSlot(origin, width, height, r)
        topHalfOrigin = np.array(
            (
                origin[0],
                origin[1],
                origin[2] + self.magnetClipThickness + self.magnetThickness * 2,
            )
        )
        topVerts, topFaces = self.generateSlot(topHalfOrigin, width, height, r)
        totalVerts = []
        totalFaces = []
        totalVerts.extend(bottomVerts)
        totalVerts.extend(topVerts)
        totalFaces.extend(bottomFaces)
        offset = len(bottomVerts)
        for i, face in enumerate(topFaces):
            topFaces[i] = (3, face[1] + offset, face[2] + offset, face[3] + offset)
        totalFaces.extend(topFaces)
        offset = len(bottomVerts)
        loopAround = len(bottomVerts) - 1
        for i in range(len(bottomVerts) - 1):
            totalFaces.append((3, i, i + offset, (i + 1) % loopAround + offset))
            totalFaces.append(
                (3, (i + 1) % loopAround + offset, (i + 1) % loopAround, i)
            )
        base = pv.PolyData(totalVerts, totalFaces).compute_normals(
            consistent_normals=True, auto_orient_normals=True
        )

        # Create holes for magnets and bottom clip
        for i in range(2):
            magnetOrigin = np.array(
                (
                    origin[0]
                    - self.distanceBetweenMagnetsInClip / 2
                    + i * self.distanceBetweenMagnetsInClip,
                    origin[1],
                    origin[2] + self.magnetClipThickness + self.magnetThickness * 3 / 2,
                )
            )
            magnetHolder = self.polygonalPrism(
                radius=self.magnetRadius + self.magnetClipRingThickness,
                res=20,
                height=self.magnetThickness,
                origin=magnetOrigin,
            ).compute_normals(consistent_normals=True, auto_orient_normals=True)

            base = self.booleanOp(base, magnetHolder, "difference")

            magnetOrigin = np.array(
                (
                    origin[0]
                    - self.distanceBetweenMagnetsInClip / 2
                    + i * self.distanceBetweenMagnetsInClip,
                    origin[1],
                    origin[2] + self.magnetClipThickness + self.magnetThickness / 2,
                )
            )
            magnet = self.polygonalPrism(
                radius=self.magnetRadius,
                res=20,
                height=self.magnetThickness,
                origin=magnetOrigin,
            ).compute_normals(consistent_normals=True, auto_orient_normals=True)

            base = self.booleanOp(base, magnet, "difference")

        # Create slot
        slotOrigin = np.array(
            (
                origin[0],
                origin[1]
                + self.distanceBetweenMagnetClipAndSlot
                + self.magnetRadius
                + self.magnetClipRingThickness
                + self.slotHeight / 2,
                origin[2],
            )
        )
        bottomVerts, bottomFaces = self.generateSlot(
            slotOrigin, self.slotHeight, self.slotWidth, self.slotHeight / 2
        )
        topHalfOrigin = slotOrigin + np.array(
            (0, 0, self.magnetClipThickness + self.magnetThickness * 2)
        )
        topVerts, topFaces = self.generateSlot(
            topHalfOrigin, self.slotHeight, self.slotWidth, self.slotHeight / 2
        )
        totalVerts = []
        totalFaces = []
        totalVerts.extend(bottomVerts)
        totalVerts.extend(topVerts)
        totalFaces.extend(bottomFaces)
        offset = len(bottomVerts)
        for i, face in enumerate(topFaces):
            topFaces[i] = (3, face[1] + offset, face[2] + offset, face[3] + offset)
        totalFaces.extend(topFaces)
        offset = len(bottomVerts)
        loopAround = len(bottomVerts) - 1
        for i in range(len(bottomVerts) - 1):
            totalFaces.append((3, i, i + offset, (i + 1) % loopAround + offset))
            totalFaces.append(
                (3, (i + 1) % loopAround + offset, (i + 1) % loopAround, i)
            )
        slot = pv.PolyData(totalVerts, totalFaces).compute_normals(
            consistent_normals=True, auto_orient_normals=True
        )

        base = self.booleanOp(base, slot, "difference")
        base.save(f"{self.userDir}/topClip.stl")
        return base


if __name__ == "__main__":
    print("Testing")
    test = Generator()
    test.generateBottomClip()
