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
from mathutils import Quaternion, Vector

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


courtyard = collection('Cụm B–C–D | Đối chiếu sơ đồ và video')
site = collection('01 | Sân vườn và lối đi', courtyard)
low_wing = collection('02 | Khối C song song khối B', courtyard)
faculty = collection('03 | Khoa Hóa học và Khoa học sự sống', courtyard)
tower = collection('04 | Khối B chữ H', courtyard)
neighbors = collection('12 | Khối D, thư viện và hai dãy A', courtyard)
furniture = collection('05 | Bàn ghế và bồn cây', courtyard)
parking = collection('06 | Bãi xe', courtyard)
utilities = collection('07 | Điện và chiếu sáng', courtyard)
trees = collection('08 | Cây và thảm thực vật', courtyard)
physics = collection('09 | Va chạm, cao độ và điểm vào', courtyard)
labs = collection('10 | Các phòng nhìn thấy từ hành lang', courtyard)
outer = collection('11 | Đường ngoài, bãi ô tô và nhà ghép', courtyard)


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
    elif style == 'ceramic':
        u,v=(x*5)%1,(y*5)%1
        seam=np.clip((np.maximum(abs(u-.5),abs(v-.5))-.487)/.013,0,1)
        value=value*.44-seam*.055
    elif style == 'plaster':
        runoff = periodic_noise(64, 3, size)
        value = value * .56 + runoff * (.16 * (coarse + .5)) - np.maximum(coarse, 0) * .1
    elif style == 'bark':
        value = periodic_noise(36, 4, size) * .25 + periodic_noise(99, 7, size) * .19 + medium * .09 + grain * .09
        value += np.maximum(coarse - .1, 0) * .35 + periodic_noise(24, 72, size)*.13
    elif style == 'stone':
        value += -np.maximum(medium + grain * .36 - .25, 0) * .48
    elif style == 'hedge':
        u = x * 23 + (np.floor(y * 30) % 2) * .5
        v = y * 30
        turns = noise_rng.uniform(-math.pi, math.pi, (30, 23))
        tones = noise_rng.uniform(-.06, .07, (30, 23))
        angle = turns[v.astype(int), u.astype(int) % 23]
        du, dv = u % 1 - .5, v % 1 - .5
        ax = du * np.cos(angle) + dv * np.sin(angle)
        ay = -du * np.sin(angle) + dv * np.cos(angle)
        leaf = np.clip((1 - (ax / .48) ** 2 - (ay / .26) ** 2) * 4, 0, 1)
        value = (value * .56 - .071 + leaf * (.23 + np.clip(ax * .21, -.05, .05))
                 + tones[v.astype(int), u.astype(int) % 23])
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
cream = tiled('Sơn kem có vệt mưa', (.86, .838, .763), 'plaster', 3.2)
plaster = tiled('Bê tông hành lang', (.688, .68, .637), 'plaster', 2.55)
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
        if isinstance(radii, (int, float)):
            radii = (radii,) * len(points)
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


def floor(x0, x1, y0, y1, low, high, *, axis="x"):
    ob = bpy.data.objects.new('Cao độ lối đi', None)
    physics.objects.link(ob)
    ob.empty_display_type = 'CUBE'
    ob.location = ((x0+x1)/2, (y0+y1)/2, 0)
    ob.scale = ((x1-x0)/2, (y1-y0)/2, .025)
    ob['floorStart'] = low
    ob['floorEnd'] = high
    ob['floorAxis'] = axis




font_path = next((path for path in (Path('/System/Library/Fonts/Supplemental/Arial Bold.ttf'),
                                    Path('C:/Windows/Fonts/arialbd.ttf')) if path.is_file()), None)
sign_font = bpy.data.fonts.load(str(font_path)) if font_path else None

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


# Blender X/Y are the horizontal site axes. The inner and outer walks are
# estimated from adjoining corners, door bays and pacing in both clips.
WEST, INNER, EAST, EAST_OUT = -23.2, -13.0, 3.25, 13.60
C_WEST, C_EAST = -45.4, -34.0
SOUTH, NORTH = -22.3, 32.7
CROSS_SOUTH,CROSS_NORTH = -.85, 10.95
CROSS_HALL_Y = 4.52
BRIDGE_Y = -21.36
GROUND = .735
STOREY = 3.08
GALLERY = 2.38
SHRINE = (-34.4, -34.65)
JUNCTION = (-10.02, -28.13)
TRANSFORMER = (-11.26, -25.26)

# The older survey used a wider, longer court. Keep the observed order of
# props and trees when fitting that survey to the southern bay of the H.
def court_position(x,y):
    return (-10.6 + (x+10.6)*.403, SOUTH + (y+24.0)*.341)

corridor_tiles = tiled('Gạch men mờ ô vuông hành lang', (.724,.731,.691), 'ceramic', 2.1)
walkway = tiled('Bê tông lối sân có mạch tấm', (.47,.493,.479), 'stone', 1.7)
asphalt = tiled('Nhựa đường nội bộ', (.287,.303,.308), 'gravel', 3.45)
skirting = material('Chân tường chống ẩm xanh đen', (.035,.064,.053))
artificial_turf = tiled('Dải cỏ nhân tạo sát chân tường', (.293,.397,.209), 'lawn', 2.4)
metal_gray = material('Khung sắt sơn xám xanh', (.35,.386,.365), roughness=.56, metal=.20)
backing = material('Hốc tối và cao su', (.028,.035,.033))
frosted = material('Kính mờ và ánh phòng lab', (.275,.335,.325), roughness=.38)
glass_clear = material('Kính trong hành lang', (.33,.447,.421), roughness=.26, two_sided=True)
glass_clear.node_tree.nodes.get('Principled BSDF').inputs['Alpha'].default_value = .22
glass_clear.surface_render_method = 'BLENDED'
glass_clear.diffuse_color = (.33,.447,.421,.22)
lab_wall = material('Tường trong phòng màu ngà', (.79,.80,.746), roughness=.77)
lab_tile = material('Gạch men trắng phòng thực hành', (.756,.787,.735), roughness=.41)
lab_counter = material('Mặt bàn màu sáng', (.50,.515,.469), roughness=.51)
stool_blue = material('Ghế nhựa xanh hành lang', (.075,.125,.455), roughness=.62)
plate_blue = material('Biển phòng xanh cobalt', (.027,.081,.346), roughness=.59)
plate_yellow = material('Vạch định vị màu vàng', (.76,.63,.079))
conduit = material('Ống PVC đã ngả kem', (.555,.537,.411))
shed_lime = material('Tôn xanh chanh nhà ghép', (.37,.555,.115), roughness=.54)
shed_blue = material('Tôn xanh dương nhà ghép', (.041,.170,.385), roughness=.54)
shed_teal = material('Tôn xanh xám tầng dưới', (.111,.251,.224), roughness=.57)
pot_clay = material('Chậu sành đỏ nâu', (.23,.105,.078), roughness=.72)
dark_gold = material('Khung bảng báo màu đồng', (.39,.249,.083), roughness=.44, metal=.33)
green_hedge = [
    material('Lá hàng rào '+str(i),c,two_sided=True) for i,c in enumerate([
        (.046,.103,.034),(.077,.156,.047),(.114,.203,.067),(.148,.245,.079),
        (.184,.274,.087),(.223,.323,.113)
    ])
]
vehicle_paint = [material('Sơn ô tô '+str(i), color, roughness=.39, metal=.3) for i,color in enumerate([
    (.065,.069,.073),(.60,.635,.629),(.36,.393,.39),(.305,.027,.022),(.095,.151,.246)
])]
road_trim = material('Sơn vạch mòn', (.67,.638,.523))


class Facade:
    def __init__(self, x,y,nx,ny,length):
        self.origin = (x,y)
        self.normal = (nx,ny)
        self.tangent = (-ny,nx)
        self.length = length
        self.angle = math.atan2(nx,-ny)

    def point(self,u,v,z):
        x,y=self.origin
        a,b=self.tangent
        nx,ny=self.normal
        return (x+a*u+nx*v, y+b*u+ny*v, z)

    def u_at(self,x,y):
        return (x-self.origin[0])*self.tangent[0] + (y-self.origin[1])*self.tangent[1]

    def box(self,mesh,u,v,z,du,dv,dz,mat):
        mesh.box(self.point(u,v,z),(du,dv,dz),mat,angle=self.angle)

    def line(self,mesh,a,b,r,mat,sides=6):
        mesh.bar(self.point(*a),self.point(*b),r,mat,sides)

    def blocker(self,u0,u1,v0,v1):
        a,b=self.point(u0,v0,0),self.point(u1,v1,0)
        collider(min(a[0],b[0]),max(a[0],b[0]),min(a[1],b[1]),max(a[1],b[1]))

    def level(self,u0,u1,v0,v1,start,end=None):
        a,b=self.point(u0,v0,0),self.point(u1,v1,0)
        # The stair descends towards positive V. The game samples Blender's
        # positive X or Y after the GLB exporter converts Y to negative Z.
        end=start if end is None else end
        nx,ny=self.normal
        if nx<0 or ny<0:
            start,end=end,start
        floor(min(a[0],b[0]),max(a[0],b[0]),min(a[1],b[1]),max(a[1],b[1]),
              start,end,axis='x' if nx else 'depth')

    def text(self, group, words, u,v,z, height, mat=paper):
        return lettering(words,words,group,self.point(u,v,z),height,self.angle,mat)


def translucent_panel(mesh, facade, u0,u1,v,z0,z1,mat):
    vertices=[facade.point(u0,v,z0),facade.point(u1,v,z0),
              facade.point(u1,v,z1),facade.point(u0,v,z1)]
    mesh.add(vertices,[(0,1,2,3)],mat)


def slab(mesh,x0,x1,y0,y1,z,mat,depth=.08):
    mesh.box(((x0+x1)/2,(y0+y1)/2,z-depth/2),(x1-x0,y1-y0,depth),mat)


def path(mesh,x0,x1,y0,y1,mat, *, top=.055, joints=True):
    slab(mesh,x0,x1,y0,y1,top,mat)
    if not joints:
        return
    vertical = y1-y0 >= x1-x0
    length=y1-y0 if vertical else x1-x0
    first=y0 if vertical else x0
    for i in range(1,int(length/2.22)+1):
        mid=first+i*2.22
        if vertical:
            mesh.box(((x0+x1)/2,mid,top+.0005),(x1-x0,.014,.002),skirting)
        else:
            mesh.box((mid,(y0+y1)/2,top+.0005),(.014,y1-y0,.002),skirting)


terrain=Geometry('Sân cỏ và cao độ nền',site)
slab(terrain,-62,29,-88,52,-.018,lawn,depth=.24)
terrain.finish(noShadow=True)
roads=Geometry('Đường bao Khối C và Khối B',outer)
for x0,x1,y0,y1 in [(-56.0,-49.3,-80.8,39.4),(-56.0,21.3,39.4,46.4),
                     (17.8,24.8,-28.3,39.4),(-56,18.5,-85.1,-80.8),
                     (-33.55,-26.10,7.25,29.50),(-33.55,-26.10,30.75,38.9)]:
    path(roads,x0,x1,y0,y1,asphalt,top=.009,joints=False)
for x in (-56.0,-49.3):
    roads.box((x,-21.0,.057),(.12,120.8,.115),terrazzo)
for y in (-28,38):
    for n in range(9):
        roads.box((-55.5+n*.65,y,.014),(.29,2.1,.007),road_trim)
for y in range(-75,39,5):
    roads.box((-52.66,y,.013),(.097,1.9,.006),road_trim)
for x in range(-52,21,5):
    roads.box((x,42.9,.013),(1.94,.10,.006),road_trim)
for y in (8.0,12.85,17.7,22.55,27.4):
    roads.box((-29.46,y,.017),(5.76,.084,.006),plate_yellow)
roads.finish(noShadow=True)

