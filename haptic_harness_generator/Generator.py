import numpy as np
import pyvista as pv
import ezdxf

from vtkbool.vtkBool import vtkPolyDataBooleanFilter


class Generator:
    def __init__(self, userDir):
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
        self.distanceBetweenMagnetsInClip = (
            2 * (self.magnetRadius + self.magnetClipThickness) + 4
        )
        self.distanceBetweenMagnetClipAndPolygonEdge = 3
        self.distanceBetweenMagnetClipAndSlot = 3
        self.foamThickness = 1

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
        if attrName == "numSides":
            setattr(self, attrName, int(val))
        else:
            setattr(self, attrName, float(val))

    def genCenter(self, msp):
        vertices = []
        pyVistaLines = []
        pyVistaVertices = []
        for i in range(6):
            theta = 2 * np.pi / 6 * i
            vertices.append(
                [
                    self.tactorRadius * np.cos(theta),
                    self.tactorRadius * np.sin(theta),
                    0,
                ]
            )
            pyVistaVertices.append(
                [
                    self.tactorRadius * np.cos(theta),
                    self.tactorRadius * np.sin(theta),
                    0,
                ]
            )
        for i in range(6):
            msp.add_line(vertices[i], vertices[(i + 1) % 6])
            pyVistaLines.append((2, i, (i + 1) % 6))
        return (pyVistaVertices, pyVistaLines)

    def generateTyvekTile(self):
        def genFlap(msp):
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
                + self.magnetClipThickness
            )
            for j in range(2):
                for i in range(resolution):
                    r = self.magnetRadius + self.magnetClipThickness
                    v1 = [
                        r * np.cos(2 * np.pi / resolution * i)
                        + self.distanceBetweenMagnetsInClip / 2 * (-1) ** j,
                        r * np.sin(2 * np.pi / resolution * i) + yOffset,
                    ]
                    v2 = [
                        r * np.cos(2 * np.pi / resolution * (i + 1))
                        + self.distanceBetweenMagnetsInClip / 2 * (-1) ** j,
                        r * np.sin(2 * np.pi / resolution * (i + 1)) + yOffset,
                    ]
                    lines.append((v1, v2))

            # slot
            yOffset = (
                self.distanceBetweenMagnetClipAndPolygonEdge
                + self.concentricPolygonRadius
                + 2 * (self.magnetRadius + self.magnetClipThickness)
                + self.distanceBetweenMagnetClipAndSlot
            )
            lines.append(
                ([-self.slotWidth / 2, yOffset], [self.slotWidth / 2, yOffset])
            )
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
                    + 2 * (self.magnetRadius + self.magnetClipThickness)
                    + self.distanceBetweenMagnetClipAndSlot
                    + self.slotHeight / 2
                )
                for j in range(2):
                    for i in range(resolution):
                        currTheta = (np.pi / 2 + initTheta) / resolution * i - initTheta
                        v1 = [
                            (-1) ** j
                            * (
                                self.slotBorderRadius * np.cos(currTheta)
                                + self.slotWidth / 2
                            ),
                            self.slotBorderRadius * np.sin(currTheta) + yOffset,
                        ]
                        nextTheta = (np.pi / 2 + initTheta) / resolution * (
                            i + 1
                        ) - initTheta
                        v2 = [
                            (-1) ** j
                            * (
                                self.slotBorderRadius * np.cos(nextTheta)
                                + self.slotWidth / 2
                            ),
                            self.slotBorderRadius * np.sin(nextTheta) + yOffset,
                        ]
                        lines.append((v1, v2))
                        if i == 0:
                            lines.append(
                                (
                                    [
                                        (-1) ** j * polygonSideHalf,
                                        self.concentricPolygonRadius,
                                    ],
                                    v1,
                                )
                            )
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
                    + 2 * (self.magnetRadius + self.magnetClipThickness)
                    + self.distanceBetweenMagnetClipAndSlot
                    + self.slotHeight
                    + self.slotBorderRadius
                )
                lines.append(([polygonSideHalf, yOffset], [-polygonSideHalf, yOffset]))
            return lines

        doc = ezdxf.new(dxfversion="AC1015")
        msp = doc.modelspace()
        pvVerts, pvLines = self.genCenter(msp)
        for i in range(self.numSides):
            theta = 2 * np.pi / self.numSides * i
            lines = genFlap(msp)
            rotationalMatrix = np.matrix(
                [[np.cos(theta), np.sin(theta)], [-np.sin(theta), np.cos(theta)]]
            )
            for k, pair in enumerate(lines):
                v1 = rotationalMatrix * np.array(pair[0]).reshape((-1, 1))
                v2 = rotationalMatrix * np.array(pair[1]).reshape((-1, 1))
                msp.add_line(v1, v2)
                offset = len(pvVerts)
                pvVerts.append((v1[0].item(), v1[1].item(), 0))
                pvVerts.append((v2[0].item(), v2[1].item(), 0))
                pvLines.append((2, offset, offset + 1))
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

    def generateMagnetRing(self):
        def genMagnetHoles(msp, pvVerts, pvLines):
            resolution = 30
            for i in range(self.numMangetsInRing):
                theta = 2 * np.pi / self.numMangetsInRing * i
                for j in range(resolution):
                    currTheta = 2 * np.pi / resolution * j
                    v1 = [
                        self.magnetRadius * np.cos(currTheta)
                        + np.cos(theta) * self.magnetRingRadius,
                        self.magnetRadius * np.sin(currTheta)
                        + np.sin(theta) * self.magnetRingRadius,
                    ]
                    nextTheta = 2 * np.pi / resolution * (j + 1)
                    v2 = [
                        self.magnetRadius * np.cos(nextTheta)
                        + np.cos(theta) * self.magnetRingRadius,
                        self.magnetRadius * np.sin(nextTheta)
                        + np.sin(theta) * self.magnetRingRadius,
                    ]
                    msp.add_line(v1, v2)
                    offset = len(pvVerts)
                    pvVerts.append((v1[0].item(), v1[1].item(), 0))
                    pvVerts.append((v2[0].item(), v2[1].item(), 0))
                    pvLines.append((2, offset, offset + 1))
            return (pvVerts, pvLines)

        doc = ezdxf.new(dxfversion="AC1015")
        msp = doc.modelspace()
        pvVerts, pvLines = self.genCenter(msp)
        pvVerts, pvLines = self.genOuterPolygon(msp, pvVerts, pvLines)
        pvVerts, pvLines = genMagnetHoles(msp, pvVerts, pvLines)
        doc.saveas(f"{self.userDir}/magnetRing.dxf")

        mesh = pv.PolyData()
        mesh.points = pvVerts
        mesh.lines = pvLines
        return mesh

    def polygonalPrism(self, radius, res, height, origin):
        totalVerts = []
        totalFaces = []
        thetaInterval = 2 * np.pi / res
        for i in range(res):
            totalVerts.append(
                (
                    radius * np.cos(thetaInterval * i) + origin[0],
                    radius * np.sin(thetaInterval * i) + origin[1],
                    -height / 2 + origin[2],
                )
            )
        for i in range(res):
            totalVerts.append(
                (
                    radius * np.cos(thetaInterval * i) + origin[0],
                    radius * np.sin(thetaInterval * i) + origin[1],
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
        prism = self.polygonalPrismSlanted(
            radiusBottom=self.tactorRadius,
            radiusTop=self.tactorRadius * 0.8,
            res=6,
            height=prismHeight,
            origin=(0, 0, self.magnetThickness / 2 + 1 + prismHeight / 2),
        )
        base = (
            self.polygonalPrism(
                radius=self.concentricPolygonRadius * 2,
                res=40,
                height=self.magnetThickness + 2,
                origin=(0, 0, 0),
            )
            .subdivide(nsub=4)
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
                radius=self.concentricPolygonRadius * 2,
                res=40,
                height=self.foamThickness,
                origin=(0, 0, self.magnetThickness / 2 + 1 + self.foamThickness / 2),
            )
            .subdivide(nsub=3)
            .compute_normals()
        )
        foamCavity = (
            self.polygonalPrism(
                radius=self.concentricPolygonRadius,
                res=self.numSides,
                height=self.foamThickness,
                origin=(0, 0, self.magnetThickness / 2 + 1 + self.foamThickness / 2),
            )
            .subdivide(nsub=3)
            .compute_normals()
        )
        outerBaseWithHole = self.booleanOp(outerBase, foamCavity, "difference")
        finalMesh = self.booleanOp(outerBaseWithHole, bottomBase, "union")
        finalMesh.save(f"{self.userDir}/base.stl")
        return finalMesh

    def generateBottomMagnetConnector(self, origin: np.array):
        def generateMagneticConnectorHalf(origin: np.array):
            resolution = 30
            vertices = []
            faces = []
            for i in range(resolution):
                theta = np.pi / resolution * i - np.pi / 2
                r = self.magnetRadius + self.magnetClipThickness
                vertices.append(
                    (
                        r * np.cos(theta)
                        + self.distanceBetweenMagnetsInClip / 2
                        + origin[0],
                        r * np.sin(theta) + origin[1],
                        origin[2],
                    )
                )
            for i in range(resolution):
                theta = np.pi / 2 - np.pi / resolution * i
                r = self.magnetRadius + self.magnetClipThickness
                vertices.append(
                    (
                        -r * np.cos(theta)
                        - self.distanceBetweenMagnetsInClip / 2
                        + origin[0],
                        r * np.sin(theta) + origin[1],
                        origin[2],
                    )
                )
            vertices.append(origin)
            for i in range(2 * resolution):
                faces.append((3, len(vertices) - 1, i, (i + 1) % (2 * resolution)))
            return vertices, faces

        bottomVerts, bottomFaces = generateMagneticConnectorHalf(origin)
        topHalfOrigin = np.array(
            (origin[0], origin[1], origin[2] + self.magnetClipThickness)
        )
        topVerts, topFaces = generateMagneticConnectorHalf(topHalfOrigin)
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
                    radius=self.magnetRadius + self.magnetClipThickness,
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

    def generateTopClip(self):
        # the origin centers at the mid point of the line connecting the two magnets
        def generateSlot(origin: np.array, width, height, r):
            resolution = 30
            vertices = []
            faces = []
            for i in range(resolution):
                theta = np.pi / resolution * i - np.pi / 2
                if i < resolution / 2:
                    vertices.append(
                        (
                            r * np.cos(theta) + height / 2 + origin[0],
                            r * np.sin(theta)
                            + origin[1]
                            - self.magnetClipThickness * 2,
                            origin[2],
                        )
                    )
                else:
                    vertices.append(
                        (
                            r * np.cos(theta) + height / 2 + origin[0],
                            r * np.sin(theta) + origin[1] + width,
                            origin[2],
                        )
                    )
            for i in range(resolution):
                theta = np.pi / 2 - np.pi / resolution * i
                if i < resolution / 2:
                    vertices.append(
                        (
                            -r * np.cos(theta) - height / 2 + origin[0],
                            r * np.sin(theta) + origin[1] + width,
                            origin[2],
                        )
                    )
                else:
                    vertices.append(
                        (
                            -r * np.cos(theta) - height / 2 + origin[0],
                            r * np.sin(theta)
                            + origin[1]
                            - self.magnetClipThickness * 2,
                            origin[2],
                        )
                    )
            vertices.append(origin)
            for i in range(2 * resolution):
                faces.append((3, len(vertices) - 1, i, (i + 1) % (2 * resolution)))
            return vertices, faces

        origin = np.array((0, 0, 0))
        width = (
            self.distanceBetweenMagnetClipAndSlot
            + self.magnetRadius * 2
            + self.magnetClipThickness * 3
        )
        height = (
            4 * self.magnetClipThickness
            + 2 * self.magnetRadius
            + self.distanceBetweenMagnetsInClip
        )
        r = 2 * self.magnetClipThickness + self.magnetRadius

        bottomVerts, bottomFaces = generateSlot(origin, width, height, r)
        topHalfOrigin = np.array(
            (
                origin[0],
                origin[1],
                origin[2] + self.magnetClipThickness + self.magnetThickness * 2,
            )
        )
        topVerts, topFaces = generateSlot(topHalfOrigin, width, height, r)
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
                radius=self.magnetRadius + self.magnetClipThickness,
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
                + self.magnetClipThickness
                + self.slotHeight / 2,
                origin[2],
            )
        )
        bottomVerts, bottomFaces = generateSlot(
            slotOrigin, self.slotHeight, self.slotWidth, self.slotHeight / 2
        )
        topHalfOrigin = slotOrigin + np.array(
            (0, 0, self.magnetClipThickness + self.magnetThickness * 2)
        )
        topVerts, topFaces = generateSlot(
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
