"""Build the courtyard in Blender and export the WebGL asset.

Run from any directory:
  Blender --background --python-exit-code 1 --python tools/build_courtyard.py
"""
import math
import random
import struct
import sys
import tempfile
import zlib
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
rng = random.Random(781)
noise_rng = np.random.default_rng(601)
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.unit_settings.system = 'METRIC'


def collection(name, parent=scene.collection):
    group = bpy.data.collections.new(name)
    parent.children.link(group)
    return group


courtyard = collection('Khu B | Mở rộng')
site = collection('01 | Sân vườn và lối đi', courtyard)
low_wing = collection('02 | Nhà hai tầng', courtyard)
faculty = collection('03 | Khoa Công nghệ Hóa học và Thực phẩm', courtyard)
tower = collection('04 | Giảng đường gạch đỏ', courtyard)
furniture = collection('05 | Bàn ghế và bồn cây', courtyard)
parking = collection('06 | Bãi xe', courtyard)
utilities = collection('07 | Điện và chiếu sáng', courtyard)
trees = collection('08 | Cây và thảm thực vật', courtyard)
physics = collection('09 | Va chạm và bậc thềm', courtyard)


def periodic_noise(grid_x, grid_y, size):
    grid = noise_rng.random((grid_y, grid_x))
    x = np.arange(size) * grid_x / size
    y = np.arange(size) * grid_y / size
    ix = x.astype(int)
    iy = y.astype(int)
    fx = x - ix
    fy = y - iy
    fx = fx * fx * (3 - 2 * fx)
    fy = fy * fy * (3 - 2 * fy)
    a = grid[iy[:, None], ix] * (1 - fx) + grid[iy[:, None], (ix + 1) % grid_x] * fx
    b = grid[((iy + 1) % grid_y)[:, None], ix] * (1 - fx) + grid[((iy + 1) % grid_y)[:, None], (ix + 1) % grid_x] * fx
    return a * (1 - fy[:, None]) + b * fy[:, None] - 0.5


def packed_image(name, rgb):
    height, width, _ = rgb.shape
    pixels = np.clip(rgb * 255, 0, 255).astype('uint8')

    def chunk(tag, data):
        return struct.pack('>I', len(data)) + tag + data + struct.pack('>I', zlib.crc32(tag + data))

    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / (name + '.png')
        raw = b''.join(b'\x00' + row.tobytes() for row in pixels)
        path.write_bytes(b'\x89PNG\r\n\x1a\n' +
                         chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0)) +
                         chunk(b'IDAT', zlib.compress(raw, 6)) + chunk(b'IEND', b''))
        image = bpy.data.images.load(str(path))
        image.pack()
        image.filepath = '//' + path.name
    return image


def texture(name, base, style, size=512):
    y, x = np.mgrid[:size, :size] / size
    coarse = periodic_noise(7, 7, size)
    medium = periodic_noise(38, 38, size)
    grain = noise_rng.random((size, size)) - .5
    base = np.array(base)
    value = coarse * .11 + medium * .09 + grain * .07
    if style in ('brick', 'tile'):
        cols, rows = (8, 12) if style == 'brick' else (16, 8)
        bx = x * cols + (np.floor(y * rows) % 2) * (.5 if style == 'brick' else 0)
        by = y * rows
        dx = np.abs(bx % 1 - .5)
        dy = np.abs(by % 1 - .5)
        mortar = np.clip((np.maximum(dx, dy) - .447) / .04, 0, 1)
        tile_value = noise_rng.uniform(-.1, .1, (rows, cols))
        value = value + tile_value[by.astype(int), bx.astype(int) % cols]
        face = base + value[:, :, None]
        return packed_image(name, face * (1 - mortar[:, :, None]) + mortar[:, :, None] * (.49, .40, .32))
    if style == 'paving':
        u = (x * 4) % 1
        v = (y * 4) % 1
        edge = np.maximum(np.abs(u - .5), np.abs(v - .5))
        upside = np.floor(x * 4 + np.floor(y * 4)) % 2 == 0
        a, b = np.where(upside, u, v), np.where(upside, v, u)
        rr = np.hypot(np.maximum(np.abs(a - .5) - .19, 0), np.maximum(np.abs(b - .5) - .08, 0)) - .15
        groove = np.exp(-((rr / .021) ** 2))
        inner = np.exp(-(((rr + .105) / .019) ** 2))
        seam = np.clip((edge - .463) / .031, 0, 1)
        value += -.20 * seam - .12 * groove - .075 * inner + .024 * np.exp(-(((rr - .033) / .018) ** 2))
        value += periodic_noise(4, 4, size) * .07
    elif style == 'plaster':
        runoff = periodic_noise(64, 3, size)
        value += runoff * (.25 * (coarse + .5)) - np.maximum(coarse, 0) * .15
    elif style == 'bark':
        value = periodic_noise(36, 4, size) * .25 + periodic_noise(99, 7, size) * .19 + medium * .09 + grain * .09
        value += np.maximum(coarse - .1, 0) * .35 + periodic_noise(24, 72, size)*.13
    elif style == 'stone':
        value += -np.maximum(medium + grain * .36 - .25, 0) * .48
    elif style in ('lawn', 'soil', 'gravel'):
        value = coarse * .23 + medium * .19 + grain * .12
        value += np.sin((y + medium * .045) * 820) * .036
        if style == 'lawn':
            dry = np.clip((coarse + .15) * 1.65, 0, .7)
            rgb = base + dry[:, :, None] * (.13, .058, -.018)
            return packed_image(name, rgb + value[:, :, None])
    return packed_image(name, base + value[:, :, None])


def material(name, color, *, image=None, scale=1, roughness=.85, metal=0, emission=0, two_sided=False):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    mat.diffuse_color = (*color, 1)
    mat.use_backface_culling = not two_sided
    shader = mat.node_tree.nodes.get('Principled BSDF')
    shader.inputs['Base Color'].default_value = (*color, 1)
    shader.inputs['Roughness'].default_value = roughness
    shader.inputs['Metallic'].default_value = metal
    if image:
        node = mat.node_tree.nodes.new('ShaderNodeTexImage')
        node.image = image
        mat.node_tree.links.new(node.outputs['Color'], shader.inputs['Base Color'])
    if emission:
        shader.inputs['Emission Color'].default_value = (*color, 1)
        shader.inputs['Emission Strength'].default_value = emission
    mat['uv_metres'] = scale
    return mat


def tiled(name, base, style, scale):
    viewport_color = tuple(channel ** 2.2 for channel in base)
    return material(name, viewport_color, image=texture(name, base, style), scale=scale)


brick = tiled('Gạch đất nung xây so le', (.53, .285, .173), 'brick', 1.77)
cladding = tiled('Gạch thẻ đỏ đầu hồi', (.60, .314, .227), 'tile', 1.47)
cream = tiled('Sơn kem có vệt mưa', (.77, .716, .58), 'plaster', 3.2)
plaster = tiled('Bê tông hành lang', (.59, .568, .49), 'plaster', 2.55)
terrazzo = tiled('Đá rửa và bậc tam cấp', (.57, .527, .473), 'stone', 1.1)
paving = tiled('Gạch vỉa hè hoa văn', (.64, .606, .531), 'paving', 1.6)
lawn = tiled('Cỏ sân vườn', (.273, .343, .155), 'lawn', 3.6)
soil = tiled('Đất dưới tán cây', (.355, .29, .201), 'soil', 2.8)
gravel = tiled('Sỏi bãi xe', (.34, .329, .31), 'gravel', 2.4)
dark_bark = tiled('Vỏ cây sẫm nứt dọc', (.30, .255, .194), 'bark', 2.05)
light_bark = tiled('Vỏ cây xám', (.49, .455, .398), 'bark', 2.45)