paths=Geometry('Lối bê tông hai sân và các ô cỏ vườn miếu',site)
for index,(x0,x1,y0,y1,mat) in enumerate([
    (-10.16,-8.55,SOUTH,-3.25,walkway),(-2.21,-.54,SOUTH,-3.25,walkway),
    (-8.55,-2.21,-4.81,-3.25,walkway),
    (-11.02,3.18,-28.87,-25.37,paving),
    (-10.16,-8.55,-25.37,SOUTH,walkway),
    (-2.21,-.54,-25.37,SOUTH,paving),
    (-8.55,-2.21,-23.80,-22.29,paving),
    (-10.21,-8.61,13.35,NORTH,walkway),(-2.21,-.54,13.35,NORTH,walkway),
    (-8.61,-2.21,13.35,14.94,walkway),(-10.21,-.54,NORTH,NORTH+1.43,walkway),
    (-48.97,-10.16,-24.10,-22.44,walkway),
    (-36.9,-11.02,-28.02,-25.45,paving),
    (-24.99,-22.48,-40.02,-28.02,paving),
    (-31.05,-28.58,-22.44,7.25,paving),(-27.24,-25.74,-22.35,7.25,paving),
    (-27.17,-24.51,32.93,39.33,walkway),(-33.55,-25.70,29.50,30.74,walkway),
    (-25.76,-23.9,-17.96,-15.41,paving),
    (-23.40,-20.13,-25.45,-24.12,paving),(-15.98,-12.49,-25.45,-24.12,paving),
    (-47.35,-26.0,-41.8,-40.02,paving),(-43.08,-41.18,-40.02,-24.10,paving),
    (-30.22,-27.84,-40.02,-24.10,paving),(-41.18,-30.22,-33.06,-31.53,paving),
    (-37.68,-35.70,-40.02,-34.63,paving),(-34.66,-33.35,-40.02,-36.02,paving),
    (-27.83,-25.95,-80.15,-41.79,walkway),(-45.66,-25.95,-79.5,-77.77,walkway),
    (-25.95,-23.26,-42.24,-29.54,paving),(-22.48,-11.02,-29.00,-27.84,paving),
    (3.18,13.78,-28.90,-27.25,paving),
    (-10.75,1.77,-77.93,-76.36,walkway),(-10.75,1.77,-67.87,-66.25,walkway),
    (-10.75,1.77,-57.11,-55.51,walkway)
]):
    path(paths,x0,x1,y0,y1,mat,top=.054+index*.00042)
for x,y,length in [(-25.76,5.2,55),(-10.45,-12.1,19),(.70,-12.1,19),
                   (-10.45,22,20),(.70,22,20)]:
    paths.box((x,y,.007),(.52,length,.032),artificial_turf)
paths.box(((INNER+EAST)/2,CROSS_SOUTH-GALLERY-.26,.006),(EAST-INNER,.47,.03),artificial_turf)
# Small rounded landing beside the red mark, joining the paved approach.
center=(-36.10,-34.17)
points=[(*center,.053)]+[(center[0]+2.46*math.cos(a),center[1]+1.88*math.sin(a),.053)
                       for a in (index*math.tau/48 for index in range(48))]
paths.add(points,[(0,n+1,(n+1)%48+1) for n in range(48)],paving)
paths.finish(noShadow=True)

west_face=Facade(WEST,(SOUTH+NORTH)/2,-1,0,NORTH-SOUTH)
inner_face=Facade(INNER,(SOUTH+NORTH)/2,1,0,NORTH-SOUTH)
entry_face=Facade((WEST+INNER)/2,SOUTH,0,-1,INNER-WEST)
return_face=Facade((WEST+INNER)/2,NORTH,0,1,INNER-WEST)
bar_south=Facade((INNER+EAST)/2,CROSS_SOUTH,0,-1,EAST-INNER)
bar_north=Facade((INNER+EAST)/2,CROSS_NORTH,0,1,EAST-INNER)
east_face=Facade(EAST,(SOUTH+NORTH)/2,-1,0,NORTH-SOUTH)
c_face=Facade(C_EAST,(SOUTH+NORTH)/2,1,0,NORTH-SOUTH)
c_back=Facade(C_WEST,(SOUTH+NORTH)/2,-1,0,NORTH-SOUTH)

# Labels are only used where the recording makes the wording legible. Open
# passages and the room bays are positioned in order along each walk.
OUTER_ROOMS=[
    (-14.9,('B109',),True), (-8.05,(),False),
    (-.15,('XƯỞNG THỰC TẬP CÔNG NGHỆ THỰC PHẨM 3','Food Technology Lab 3'),False),
    (14.35,(),False),(20.87,(),True),
    (28.05,('PHÒNG PHÂN TÍCH KỸ THUẬT CAO 1','Advanced Technology Lab 1'),False)
]
INNER_ROOMS=[
    (-17.6,(),True),(-10.65,('KHO HÓA CHẤT','Chemical Warehouse'),False),(-5.1,(),False),
    (.25,('PHÒNG THÍ NGHIỆM QUÁ TRÌNH VÀ THIẾT BỊ','Unit Operations Lab'),True),
    (11.9,(),True),(19.0,(),True),
    (26.6,('PHÒNG PHÂN TÍCH KỸ THUẬT CAO 1','Advanced Technology Lab 1','B106A'),False)
]


def vertical_post(face, mesh, u,v,low,high, width=.25, depth=.27, mat=cream):
    face.box(mesh,u,v,(low+high)/2,width,depth,high-low,mat)


def runs(length, openings):
    """Continuous runs of a wall between stair or passage openings."""
    cursor=-length/2
    for a,b in sorted(openings):
        if a>cursor:
            yield cursor,a
        cursor=max(cursor,b)
    if cursor<length/2:
        yield cursor,length/2


def handrail(face, mesh, lo,hi,v,z):
    face.line(mesh,(lo,v,z+.82),(hi,v,z+.82),.019,rail,7)
    face.line(mesh,(lo,v,z+.10),(hi,v,z+.10),.013,rail,6)
    count=max(1,round((hi-lo)/.213))
    for i in range(count+1):
        u=lo+(hi-lo)*i/count
        face.line(mesh,(u,v,z),(u,v,z+.82),.013 if i%8 else .022,rail,6)


def base_steps(face, u, width, *, depth=GALLERY, length=1.35, mat=terrazzo):
    mesh=Geometry('Tam cấp · '+str(tuple(round(v,1) for v in face.point(u,depth,0)[:2])),faculty)
    for i in range(5):
        tread=length/5
        v=depth+(4.5-i)*tread
        top=GROUND*(i+1)/5
        face.box(mesh,u,v,top/2,width,tread+.002,top,mat)
        face.box(mesh,u,v+tread*.42,top-.012,width+.018,.038,.032,terrazzo)
    for s in (-1,1):
        off=u+s*(width/2+.083)
        v0,v1=depth-.085,depth+length+.018
        points=[(off-.083,v0,0),(off+.083,v0,0),(off+.083,v1,0),(off-.083,v1,0),
                (off-.083,v0,GROUND+.84),(off+.083,v0,GROUND+.84),
                (off+.083,v1,.66),(off-.083,v1,.66)]
        mesh.add([face.point(*p) for p in points],[tuple(reversed(p)) for p in BOX_FACES],cream)
        face.blocker(off-.091,off+.091,v0,v1)
    face.level(u-width/2,u+width/2,depth,depth+length,GROUND,0)
    mesh.finish()


def grille(face, mesh, panes, u,v,z,w,h, *, open_window=False, frosted_window=False):
    # Recessed glazing and the square grid continue across the fixed transom.
    low,high=z-h/2,z+h/2
    for off in (-w/2,w/2):
        face.box(mesh,u+off,v,z,.054,.10,h+.058,metal_gray)
    for height in (low,high):
        face.box(mesh,u,v,height,w+.056,.106,.052,metal_gray)
    translucent_panel(panes,face,u-w/2+.025,u+w/2-.025,v-.005,low+.018,high-.02,
                      frosted if frosted_window else glass_clear)
    for j in range(1,max(3,int(w/.44))):
        divisions=max(3,int(w/.44))
        off=u-w/2+j*w/divisions
        face.box(mesh,off,v+.032,z,.038,.054,h,metal_gray)
    for j in range(1,max(3,int(h/.175))):
        divisions=max(3,int(h/.175))
        height=low+j*h/divisions
        face.box(mesh,u,v+.036,height,w,.03,.024,metal_gray)
    if open_window:
        hinge=face.point(u+w*.491,v+.08,z)
        offset=(.23*face.normal[0],.23*face.normal[1],0)
        mesh.box((hinge[0]+offset[0],hinge[1]+offset[1],hinge[2]),(.43,.035,h-.08),frosted,angle=face.angle-.82)


def lab_name_plate(face, mesh, group, u, z, words):
    if not words:
        return
    width=.93 if len(words)==1 else max(1.08,min(1.68,len(words[0])*.031))
    height=.245 if len(words)==1 else .335
    face.box(mesh,u,.149,z,width,.048,height,plate_blue)
    for h in (-height/2+.012,height/2-.012):
        face.box(mesh,u,.179,z+h,width-.026,.005,.006,paper)
    if len(words)==1:
        face.text(group,words[0],u,.183,z,.148)
        return
    face.text(group,'KHOA HÓA HỌC VÀ KHOA HỌC SỰ SỐNG',u,.187,z+.106,.037)
    face.text(group,words[0],u,.187,z+.007,min(.100,width/max(len(words[0]),1)*1.31))
    face.text(group,words[1],u,.187,z-.104,.059)
    if len(words)>2:
        face.box(mesh,u+.59,.185,z-.284,.37,.036,.133,plate_blue)
        face.text(group,words[2],u+.59,.216,z-.29,.079)


def extract_fan(face, mesh, u,z,r=.23):
    face.box(mesh,u,.052,z,r*2.32,.103,r*2.22,backing)
    parts=[]
    for i in range(18):
        a=i*math.tau/18
        parts.append((u+(r-.013)*math.cos(a),.121,z+(r-.013)*math.sin(a)))
    mesh.tube([face.point(*p) for p in parts+[parts[0]]],.016,metal_gray,6)
    for leaf in range(4):
        a=leaf*math.pi/2+.45
        pts=[face.point(u+dr*math.cos(t+a),.134,z+dr*math.sin(t+a))
             for dr,t in [(.024,0),(r*.80,-.31),(r*.89,.05),(r*.59,.58),(.033,.29)]]
        mesh.add(pts,[(0,1,2,3,4)],roof)
    face.line(mesh,(u,.10,z),(u,.163,z),.061,metal_gray,13)
    for row in range(-2,3):
        h=row*.074
        width=math.sqrt(max(0,r*r-h*h))*2
        face.box(mesh,u,.159,z+h,width,.019,.013,metal_gray)


def notice_board(face, mesh, u,v,z,w,h, *, blue_strip=False):
    face.box(mesh,u,v,z,w+.056,.049,h+.042,dark_gold)
    face.box(mesh,u,v+.028,z,w,.029,h,paper)
    if blue_strip:
        face.box(mesh,u,v+.048,z+h*.346,w*.945,.008,h*.156,plate_blue)
    for j in range(9):
        off=rng.uniform(.686,.92)*w
        face.box(mesh,u-w*.44+off/2,v+.049,z+h*.242-j*h*.076,off,.008,.007,metal_gray)


def safety_signs(face, mesh, u, z):
    face.box(mesh,u,.167,z,.635,.030,.138,paper)
    for j in range(4):
        x=u+(j-1.5)*.146
        pts=[(x+.041*math.cos(a),.188,z+.043*math.sin(a))
             for a in (i*math.tau/10 for i in range(11))]
        mesh.tube([face.point(*p) for p in pts],.006,red,4)
        face.line(mesh,(x-.026,.190,z-.026),(x+.026,.190,z+.026),.006,red,4)


def make_door(face, details, glazing, u,w, words,is_open,group):
    low,top=GROUND,GROUND+2.28
    head=top+.48
    face.box(details,u,.005,top+.025,w+.08,.118,.075,metal_gray)
    for x in (u-w/2,u+w/2):
        vertical_post(face,details,x,.028,low,head,.078,.14,metal_gray)
    grille(face,details,glazing,u,.051,(top+head)/2,w-.026,head-top)
    face.box(details,u,.083,low+.018,w,.156,.037,terrazzo)
    # Open metal leaves are modelled on their real hinges so the exposed room
    # remains visible from a moving viewpoint.
    if is_open:
        for side in (-1,1):
            x=u+side*(w*.5-.05)
            origin=face.point(x,.056,0)
            angle=face.angle+side*.96
            door_axis=(math.cos(angle),math.sin(angle))
            width=w*.5-.085
            direction=-side
            x0,y0=origin[:2]
            center=(x0+door_axis[0]*width*.5*direction,y0+door_axis[1]*width*.5*direction)
            both=Geometry('Cánh cửa phòng mở',group)
            for z in (low+.155,top-.035):
                both.box((*center,z),(width,.074,.285 if z<low+.22 else .071),metal_gray,angle=angle)
            for s in (-1,1):
                both.box((center[0]+door_axis[0]*width*.47*s,center[1]+door_axis[1]*width*.47*s,(low+top)/2),
                         (.058,.083,top-low),metal_gray,angle=angle)
            for j in range(11):
                both.box((*center,low+.34+j*.165),(width,.034,.025),metal_gray,angle=angle)
            for j in (-1,0,1):
                both.box((center[0]+door_axis[0]*width*.235*j,center[1]+door_axis[1]*width*.235*j,(low+top)/2),
                         (.024,.039,top-low),metal_gray,angle=angle)
            both.finish()
    else:
        for side in (-1,1):
            v=u+side*w/4
            grille(face,details,glazing,v,.069,low+(top-low)/2,w/2-.047,top-low-.12,
                   frosted_window=True)
            face.box(details,v,.103,low+.12,w*.5-.044,.037,.233,metal_gray)
            face.line(details,(u+side*.084,.144,low+.92),(u+side*.084,.144,low+1.112),.015,rail,8)
    lab_name_plate(face,details,group,u-.145,top+.258,words)
    if words and len(words)>1:
        safety_signs(face,details,u+.80,top+.252)
    if is_open:
        for j in (-1,1):
            face.box(details,u+j*w*.36,.114,top+.226,.022,.027,.316,rail)
    return low,head