rail = material('Sắt mạ xám sáng', (.49, .51, .47), roughness=.5, metal=.34)
roof = material('Tôn kẽm ngả xám', (.23, .24, .23), roughness=.62, metal=.35)
shutter = material('Cửa chớp nâu', (.112, .076, .053))
slat = material('Nan cửa chớp', (.151, .107, .081))
frame = material('Khung nhôm ô kính', (.26, .29, .28), roughness=.52, metal=.25)
glass = [material(f'Kính phòng học {i + 1}', color, roughness=.31, metal=.15)
         for i, color in enumerate([(.044, .073, .078), (.066, .100, .104), (.075, .095, .10), (.042, .059, .067)])]
lit_glass = material('Phòng còn sáng', (.36, .265, .129), roughness=.53, emission=.26)
charcoal = material('Cao su và dây điện', (.034, .036, .037))
wood = material('Ghế bê tông giả gỗ', (.287, .17, .099))
red = material('Đỏ thùng rác và chắn xe', (.46, .052, .027))
yellow = material('Vàng sọc chắn xe', (.77, .44, .05))
green = material('Xanh lá thùng phân loại', (.055, .266, .113))
blue = material('Bảng tên khoa xanh lam', (.067, .238, .389))
paper = material('Chữ trắng', (.88, .857, .745))
tube_light = material('Đèn hành lang', (.91, .831, .613), emission=1.1)
lamp_glass = material('Đèn sân', (.91, .698, .434), emission=1.8)
leaf_mats = [material('Leaves | ' + name, color, two_sided=True) for name, color in
             [('xanh sẫm', (.047, .10, .033)), ('xanh lá', (.087, .178, .046)),
              ('xanh ô liu', (.155, .219, .067)), ('đọt non', (.216, .303, .091))]]
dry_leaves = [material(f'Lá rụng {i}', c, two_sided=True) for i, c in
              enumerate([(.23, .118, .053), (.355, .214, .086), (.123, .084, .044)])]