def low_wall(face,mesh,a,b,v,height):
    face.box(mesh,(a+b)/2,v,height/2,b-a,.183,height,cream)
    face.box(mesh,(a+b)/2,v,.085,b-a+.007,.184,.165,skirting)
    face.box(mesh,(a+b)/2,v,height+.023,b-a+.053,.236,.045,plaster)
    for i in range(max(1,int((b-a)//5.4))+1):
        u=a+.31+i*(b-a-.64)/max(1,int((b-a)//5.4))
        if a+.24<u<b-.23:
            face.box(mesh,u,v+.109,.354,.21,.16,.196,plaster)
            face.box(mesh,u,v+.194,.349,.127,.026,.105,backing)


def ac_unit(face,mesh,u,v,z):
    face.box(mesh,u,v,z,.70,.28,.57,cream)
    face.box(mesh,u-.08,v+.155,z,.41,.026,.39,metal_gray)
    for j in range(8):
        face.box(mesh,u-.08,v+.172,z-.169+j*.049,.41,.024,.015,roof)
    face.box(mesh,u+.227,v+.148,z-.172,.085,.026,.049,blue)
    for side in (-1,1):
        face.box(mesh,u+side*.23,v,z-.299,.073,.37,.068,rail)


def drainpipe(face,mesh,u,z0,roof_z,v=.188):
    pts=[(u,v+.18,z0),(u,v,z0+.163),(u,v,roof_z-.71),
         (u+.19,v,roof_z-.48),(u+.19,v+.19,roof_z-.32)]
    mesh.tube([face.point(*p) for p in pts],(.053,.053,.053,.048,.045),conduit,8)
    for offset in (1.2,2.85,5.3):
        if z0+offset<roof_z-.8:
            face.line(mesh,(u,v,z0+offset),(u,v,z0+offset+.043),.064,metal_gray,9)


def visible_lab(face, u, group):
    # Only the front part visible from the corridor is represented.
    inner_width=4.96
    room_depth=4.15
    shell=Geometry('Phòng thực hành nhìn từ cửa · tường và nền',group)
    props=Geometry('Bàn, tủ kính, ghế và chậu phòng thực hành',group)
    for off in (-inner_width/2,inner_width/2):
        vertical_post(face,shell,u+off,-room_depth/2,GROUND,GROUND+2.88,.138,room_depth,lab_wall)
        face.blocker(u+off-.073,u+off+.073,-room_depth,-.017)
    face.box(shell,u,-room_depth,GROUND+1.44,inner_width,.189,2.88,lab_wall)
    face.blocker(u-inner_width/2,u+inner_width/2,-room_depth-.09,-room_depth+.09)
    face.box(shell,u,-room_depth/2,GROUND-.087,inner_width+.12,room_depth,.174,lab_tile)
    face.box(shell,u,-room_depth/2,GROUND+2.906,inner_width+.1,room_depth,.25,lab_wall)
    for j in range(10):
        face.box(shell,u+(j-4.5)*.447,-room_depth/2,GROUND+.003,.007,room_depth,.004,plaster)
    for j in range(9):
        face.box(shell,u,-(j+.5)*.442,GROUND+.003,inner_width,.009,.004,plaster)
    nx,ny=face.normal
    if nx:
        a,b=face.point(u-inner_width/2,-room_depth,0),face.point(u+inner_width/2,0,0)
        floor(min(a[0],b[0]),max(a[0],b[0]),min(a[1],b[1]),max(a[1],b[1]),GROUND,GROUND)
    for t in (-1.19,1.095):
        face.box(props,u+t,-2.45,GROUND+.895,1.71,.81,.092,lab_counter)
        face.box(props,u+t,-2.45,GROUND+.44,1.65,.74,.84,wood)
        for col in (-.48,.0,.48):
            face.box(props,u+t+col,-2.035,GROUND+.456,.435,.064,.663,slat)
            face.box(props,u+t+col,-1.994,GROUND+.678,.134,.028,.029,rail)
        for k in range(4):
            face.box(props,u+t-.43+k*.28,-2.50,GROUND+1.11,.156,.19,.321,
                     rng.choice((cream,metal_gray,roof)))
        face.blocker(u+t-.87,u+t+.87,-2.87,-2.035)
    face.box(props,u+.79,-3.51,GROUND+1.15,1.80,.79,2.23,metal_gray)
    face.box(props,u+.79,-3.104,GROUND+1.25,1.65,.035,1.50,frosted)
    for i in range(4):
        face.box(props,u+.79,-3.079,GROUND+.607+i*.382,1.65,.019,.022,rail)
    for j in range(2):
        face.box(props,u+(j-.5)*1.70,-1.0,GROUND+2.68,1.14,.083,.055,tube_light)
    face.box(props,u,-3.54,GROUND+2.42,1.16,.222,.279,cream)
    face.box(props,u,-3.412,GROUND+2.192,1.03,.028,.042,backing)
    shell.finish()
    props.finish()


def gallery(face, group, name, *, storeys=3, depth=GALLERY, breaks=(), joins=(), doors=(),
            cross=None, brick_ground=False, low=False, ends=True, construction=False,
            junction_offset=0, shutters_after=None):
    structure=Geometry(name+' · dầm, sàn, mái và tường',group)
    details=Geometry(name+' · cửa, khung sắt, thiết bị và lan can',group)
    glazing=Geometry(name+' · kính',group)
    services=Geometry(name+' · máng cáp, ống nước và đèn',group)
    n=face.length
    top=GROUND+storeys*STOREY+junction_offset
    for fl in range(storeys):
        z=GROUND+fl*STOREY
        slab_depth=depth+(.12 if fl else 0)
        face.box(structure,0,slab_depth*.50-.055,z-.125+junction_offset,n+.014,slab_depth+.15,.248,
                 corridor_tiles if not fl else plaster)
        if fl:
            for i in range(1,round(n/3.72)+1):
                u=(i*3.72)-n/2
                if u<n/2:
                    face.box(structure,u,depth*.5,z-.251,.172,depth,.225,plaster)
        if fl==0:
            for a,b in runs(n,[*joins,*[(pos-width/2,pos+width/2) for pos,width in breaks]]):
                low_wall(face,structure,a,b,depth,GROUND+.86)
                face.blocker(a,b,depth-.09,depth+.09)
        elif fl==1 or low:
            face.box(structure,0,depth+.008,z+.415,n+.04,.243,.83 if not low else .50,cream)
            if low:
                handrail(face,details,-n/2,n/2,depth+.055,z+.258)
            else:
                face.box(structure,0,depth+.016,z+.825,n+.06,.29,.047,plaster)
        else:
            handrail(face,details,-n/2,n/2,depth+.024,z+.031)
        # Wall backing on the two upper floors is recessed behind the corridor.
        if fl:
            face.box(structure,0,-.145,z+STOREY/2,n,.258,STOREY,brick if fl==2 or low else cream)
            bays=round(n/(3.37 if low else 3.71))
            for j in range(bays):
                pitch=n/bays
                at=(j+.50)*pitch-n/2
                w=pitch-.66
                face.box(details,at,.023,z+1.579,w,.082,1.525,roof)
                for i in (0,1,2,3):
                    face.box(details,at+(i-1.5)*w*.232,.069,z+1.59,w*.219,.022,1.375,rng.choice(glass))
                for i in range(5):
                    face.box(details,at+(i-2)*w*.24,.084,z+1.593,.038,.053,1.53,metal_gray)
                for zoff in (.874,1.56,2.28):
                    face.box(details,at,.085,z+zoff,w+.048,.051,.043,metal_gray)
        for i in range(round(n/3.72)+1):
            u=min(n/2-.16,-n/2+.16+i*3.72)
            vertical_post(face,structure,u,depth+.065,z+.035,z+STOREY-.105,.208,.24,cream)
            if fl==0:
                face.blocker(u-.12,u+.12,depth-.12,depth+.16)
    if ends:
        face.box(structure,0,depth*.52,top-.009,n+.68,depth+1.38,.242,roof)
        face.box(structure,0,depth+1.05,top+.007,n+.75,.124,.297,plaster)
        for i in range(round(n/.205)):
            u=-n/2+i*.205
            face.box(structure,u,depth*.65,top-.146,.032,depth+1.0,.042,roof)
    else:
        face.box(structure,0,depth*.53,top,n+.38,depth+1.05,.238,roof)
        face.box(structure,0,depth+1.00,top,n+.42,.118,.26,plaster)
    face.level(-n/2,n/2,-.025,depth+.026,GROUND)
    if ends:
        for side in (-1,1):
            u=side*(n/2+.06)
            face.box(structure,u,depth*.5,.42,.189,depth,.84,cream)
            face.blocker(u-.091,u+.091,0,depth)
    # Ground-floor doors alternate with window banks. A plaster ribbon fills
    # the sill and the dark brick wall sections visible from the long hall.
    room_records=sorted(doors,key=lambda record: record[0])
    cuts=[(u-1.079,u+1.079) for u,*_ in room_records]
    if cross is not None:
        cuts.append((cross-1.19,cross+1.19))
    for a,b in runs(n,cuts):
        if b-a<.10:
            continue
        c=(a+b)/2
        w=b-a
        face.box(structure,c,-.116,GROUND+.403,w,.251,.806,
                 brick if brick_ground else lab_wall)
        face.box(structure,c,-.116,GROUND+2.869,w,.251,.435,
                 brick if brick_ground else lab_wall)
        face.blocker(a,b,-.247,.013)
        if brick_ground or w<.94 or (abs(c) > n/2-4.6 and room_records):
            face.box(structure,c,-.117,GROUND+1.71,w,.251,1.876,brick)
            if w>1.83 and (brick_ground or rng.random()<.49):
                notice_board(face,details,c-.32,.043,GROUND+1.48,.34,.489,blue_strip=True)
                if w>2.20:
                    notice_board(face,details,c+.25,.04,GROUND+1.45,.32,.429)
            continue
        width=max(.61,w-.58)
        nwin=max(1,round(width/2.60))
        size=width/nwin
        for i in range(nwin):
            at=c+(i+.5)*size-width/2
            grille(face,details,glazing,at,.035,GROUND+1.678,size-.084,1.72,
                   open_window=(i==1 and low is False),frosted_window=not low)
            if shutters_after is not None and at>shutters_after:
                for side in (-1,1):
                    panel=at+side*size*.339
                    face.box(details,panel,.161,GROUND+1.665,size*.25,.068,1.68,shutter)
                    for sl in range(16):
                        face.box(details,panel,.203,GROUND+.939+sl*.095,size*.22,.032,.023,slat)
        for x in (c-width*.5-.12,c+width*.5+.12):
            face.box(structure,x,-.119,GROUND+1.717,.25,.24,1.89,lab_wall)
        if w>2.44 and rng.random()<.73:
            ac_unit(face,services,c-.31,.225,GROUND+.407)
        if w>3.7 and rng.random()<.62:
            extract_fan(face,details,c+.57,GROUND+2.373,.228)
    for u,words,is_open in room_records:
        low_z,top_z=make_door(face,details,glazing,u,2.04,words,is_open,group)
        face.box(structure,u,-.144,(top_z+GROUND+STOREY)/2,2.148,.295,
                 GROUND+STOREY-top_z,lab_wall)
        if is_open:
            visible_lab(face,u,labs)
        else:
            face.blocker(u-1.082,u+1.082,-.27,.145)
            if rng.random()<.55:
                notice_board(face,details,u+.51,.116,low_z+1.425,.364,.52,blue_strip=True)
    if cross is not None:
        face.box(structure,cross,-.117,GROUND+2.878,2.38,.249,.443,brick)
    for j in range(round(n/3.85)):
        u=-n/2+1.38+j*3.85
        face.box(services,u,depth*.56,GROUND+2.793,1.16,.095,.039,tube_light)
        face.box(services,u,depth*.56,GROUND+2.827,1.22,.127,.041,roof)
        if j%4==0 and construction:
            loc=face.point(u,depth*.51,GROUND+2.60)
            light=bpy.data.objects.new('Đèn hắt hành lang',None)
            utilities.objects.link(light)
            light.location=loc
            light['courtyardLight']='corridor'
    if construction:
        # Continuous perforated cable tray on the courtyard side, and the
        # cream drainpipes and larger bends recorded on the outer side.
        if face is inner_face:
            tray_v=.443
            z=GROUND+2.778
            face.box(services,0,tray_v,z,n-.055,.312,.045,rail)
            face.box(services,0,tray_v-.164,z+.049,n-.054,.03,.121,rail)
            face.box(services,0,tray_v+.163,z+.049,n-.054,.03,.121,rail)
            for i in range(int(n/.195)):
                u=-n/2+.094+i*.195
                row_shift=.044 if i%2 else 0
                for v in (-.088,.005,.093):
                    face.box(services,u+row_shift,tray_v+v,z-.025,.05,.018,.004,backing)
            for i in range(int(n/1.92)+1):
                u=-n/2+.28+i*1.92
                if u>n/2: break
                face.box(services,u,tray_v,z-.041,.095,.417,.065,frame)
                for v in (tray_v-.185,tray_v+.186):
                    face.line(services,(u,v,z-.014),(u,v,GROUND+3.05),.012,roof,5)
            for i in range(3):
                pts=[(u,.174+i*.026,GROUND+2.655+.03*i-.054*math.sin(u*.6+i)**2)
                     for u in np.linspace(-n/2+.01,n/2-.01,72)]
                services.tube([face.point(*p) for p in pts],.012,backing,5)
        for u in np.linspace(-n/2+.43,n/2-.43,11):
            if any(abs(u-p)<1.3 for p,*_ in room_records): continue
            drainpipe(face,services,u,GROUND+.012,top)
        if face is west_face:
            for i,u in enumerate((-20.8,-15.62,-10.54)):
                z=GROUND+2.05
                pts=[(u,-.070,z),(u,.23,z),(u,.38,z+.17),(u,.38,z+.58),
                     (u-.17,.38,z+.77),(u-.24,.315,z+.83)]
                services.tube([face.point(*p) for p in pts],(.169,.169,.162,.149,.14,.121),
                              roof,13,irregular=.040)
    structure.finish()
    details.finish()
    glazing.finish(noShadow=True)
    services.finish()


outer_doors=[(west_face.u_at(WEST,y),label,opened) for y,label,opened in OUTER_ROOMS]
inner_doors=[(inner_face.u_at(INNER,y),label,opened) for y,label,opened in INNER_ROOMS]
inner_join=inner_face.u_at(INNER,CROSS_HALL_Y)
east_join=east_face.u_at(EAST,CROSS_HALL_Y)
gallery(west_face,faculty,'Mặt ngoài dãy phòng lab',ends=False,doors=outer_doors,
        breaks=[(west_face.u_at(WEST,3.52),2.37)], joins=[(-27.5,-25.12),(25.12,27.5)],
        cross=west_face.u_at(WEST,CROSS_HALL_Y),construction=True)
gallery(inner_face,faculty,'Mặt nhìn vào sân trong',ends=False,doors=inner_doors,
        joins=[(-27.5,-25.12),(inner_join-1.19,inner_join+1.19),(25.12,27.5)],
        cross=inner_join,construction=True)
gallery(entry_face,faculty,'Mặt biển khoa và hai bậc vào',ends=False,brick_ground=True,
        breaks=[(-3.64,2.42),(3.58,2.42)])
gallery(return_face,faculty,'Bẻ góc hành lang cạnh cụm nhà ghép',ends=False,
        breaks=[(-3.63,2.12)],brick_ground=True)
gallery(bar_south,tower,'Thanh ngang phía vườn có chữ B',ends=False,
        breaks=[(-6.39,1.89),(6.25,1.93)], doors=[(-3.95,(),False),(1.18,(),False),(3.4,(),False)],
        junction_offset=.024)
gallery(bar_north,tower,'Thanh ngang phía sân sau',ends=False,
        doors=[(-4.25,(),False),(1.55,(),False),(4.55,(),False)],junction_offset=.024)
gallery(east_face,tower,'Cánh đối diện của khối B',ends=False,
        breaks=[(-22.4,2.16),(22.8,2.18)], joins=[(-27.5,-25.12),(east_join-1.19,east_join+1.19),(25.12,27.5)],
        doors=[(-18.2,(),False),(-9.55,(),False),(-1.33,(),False),(8.15,(),False),(17.00,(),False)],
        shutters_after=east_face.u_at(EAST,-13.5))
gallery(c_face,low_wing,'Khối C nhìn sang hành lang khoa',storeys=2,depth=1.47,
        doors=[(-18.1,(),False),(-6.6,(),False),(6.45,(),False),(17.1,(),False)],
        breaks=[(-12.6,2.37)],low=True)
gallery(c_back,low_wing,'Mặt ngoài khối C về đường bao',storeys=2,depth=1.50,low=True)

for face,u,width,depth,length,mat in [
    (entry_face,-3.64,2.42,GALLERY,1.51,terrazzo),(entry_face,3.58,2.42,GALLERY,1.49,terrazzo),
    (return_face,-3.63,2.12,GALLERY,1.42,terrazzo),
    (west_face,west_face.u_at(WEST,3.52),2.37,GALLERY,1.02,terrazzo),
    (bar_south,-6.39,1.89,GALLERY,1.19,brick),(bar_south,6.25,1.93,GALLERY,1.20,brick),
    (east_face,-22.4,2.16,GALLERY,1.32,brick),(east_face,22.8,2.18,GALLERY,1.17,brick),
    (c_face,-12.6,2.37,1.47,1.15,terrazzo)
]:
    base_steps(face,u,width,depth=depth,length=length,mat=mat)

shells=Geometry('Khối mái, góc giao và các mặt hậu',tower)
for x0,x1,y0,y1,storeys in [(WEST,INNER,SOUTH,NORTH,3),
                            (INNER,EAST,CROSS_SOUTH,CROSS_NORTH,3),
                            (EAST,EAST_OUT,SOUTH,NORTH,3),(C_WEST,C_EAST,SOUTH,NORTH+.58,2)]:
    top=GROUND+storeys*STOREY
    shells.box(((x0+x1)/2,(y0+y1)/2,top+.019),(x1-x0,y1-y0,.218),roof)
    for y in (y0+.105,y1-.105):
        shells.box(((x0+x1)/2,y,top+.083),(x1-x0,.153,.23),plaster)
    for x in (x0+.085,x1-.085):
        shells.box((x,(y0+y1)/2,top+.082),(.15,y1-y0,.237),plaster)
for x0,x1,y0,y1 in [(WEST-GALLERY,WEST,SOUTH-GALLERY,SOUTH),
                     (INNER,INNER+GALLERY,SOUTH-GALLERY,SOUTH),
                     (WEST-GALLERY,WEST,NORTH,NORTH+GALLERY),
                     (INNER,INNER+GALLERY,NORTH,NORTH+GALLERY)]:
    for floor_index in range(4):
        z=GROUND+floor_index*STOREY-.006
        slab(shells,x0,x1,y0,y1,z,corridor_tiles if not floor_index else cream,
             depth=.175 if not floor_index else .215)
    floor(x0,x1,y0,y1,GROUND,GROUND)

# Close the raised slab at the signed corner down to the grass.
slab(shells,INNER,INNER+GALLERY,SOUTH-GALLERY,SOUTH,GROUND-.176,cream,depth=GROUND-.176)
shells.box((INNER+GALLERY-.04,SOUTH-GALLERY*.5,.093),(.12,GALLERY,.186),skirting)
shells.box((INNER+GALLERY*.5,SOUTH-GALLERY+.08,.093),(GALLERY,.16,.186),skirting)
collider(INNER,INNER+GALLERY,SOUTH-GALLERY-.07,SOUTH-GALLERY+.10)

def end_wall(mesh,x0,x1,y,levels,material):
    height=GROUND+STOREY*levels
    mesh.box(((x0+x1)/2,y,height/2),(x1-x0,.236,height),material)
    facing=-1 if y==SOUTH else 1
    for floor_index in range(levels):
        for j in range(3):
            x=x0+(j+.5)*(x1-x0)/3
            z=GROUND+1.63+floor_index*STOREY
            mesh.box((x,y+facing*.153,z),(1.7,.073,1.05),frame)
            for offset in (-.45,0,.45):
                mesh.box((x+offset,y+facing*.195,z),(.412,.039,.88),glass[(j+floor_index)%len(glass)])
    collider(x0,x1,y-.12,y+.12)

for edge in (SOUTH,NORTH):
    end_wall(shells,EAST,EAST_OUT,edge,3,cream)
    end_wall(shells,C_WEST,C_EAST,edge,2,brick)
z=GROUND+STOREY*3
shells.box((EAST_OUT,(SOUTH+NORTH)/2,z/2),(.24,NORTH-SOUTH,z),cream)
for floor_index in range(3):
    for i in range(16):
        y=SOUTH+1.72+i*3.27
        h=GROUND+1.67+floor_index*STOREY
        shells.box((EAST_OUT+.145,y,h),(.081,1.86,1.13),frame)
        for j in range(3):
            shells.box((EAST_OUT+.19,y+(j-1)*.541,h),(.04,.50,.954),glass[(i+j)%len(glass)])
collider(EAST_OUT-.12,EAST_OUT+.12,SOUTH,NORTH)
# Middle bar of the H: upper slabs continue through, while the covered
# ground-floor passage joins the recorded brick corridor in B's west arm.
for k in range(4):
    z=GROUND+STOREY*k
    slab(shells,INNER,EAST,CROSS_SOUTH,CROSS_NORTH,z,plaster,depth=.19)
for y in (CROSS_SOUTH+.14,CROSS_NORTH-.14):
    shells.box(((INNER+EAST)/2,y,GROUND+1.36),(EAST-INNER,.25,2.72),brick)
    collider(INNER,EAST,y-.125,y+.125)
for x in (INNER+2.92,INNER+7.46,INNER+11.88):
    shells.box((x,CROSS_HALL_Y,GROUND+2.64),(1.25,.115,.048),tube_light)
floor(INNER,EAST,3.35,5.70,GROUND,GROUND)
shells.finish()

cross_hall=Geometry('Hành lang gạch ngang giữa hai mặt dãy phòng lab',faculty)
lo,hi=3.35,5.70
slab(cross_hall,WEST,INNER,lo,hi,GROUND,corridor_tiles,depth=.181)
slab(cross_hall,WEST,INNER,lo,hi,GROUND+STOREY,plaster,depth=.202)
floor(WEST,INNER,lo,hi,GROUND,GROUND)
for y in (lo-.099,hi+.099):
    cross_hall.box(((WEST+INNER)/2,y,GROUND+1.46),(INNER-WEST,.191,2.92),brick)
    collider(WEST,INNER,y-.097,y+.097)
    for x in (-21.54,-19.24,-16.85,-14.83):
        for direction in (1,-1):
            if (direction>0)!=(y<3.5): continue
            cross_hall.box((x,y+direction*.11,GROUND+1.6),(.45,.033,.55),paper)
for x in (-21.43,-18.22,-14.41):
    cross_hall.box((x,(lo+hi)/2,GROUND+STOREY-.14),(1.11,.105,.049),tube_light)
cross_hall.finish()

# The exterior bridge in 4187 is at the entrance approached from the sign.
# Its floor runs above the concrete walk and does not close the courtyard.
bridge=Geometry('Cầu nối tầng một ngay lối vào sân B',faculty)
x0,x1=INNER+GALLERY-.09,EAST-GALLERY+.09
y0,y1=BRIDGE_Y-.93,BRIDGE_Y+.93
deck=GROUND+STOREY
slab(bridge,x0,x1,y0,y1,deck,cream,depth=.31)
for y in (y0+.111,y1-.112):
    bridge.box(((x0+x1)/2,y,deck+.253),(x1-x0,.246,.54),cream)
    railing(bridge,(x0,y,deck+.51),(x1,y,deck+.51),.36)
    for x in (x0+.20,x1-.26):
        bridge.box((x,y,(deck-.3)/2),(.263,.255,deck-.30),cream)
        collider(x-.14,x+.14,y-.14,y+.14)
bridge.finish()

staircase=Geometry('Thang hai vế bên phải cầu nối sân B',faculty)
for flight in range(2):
    z0=flight*(STOREY/2)
    x=.48+flight*1.13
    y0=BRIDGE_Y-3.26 if not flight else BRIDGE_Y-.46
    direction=1 if not flight else -1
    for i in range(9):
        y=y0+direction*(i+.5)*.30
        z=GROUND+z0+STOREY/2*(i+1)/9
        staircase.box((x,y,z-.075),(1.10,.302,.15),terrazzo)
        staircase.box((x,y-direction*.12,z-.024),(1.11,.065,.052),rail)
    y1=y0+direction*2.70
    for off in (-.55,.55):
        railing(staircase,(x+off,y0,GROUND+z0),(x+off,y1,GROUND+z0+STOREY/2),.92)
        staircase.bar((x+off,y0,GROUND+z0-.12),(x+off,y1,GROUND+z0+STOREY/2-.12),.087,cream,8)
    collider(x-.56,x+.56,min(y0,y1),max(y0,y1))
staircase.box((1.04,BRIDGE_Y-.16,GROUND+STOREY/2-.11),(2.24,.83,.23),cream)
staircase.box((1.94,BRIDGE_Y-3.52,GROUND+STOREY-.11),(2.66,.79,.23),cream)
staircase.box((1.63,BRIDGE_Y-1.86,GROUND+STOREY-.11),(1.63,3.06,.22),cream)
railing(staircase,(.74,BRIDGE_Y-3.89,deck),(3.23,BRIDGE_Y-3.89,deck),.92)
staircase.finish()

signs=Geometry('Biển xanh mới, mặt chữ B và bảng sơ đồ chân thang',faculty)
u,v,z=2.36,GALLERY+.191,GROUND+STOREY+.391
entry_face.box(signs,u,v,z,5.27,.075,.684,blue)
entry_face.box(signs,u,v+.047,z,5.18,.024,.593,plate_blue)
for side in (-1,1):
    entry_face.line(signs,(u+side*2.335,v+.065,z),(u+side*2.335,v+.088,z),.201,paper,24)
    entry_face.line(signs,(u+side*2.335,v+.086,z),(u+side*2.335,v+.093,z),.164,blue,24)
    entry_face.line(signs,(u+side*2.335,v+.091,z),(u+side*2.335,v+.099,z),.139,paper,24)
    entry_face.line(signs,(u+side*2.335,v+.097,z),(u+side*2.335,v+.106,z),.086,
                    red if side < 0 else plate_blue,16)
entry_face.text(faculty,'TRƯỜNG ĐẠI HỌC CÔNG NGHỆ KỸ THUẬT TP. HỒ CHÍ MINH',
                u,v+.082,z+.178,.109)
entry_face.text(faculty,'KHOA HÓA HỌC VÀ KHOA HỌC SỰ SỐNG',u,v+.080,z+.016,.205)
entry_face.text(faculty,'FACULTY OF CHEMISTRY AND LIFE SCIENCES',u,v+.079,z-.186,.102)
board_angle=-.50
board=Facade(-12.29,-25.37,math.sin(board_angle),-math.cos(board_angle),.93)
board.box(signs,0,0,1.19,.93,.063,1.67,frame)
board.box(signs,0,.046,1.19,.87,.029,1.61,paper)
board.text(faculty,'SƠ ĐỒ PHÒNG KHU B',0,.064,1.89,.066,plate_blue)
for col in (-.275,.075):
    board.box(signs,col,.065,1.37,.085,.006,.79,metal_gray)
    for row in range(7):
        board.box(signs,col,.067,1.04+row*.109,.189,.006,.024,blue)
board.box(signs,-.10,.065,1.36,.35,.006,.084,metal_gray)
for i in range(12):
    board.box(signs,.276,.067,.81+i*.069,.151+(i%3)*.024,.006,.009,metal_gray)
for dx in (-.37,.37):
    board.line(signs,(dx,0,0),(dx,0,1.72),.034,rail)
board.blocker(-.47,.47,-.07,.07)
entry_light=bpy.data.objects.new('Đèn hắt bảng khoa',None)
utilities.objects.link(entry_light)
entry_light.location=entry_face.point(u,GALLERY+1.27,z-.22)
entry_light['courtyardLight']='gallery'
bar_south.text(tower,'B',.62,GALLERY+.184,GROUND+STOREY+.428,1.06,plate_blue)
signs.finish()

# The adjacent footprints are positioned from the supplied plan. The garden
# is west of the library, between the south end of C and the north end of D.
wing(neighbors,'Khối D quay ra vườn miếu',-34.15,-60.45,38.2,11.25,3,1,chemistry=False)
wing(neighbors,'Mặt thư viện nhìn về phía miếu',-22.70,-37.9,17.65,34.05,4,-1,chemistry=True)
wing(neighbors,'Dãy A phía gần vườn',-22.3,-62.6,32.0,10.35,2,-1)
wing(neighbors,'Dãy A phía còn lại',11.20,-62.6,32.0,9.60,2,1)

adjacent=Geometry('Ốp gạch đỏ, đầu hồi C và lối vào thư viện',neighbors)
for x,y,w,d,h in [(-22.28,-30.25,1.12,3.25,12.1),(-33.33,-43.0,1.66,3.37,9.7)]:
    adjacent.box((x,y,h*.5),(w,d,h),cladding)
    for floor_index in range(3):
        z=2.0+floor_index*3.05
        adjacent.box((x,y-d/2-.07,z),(.735,.123,1.12),frame)
        adjacent.box((x,y-d/2-.143,z),(.621,.049,.927),glass[2])
        adjacent.box((x+.025,y-d/2-.18,z),(.05,.032,1.02),rail)
    collider(x-w*.5,x+w*.5,y-d*.5,y+d*.5)
library_front=Facade(-5.7,-29.075,0,1,34)
for floor_index in range(4):
    z=1.61+floor_index*STOREY
    for j in range(9):
        u=-14.4+j*3.37
        library_front.box(adjacent,u,.107,z,2.6,.23,1.24,frame)
        for k in (-1,0,1):
            library_front.box(adjacent,u+k*.8,.249,z,.747,.08,1.048,glass[2])
library_front.box(adjacent,.9,.154,3.18,5.06,.25,.72,cladding)
library_front.text(neighbors,'THƯ VIỆN',.9,.303,3.18,.39)
for y in (-46.4,-29.15):
    adjacent.box((-5.6,y,6.25),(34.05,.26,12.5),cladding)
    collider(-22.65,11.44,y-.13,y+.13)
adjacent.finish()

# 4187 02:08–02:48 shows planting as layered, low curved edges with the
# palm and two columns of drooping foliage in the middle.
hedge_bed=Geometry('Bồn xây cong và hàng viền cắt tỉa',site)
hedge_leaves=Geometry('Lá thường xanh trên hàng viền',trees)
border_stone=tiled('Đá nâu ốp chân bồn cong',(.396,.286,.237),'stone',1.7)
mulch_texture=tiled('Đất ẩm dưới tán',(.276,.240,.170),'soil',2.6)
hedge_top=tiled('Mặt hàng cây cắt tỉa',(.258,.365,.181),'hedge',1.2)
hedge_edge=tiled('Cạnh hàng cây cắt tỉa',(.215,.31,.149),'hedge',1.2)
BED_X,BED_Y=-5.42,-12.65
BED_RX,BED_RY=2.72,6.89


def ellipse(cx,cy,rx,ry,a,z):
    return (cx+rx*math.cos(a),cy+ry*math.sin(a),z)


def hedge(cx,cy,rx,ry,height, *, from_angle=0,to_angle=math.tau):
    n=round(69*(to_angle-from_angle)/math.pi)
    for i in range(n):
        a=from_angle+(to_angle-from_angle)*i/n
        b=from_angle+(to_angle-from_angle)*(i+1)/n
        contour=[ellipse(cx,cy,rx,ry,ang,z) for ang,z in ((a,.003),(b,.003),(b,.205),(a,.205))]
        hedge_bed.add(contour,[(0,1,2,3)],border_stone)
        rim=[ellipse(cx,cy,rx-off,ry-off,theta,z)
             for off,theta,z in [(-.073,a,.193),(-.073,b,.193),(-.073,b,.255),(-.073,a,.255),
                                 (.17,a,.255),(.17,b,.255)]]
        hedge_bed.add(rim,[(0,1,2,3),(3,2,5,4)],terrazzo)
        upper=[ellipse(cx,cy,rx-.135,ry-.135,theta,z)
               for theta,z in ((a,.236),(b,.236),(b,height-.067),(a,height-.070))]
        inner=[ellipse(cx,cy,rx-.75,ry-.75,theta,z)
               for theta,z in ((a,height-.06),(b,height-.055),(b,.237),(a,.237))]
        top=[upper[-1],upper[-2],inner[1],inner[0]]
        hedge_bed.add(upper,[(0,1,2,3)],hedge_edge)
        hedge_bed.add(inner,[(0,1,2,3)],hedge_edge)
        hedge_bed.add(top,[(0,1,2,3)],hedge_top)
        for j in range(21):
            theta=rng.uniform(a,b)
            d=rng.uniform(.10,.83)
            z=height+rng.uniform(-.065,.045)
            if j%3==0:
                d=rng.choice((.105,.778))+rng.uniform(-.035,.038)
                z=rng.uniform(.29,height-.02)
            p=ellipse(cx,cy,rx-d,ry-d,theta,z)
            phi=rng.uniform(0,math.tau)
            length=rng.uniform(.074,.144)
            hedge_leaves.leaf(p,(math.cos(phi),math.sin(phi),rng.uniform(-.63,.67)),
                              length,rng.uniform(.034,.077),rng.choice(green_hedge))
    for j in range(0,n,4):
        a=from_angle+(to_angle-from_angle)*(j+.5)/n
        x,y,_=ellipse(cx,cy,rx-.36,ry-.36,a,0)
        collider(x-.56,x+.56,y-.56,y+.56)


hedge(BED_X,BED_Y,BED_RX,BED_RY,.66)
hedge(-5.43,-12.58,1.90,4.92,.83,from_angle=.10,to_angle=3.33)
hedge(-5.4,-12.59,1.24,3.03,.76,from_angle=3.30,to_angle=6.32)
center=(BED_X,BED_Y,.035)
floor_points=[center]+[ellipse(BED_X,BED_Y,BED_RX-.23,BED_RY-.23,i*math.tau/76,.035) for i in range(76)]
hedge_bed.add(floor_points,[(0,i+1,(i+1)%76+1) for i in range(76)],mulch_texture)
hedge_bed.finish()
hedge_leaves.finish(noShadow=True)

beds=Geometry('Nắp hố kỹ thuật, ống tưới và bảng thấp cạnh bồn',site)
for ox,oy,w,d,mat in [(-3.79,-8.63,1.10,.92,artificial_turf),(-2.55,-9.17,.93,.77,artificial_turf),
                    (-4.51,12.77,.72,.61,terrazzo),(13.21,15.65,.94,.67,walkway),
                    (-5.25,23.79,.69,.81,walkway),(11.76,-9.48,.68,.86,walkway)]:
    x,y=court_position(ox,oy)
    beds.box((x,y,.061),(w*.70,d*.72,.125),mat,angle=.05)
    beds.box((x,y,.124),(w*.70-.057,d*.72-.06,.019),mat,angle=.05)
hose=[(-7.88,-16.62,.10),(-8.13,-16.58,.038),(-8.42,-16.81,.031),
      (-8.36,-17.19,.035),(-8.02,-17.34,.03),(-7.71,-17.19,.042),
      (-7.88,-16.92,.054),(-7.78,-16.60,.224),(-7.77,-16.60,.63)]
beds.tube(hose,.018,conduit,8)
beds.bar((-7.77,-16.60,.02),(-7.77,-16.60,.64),.033,rail,8)
beds.box((-7.74,-16.51,.58),(.68,.052,.32),roof,angle=.19)
for dx in (-.24,.24):
    beds.bar((-7.74+dx,-16.50,0),(-7.74+dx,-16.50,.72),.023,rail)
for i in range(6):
    beds.box((-7.74,-16.548,.697-i*.037),(.51-i*.043,.012,.008),plaster,angle=.19)
beds.finish()

vegetation=Geometry('Cọ, cụm lá rủ và cây sứ sân trong',trees)
foliage=Geometry('Lá thật dựng bằng lưới',trees)


def palm(x,y,h,spread):
    p=Vector((x,y,0))
    stem=[p+Vector((t*t*.28,-t*.17,t*h)) for t in (0,.18,.4,.59,.78,1)]
    vegetation.tube(stem,(.27,.218,.199,.181,.161,.18),light_bark,12,irregular=.073)
    for i in range(25):
        t=(i+.45)/25
        p2=p+Vector((t*t*.28,-t*.17,t*h))
        vegetation.bar(p2,p2+Vector((0,0,.021)),.19+.024*(1-t),light_bark,8)
    center=stem[-1]
    for i in range(19):
        theta=i*2.39996
        a=Vector((math.cos(theta),math.sin(theta),0))
        b=Vector((-a.y,a.x,0))
        size=spread*rng.uniform(.65,1.04)
        points=[center+a*(size*t)+Vector((0,0,size*(.66*math.sin(t*2.45)-t*.82))) for t in np.linspace(0,1,8)]
        vegetation.tube(points,[.028*(1-j/8) for j in range(8)],green_hedge[2],5)
        for j in range(19):
            t=(j+1)/20
            bucket=min(6,int(t*7))
            pt=points[bucket].lerp(points[bucket+1],t*7-bucket)
            for flip in (-1,1):
                length=size*(.073+.25*math.sin(t*math.pi))*rng.uniform(.84,1.10)
                foliage.leaf(pt,a*.59+b*flip*.83+Vector((0,0,-.28)),length,length*.135,rng.choice(green_hedge))
    collider(x-.25,x+.25,y-.25,y+.25)


def hanging_crown(x,y,h,radius):
    p=Vector((x,y,0))
    vegetation.tube([p,p+Vector((-.14,.11,h*.44)),p+Vector((.09,.14,h*.87)),p+Vector((.21,.15,h))],
                     (.178,.128,.076,.025),light_bark,10,irregular=.092)
    for i in range(35):
        a=i*2.39996
        level=rng.uniform(.50,.98)
        r=radius*rng.uniform(.55,1.10)*math.sin((level-.38)*math.pi/1.15)
        start=p+Vector((.09,.13,h*level))
        end=start+Vector((r*math.cos(a),r*math.sin(a),rng.uniform(.17,.65)))
        vegetation.tube([start,start.lerp(end,.61),end],(.048,.023,.008),dark_bark,6)
        for j in range(34):
            pt=start.lerp(end,rng.uniform(.40,1.06))+Vector((rng.uniform(-.29,.29),rng.uniform(-.29,.29),rng.uniform(-.32,.27)))
            phi=rng.uniform(0,math.tau)
            l=rng.uniform(.37,.85)
            foliage.leaf(pt,(math.cos(phi)*.54,math.sin(phi)*.54,-rng.uniform(.87,1.6)),
                         l,l*.20,rng.choice(green_hedge))
    collider(x-.18,x+.18,y-.18,y+.18)


def plumeria(x,y,h,size,phase):
    p=Vector((x,y,-.06))
    q=Vector((math.cos(phase),math.sin(phase),0))
    k=Vector((-q.y,q.x,0))
    trunk=[p,p+q*.13+Vector((0,0,.47)),p-q*.24+Vector((0,0,h*.28)),
           p+q*.09+Vector((0,0,h*.41)),p+q*.26+Vector((0,0,h*.59))]
    vegetation.tube(trunk,(.33,.27,.222,.17,.11),dark_bark,12,irregular=.25)
    for i in range(7):
        theta=i*2.39996+phase
        a=Vector((math.cos(theta),math.sin(theta),0))
        a2=Vector((-a.y,a.x,0))
        root=trunk[2+i%3]
        mid=root+a*size*.35+Vector((0,0,h*.14))
        end=root+a*size*rng.uniform(.75,1.035)+Vector((0,0,h*rng.uniform(.27,.44)))
        vegetation.tube([root,root.lerp(mid,.45),mid,mid.lerp(end,.52)+k*.14,end],
                         (.112,.094,.069,.044,.013),dark_bark,8,irregular=.23)
        for j in range(5):
            f=(j+2)/7
            at=mid.lerp(end,f)
            tip=at+a*rng.uniform(.31,.76)+((-1)**j)*a2*rng.uniform(.31,.79)+Vector((0,0,h*.13))
            vegetation.tube([at,at.lerp(tip,.49),tip],(.031,.022,.007),light_bark,6,irregular=.12)
            for leaf in range(2 if j%3 else 7):
                angle=theta+leaf*1.15
                foliage.leaf(tip+Vector((rng.uniform(-.075,.075),rng.uniform(-.075,.075),0)),
                             (math.cos(angle),math.sin(angle),.18),rng.uniform(.19,.37),.076,rng.choice(leaf_mats))
    collider(x-.32,x+.32,y-.32,y+.32)


palm(-5.49,-8.04,4.31,2.39)
hanging_crown(-5.95,-15.70,5.93,1.38)
hanging_crown(-4.92,-12.26,6.34,1.39)
for i,(x,y,h,r) in enumerate([
    (-27.19,2.22,5.6,2.8),(-26.31,-11.56,5.54,2.82),(-30.1,-23.48,4.76,2.98),
    (-12.15,-19.04,5.1,2.61),
    (-9.94,-18.2,4.85,2.26),(-9.88,-5.64,5.4,2.49),(-1.38,-7.37,5.02,2.63),
    (-27.4,-29.3,5.99,3.42),(-37.10,-28.5,5.18,3.21),(-31.50,-37.1,4.92,2.52)
]):
    plumeria(x,y,h,r,i*.98)
vegetation.finish()
foliage.finish()

for i,(x,y,h,r,w,gray) in enumerate([
    (-47.45,-17.2,15.9,4.52,.46,True),(-47.16,-5.1,16.4,4.7,.52,True),
    (-47.39,12.22,17.1,4.8,.51,False),(-47.36,25.62,15.4,4.4,.39,False),
    (-27.83,-17.6,14.6,4.59,.57,False),(-31.61,-10.81,15.6,4.5,.51,True),
    (-27.46,-2.81,16.02,4.97,.54,False),(-31.90,13.8,17.34,4.92,.57,True),
    (-28.38,33.62,13.1,4.38,.41,True),(-17.89,37.51,15.24,4.98,.51,False),
    (-8.40,36.85,15.77,4.43,.49,False),(-.10,-5.51,14.98,4.36,.61,False),
    (-8.1,-10.1,15.9,4.92,.52,True),(-2.95,-18.88,16.7,4.46,.59,False),
    (-6.65,24.13,13.40,4.5,.44,True),(-37.57,-24.80,15.97,4.81,.43,True),
    (-6.99,-24.58,15.4,4.63,.58,False),(-2.85,-27.15,11.73,3.56,.36,True),
    (-33.15,-29.31,17.1,5.46,.68,False),(-31.80,-36.31,16.35,4.96,.62,False),
    (-39.14,-34.92,15.56,4.61,.51,True),(-38.95,-39.75,15.78,4.91,.57,False),
    (-28.91,-43.44,14.88,4.66,.42,True),(-30.35,-61.53,14.34,4.41,.51,False),
    (-30.21,-70.16,16.42,4.72,.53,True)
]):
    broad_tree(f'Cây cao {i+1:02}',x,y,h,r,w,gray)

for i,y in enumerate((-19.76,-16.1,-11.23,-7.85)):
    bench(f'Ghế đá sát lối bê tông {i+1}',-10.13,y,math.pi/2)
bench('Ghế đá trắng cạnh ngã rẽ',-4.72,-24.53,.10)
for i,(x,y,a) in enumerate([(.03,-17.02,-math.pi/2),(.03,-9.83,-math.pi/2),
                            (-28.97,-25.51,.12),(-32.28,-26.11,-.04),(-35.45,-31.0,.84),
                            (-37.91,-37.95,.25),(-28.15,-39.44,-.75),(-40.36,-29.13,.20)]):
    bench(f'Ghế đá trong vườn {i+1}',x,y,a,brown=i in (0,3,6))
for x,y,brown in [(-35.46,-26.81,True),(-39.14,-38.11,False),(-31.61,-39.13,True),(-39.96,-27.22,False)]:
    seating(x,y,brown)

shrine_court=Geometry('Bệ và hàng rào thấp ở vườn miếu',furniture)
x,y=SHRINE
slab(shrine_court,x-1.83,x+1.83,y-1.59,y+1.59,.039,terrazzo)
for side in (-1,1):
    edge=x+side*1.83
    railing(shrine_court,(edge,y-1.60,.072),(edge,y+1.58,.072),.53)
    collider(edge-.064,edge+.064,y-1.60,y+1.58)
for a,b in [(x-1.81,x-.80),(x+.80,x+1.81)]:
    railing(shrine_court,(a,y+1.58,.065),(b,y+1.58,.065),.53)
shrine_court.finish()

grass=Geometry('Cỏ thấp, đất gốc và lá khô',trees)
grass_areas=[
    (-48.96,-46.89,SOUTH,NORTH),(-33.67,-25.70,SOUTH,7.08),
    (INNER+GALLERY,EAST-GALLERY,SOUTH,-3.30),
    (INNER+GALLERY,EAST-GALLERY,13.40,NORTH),
    (-47.31,-26.20,-40.0,-24.14),(-33.42,-26.00,-78.9,-42.25),
]
for x0,x1,y0,y1 in grass_areas:
    for i in range(int((x1-x0)*(y1-y0)*4.25)):
        x,y=rng.uniform(x0,x1),rng.uniform(y0,y1)
        if ((x-BED_X)/(BED_RX+.04))**2+((y-BED_Y)/(BED_RY+.04))**2<1:
            continue
        for j in range(2):
            phi=rng.uniform(0,math.tau)
            l=rng.uniform(.049,.145)
            grass.leaf((x+rng.uniform(-.06,.06),y+rng.uniform(-.06,.06),-.011),
                       (math.cos(phi),math.sin(phi),1.6),l,l*.212,rng.choice(green_hedge))
for i in range(380):
    x=rng.choice((-9.38,-1.31,-29.02))+rng.uniform(-.71,.71)
    y=rng.uniform(-22.2,-3.31)
    a=rng.uniform(0,math.tau)
    l=rng.uniform(.052,.13)
    grass.leaf((x,y,.06),(math.cos(a),math.sin(a),.06),l,l*.37,rng.choice(dry_leaves))
grass.finish(noShadow=True)

# 4185 01:04–01:34: the strip in front of the outside parapet switches
# from lawn to parked cars and scooters, with the low bridge into the lot.
def parked_car(x,y,angle,color):
    mesh=Geometry('Ô tô đỗ khu hành lang ngoài',parking)
    co,si=math.cos(angle),math.sin(angle)
    def point(a,b,z):
        return (x+a*co-b*si,y+a*si+b*co,z)
    p=[(-2.22,.63,.29,.61),(-2.07,.84,.27,.75),(-1.63,.91,.31,.845),
       (-.73,.922,.29,.90),(.4,.93,.28,.867),(1.47,.87,.31,.78),(2.11,.79,.37,.63)]
    vertices=[]
    for at,w,low,high in p:
        vertices.extend([point(at,a,z) for a,z in
                         [(-w*.87,low),(w*.87,low),(w,high-.10),(w*.82,high),
                          (-w*.82,high),(-w,high-.10)]])
    faces=[tuple(reversed(range(6))),tuple(range(len(vertices)-6,len(vertices)))]
    for i in range(len(p)-1):
        faces.extend((i*6+j,i*6+(j+1)%6,(i+1)*6+(j+1)%6,(i+1)*6+j) for j in range(6))
    mesh.add(vertices,faces,color,smooth=True)
    sides=[point(-1.50,-.77,.85),point(1.14,-.78,.82),point(.39,-.60,1.53),
           point(-.82,-.64,1.59),point(-1.50,.77,.85),point(1.14,.78,.82),
           point(.39,.60,1.53),point(-.82,.64,1.59)]
    mesh.add(sides,[(3,2,6,7)],color)
    mesh.add(sides,[(0,1,2,3),(7,6,5,4),(1,5,6,2),(4,0,3,7)],glass[1])
    for side in (-1,1):
        mesh.tube([point(-1.5,side*.77,.85),point(-.82,side*.64,1.59),
                   point(.39,side*.60,1.53),point(1.14,side*.78,.82)],.035,color,7)
        mesh.bar(point(-.26,side*.778,.85),point(-.21,side*.637,1.569),.028,frame)
        for wheel in (-1.44,1.40):
            mesh.tube([point(wheel,side*.746,.344),point(wheel,side*.937,.344)],.337,charcoal,18)
            mesh.tube([point(wheel,side*.940,.344),point(wheel,side*.956,.344)],.226,rail,18)
            for spoke in range(5):
                a=spoke*math.tau/5
                mesh.bar(point(wheel,side*.962,.344),
                         point(wheel+.194*math.cos(a),side*.963,.344+.194*math.sin(a)),.020,frame)
        mesh.box(point(2.055,side*.53,.62),(.10,.32,.113),headlight,angle=angle)
        mesh.box(point(-2.147,side*.52,.60),(.06,.34,.120),red,angle=angle)
        mesh.box(point(.59,side*.922,1.06),(.248,.244,.108),color,angle=angle)
    mesh.box(point(2.056,0,.52),(.093,.516,.205),backing,angle=angle)
    mesh.box(point(2.112,0,.53),(.03,.35,.099),paper,angle=angle)
    mesh.box(point(-2.194,0,.484),(.046,.38,.111),paper,angle=angle)
    mesh.finish()
    dx=abs(co)*2.21+abs(si)*.95
    dy=abs(si)*2.21+abs(co)*.95
    collider(x-dx,x+dx,y-dy,y+dy)


for i,(x,y,a) in enumerate([(-29.78,13.79,.045),(-29.22,17.72,-.061),(-29.6,21.57,.07),
                             (-29.3,25.51,-.049),(-29.70,28.42,.01),
                             (-6.11,44.3,.087),(-13.09,44.5,-.19),(-30.3,36.3,math.pi/2)]):
    parked_car(x,y,a,vehicle_paint[i%len(vehicle_paint)])
lot=Geometry('Bãi xe máy cạnh lối gạch · nền sỏi và rào ống',parking)
path(lot,-33.45,-25.90,-22.42,-16.46,asphalt,top=.018,joints=False)
for start,end in [((-33.45,-22.33),(-27.50,-22.33)),((-33.45,-22.33),(-33.45,-16.58)),
                  ((-25.91,-22.33),(-25.91,-19.33))]:
    a,b=Vector(start),Vector(end)
    intervals=math.ceil((b-a).length/.76)
    for i in range(intervals):
        p,q=a.lerp(b,i/intervals),a.lerp(b,(i+1)/intervals)
        lot.bar((*p,.28),(*q,.28),.028,(plate_yellow,red)[i%2])
        if i%2==0:
            lot.bar((*p,0),(*p,.71),.033,rail)
    lot.bar((*a,.69),(*b,.69),.029,rail)
    lot.bar((*b,0),(*b,.71),.033,rail)
    collider(min(a.x,b.x)-.05,max(a.x,b.x)+.05,min(a.y,b.y)-.05,max(a.y,b.y)+.05)
lot.finish()

motorcycles=Geometry('Xe máy ở sân B, bên lối gạch và ngoài bãi ô tô',parking)
bikes=[
    (-8.66,-5.42,1.39),(-7.88,-5.77,1.62),(-24.25,37.6,1.81),(-26.74,36.45,-.63),
    (-31.55,10.69,-.55),(-31.77,9.62,-.61),(-32.1,8.58,-.61),
    (-25.58,-35.31,math.pi/2),(-24.87,-35.62,math.pi/2)
]
for row,y in enumerate((-21.23,-19.22,-17.49)):
    for column in range(8):
        bikes.append((-32.72+column*.81+(row%2)*.21,y+rng.uniform(-.15,.15),
                      (-1 if row==1 else 1)*1.40+rng.uniform(-.15,.15)))
for i,(x,y,angle) in enumerate(bikes):
    scooter(motorcycles,x,y,angle,[bike_blue,bike_dark,bike_red,bike_gray][i%4],i)
    hx=abs(math.cos(angle))*.88+abs(math.sin(angle))*.38
    hy=abs(math.sin(angle))*.88+abs(math.cos(angle))*.38
    collider(x-hx,x+hx,y-hy,y+hy)
motorcycles.finish()

portable=Geometry('Nhà ghép xanh hai tầng đối diện cuối hành lang',outer)
for index,(x0,x1,mat_upper) in enumerate([(-24.8,-19.52,shed_blue),(-19.52,-13.7,shed_lime),
                                         (-13.7,-7.85,shed_lime),(-7.85,-3.24,shed_lime)]):
    for z0,z1,mat in [(0,2.69,shed_teal),(2.69,5.33,mat_upper)]:
        portable.box(((x0+x1)/2,53.60,(z0+z1)/2),(x1-x0,6.1,z1-z0),mat)
        portable.box(((x0+x1)/2,50.48,z1-.105),(x1-x0+.04,.171,.165),roof)
        for j in range(round((x1-x0)/.23)):
            x=x0+.058+j*.23
            portable.box((x,50.523,(z0+z1)/2),(.036,.065,z1-z0-.16),mat)
        for off in (-.28,.28):
            x=(x0+x1)/2+off*(x1-x0)
            z=z0+(1.69 if z0 else 1.29)
            portable.box((x,50.46,z),(.79,.09,.71 if z0 else .97),cream)
            portable.box((x,50.405,z),(.66,.025,.58 if z0 else .82),glass[2])
            portable.box((x,50.386,z),(.027,.027,.61 if z0 else .86),rail)
    collider(x0,x1,50.55,56.65)
for x,y in [(-20.3,49.72),(-10.05,49.8),(-4.07,49.76)]:
    for i in range(14):
        portable.box((x-.323+i*.218,y,.189*(i+1)),(.221,.85,.078),roof)
    for off in (-.43,.43):
        railing(portable,(x-.45,y+off,.035),(x+2.73,y+off,2.64),.82)
portable.finish()

context=Geometry('Tường và các nhà xa ở rìa sơ đồ',outer)
context.box((-60.1,6.3,5.10),(4.0,43.17,10.2),cream)
context.box((-60.1,6.3,10.19),(4.25,43.34,.18),plaster)
for i in range(3):
    for j in range(10):
        y=-13.7+j*4.06
        z=1.63+i*3.05
        context.box((-58.03,y,z),(.111,1.46,1.05),frame)
        for off in (-.452,0,.452):
            context.box((-57.93,y+off,z),(.072,.39,.92),glass[(i+j)%len(glass)])
context.box((-56.76,-17.6,.67),(.17,121.8,1.33),plaster)
collider(-56.85,-56.67,-78.5,43.3)
for y in (-83.9,48.80):
    for x0,x1 in [(-56.6,-50.83),(16.0,24.78)]:
        context.box(((x0+x1)/2,y,1.13),(x1-x0,.24,2.27),plaster)
context.finish()

props=Geometry('Ghế nhựa, tủ lạnh, can và thùng rác thấy trong video',utilities)
def plastic_stool(face,u,v,z,mat=stool_blue):
    face.box(props,u,v,z+.44,.301,.29,.061,mat)
    face.box(props,u,v,z+.463,.217,.093,.026,mat)
    for a in (-.111,.111):
        for b in (-.105,.105):
            face.line(props,(u+a*1.195,v+b*1.205,z),(u+a,v+b,z+.43),.034,mat,5)
    for off in (-.121,.121):
        face.box(props,u,v+off,z+.165,.245,.048,.051,mat)


def jug(face,u,v,z,mat):
    face.box(props,u,v,z+.169,.197,.163,.332,mat)
    face.line(props,(u-.039,v,z+.323),(u-.039,v,z+.378),.045,mat,8)
    face.line(props,(u-.039,v,z+.377),(u-.039,v,z+.393),.048,red,8)
    face.line(props,(u+.049,v,z+.292),(u+.062,v,z+.369),.022,mat,6)


for face,world_y,to_wall in [(west_face,-12.3,.34),(west_face,19.0,.30),(west_face,23.1,.44),
                             (inner_face,13.65,.372),(inner_face,-1.64,.44),(inner_face,-17.01,.28)]:
    u=face.u_at(face.origin[0],world_y)
    plastic_stool(face,u,to_wall,GROUND)
for y in (15.46,16.25,17.10,18.67,21.98):
    u=west_face.u_at(WEST,y)
    jug(west_face,u,.22,GROUND,cream if y<18 else paper)
    west_face.box(props,u,.33,GROUND+.003,.65,.70,.006,plate_yellow)
for face,y in [(west_face,.39),(return_face,33.0)]:
    u=west_face.u_at(WEST,y) if face is west_face else -1.95
    face.box(props,u,.38,GROUND+.801,.597,.658,1.60,metal_gray)
    face.box(props,u,.731,GROUND+.80,.557,.052,1.52,plaster)
    face.box(props,u,.764,GROUND+.991,.568,.026,.025,frame)
    for off in (-.018,.333):
        face.box(props,u+.184,.782,GROUND+.951+off,.039,.034,.222,rail)
    face.blocker(u-.305,u+.305,.07,.72)
for x,y in [(-26.60,3.19),(-31.62,5.94),(-25.68,35.58),(-10.48,-3.82)]:
    props.tube([(x,y,.016),(x,y,.21),(x,y,.337)],(.120,.176,.190),cream,15)
    for j in range(9):
        a=j*2.39996
        props.leaf((x,y,.322),(math.cos(a),math.sin(a),rng.uniform(.47,1.56)),
                   rng.uniform(.21,.38),.11,rng.choice(green_hedge))
for x,y in [(-30.99,-26.33),(-1.73,-6.97),(-26.5,33.89),(-34.23,-38.79)]:
    props.bar((x,y,.021),(x,y,1.11),.035,rail,8)
    for sign,mat in [(-1,red),(1,green)]:
        a=x+sign*.207
        props.tube([(a,y,.137),(a,y,.77)],(.141,.171),mat,13)
        props.tube([(a,y,.784),(a,y,.817)],.175,roof,13)
        props.box((a,y,1.02),(.399,.43,.084),mat)
    collider(x-.35,x+.35,y-.20,y+.20)
for x,y in [(-8.44,-6.47),(-8.31,-5.49),(-9.69,-5.18)]:
    props.bar((x,y,0),(x,y,.74),.028,rail)
for a,b in [((-8.44,-6.47,.66),(-8.31,-5.49,.665)),((-8.31,-5.49,.66),(-9.69,-5.18,.665))]:
    props.bar(a,b,.012,red)
props.finish()

lights=Geometry('Cột điện, ống kỹ thuật, và đèn sân',utilities)
for x,y,h in [(-7.76,-17.72,8.7),(*TRANSFORMER,8.37),(-32.91,17.28,8.5),(-36.18,-29.47,8.24)]:
    lights.tube([(x,y,0),(x,y,h)],(.168,.123),plaster,9,irregular=.032)
    lights.box((x,y-.163,1.44),(.31,.161,.42),cream)
    lights.box((x,y-.248,1.46),(.076,.062,.119),frame)
    collider(x-.162,x+.162,y-.165,y+.162)
# The transformer and the red corrugated conduits anchor the viewpoint in
# the lane between the two wings.
x,y=TRANSFORMER
for off in (-.32,.36):
    lights.box((x+off,y,6.25),(.10,1.12,.105),rail)
    lights.bar((x,y-.08,5.74),(x+off,y-.47,6.24),.052,rail,8)
lights.box((x+.22,y-.29,6.79),(.79,.75,1.10),frame)
lights.box((x+.22,y-.29,7.365),(.84,.82,.083),roof)
for i in range(10):
    lights.box((x-.156+i*.083,y-.698,6.78),(.033,.145,.938),roof)
for i in range(3):
    lights.bar((x+.06+i*.172,y-.31,7.36),(x+.06+i*.172,y-.31,7.56),.053,backing,8)
for off,side in [(-.29,-1),(.29,1)]:
    lights.box((x+off,y-.055,1.31),(.31,.30,.551),cream)
    lights.box((x+off,y-.213,1.32),(.28,.029,.522),plaster)
    for i in range(5):
        lights.box((x+off,y-.232,1.26+i*.04),(.10,.021,.014),metal_gray)
    wire=[(x+off,y-.122,.985),(x+off,y-.118,.819),(x+off*.77,y-.218,.65),
          (x+.067*side,y-.224,.845),(x+.073*side,y-.221,.15),(x+.096*side,y-.261,.024)]
    lights.tube(wire,.034,red,9)
    for i in range(10):
        z=.14+i*.058
        lights.bar((x+.072*side,y-.221,z),(x+.072*side,y-.221,z+.018),.038,red,8)
for a,b in [((*TRANSFORMER,8.29),(-36.18,-29.47,8.16)),
            ((-36.18,-29.47,8.16),(-32.91,17.28,8.38)),
            ((-7.76,-17.72,8.62),(*TRANSFORMER,8.29))]:
    for line in range(3):
        points=[(a[0]*(1-t)+b[0]*t,a[1]*(1-t)+b[1]*t+.154*line,
                 a[2]*(1-t)+b[2]*t-4*t*(1-t)*(.54+line*.16)) for t in np.linspace(0,1,17)]
        lights.tube(points,.011,backing,6)
for x,y in [(-29.99,1.9),(-10.18,-15.19),(-2.26,-10.1),(-8.3,-4.79),
            (-7.86,19.3),(-25.96,32.3),(-29.71,-27.3),(-35.17,-31.47),(-37.39,-38.47)]:
    lights.bar((x,y,.0),(x,y,3.6),.044,rail,8)
    lights.bar((x,y,3.54),(x+.42,y,3.72),.032,rail)
    lights.box((x+.45,y,3.69),(.25,.12,.09),roof)
    lights.box((x+.45,y,3.638),(.216,.098,.02),lamp_glass)
    light=bpy.data.objects.new('Đèn lối đi',None)
    utilities.objects.link(light)
    light.location=(x+.46,y,3.53)
    light['courtyardLight']='path'
lights.finish()

# Carry the original shrine and two low concrete seats into the adjacent
# garden from the earlier photographs.
original=collection('Khu B | Đồ gốc ở vườn miếu')
existing=set(scene.objects)
bpy.ops.import_scene.gltf(filepath=str(ROOT/'hcmute-khu-b.glb'))
imported=set(scene.objects)-existing
original_root=bpy.data.objects.new('OriginalKhuB',None)
original.objects.link(original_root)
benches_original={'Bench.003':(-32.17,-29.95,-.02),'Bench.006':(-31.18,-36.17,-.02)}
for ob in sorted(imported,key=lambda item:item.name):
    keep=ob.name.startswith('tripo_node_9f7') or ob.name in benches_original
    if not keep:
        bpy.data.objects.remove(ob,do_unlink=True)
        continue
    for group in list(ob.users_collection):
        group.objects.unlink(ob)
    original.objects.link(ob)
    ob.parent=original_root
    if ob.name in benches_original:
        ob.location=benches_original[ob.name]
        modifier=ob.modifiers.new('Giảm mật độ lưới cho bản web','DECIMATE')
        modifier.ratio=.17
    else:
        ob.location=(SHRINE[0],SHRINE[1],.03)
        ob.rotation_mode='QUATERNION'
        ob.rotation_quaternion=Quaternion((0,0,1),math.pi)

asset=ROOT/'assets'/'khu-b-courtyard.glb'
with tempfile.TemporaryDirectory(dir=asset.parent) as temporary:
    scratch=Path(temporary)/asset.name
    bpy.ops.export_scene.gltf(filepath=str(scratch),export_format='GLB',
                             export_extras=True,export_yup=True,export_apply=True,
                             export_cameras=False,export_lights=False,export_animations=False)
    scratch.replace(asset)

studio=collection('Góc đối chiếu với video')
sun_data=bpy.data.lights.new('Nắng xiên sân Khu B','SUN')
sun_data.energy=2.55
sun_data.angle=math.radians(10)
sun=bpy.data.objects.new(sun_data.name,sun_data)
studio.objects.link(sun)
sun.rotation_euler=Vector((-.48,-.09,-.87)).to_track_quat('-Z','Y').to_euler()
scene.world=bpy.data.worlds.new('Trời nhiều mây nhẹ')
scene.world.use_nodes=True
background=scene.world.node_tree.nodes.get('Background')
background.inputs['Color'].default_value=(.527,.67,.851,1)
background.inputs['Strength'].default_value=1.06


def camera(name,position,target,lens):
    data=bpy.data.cameras.new(name)
    ob=bpy.data.objects.new(name,data)
    studio.objects.link(ob)
    ob.location=position
    ob.rotation_euler=(Vector(target)-Vector(position)).to_track_quat('-Z','Y').to_euler()
    data.lens=lens
    data.clip_end=310
    return ob


cameras={
    'cua-khoa':camera('Ảnh mới · Bảng khoa bên trái và lối vào sân B',(*JUNCTION,1.73),(-13.32,-18.7,2.24),12.6),
    're-phai':camera('Từ ngã rẽ phải nhìn vào sân và cầu thang ngoài',(-1.39,-26.92,1.73),(-3.98,-13.62,2.10),16.8),
    'hanh-lang':camera('4187 · Máng cáp và cửa lab',(-11.55,28.90,GROUND+1.70),(-12.30,17.42,GROUND+1.62),17.8),
    'san-trong':camera('Ảnh 5 · Bồn cong dưới chữ B',(-9.09,-18.90,1.73),(-4.95,-2.45,2.45),19.7),
    'cau-noi':camera('4187 · Dưới cầu nối nhìn theo lối bê tông',(-9.36,-23.6,1.73),(-8.6,-9.6,1.92),17.8),
    'vuon-mieu':camera('Lối gạch · Vườn miếu bên trái, xe máy bên phải',(-25.98,-26.58,1.73),(-36.37,-29.08,1.75),16.8),
    'duong-ngoai':camera('4185 · Hết hành lang ngoài B',(-24.02,33.96,GROUND+1.70),(-15.42,53.56,2.77),20),
    'toan-canh':camera('Mặt bằng · Chữ H, dãy C, D và thư viện',(-5,-28,112),(-16,-17,0),30),
}
plan_camera=camera('Mặt bằng trực giao',(-17,-17.5,165),(-17,-17.5,0),30)
plan_camera.data.type='ORTHO'
plan_camera.data.ortho_scale=142
plan_camera.rotation_euler=(0,0,0)
scene.camera=cameras['cua-khoa']
scene.render.engine='CYCLES'
scene.cycles.samples=10
scene.cycles.use_denoising=True
scene.cycles.max_bounces=5
scene.cycles.transparent_max_bounces=8
scene.render.resolution_x=1410
scene.render.resolution_y=840
scene.render.resolution_percentage=100
scene.render.image_settings.file_format='JPEG'
scene.render.image_settings.quality=91
scene.view_settings.view_transform='AgX'
scene.view_settings.exposure=.60
scene.render.filepath='//'
bpy.ops.file.pack_all()
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            view=area.spaces.active
            view.clip_end=400
            view.region_3d.view_distance=105
            view.region_3d.view_location=(-19,-16,0)
            view.region_3d.view_rotation=cameras['toan-canh'].rotation_euler.to_quaternion()
            view.region_3d.view_perspective='PERSP'
            view.shading.color_type='MATERIAL'
            view.shading.show_cavity=True
            view.overlay.show_extras=False
bpy.ops.object.select_all(action='DESELECT')
bpy.context.view_layer.objects.active=None
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'khu-b-mo-rong.blend'),compress=True)

if '--preview' in sys.argv:
    preview_args=sys.argv[sys.argv.index('--preview')+1:]
    prefix,*selected=preview_args
    for name,view in cameras.items():
        if selected and name not in selected:
            continue
        scene.camera=view
        scene.render.filepath=f'{prefix}-{name}.jpg'
        bpy.ops.render.render(write_still=True)
    if not selected or 'mat-bang' in selected:
        scene.camera=plan_camera
        scene.render.resolution_x=990
        scene.render.resolution_y=1400
        scene.render.filepath=f'{prefix}-mat-bang.jpg'
        bpy.ops.render.render(write_still=True)