BOX_FACES = [(3, 2, 1, 0), (4, 5, 6, 7), (0, 1, 5, 4),
             (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]


class Geometry:
    """Accumulate details per architectural part to limit WebGL draw calls."""
    def __init__(self, name, group):
        self.name = name
        self.group = group
        self.vertices = []
        self.faces = []
        self.mats = []
        self.indices = []
        self.uvs = []
        self.smooth = []

    def add(self, vertices, faces, mat, *, smooth=False, uvs=None):
        offset = len(self.vertices)
        self.vertices.extend(vertices)
        if mat not in self.mats:
            self.mats.append(mat)
        index = self.mats.index(mat)
        scale = mat['uv_metres']
        for i, face in enumerate(faces):
            self.faces.append(tuple(offset + j for j in face))
            self.indices.append(index)
            self.smooth.append(smooth)
            if uvs is not None:
                self.uvs.extend(uvs[i])
                continue
            va, vb, vc = (Vector(vertices[j]) for j in face[:3])
            normal = (vb - va).cross(vc - va)
            axis = max(range(3), key=lambda a: abs(normal[a]))
            axes = ((1, 2), (0, 2), (0, 1))[axis]
            self.uvs.extend(tuple(vertices[j][a] / scale for a in axes) for j in face)

    def box(self, center, size, mat, *, angle=0, pitch=0):
        x, y, z = center
        w, d, h = (value / 2 for value in size)
        vertices = []
        for a, b, c in [(-w, -d, -h), (w, -d, -h), (w, d, -h), (-w, d, -h),
                         (-w, -d, h), (w, -d, h), (w, d, h), (-w, d, h)]:
            bz = b * math.cos(pitch) - c * math.sin(pitch)
            cz = b * math.sin(pitch) + c * math.cos(pitch)
            vertices.append((x + a * math.cos(angle) - bz * math.sin(angle),
                             y + a * math.sin(angle) + bz * math.cos(angle), z + cz))
        self.add(vertices, BOX_FACES, mat)

    def tube(self, points, radii, mat, sides=8, *, irregular=0):
        vertices = []
        faces = []
        distance = [0]
        for i in range(1, len(points)):
            distance.append(distance[-1] + (Vector(points[i]) - Vector(points[i - 1])).length)
        scale = mat['uv_metres']
        for i, point in enumerate(points):
            tangent = Vector(points[min(i+1, len(points)-1)]) - Vector(points[max(i-1, 0)])
            tangent.normalize()
            if i == 0:
                ref = Vector((0, 1, 0)) if abs(tangent.y) < .83 else Vector((1, 0, 0))
            u = tangent.cross(ref).normalized()
            v = tangent.cross(u)
            for j in range(sides):
                angle = j * math.tau / sides
                radius = radii[i] * (1 + irregular * math.sin(j * 17.2 + i * 1.4))
                vertices.append(tuple(Vector(point) + radius * (u * math.cos(angle) + v * math.sin(angle))))
        uvs = []
        perimeter = 4 * max(radii)
        for i in range(len(points) - 1):
            for j in range(sides):
                k = (j + 1) % sides
                faces.append((i*sides+j, i*sides+k, (i+1)*sides+k, (i+1)*sides+j))
                a = j / sides * perimeter / scale
                b = (j + 1) / sides * perimeter / scale
                c, d = distance[i] / scale, distance[i+1] / scale
                uvs.append(((a, c), (b, c), (b, d), (a, d)))
        cap_uv = tuple((.5 + math.cos(i*math.tau/sides)*.45, .5 + math.sin(i*math.tau/sides)*.45) for i in range(sides))
        faces.extend([tuple(reversed(range(sides))), tuple(range(len(vertices)-sides, len(vertices)))])
        uvs.extend([tuple(reversed(cap_uv)), cap_uv])
        self.add(vertices, faces, mat, smooth=True, uvs=uvs)

    def bar(self, a, b, radius, mat, sides=6):
        self.tube((a, b), (radius, radius), mat, sides)

    def leaf(self, center, direction, length, width, mat):
        d = Vector(direction).normalized() * length
        ref = Vector((0, 0, 1)) if abs(d.z / length) < .95 else Vector((0, 1, 0))
        w = d.cross(ref).normalized() * width / 2
        bend = w.cross(d).normalized() * width * .23
        p = Vector(center)
        if width < .07:
            vertices = [p, p+d*.39-w, p+d, p+d*.36+w]
            self.add(vertices, [(0,1,3), (1,2,3)], mat)
        else:
            vertices = [p, p+d*.34-w, p+d, p+d*.39+w, p+d*.44+bend]
            self.add(vertices, [(i,(i+1)%4,4) for i in range(4)], mat)

    def finish(self, **extras):
        mesh = bpy.data.meshes.new(self.name)
        mesh.from_pydata(self.vertices, [], self.faces)
        mesh.update()
        for mat in self.mats:
            mesh.materials.append(mat)
        mesh.polygons.foreach_set('material_index', self.indices)
        mesh.polygons.foreach_set('use_smooth', self.smooth)
        mesh.uv_layers.new(name='UVMap').uv.foreach_set('vector', [c for uv in self.uvs for c in uv])
        ob = bpy.data.objects.new(self.name, mesh)
        self.group.objects.link(ob)
        for key, value in extras.items():
            ob[key] = value
        return ob


def coordinates(x, y, side):
    """A facade's local U runs along the building and positive V faces the courtyard."""
    return lambda u, v, z: (x + v * side, y + u * side, z)


def local_box(mesh, at, u, v, z, length, depth, height, mat):
    size = (length, depth, height) if getattr(at, "end_wall", False) else (depth, length, height)
    mesh.box(at(u, v, z), size, mat)


def window(mesh, at, u, v, z, w, h, *, pane=None, bars=3, slatted=False):
    local_box(mesh, at, u, v, z, w, .075, h, shutter if slatted else frame)
    local_box(mesh, at, u, v+.048, z+.015, w-.09, .02, h-.1, pane or rng.choice(glass))
    for i in range(1, bars):
        local_box(mesh, at, u-w/2+w*i/bars, v+.073, z, .034, .053, h, frame)
    local_box(mesh, at, u, v+.074, z+h*.27, w, .047, .045, frame)
    local_box(mesh, at, u, v+.12, z-h/2-.04, w+.14, .23, .085, terrazzo)
    if slatted:
        for offset in (-w*.37, w*.37):
            local_box(mesh, at, u+offset, v+.09, z, w*.24, .035, h-.06, shutter)
            for row in range(int(h/.102)):
                local_box(mesh, at, u+offset, v+.114, z-h/2+.065+row*.10, w*.22, .026, .029, slat)


def railing(mesh, a, b, height, *, horizontal=False):
    a, b = Vector(a), Vector(b)
    distance = (b-a).length
    lift = Vector((0, 0, height))
    mesh.bar(a+lift, b+lift, .024, rail)
    levels = (.30, .53, .76) if horizontal else (.14,)
    for level in levels:
        offset = lift * level
        mesh.bar(a+offset, b+offset, .013, rail)
    spacing = 1.28 if horizontal else .205
    steps = math.ceil(distance / spacing)
    for i in range(steps+1):
        p = a.lerp(b, i/steps)
        mesh.bar(p, p+lift, .019 if i % 5 else .026, rail)


def collider(x0, x1, y0, y1):
    ob = bpy.data.objects.new('Va chạm', None)
    physics.objects.link(ob)
    ob.empty_display_type = 'CUBE'
    ob.empty_display_size = 1
    ob.location = ((x0+x1)/2, (y0+y1)/2, .49)
    ob.scale = ((x1-x0)/2, (y1-y0)/2, .49)
    ob['walkCollider'] = True


def floor(x0, x1, y0, y1, low, high):
    ob = bpy.data.objects.new('Cao độ lối đi', None)
    physics.objects.link(ob)
    ob.empty_display_type = 'CUBE'
    ob.location = ((x0+x1)/2, (y0+y1)/2, 0)
    ob.scale = ((x1-x0)/2, (y1-y0)/2, .025)
    ob['floorStart'] = low
    ob['floorEnd'] = high


ground = Geometry('Nền cỏ liên tục', site)
ground.box((0, 0, -.14), (49.95, 50, .26), lawn)
ground.finish(noShadow=True)
paths = Geometry('Gạch vỉa hè và bo mép', site)
for x, width in [(-9.35, 2.55), (5.18, 2.60)]:
    paths.box((x, 0, .008), (width, 50, .055), paving)
    for offset in (-width/2, width/2):
        paths.box((x+offset, 0, .006), (.09, 50, .07), terrazzo)
for y, width, x0, x1 in [(-17.1, 2.3, -8.08, 3.88), (-.95, 1.45, -8.08, 3.88),
                          (13.0, 2.75, -8.08, 3.88), (10.35, 1.8, 6.48, 14.3),
                          (3.8, 2.7, -22.5, -10.625), (17.9, 2.05, 6.48, 12.0)]:
    paths.box(((x0+x1)/2, y, .008), (x1-x0, width, .055), paving)
    for offset in (-width/2, width/2):
        paths.box(((x0+x1)/2, y+offset, .006), (x1-x0, .085, .07), terrazzo)
paths.finish(noShadow=True)
dirt = Geometry('Đất trống sát chân tường', site)
dirt.box((-11.32, -5.1, -.013), (1.25, 28, .025), soil)
dirt.box((10.6, -9.1, -.015), (8.15, 18.9, .035), gravel)
dirt.box((11.7, 10.6, -.064), (12.0, 27.7, .1), soil)
dirt.finish(noShadow=True)


def wing(group, name, x, y, length, depth, floors, side, *, chemistry=False):
    at = coordinates(x, y, side)
    step = 3.07
    base = .56 if chemistry else .25
    height = base + step*floors
    shell = Geometry(name + ' | khung bê tông và gạch', group)
    detail = Geometry(name + ' | cửa và lan can', group)
    service = Geometry(name + ' | điện và thoát nước', group)
    roof_mesh = Geometry(name + ' | mái đua và máng xối', group)
    local_box(shell, at, 0, -depth/2, height/2, length, depth, height, brick)
    local_box(shell, at, 0, -.1, base/2, length+.22, .3, base, plaster)
    extension = 1.40 if chemistry else 1.18
    local_box(shell, at, 0, extension/2, base-.10, length, extension, .20, terrazzo)
    bays = round(length/2.58)
    spacing = length/bays
    is_lit = (1, bays-2)
    for level in range(floors):
        z = base + level*step
        if level:
            local_box(shell, at, 0, extension/2, z-.12, length+.16, extension+.22, .27, plaster)
            local_box(shell, at, 0, extension+.08, z+.10, length+.18, .18, .50 if floors>2 else .38, cream)
            for i in range(bays + 1):
                u = -length/2 + i*spacing
                local_box(shell, at, u, extension*.52, z-.18, .19, extension, .36, cream)
            for i in range(bays):
                left = -length/2+i*spacing
                railing(detail, at(left+.10, extension+.1, z+.28),
                        at(left+spacing-.10, extension+.1, z+.28), .68, horizontal=floors>2)
                local_box(shell, at, left+.056, extension+.09, z+.48, .18, .24, .91, cream)
        for i in range(bays):
            u = (i+.5)*spacing-length/2
            local_box(shell, at, u-spacing/2+.10, .065, z+1.34, .24, .25, 2.72, cream)
            has_shutter = not level and not chemistry
            if chemistry and not level and i in (1, 2):
                local_box(detail, at, u-.18, .09, z+1.12, .62, .1, .84, frame)
                local_box(detail, at, u-.18, .148, z+1.12, .54, .025, .74, blue)
                for line in range(7):
                    local_box(detail, at, u-.18, .167, z+1.36-line*.069, .41-rng.random()*.12, .011, .009, paper)
            else:
                window(detail, at, u, .065, z+1.48, spacing-.49, 1.96 if has_shutter else 1.6,
                       pane=lit_glass if (i+level*3)%bays in is_lit and level<2 else None,
                       slatted=has_shutter)
            if chemistry or level or i % 2 == 0:
                local_box(service, at, u, extension*.65, z+2.77, .82, .095, .077, roof)
                if i % 3 != 2:
                    local_box(service, at, u, extension*.65, z+2.72, .75, .063, .025, tube_light)
            if i % 3 == 1 and level < 2:
                a = u+spacing*.17
                local_box(service, at, a, .22, z+.48, .68, .34, .52, cream)
                local_box(service, at, a-.11, .403, z+.48, .39, .028, .39, charcoal)
                for fin in range(8):
                    local_box(service, at, a-.11, .426, z+.31+fin*.049, .40, .028, .012, rail)
    eave = extension+.4
    local_box(roof_mesh, at, 0, (eave-depth)/2, height+.02, length+.62, depth+eave, .23, roof)
    local_box(roof_mesh, at, 0, eave, height+.016, length+.71, .16, .24, plaster)
    for i in range(round((length+.4)/.16)):
        u = i*.16 - length/2
        local_box(roof_mesh, at, u, eave*.48, height-.11, .026, eave+.08, .032, roof)
    for u in (-length*.47, length*.46):
        points = [at(u,eave-.03,height), at(u,eave-.03,height-.23), at(u,.28,height-.46),
                  at(u,.28,.44), at(u,.70,.24)]
        service.tube(points, [.047]*len(points), roof, 8)
        for z in (1.2, 3.1, height-.5):
            service.bar(at(u,.28,z), at(u,.28,z+.065), .058, rail)
    # Windows wrapping the visible short ends and an upper return railing.
    for sign in (-1, 1):
        at_end = lambda u, v, z: (x + u, y + sign*(length/2 + v), z)
        at_end.end_wall = True
        for level in range(floors):
            z = base+level*step
            for i in range(3):
                window(detail, at_end, -side*depth*(i+1)/4, .065, z+1.49,
                       depth*.19, 1.48, slatted=(not chemistry and level == 0))
            if level:
                shell.box((x-side*(depth-extension)/2, y+sign*(length/2+.64), z-.09),
                          (depth+extension, 1.28, .25), cream)
                railing(detail, (x-side*depth, y+sign*(length/2+1.18), z+.03),
                        (x+side*extension, y+sign*(length/2+1.18), z+.03), .97,
                        horizontal=floors>2)
    xmin, xmax = sorted((x, x-depth*side))
    collider(xmin, xmax, y-length/2, y+length/2)
    for mesh in (shell, detail, service, roof_mesh):
        mesh.finish()


wing(low_wing, 'Nhà hai tầng', -11.81, -7.95, 23.0, 7.15, 2, 1)
wing(faculty, 'Khoa Hóa - Thực phẩm', -12.25, 13.4, 16.7, 7.4, 3, 1, chemistry=True)
wing(tower, 'Hành lang giảng đường', 13.65, 9.55, 26.0, 7.8, 5, -1, chemistry=True)


def end_wall(x, y, w, d, h):
    body = Geometry('Tháp đầu hồi ốp gạch thẻ', tower)
    trim = Geometry('Chỉ bê tông và cửa ô vuông đầu hồi', tower)
    body.box((x, y, h/2), (w, d, h), cladding)
    body.box((x, y, .20), (w+.1, d+.1, .37), brick)
    body.box((x, y, h), (w+.33, d+.36, .24), cream)
    west = coordinates(x-w/2, y, -1)
    front = lambda u, v, z: (x+u, y-d/2-v, z)
    front.end_wall = True
    for j in range(5):
        z = 1.58+j*3.07
        for at in (west, front):
            window(trim, at, -.91, .039, z, 1.64, 1.27, bars=3)
            window(trim, at, 1.11, .039, z+.18, .57, .84, bars=1)
        if j:
            body.box((x, y, 3.07*j+.34), (w+.052, d+.052, .072), terrazzo)
    for z in (.4, 1.1, 4.3, 7.4, 10.5, 13.6):
        trim.bar((x-w/2-.10, y-d/2+.36, z), (x-w/2-.10, y-d/2+.36, z+.15), .058, roof)
    trim.bar((x-w/2-.10, y-d/2+.36,.32), (x-w/2-.10, y-d/2+.36,h-.1), .042, roof)
    body.finish()
    trim.finish()
    collider(x-w/2, x+w/2, y-d/2, y+d/2)


end_wall(15.50, 8.6, 6.32, 5.4, 15.9)

bridge = Geometry('Cầu nối qua lối đi phía Tây', faculty)
bridge.box((-16.3, 3.89, 3.17), (2.35, 5.0, .38), cream)
for x in (-17.33, -15.27):
    for y in (2.83, 4.98):
        bridge.box((x, y, 1.49), (.28, .30, 2.98), cream)
        collider(x-.14, x+.14, y-.15, y+.15)
    railing(bridge, (x, 1.4, 3.36), (x, 6.39, 3.36), .92)
bridge.finish()

stairs = Geometry('Cầu thang ngoài trời và chiếu nghỉ', low_wing)
stair_rail = Geometry('Tay vịn cầu thang ngoài trời', low_wing)
stair_x = -13.25
start_y = -24.36
for i in range(18):
    y = start_y+(i+.5)*.258
    top = (i+1)*.183
    thickness = min(top,.30)
    stairs.box((stair_x,y,top-thickness/2),(1.50,.259,thickness),terrazzo)
    stairs.box((stair_x,y-.117,top-.017),(1.54,.040,.041),cream)
for x in (stair_x-.77,stair_x+.77):
    railing(stair_rail,(x,start_y,.035),(x,-19.71,3.294),.93)
stairs.box((stair_x,-19.72,3.17),(1.56,.80,.25),cream)
stairs.box((stair_x,-21.33,.96),(.31,.45,1.92),cream)
railing(stair_rail,(stair_x-.78,start_y,.04),(stair_x+.78,start_y,.04),.96)
collider(stair_x-.78,stair_x+.78,start_y,-19.70)
stairs.finish()
stair_rail.finish()


def entrance_steps(name, x, y, side, ground_z, group):
    mesh = Geometry(name, group)
    for i in range(4):
        top = ground_z*(i+1)/4
        mesh.box((x + side*(3.5-i)*.25, y, top/2), (.25, 2.52, top), terrazzo)
        mesh.box((x + side*(3.65-i)*.25, y, top-.012), (.051, 2.55, .027), cream)
    for dy in (-1.29, 1.29):
        # Low sloped cheek walls frame the exterior steps.
        xa, xb = x+side*.015, x+side*1.008
        v = [(xa,y+dy-.09,0),(xb,y+dy-.09,0),(xb,y+dy+.09,0),(xa,y+dy+.09,0),
             (xa,y+dy-.09,ground_z+.55),(xb,y+dy-.09,.52),
             (xb,y+dy+.09,.52),(xa,y+dy+.09,ground_z+.55)]
        faces = BOX_FACES if side > 0 else [tuple(reversed(face)) for face in BOX_FACES]
        mesh.add(v, faces, cream)
        collider(min(xa, xb), max(xa, xb), y+dy-.09, y+dy+.09)
    x0, x1 = sorted((x, x+side*1.0))
    floor(x0, x1, y-1.21, y+1.21, ground_z if side>0 else 0, 0 if side>0 else ground_z)
    mesh.finish()


entrance_steps('Tam cấp trước bảng tên khoa', -10.85, 7.1, 1, .56, faculty)
floor(-12.25, -10.85, 5.05, 21.75, .56, .56)
entrance_steps('Tam cấp cạnh giảng đường', 12.25, 17.9, -1, .56, tower)
floor(12.25, 13.65, -3.45, 22.55, .56, .56)
# Low retaining walls make it clear where to enter the raised corridors.
retaining = Geometry('Tường thấp mép hành lang khoa', faculty)
for x, y0, y1 in [(-10.85,5.05,5.81),(-10.85,8.39,21.75),
                  (12.25,-3.45,16.61),(12.25,19.19,22.55)]:
    retaining.box((x,(y0+y1)/2,.47),(.16,y1-y0,.94),cream)
    retaining.box((x,(y0+y1)/2,.96),(.22,y1-y0,.055),terrazzo)
    collider(x-.085,x+.085,y0,y1)
for x0, x1, y in [(-12.25,-10.85,5.05),(-12.25,-10.85,21.75),
                  (12.25,13.65,-3.45),(12.25,13.65,22.55)]:
    retaining.box(((x0+x1)/2,y,.47),(x1-x0,.16,.94),cream)
    collider(x0,x1,y-.08,y+.08)
retaining.finish()

signs = Geometry('Bảng tên và sơ đồ ngoài hành lang', faculty)
signs.box((-10.91, 7.65, 3.17), (.34, 4.48, .92), cream)
signs.box((-10.68, 7.65, 3.15), (.085, 4.15, .82), blue)
for y in (5.7, 9.6):
    signs.box((-10.63,y,3.15),(.016,.028,.78),frame)
signs.box((-8.09, 8.61, 1.42), (.055,.83,1.68), rail)
signs.box((-8.053,8.61,1.42),(.023,.775,1.61),paper)
for y in (8.25,8.97):
    signs.bar((-8.10,y,0),(-8.10,y,1.53),.025,rail)
for row in range(15):
    signs.box((-8.036,8.74,1.87-row*.069),(.009,.28-rng.random()*.09,.011),blue)
for col in range(4):
    signs.box((-8.034,8.25+col*.064,1.25),(.012,.022,.71),frame)
for row in range(5):
    signs.box((-8.032,8.34,1.0+row*.133),(.011,.23,.016),frame)
signs.finish()
collider(-8.16,-7.98,8.24,8.98)

font_path = Path('/System/Library/Fonts/Supplemental/Arial Bold.ttf')
sign_font = bpy.data.fonts.load(str(font_path)) if font_path.is_file() else None


def lettering(name, words, group, position, size, angle, material_, *, tilt=math.pi/2):
    curve = bpy.data.curves.new(name, 'FONT')
    curve.body = words
    curve.align_x = 'CENTER'
    curve.align_y = 'CENTER'
    curve.size = size
    curve.resolution_u = 5
    if sign_font:
        curve.font = sign_font
    curve.materials.append(material_)
    source = bpy.data.objects.new(name, curve)
    group.objects.link(source)
    source.location = position
    source.rotation_euler = (tilt, 0, angle)
    dependency_graph = bpy.context.evaluated_depsgraph_get()
    data = bpy.data.meshes.new_from_object(source.evaluated_get(dependency_graph))
    mesh = bpy.data.objects.new(name, data)
    group.objects.link(mesh)
    mesh.matrix_world = source.matrix_world.copy()
    bpy.data.objects.remove(source, do_unlink=True)
    return mesh


for line, z, size in [
    ('TRƯỜNG ĐẠI HỌC SƯ PHẠM KỸ THUẬT TP. HCM',3.41,.116),
    ('KHOA CÔNG NGHỆ HÓA HỌC & THỰC PHẨM',3.16,.193),
    ('FACULTY OF CHEMICAL AND FOOD TECHNOLOGY',2.91,.108),
]:
    lettering('Chữ bảng tên khoa', line, faculty, (-10.63,7.65,z), size, math.pi/2, paper)
lettering('Chữ đầu trang sơ đồ', 'SƠ ĐỒ KHU B', faculty, (-8.029,8.61,2.04), .079, math.pi/2, blue)


def bench(name, x, y, angle, *, brown=False):
    mesh = Geometry(name, furniture)
    m = wood if brown else terrazzo
    def box(a,b,z,w,d,h, pitch=0):
        p = (x+a*math.cos(angle)-b*math.sin(angle), y+a*math.sin(angle)+b*math.cos(angle),z)
        mesh.box(p, (w,d,h), m, angle=angle, pitch=pitch)
    box(0,0,.46,1.76,.55,.084, .044)
    box(0,.245,.80,1.76,.078,.37,-.20)
    for a in (-.56,.56):
        box(a,-.14,.224,.105,.135,.44,-.28)
        box(a,.16,.395,.105,.102,.78,-.21)
        box(a,0,.065,.13,.40,.089)
    mesh.finish()
    extent_x = abs(math.cos(angle))*.88 + abs(math.sin(angle))*.285
    extent_y = abs(math.sin(angle))*.88 + abs(math.cos(angle))*.285
    collider(x-extent_x,x+extent_x,y-extent_y,y+extent_y)


for index,(x,y,angle) in enumerate([(-7.08,-14.25,1.57),(-5.07,-10.20,.13),
                                     (3.05,-14.32,-1.57),(3.13,-2.35,-1.57),
                                     (-6.5,6.55,-.16),(3.33,4.11,-1.57),
                                     (-3.22,11.0,.15), (8.90,14.15,.21),
                                     (-4.25,15.83,1.61), (3.89,19.64,.1)]):
    bench(f'Ghế sân vườn {index+1:02}',x,y,angle,brown=index in (1,4,7))


def seating(x,y,brown):
    mesh = Geometry('Bộ bàn ghế đá', furniture)
    m = wood if brown else terrazzo
    mesh.box((x,y,.71),(1.39,.90,.107),m)
    mesh.box((x,y,.035),(3.30,2.6,.055),plaster)
    for dx in (-.45,.45):
        mesh.box((x+dx,y,.365),(.143,.57,.66),m,pitch=.15)
        mesh.box((x+dx,y,.076),(.28,.71,.083),m)
    mesh.finish()
    bench('Ghế cạnh bàn',x,y-1.01,0,brown=brown)
    bench('Ghế cạnh bàn',x,y+1.01,math.pi,brown=brown)
    collider(x-.69,x+.69,y-.44,y+.44)


for x,y,brown in [(-4.7,-13.7,True),(-4.9,-3.65,False),(2.51,2.35,True),(-4.58,8.55,True),
                   (2.52,-6.85,False),(9.0,11.55,False)]:
    seating(x,y,brown)

bins = Geometry('Thùng rác đôi đỏ xanh có mái', furniture)
for x,y in [(-7.65,-12.24),(3.46,-9.95),(7.68,9.0),(-7.5,7.65)]:
    bins.bar((x,y,0),(x,y,1.05),.054,rail)
    for dx,m in ((-.215,red),(.215,green)):
        bins.tube(((x+dx,y,.14),(x+dx,y,.79)),(.146,.186),m,13)
        bins.tube(((x+dx,y,.797),(x+dx,y,.842)),(.193,.193),roof,13)
        bins.tube(((x+dx,y,.844),(x+dx,y,.849)),(.135,.135),charcoal,13)
        bins.box((x+dx,y,1.045),(.43,.46,.068),m,pitch=.11)
    collider(x-.39,x+.39,y-.21,y+.21)
bins.finish()

shrine_court = Geometry('Nền và hàng rào thấp quanh miếu', furniture)
shrine_court.box((0,14.04,.005),(3.65,3.17,.053),terrazzo)
for x in (-1.83,1.83):
    shrine_court.box((x,14.11,.06),(.13,3.28,.12),cream)
    railing(shrine_court,(x,12.57,.08),(x,15.73,.08),.53)
    collider(x-.077,x+.077,12.57,15.73)
for x0,x1 in [(-1.83,-.96),(.96,1.83)]:
    railing(shrine_court,(x0,15.73,.08),(x1,15.73,.08),.53)
shrine_court.finish()

perimeter = Geometry('Tường rào cuối sân và hàng song', site)
for y in (-24.83,24.83):
    perimeter.box((0,y,.48),(43.3,.28,.97),plaster)
    perimeter.box((0,y,.99),(43.3,.34,.12),terrazzo)
    for x in range(-21,22,3):
        perimeter.box((x,y,1.02),(.29,.39,2.03),cream)
    for i in range(160):
        x = (i-79.5)*.267
        perimeter.box((x,y,1.38),(.045,.048,.83),rail)
    for z in (1.08,1.73):
        perimeter.box((0,y,z),(43.2,.09,.06),rail)
# Campus wings beyond the rear fence close the sightlines from inside the garden.
for x, y, w, d in [(-14.2,28.6,13.0,6.6),(13.0,29.2,14.6,7.2)]:
    perimeter.box((x,y,3.1),(w,d,6.2),cream)
    front_y = y-d/2
    at = lambda u,v,z: (x+u,front_y-v,z)
    at.end_wall = True
    for level in range(2):
        z = 1.48+level*2.94
        for i in range(5):
            u = ((i+1)/6-.5)*w
            window(perimeter,at,u,.035,z,1.31,1.31,bars=3)
        perimeter.box((x,front_y-.12,z-1.14),(w+.1,.26,.25),plaster)
    perimeter.box((x,y,6.25),(w+.38,d+.45,.30),roof)
perimeter.box((0,27.9,-.09),(48,6.5,.15),lawn)
perimeter.finish()

pole = Geometry('Cột điện, hộp cầu dao và dây võng', utilities)
for x,y,h in [(8.3,-13.6,7.6),(-7.15,4.25,7.0),(8.60,10.2,7.8)]:
    pole.tube(((x,y,0),(x,y,h)),(.19,.115),plaster,10)
    pole.box((x,y,.082),(.47,.46,.16),terrazzo)
    pole.box((x,y,h-.28),(1.29,.125,.14),roof)
    for dx in (-.51,.51):
        pole.bar((x,y,h-.76),(x+dx,y,h-.27),.036,rail)
        for off in (0,.057,.114):
            pole.bar((x+dx,y,h-.22+off),(x+dx,y,h-.192+off),.065,terrazzo,10)
    for dx in (-.265,.265):
        pole.box((x+dx,y-.096,1.56),(.28,.34,.54),cream)
        pole.box((x+dx,y-.273,1.56),(.243,.023,.49),plaster)
        pole.box((x+dx+.08,y-.289,1.56),(.037,.017,.080),charcoal)
        for v in (1.67,1.71,1.75):
            pole.box((x+dx,y-.291,v),(.102,.016,.011),roof)
        pole.tube(((x+dx,y-.13,1.29),(x+dx,y-.13,1.08),(x+dx*.54,y-.13,.91),
                   (x+dx*.39,y-.13,.85),(x+dx*.39,y-.13,.02)),(.026,)*5,red,7)
    collider(x-.4,x+.4,y-.3,y+.23)

for a,b in [((8.3,-13.6,7.52),(-7.15,4.25,6.92)),((-7.15,4.25,6.92),(8.6,10.2,7.72)),
            ((8.6,10.2,7.72),(12.19,20.9,6.55)),((8.3,-13.6,7.52),(17.9,-22.1,6.85))]:
    for index,off in enumerate((-.46,-.21,.21,.46)):
        points = []
        for step in range(17):
            t = step/16
            points.append((a[0]*(1-t)+b[0]*t+off,a[1]*(1-t)+b[1]*t,
                           a[2]*(1-t)+b[2]*t-4*t*(1-t)*(.72+index*.18)))
        pole.tube(points,(.017,)*len(points),charcoal,6)
pole.finish()

lamps = Geometry('Đèn sân thân thép và chụp đèn', utilities)
for x,y,reach in [(-7.86,-16.55,1),(-7.73,-3.9,1),(6.90,-7.55,-1),
                  (-7.7,10.75,1),(7.02,15.4,-1),(3.54,20.45,1),(8.80,2.45,-1)]:
    height = 3.78
    hx = x+reach*.53
    lamps.bar((x,y,0),(x,y,height-.25),.043,roof,10)
    lamps.bar((x,y,0),(x,y,.24),.079,rail,10)
    lamps.tube(((x,y,height-.28),(x+reach*.13,y,height-.06),(hx,y,height)),
               (.043,.035,.028),roof,9)
    lamps.box((hx,y,height-.053),(.31,.16,.10),roof)
    lamps.box((hx,y,height-.108),(.24,.12,.025),lamp_glass)
    light = bpy.data.objects.new('Nguồn sáng đèn sân', None)
    utilities.objects.link(light)
    light.location = (hx,y,height-.24)
    light['courtyardLight'] = 'path'
    collider(x-.072,x+.072,y-.072,y+.072)
lamps.finish()
for x,y in [(-10.50,-13),(-10.50,-3),(-11.19,7.10),(-11.19,14.5),(12.52,15.5),(12.52,21.0)]:
    light = bpy.data.objects.new('Nguồn sáng hành lang', None)
    utilities.objects.link(light)
    light.location = (x,y,2.80)
    light['courtyardLight'] = 'corridor'

def torus(mesh, p, radius, thickness, mat):
    x,y,z = p
    rings, sides = 14, 6
    vertices = []
    for i in range(rings):
        angle = i*math.tau/rings
        for j in range(sides):
            section = j*math.tau/sides
            r = radius+thickness*math.cos(section)
            vertices.append((x+r*math.cos(angle),y-thickness*math.sin(section),z+r*math.sin(angle)))
    faces = [(i*sides+j,((i+1)%rings)*sides+j,((i+1)%rings)*sides+(j+1)%sides,i*sides+(j+1)%sides)
             for i in range(rings) for j in range(sides)]
    mesh.add(vertices,faces,mat,smooth=True)


bike_blue = material('Sơn xanh xe máy', (.051,.155,.268), roughness=.32, metal=.28)
bike_red = material('Sơn đỏ xe máy', (.45,.040,.036), roughness=.33, metal=.24)
bike_gray = material('Sơn xám xe máy', (.43,.45,.44), roughness=.4, metal=.25)
bike_dark = material('Sơn đen xe máy', (.066,.073,.082), roughness=.35, metal=.26)
headlight = material('Choá đèn xe', (.63,.67,.65), roughness=.22, metal=.22)
indicator = material('Xi nhan hổ phách', (.72,.32,.049), roughness=.37)


def scooter(mesh,x,y,angle,paint,variant):
    co, si = math.cos(angle), math.sin(angle)
    start = len(mesh.vertices)

    for wx in (-.66,.63):
        torus(mesh,(wx,0,.245),.191,.052,charcoal)
        torus(mesh,(wx,0,.245),.135,.017,rail)
        mesh.bar((wx,-.076,.245),(wx,.076,.245),.058,frame,9)
        for index in range(5):
            a = index*math.tau/5
            mesh.bar((wx,0,.245),(wx+math.cos(a)*.137,0,.245+math.sin(a)*.137),.011,rail)
    mesh.bar((-.66,0,.25),(-.31,0,.51),.064,roof)
    for wy in (-.075,.075):
        mesh.bar((.64,wy,.25),(.44,wy,.88),.025,rail,8)
    # Body is a loft with a raised rear cowling and a low step-through footwell.
    profiles = [(-.88,.10,.60,.67),(-.65,.205,.38,.71),(-.36,.219,.41,.79),
                (-.08,.174,.42,.69),(.15,.149,.39,.49),(.36,.142,.43,.52),
                (.52,.187,.47,.96),(.62,.142,.56,.90)]
    vertices = []
    for px,width,bottom,top in profiles:
        vertices.extend([(px,-width*.70,bottom),(px,width*.70,bottom),
                         (px,width,(bottom+top)/2),(px,width*.62,top),
                         (px,-width*.62,top),(px,-width,(bottom+top)/2)])
    faces = [tuple(reversed(range(6))),tuple(range(len(vertices)-6,len(vertices)))]
    for i in range(len(profiles)-1):
        for j in range(6):
            k=(j+1)%6
            faces.append((6*i+j,6*i+k,6*(i+1)+k,6*(i+1)+j))
    mesh.add(vertices,faces,paint)
    mesh.box((-.401,0,.78),(.63,.33,.103),charcoal,angle=variant*.004,pitch=.035)
    mesh.box((.136,0,.482),(.46,.31,.059),charcoal)
    for wy in (-.12,.12):
        mesh.box((.633,wy,.790),(.034,.096,.087),indicator)
    mesh.box((.663,0,.941),(.055,.24,.107),headlight)
    mesh.box((-.878,0,.64),(.048,.198,.103),red)
    mesh.box((-.904,0,.48),(.02,.137,.076),paper)
    mesh.box((-.61,-.163,.338),(.428,.091,.108),roof)
    mesh.box((-.61,-.217,.335),(.31,.025,.06),rail)
    mesh.tube(((.37,-.30,1.015),(.419,-.14,1.03),(.443,.14,1.03),(.37,.30,1.015)),(.021,)*4,rail)
    for wy in (-.26,.26):
        mesh.bar((.375,wy,1.018),(.407,wy*1.39,1.252),.012,frame)
        mesh.box((.407,wy*1.39,1.254),(.054,.142,.073),charcoal)
        mesh.box((.375,wy*1.39,1.255),(.014,.108,.049),headlight)
    for i in range(start,len(mesh.vertices)):
        a,b,c=mesh.vertices[i]
        mesh.vertices[i]=(x+a*co-b*si,y+a*si+b*co,c+.008)


for row,x in enumerate((9.85,12.05,14.15)):
    fleet = Geometry(f'Hàng xe máy {row+1}',parking)
    for i in range(15):
        y = -17.8+i*.99+rng.uniform(-.084,.084)
        scooter(fleet,x+rng.uniform(-.15,.15),y,(-.25 if row%2 else 2.9)+rng.uniform(-.13,.13),
                rng.choice((bike_blue,bike_red,bike_gray,bike_dark,bike_dark)),i)
    fleet.finish()
    collider(x-1.0,x+1.0,-18.23,-3.52)

barrier = Geometry('Hàng chắn xe sơn vàng đỏ', parking)
x = 8.06
for y in (-18.65,-15.55,-12.45,-9.35,-6.25,-3.15):
    barrier.bar((x,y,.01),(x,y,.70),.025,red)
    barrier.box((x,y,.035),(.23,.23,.052),terrazzo)
barrier.bar((x,-18.65,.70),(x,-3.15,.70),.021,rail)
for i in range(34):
    y = -18.65+i*15.5/34
    barrier.bar((x,y,.34),(x,y+15.5/34,.34),.019,yellow if i%2 else red)
barrier.finish()
collider(x-.07,x+.07,-18.65,-3.15)


def broad_tree(name,x,y,h,crown,radius,gray):
    timber = Geometry(name + ' | thân và cành', trees)
    leaves = Geometry(name + ' | tán lá', trees)
    bark = light_bark if gray else dark_bark
    p = Vector((x,y,0))
    near_wing = x < -10
    dx = rng.uniform(.55,.96) if near_wing else rng.uniform(-.44,.44)
    dy = rng.uniform(-.34,.34)
    trunk = [p+Vector((dx*t,dy*t+math.sin(t*6)*radius*.48,h*t))
             for t in (-.008,.037,.17,.33,.5,.67,.80,.93,1)]
    timber.tube(trunk,[radius*k for k in (1.6,1.07,.83,.70,.57,.42,.32,.16,.018)],bark,13,irregular=.15)
    for i in range(7):
        angle = math.tau*i/7+rng.uniform(-.28,.28)
        a = Vector((math.cos(angle),math.sin(angle),0))
        reach = radius*rng.uniform(1.65,3.45)
        timber.tube([p+Vector((0,0,radius*.39)),
                     p+a*reach*.38+Vector((0,0,radius*.10)),
                     p+a*reach*.71+Vector((0,0,-radius*.038)),
                     p+a*reach+Vector((0,0,-.065))],
                    [radius*.33,radius*.21,radius*.115,.012],bark,8,irregular=.14)
    for j in range(10):
        angle = j*2.39996+rng.uniform(-.32,.32)
        if near_wing:
            angle = math.atan2(math.sin(angle),abs(math.cos(angle))+.25)
        a = Vector((math.cos(angle),math.sin(angle),0))
        q = Vector((-a.y,a.x,0))
        limb = trunk[3+j//4]
        reach = crown*rng.uniform(.52,1.01)
        end = p+a*reach+Vector((dx,dy,h*rng.uniform(.74,1.05)))
        bend = limb.lerp(end,.62)+Vector((0,0,-h*.07))
        timber.tube([limb,limb.lerp(bend,.40),bend,end],
                    [radius*.48,radius*.33,radius*.18,.013],bark,8,irregular=.11)
        for k in range(7):
            root = bend.lerp(end,(k+.45)/7)
            sign = 1 if k%2 else -1
            tip = root+a*rng.uniform(.20,.66)+q*sign*rng.uniform(.44,1.14)+Vector((0,0,rng.uniform(.18,.61)))
            timber.tube((root,root.lerp(tip,.57),tip),(.027,.015,.005),bark,6)
            for count in range(23):
                f = rng.uniform(.19,1.09)
                pos = root.lerp(tip,f)+Vector((rng.uniform(-.29,.29),rng.uniform(-.30,.30),rng.uniform(-.22,.23)))
                angle = rng.uniform(0,math.tau)
                direction = (math.cos(angle),math.sin(angle),rng.uniform(-.72,.37))
                length = rng.uniform(.19,.43)* (1.25 if h<9 else 1.02)
                leaves.leaf(pos,direction,length,length*rng.uniform(.32,.49),
                           rng.choices(leaf_mats,weights=(3,7,4,1),k=1)[0])
            for count in range(9):
                pos=tip+Vector((rng.uniform(-.55,.55),rng.uniform(-.52,.52),rng.uniform(-.38,.38)))
                leaves.leaf(pos,(rng.uniform(-1,1),rng.uniform(-1,1),rng.uniform(-.25,.50)),
                           rng.uniform(.32,.64),rng.uniform(.11,.25),rng.choice(leaf_mats[:3]))
    timber.finish()
    leaves.finish()
    collider(x-radius*.87,x+radius*.87,y-radius*.87,y+radius*.87)


for i,(x,y,h,crown,radius,gray) in enumerate([
    (-6.86,-17.92,10.74,4.37,.55,False),(-10.69,-11.9,7.35,3.43,.31,False),
    (-10.74,-4.80,7.6,3.22,.31,False),(-8.19,2.98,8.4,3.46,.37,False),
    (-6.90,12.38,12.7,3.82,.41,True),(3.42,-11.35,12.5,3.46,.49,False),
    (7.42,-15.88,13.9,3.93,.50,False),(7.53,5.61,13.1,3.24,.40,True),
    (3.37,11.32,13.05,3.06,.34,True),(8.95,-.83,8.9,3.15,.30,False),
    (-5.68,18.55,12.02,3.61,.34,True),(7.35,19.90,9.3,3.58,.35,False)
]):
    broad_tree(f'Cây sân {i+1:02}',x,y,h,crown,radius,gray)

plants = Geometry('Lá ráy, cỏ mép gạch và lá khô', trees)
mulch = Geometry('Bồn đất và nền chân cây',site)
for x,y,spread in [(-2.52,14.2,1.0),(2.47,14.75,1.0),(-3.03,16.5,.82),
                   (-7.05,6.72,.75),(-8.0,2.05,.98),(7.49,8.48,.75),
                   (-11.01,-5.1,.62),(-10.98,-11.7,.63),(7.42,-15.88,.7),
                   (3.42,-11.35,.76),(-6.86,-17.92,.66),(7.36,19.8,.78)]:
    # Ragged soil patch with its edge just below the surrounding grass blades.
    ring = [(x+math.cos(a)*spread*rng.uniform(.8,1.19),y+math.sin(a)*spread*rng.uniform(.63,.98),.0014)
            for a in (i*math.tau/20 for i in range(20))]
    mulch.add(ring,[tuple(range(20))],soil)
    for j in range(24):
        angle = rng.uniform(0,math.tau)
        dx,dy = rng.uniform(-spread*.75,spread*.75),rng.uniform(-spread*.70,spread*.70)
        h = rng.uniform(.11,.55)
        sign = (math.cos(angle),math.sin(angle),rng.uniform(-.40,-.15))
        plants.bar((x+dx,y+dy,0),(x+dx+sign[0]*.16,y+dy+sign[1]*.16,h),.010,leaf_mats[1],5)
        plants.leaf((x+dx+sign[0]*.16,y+dy+sign[1]*.16,h),sign,rng.uniform(.24,.49),
                    rng.uniform(.14,.28),rng.choice(leaf_mats))
for x0,x1,y0,y1 in [(-8.0,3.83,-24.5,24.5),(6.55,8.0,-24,24),
                      (-11.72,-10.69,-19,3.2)]:
    area = (x1-x0)*(y1-y0)
    for i in range(int(area*9)):
        x,y = rng.uniform(x0,x1),rng.uniform(y0,y1)
        if x < 3.83 and x > -8.01 and (abs(y+17.1)<1.2 or abs(y+.95)<.78 or
                abs(y-13)<1.44 or (abs(x)<1.9 and abs(y-14.0)<1.7)):
            continue
        for strand in range(rng.randint(2,4)):
            angle = rng.uniform(0,math.tau)
            length = rng.uniform(.035,.137)
            plants.leaf((x+rng.uniform(-.08,.08),y+rng.uniform(-.08,.08),-.003),
                        (math.cos(angle),math.sin(angle),rng.uniform(.76,1.95)),
                        length,rng.uniform(.010,.027),rng.choice(leaf_mats))
for i in range(890):
    center_x = rng.choice((-9.35,-7.65,5.18,6.7,8.35))
    x,y = center_x+rng.uniform(-.87,.87),rng.uniform(-23.8,24.1)
    angle = rng.uniform(0,math.tau)
    z = .043 if abs(x+9.35)<1.3 or abs(x-5.18)<1.37 or abs(y+17.1)<1.18 or abs(y-13)<1.4 else .003
    plants.leaf((x,y,z),(math.cos(angle),math.sin(angle),.08),
                rng.uniform(.035,.151),rng.uniform(.021,.067),rng.choice(dry_leaves))
mulch.finish(noShadow=True)
plants.finish(noShadow=True)

# Keep the recognizable trees, shrine and lettered benches from the source scene.
original = collection('Khu B | Cảnh gốc')
before = set(scene.objects)
bpy.ops.import_scene.gltf(filepath=str(ROOT/'hcmute-khu-b.glb'))
imported = set(scene.objects)-before
original_root = bpy.data.objects.new('OriginalKhuB', None)
original.objects.link(original_root)
retained_benches = {'Bench.003', 'Bench.006'}
for ob in sorted(imported, key=lambda item: item.name):
    if (ob.name.startswith(('Plane', 'Grass', 'tripo_node_36487')) or
            (ob.name.startswith('Bench') and ob.name not in retained_benches)):
        bpy.data.objects.remove(ob,do_unlink=True)
        continue
    for group in list(ob.users_collection):
        group.objects.unlink(ob)
    original.objects.link(ob)
    if ob.parent is None:
        ob.parent = original_root
    if ob.name in retained_benches:
        modifier = ob.modifiers.new('Lưới tối ưu cho game web', 'DECIMATE')
        modifier.ratio = .16
    if ob.name.startswith('tripo_node_9f7'):
        ob.location = (0,14,0)
for name, roughness in [('Tree', .87), ('Leaves_NormalTree', .79)]:
    mat = bpy.data.materials[name]
    shader = mat.node_tree.nodes.get('Principled BSDF')
    shader.inputs['Metallic'].default_value = 0
    shader.inputs['Roughness'].default_value = roughness
    if name.startswith('Leaves'):
        mat.use_backface_culling = False
        mat.alpha_threshold = .36

bpy.ops.export_scene.gltf(filepath=str(ROOT/'assets'/'khu-b-courtyard.glb'),
                         export_format='GLB', export_extras=True, export_yup=True, export_apply=True,
                         export_cameras=False, export_lights=False, export_animations=False,
                         export_image_format='AUTO')

# Matching gameplay camera and a daylight camera make the new scene easy to inspect.
studio = collection('Góc nhìn và ánh sáng xem trước')
sun_data = bpy.data.lights.new('Nắng chiều khu B','SUN')
sun_data.energy = 2.25
sun_data.angle = math.radians(11)
sun = bpy.data.objects.new(sun_data.name,sun_data)
studio.objects.link(sun)
sun.rotation_euler = (math.radians(16),math.radians(31),math.radians(14))
scene.world = bpy.data.worlds.new('Trời sáng')
scene.world.use_nodes = True
background = scene.world.node_tree.nodes.get('Background')
background.inputs['Color'].default_value = (.53,.63,.80,1)
background.inputs['Strength'].default_value = 1.08


def camera(name,position,target,lens):
    data=bpy.data.cameras.new(name)
    ob=bpy.data.objects.new(name,data)
    studio.objects.link(ob)
    ob.location=position
    ob.rotation_euler=(Vector(target)-Vector(position)).to_track_quat('-Z','Y').to_euler()
    data.lens=lens
    return ob


scene.camera = camera('Lối đi cạnh nhà hai tầng',(-9.38,-16.82,1.70),(-5.6,8,3.14),24)
front_camera = camera('Bậc thềm khoa Hóa',(-7.95,4.25,1.75),(-11.3,9.0,3.3),22)
parking_camera = camera('Lối đi sát bãi xe',(5.18,-14.9,1.7),(8.37,9,3.2),23)
overhead = camera('Toàn cảnh khu B', (29,-49,35),(-1,0,1.2),44)
scene.render.engine='CYCLES'
scene.cycles.samples=12
scene.cycles.max_bounces=5
scene.cycles.transparent_max_bounces=5
scene.cycles.use_denoising=True
scene.render.resolution_x=1320
scene.render.resolution_y=785
scene.render.resolution_percentage=100
scene.render.image_settings.file_format='JPEG'
scene.render.image_settings.quality=91
scene.view_settings.view_transform='AgX'
scene.view_settings.exposure=.45
scene.render.filepath='//'

bpy.ops.file.pack_all()
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            area.spaces.active.region_3d.view_distance=32
            area.spaces.active.region_3d.view_location=(0,1,2)
            area.spaces.active.region_3d.view_rotation=overhead.rotation_euler.to_quaternion()
            area.spaces.active.shading.color_type='MATERIAL'
            area.spaces.active.shading.show_cavity = True
            area.spaces.active.overlay.show_extras = False
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'khu-b-mo-rong.blend'),compress=True)

if '--preview' in sys.argv:
    prefix = sys.argv[-1]
    for label, angle in [('loi-di', scene.camera), ('khoa-hoa', front_camera), ('bai-xe', parking_camera)]:
        scene.camera = angle
        scene.render.filepath = f'{prefix}-{label}.jpg'
        bpy.ops.render.render(write_still=True)
