"""Build the Khu A exterior in the active Blender scene. Run from Scripting."""

import math
import random
import sys
from pathlib import Path

import bmesh
import bpy
from mathutils import Vector


# A text opened in Blender may have a path relative to the saved .blend.
text = getattr(bpy.context.space_data, "text", None)
source = bpy.path.abspath(text.filepath) if text and text.filepath else __file__
sys.dont_write_bytecode = True
tools_dir = str(Path(source).resolve().parent)
if tools_dir not in sys.path:
    sys.path.insert(0, tools_dir)
from campus_mesh import collection, empty, view_marker, walk_limits


# Dimensions in metres, estimated from the aerial references. +Y runs from
# the road facing the central building towards the far end of the long court.
MAIN_WIDTH = 30.0
MAIN_LENGTH = 60.0
WING_WIDTH = 8.5
END_WIDTH = 7.0
FLOOR_HEIGHT = 3.15
FLOORS = 3
ROOF_RISE = 1.05
SEED = 124
OWNER = "ute_zone_a_demo"


def remove_previous_build(scene):
    for root in tuple(scene.collection.children):
        if not root.get(OWNER):
            continue
        groups = [*reversed(list(root.children_recursive)), root]
        objects = set(root.all_objects)
        data_blocks = {obj.data for obj in objects if obj.data is not None}
        materials = {
            mat for data in data_blocks for mat in getattr(data, "materials", ())
            if mat is not None and mat.get(OWNER)
        }
        for group in groups:
            bpy.data.collections.remove(group)
        for obj in objects:
            if not obj.users_collection:
                bpy.data.objects.remove(obj, do_unlink=True)
        bpy.data.batch_remove(ids=[data for data in data_blocks if data.users == 0])
        bpy.data.batch_remove(ids=[mat for mat in materials if mat.users == 0])


def material(name, color, other=None, scale=4.0, roughness=0.78):
    mat = bpy.data.materials.new("Khu A · " + name)
    mat[OWNER] = True
    mat.diffuse_color = (*color, 1.0)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    shader = nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = mat.diffuse_color
    shader.inputs["Roughness"].default_value = roughness
    if other is not None:
        coords = nodes.new("ShaderNodeTexCoord")
        noise = nodes.new("ShaderNodeTexNoise")
        noise.inputs["Scale"].default_value = scale
        noise.inputs["Detail"].default_value = 3.0
        ramp = nodes.new("ShaderNodeValToRGB")
        ramp.color_ramp.elements[0].position = 0.33
        ramp.color_ramp.elements[0].color = (*color, 1.0)
        ramp.color_ramp.elements[1].position = 0.68
        ramp.color_ramp.elements[1].color = (*other, 1.0)
        links.new(coords.outputs["Object"], noise.inputs["Vector"])
        links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
        links.new(ramp.outputs["Color"], shader.inputs["Base Color"])
    return mat


def mesh(group, name, vertices, faces, mat):
    data = bpy.data.meshes.new(name)
    data.from_pydata(vertices, [], faces)
    data.update()
    data.materials.append(mat)
    obj = bpy.data.objects.new(name, data)
    group.objects.link(obj)
    return obj


def box(group, name, x, y, z, width, length, height, mat):
    left, right = x - width / 2, x + width / 2
    front, back = y - length / 2, y + length / 2
    top = z + height
    vertices = [(left, front, z), (right, front, z), (right, back, z), (left, back, z),
                (left, front, top), (right, front, top), (right, back, top), (left, back, top)]
    return mesh(group, name, vertices,
                [(3, 2, 1, 0), (4, 5, 6, 7), (0, 1, 5, 4),
                 (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)], mat)


def disc(group, name, x, y, z, radius, height, mat, count=36):
    ring = [(x + radius * math.cos(i * math.tau / count),
             y + radius * math.sin(i * math.tau / count)) for i in range(count)]
    vertices = [(px, py, pz) for pz in (z, z + height) for px, py in ring]
    faces = [tuple(reversed(range(count))), tuple(range(count, count * 2))]
    for i in range(count):
        j = (i + 1) % count
        faces.append((i, j, j + count, i + count))
    return mesh(group, name, vertices, faces, mat)


def rectangle(x, y, width, length, z):
    return [(x + dx * width / 2, y + dy * length / 2, z)
            for dx, dy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]


def ring_roof(group, eave, roof, trim):
    overhang = 0.42
    outer = rectangle(0, MAIN_LENGTH / 2, MAIN_WIDTH + overhang * 2,
                      MAIN_LENGTH + overhang * 2, eave)
    inner = rectangle(0, MAIN_LENGTH / 2, MAIN_WIDTH - 2 * (WING_WIDTH + overhang),
                      MAIN_LENGTH - 2 * (END_WIDTH + overhang), eave)
    ridge = [((a[0] + b[0]) / 2, (a[1] + b[1]) / 2, eave + ROOF_RISE)
             for a, b in zip(outer, inner)]
    vertices = outer + ridge + inner
    faces = []
    for i in range(4):
        j = (i + 1) % 4
        faces.extend([(i, j, 4 + j, 4 + i), (4 + i, 4 + j, 8 + j, 8 + i)])
    mesh(group, "Mái xanh bao quanh sân cây", vertices, faces, roof)

    # Fascia along both open edges and raised ridge caps around the four sides.
    for ring in (outer, inner, ridge):
        for i in range(4):
            a = ring[i]
            b = ring[(i + 1) % 4]
            box(group, "Nẹp mái xanh", (a[0] + b[0]) / 2, (a[1] + b[1]) / 2,
                a[2] - 0.10, abs(a[0] - b[0]) + 0.14, abs(a[1] - b[1]) + 0.14, 0.20, trim)
    for side in (-1, 1):
        x = side * (MAIN_WIDTH - WING_WIDTH) / 2
        y = MAIN_LENGTH / 2
        monitor_length = MAIN_LENGTH - 2 * END_WIDTH - 2.0
        box(group, "Gờ nổi dọc hai dãy mái", x, y, eave + ROOF_RISE - .32,
            2.05, monitor_length, .59, roof)
        hip_roof(group, "Nắp gờ mái xanh", x, y, 2.21, monitor_length + .24,
                 eave + ROOF_RISE + .27, .24, roof)


def hip_roof(group, name, x, y, width, length, eave, rise, mat):
    corners = rectangle(x, y, width, length, eave)
    if width >= length:
        run = max((width - length) / 2, width * 0.12)
        ridge = [(x - run, y, eave + rise), (x + run, y, eave + rise)]
        faces = [(0, 1, 5, 4), (1, 2, 5), (2, 3, 4, 5), (3, 0, 4)]
    else:
        run = max((length - width) / 2, length * 0.12)
        ridge = [(x, y - run, eave + rise), (x, y + run, eave + rise)]
        faces = [(0, 1, 4), (1, 2, 5, 4), (2, 3, 5), (3, 0, 4, 5)]
    return mesh(group, name, corners + ridge, faces, mat)


def long_building(zones, shared, palette):
    wall, concrete, glass, frame, roof, trim = palette
    eave = FLOORS * FLOOR_HEIGHT + 0.25
    outer_x = MAIN_WIDTH / 2
    inner_x = outer_x - WING_WIDTH
    middle_length = MAIN_LENGTH - 2 * END_WIDTH
    for side in (-1, 1):
        group = zones[7 if side < 0 else 9]
        # The classroom walls sit behind the courtyard-facing galleries.
        wall_width = WING_WIDTH - 1.85
        center_x = side * (outer_x - wall_width / 2)
        box(group, "Dãy lớp học", center_x, MAIN_LENGTH / 2, 0.18,
            wall_width, middle_length, eave - 0.18, wall)
        for floor in range(FLOORS):
            z = 0.18 + floor * FLOOR_HEIGHT
            box(group, "Sàn hành lang", side * (outer_x + inner_x) / 2, MAIN_LENGTH / 2,
                z - 0.16, WING_WIDTH + 0.12, middle_length, 0.20, concrete)
            if floor:
                box(group, "Lan can sân trong", side * inner_x, MAIN_LENGTH / 2,
                    z + 0.08, 0.16, middle_length, 0.77, concrete)
                box(group, "Tay vịn sân trong", side * inner_x, MAIN_LENGTH / 2,
                    z + 0.92, 0.11, middle_length, 0.075, frame)
            for bay in range(11):
                y = END_WIDTH + (bay + 0.5) * middle_length / 11
                box(group, "Kính lớp học", side * (outer_x + 0.015), y, z + 1.0,
                    0.06, 2.72, 1.16, glass)
                box(group, "Đố kính", side * (outer_x + 0.052), y, z + 1.0,
                    0.09, 0.075, 1.16, frame)
                box(group, "Cửa vào lớp", side * (outer_x - wall_width - 0.02), y, z + 0.04,
                    0.07, 0.86, 2.05, frame)
        for post in range(12):
            y = END_WIDTH + post * middle_length / 11
            box(group, "Cột hành lang", side * inner_x, y, 0.12,
                0.36, 0.40, eave - 0.12, concrete)

    for y in (END_WIDTH / 2, MAIN_LENGTH - END_WIDTH / 2):
        group = zones[6 if y < MAIN_LENGTH / 2 else 10]
        connector = box(group, "Khối nối hai dãy", 0, y, FLOOR_HEIGHT, MAIN_WIDTH, END_WIDTH,
            eave - FLOOR_HEIGHT, wall)
        if group == zones[6]:
            source = empty("Bước chân trên hành lang", group, (-4, y, FLOOR_HEIGHT + 0.2), zoneSound="step")
            source.parent = connector
        for x in (-12, -8, -4, 4, 8, 12):
            for column_y in (y - END_WIDTH / 2 + 0.24, y + END_WIDTH / 2 - 0.24):
                box(group, "Cột lối vào sân cây", x, column_y, 0.12,
                    0.44, 0.44, FLOOR_HEIGHT, concrete)
        for floor in range(1, FLOORS):
            z = floor * FLOOR_HEIGHT
            for facade_y in (y - END_WIDTH / 2 - 0.025, y + END_WIDTH / 2 + 0.025):
                box(group, "Gờ ngang khối nối", 0, facade_y, z, MAIN_WIDTH + 0.16,
                    0.18, 0.22, concrete)
                for x in range(-12, 13, 3):
                    box(group, "Cửa sổ khối nối", x, facade_y, z + 1.03,
                        1.74, 0.09, 1.16, glass)
    ring_roof(shared, eave, roof, trim)


def annex(group, name, x, y, width, length, height, palette, roof, rise):
    wall, concrete, glass, frame = palette
    box(group, name, x, y, 0.08, width, length, height - 0.08, wall)
    box(group, "Diềm mái " + name, x, y, height - 0.16, width + 0.8, length + 0.8,
        0.18, concrete)
    hip_roof(group, "Mái " + name, x, y, width + 0.82, length + 0.82, height, rise, roof)
    floors = max(1, int(height / 2.9))
    bays = int(width / 3)
    for floor in range(floors):
        z = floor * (height / floors) + 1.03
        for side in (-1, 1):
            for i in range(bays):
                bay = x - width / 2 + (i + 0.5) * width / bays
                box(group, "Cửa sổ " + name, bay, y + side * (length / 2 + 0.025), z,
                    1.68, 0.075, 1.13, glass)
    box(group, "Lối vào " + name, x, y + length / 2 + 0.035, 0.08,
        1.7, 0.12, 2.35, frame)


def canopy(group, x, y, width, length, under, concrete, roof, trigger=False):
    for side in (-1, 1):
        for end in (-1, 1):
            box(group, "Cột mái che", x + side * (width / 2 - 0.30),
                y + end * (length / 2 - 0.35), 0.10, 0.26, 0.26, under, concrete)
    box(group, "Sàn lối có mái che", x, y, 0.047, width, length, 0.071, concrete)
    box(group, "Diềm mái che", x, y, under + 0.10, width + 0.36, length + 0.42, 0.15, roof)
    cover = hip_roof(group, "Mái che lối nối", x, y, width + 0.4, length + 0.46,
             under + 0.24, 0.42, roof)


    if trigger:
        zone = empty("Vùng dưới mái che", group, (x, y + length / 2 - 1.8, 1.7),
                     (width / 2, 1.6, 2.0), zoneSound="trigger")
        zone.parent = cover


def tree_mesh(mat):
    data = bpy.data.meshes.new("Tán cây · " + mat.name)
    with_mesh = bmesh.new()
    try:
        bmesh.ops.create_icosphere(with_mesh, subdivisions=2, radius=1.0)
        with_mesh.to_mesh(data)
    finally:
        with_mesh.free()
    data.materials.append(mat)
    return data


def plant_trees(zones, layouts, bark, greens):
    rng = random.Random(SEED)
    crowns = [tree_mesh(color) for color in greens]
    for x, y, radius in layouts:
        if abs(x) < MAIN_WIDTH / 2 and y > 0:
            group = zones[8]
        elif abs(x) < MAIN_WIDTH / 2 and y < 0:
            group = zones[5]
        else:
            group = zones[1]
        trunk = radius * rng.uniform(0.90, 1.17)
        disc(group, "Thân cây", x, y, 0.03, 0.105 * radius, trunk + radius * 0.45, bark, 8)
        for dx, dy, dz, size in ((0, 0, .64, .90), (-.47, .19, .36, .72),
                                  (.46, .22, .35, .66), (.10, -.47, .30, .70),
                                  (-.18, .39, .68, .59)):
            crown = bpy.data.objects.new("Tán cây", rng.choice(crowns))
            group.objects.link(crown)
            crown.location = (x + dx * radius, y + dy * radius, trunk + dz * radius)
            crown.scale = (radius * size, radius * size * rng.uniform(.89, 1.16), radius * size * .94)
            crown.rotation_euler.z = rng.uniform(0, math.tau)


def camera(group, name, location, target, *, lens=32, ortho=None):
    data = bpy.data.cameras.new(name)
    data.lens = lens
    data.clip_end = 500
    if ortho is not None:
        data.type = "ORTHO"
        data.ortho_scale = ortho
    obj = bpy.data.objects.new(name, data)
    group.objects.link(obj)
    obj.location = location
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()
    return obj


def set_preview(scene, group):
    target = Vector((0, 9, 0))
    overview = camera(group, "Khu A · Từ trên cao", (46, -91, 153), target, ortho=152)
    camera(group, "Khu A · Từ mặt đất", (11.25, -16.85, 1.75), (-3.5, -5.0, 3.5), lens=26)
    scene.camera = overview
    scene.render.engine = "CYCLES"
    scene.cycles.samples = 24
    scene.cycles.use_denoising = True
    scene.render.resolution_x = 1440
    scene.render.resolution_y = 1000
    scene.render.resolution_percentage = 100

    world = scene.world
    if world is None or not world.get(OWNER) or world.users > 1:
        world = bpy.data.worlds.new("Khu A · Trời ban ngày")
        world[OWNER] = True
        scene.world = world
    world.use_nodes = True
    background = world.node_tree.nodes.get("Background")
    background.inputs["Color"].default_value = (0.69, 0.79, 0.92, 1.0)
    background.inputs["Strength"].default_value = 0.43
    sun_data = bpy.data.lights.new("Khu A · Nắng", "SUN")
    sun_data.energy = 2.6
    sun_data.angle = math.radians(7)
    sun = bpy.data.objects.new(sun_data.name, sun_data)
    group.objects.link(sun)
    sun.location = (22, -34, 58)
    sun.rotation_euler = (-sun.location).to_track_quat("-Z", "Y").to_euler()

    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type == "VIEW_3D":
                view = area.spaces.active
                view.clip_end = 500
                view.shading.color_type = "MATERIAL"
                view.region_3d.view_perspective = "ORTHO"
                view.region_3d.view_location = target
                view.region_3d.view_rotation = overview.rotation_euler.to_quaternion()
                view.region_3d.view_distance = 146


# Walk proxies are derived again at export from the current world-space bounds.
WALLS = {"Dãy lớp học", "Dãy mái bạc đỏ", "Dãy mái đỏ", "Cánh dãy mái đỏ",
         "Khối mái sáng", "Cánh khối mái sáng", "Sảnh thấp khối mái sáng",
         "Mốc tròn giữa sân", "Bồn cây dài trong khối A", "Vườn nhỏ cạnh mái che", "Thân cây"}
FLOOR_SURFACES = {"Đường phía Tòa nhà Trung tâm", "Vỉa hè phía Khu A", "Nền cụm nhà phía đường",
                  "Lối đi quanh khối A", "Sân nhỏ ở chân khối A", "Sàn lối có mái che",
                  "Lối lát vào sân nhỏ", "Bệ tròn trong sân nhỏ", "Mặt lát quanh mốc tròn"}


def configure_walk_surfaces(root, hand):
    bpy.context.view_layer.update()
    replacements = {obj.get("ka_replaces") for obj in hand.all_objects}
    for obj in list(root.all_objects):
        if obj.type != "MESH":
            continue
        label = obj.name.split(".")[0]
        center = sum((Vector(v) for v in obj.bound_box), Vector()) / 8
        center = obj.matrix_world @ center
        obj["ka_id"] = f"{label}@{center.x:.2f},{center.y:.2f},{center.z:.2f}"
        if obj["ka_id"] in replacements:
            bpy.data.objects.remove(obj, do_unlink=True)
        elif label in WALLS or label.startswith("Cột "):
            obj["ka_walk"] = "wall"
        elif label in FLOOR_SURFACES or (label == "Sàn hành lang" and center.z < 1):
            obj["ka_walk"] = "floor"


def build():
    scene = bpy.context.scene
    remove_previous_build(scene)
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.scale_length = 1.0
    root = bpy.data.collections.new("Khu A · Demo ngoại cảnh")
    root[OWNER] = True
    scene.collection.children.link(root)
    names = ("Đường và vòng ngoài", "Nhà mái sáng", "Nhà mái bạc đỏ", "Nhà mái đỏ",
             "Sân nhỏ và mái che", "Khối nối trước", "Dãy lớp trái", "Sân cây dài",
             "Dãy lớp phải", "Khối nối sau")
    hand = next((c for c in scene.collection.children if c.get("ka_manual")), None)
    if hand is None:
        hand = collection("Khu A · Chi tiết chỉnh tay")
        hand["ka_manual"] = True
    zones = {}
    for code, name in enumerate(names, 1):
        key = f"KA-{code:02}"
        zones[code] = collection(f"{key} · {name}", root)
        if not any(c.get("ka_zone") == key for c in hand.children):
            collection(f"{key} · Tay · {name}", hand)["ka_zone"] = key
    shared = collection("Khu A · Nền và mái chung", root)
    preview = collection("Khu A · Camera và nắng", root)
    markers = collection("Khu A · Mốc đi bộ", root)
    ground, court = zones[1], zones[5]

    lawn = material("Cỏ", (.096, .16, .061), (.24, .33, .10), .30)
    asphalt = material("Nhựa đường", (.067, .074, .080), (.14, .148, .15), 2.0)
    paver = material("Lát sân", (.39, .37, .32), (.57, .54, .46), 2.8)
    concrete = material("Sơn kem", (.78, .75, .63))
    wall = material("Tường vàng nhạt", (.66, .65, .49), (.78, .75, .59), .52)
    glass = material("Kính xanh xám", (.087, .17, .20), roughness=.29)
    frame = material("Cửa và tay vịn", (.14, .25, .25))
    turquoise = material("Tôn xanh nhạt", (.23, .55, .60), (.36, .70, .72), 1.6)
    trim = material("Diềm tôn xanh", (.44, .68, .68))
    dark_red = material("Tôn đỏ cũ", (.22, .086, .061), (.38, .19, .13), .85)
    rusty = material("Tôn bạc loang đỏ", (.33, .14, .08), (.69, .66, .56), .90)
    pale = material("Tôn sáng", (.56, .68, .57), (.76, .81, .67), 1.45)
    marker = material("Mốc tròn xanh lam", (.078, .38, .56), roughness=.35)
    solar = material("Pin mặt trời", (.038, .097, .18), roughness=.23)

    box(shared, "Nền khuôn viên", 0, 8, -0.24, 210, 210, .24, lawn)
    box(ground, "Đường phía Tòa nhà Trung tâm", 0, -47, .003, 105, 7.2, .032, asphalt)
    box(ground, "Vỉa hè phía Khu A", 0, -42.2, .013, 93, 2.5, .060, paver)
    for x in range(-44, 45, 8):
        box(ground, "Vạch đường", x, -47, .037, 2.5, .11, .005, concrete)
    box(shared, "Nền cụm nhà phía đường", 0, -21.2, .012, 62, 39, .058, paver)
    box(shared, "Lối đi quanh khối A", 0, MAIN_LENGTH / 2, .012,
        MAIN_WIDTH + 4, MAIN_LENGTH + 3, .06, paver)
    court_length = MAIN_LENGTH - 2 * END_WIDTH
    court_width = MAIN_WIDTH - 2 * WING_WIDTH
    box(zones[8], "Bồn cây dài trong khối A", 0, MAIN_LENGTH / 2, .073,
        court_width - 2.6, court_length - 4.0, .125, lawn)
    long_building(zones, shared, (wall, concrete, glass, frame, turquoise, trim))

    palette = (wall, concrete, glass, frame)
    annex(zones[3], "Dãy mái bạc đỏ", -24.0, -15.0, 20.0, 21.0, 6.45, palette, rusty, 2.9)
    annex(zones[4], "Dãy mái đỏ", 25.6, -13.6, 22.0, 14.8, 6.45, palette, dark_red, 2.65)
    annex(zones[4], "Cánh dãy mái đỏ", 30.9, -22.0, 11.4, 4.9, 6.38, palette, dark_red, .94)
    box(zones[3], "Thân tum mái bạc đỏ", -24.0, -15.0, 8.0, 6.7, 8.0, 1.59, trim)
    hip_roof(zones[3], "Tum mái bạc đỏ", -24.0, -15.0, 7.0, 8.3, 9.59, .83, rusty)
    box(zones[4], "Thân tum mái đỏ", 25.6, -13.6, 8.2, 9.2, 4.8, 1.04, dark_red)
    hip_roof(zones[4], "Tum mái đỏ", 25.6, -13.6, 9.5, 5.1, 9.24, .68, dark_red)
    annex(zones[2], "Khối mái sáng", -1.0, -31.0, 23.0, 14.7, 7.04, palette, pale, 1.38)
    annex(zones[2], "Cánh khối mái sáng", -1.0, -31.0, 16.8, 20.4, 7.08, palette, pale, 1.32)
    annex(zones[2], "Sảnh thấp khối mái sáng", -1.0, -19.6, 12.1, 5.0, 5.65, palette, pale, .44)
    for row in range(2):
        for i in range(8):
            box(zones[2], "Tấm pin trên mái sảnh", -5.15 + i * .99, -18.56 - row * 1.29,
                6.13, .90, .62, .043, solar)

    box(court, "Sân nhỏ ở chân khối A", 0, -12.2, .074, 11.2, 13.5, .038, lawn)
    disc(court, "Bệ tròn trong sân nhỏ", 0, -12.6, .113, 3.54, .12, concrete)
    disc(court, "Mặt lát quanh mốc tròn", 0, -12.6, .232, 3.21, .035, paver)
    disc(court, "Mốc tròn giữa sân", 0, -12.6, .267, .65, .23, marker)
    for x in (-7.6, 7.6):
        canopy(court, x, -9.2, 4.0, 10.7, 3.45, concrete, turquoise, trigger=True)
    canopy(court, -12.2, -22.0, 8.6, 4.5, 3.45, concrete, turquoise)
    box(court, "Vườn nhỏ cạnh mái che", -12.1, -13.0, .074, 4.2, 10.4, .064, lawn)
    box(court, "Lối lát vào sân nhỏ", 10.25, -26, .075, 2.9, 30.6, .017, paver)

    bark = material("Thân cây", (.18, .104, .051))
    greens = [material(f"Tán cây {i}", color) for i, color in enumerate(
        ((.068, .18, .045), (.11, .27, .053), (.17, .33, .065), (.23, .37, .078)), 1)]
    trees = [(-2.7, 13.0, 2.2), (1.8, 21, 2.55), (-2, 28, 2.1), (1.8, 35, 2.7),
             (-1.7, 43, 3.0), (1.3, 49, 2.45), (-3.55, -9.1, 1.72), (3.55, -16.6, 1.6),
             (-12.5, -14.8, 1.65), (-12.1, -9.7, 1.48), (-34, -32, 3.3), (30.5, -33, 2.9),
             (-24, -36, 2.6), (21.6, -34, 2.5), (39, -20, 3.25), (-40, -13, 2.8)]
    for side in (-1, 1):
        for i, y in enumerate((2, 12, 22, 33, 44, 55, 63)):
            trees.append((side * (20.8 + (i % 3) * 1.55), y, 2.9 + (i % 4) * .38))
    plant_trees(zones, trees, bark, greens)
    walk_limits(markers, -44, 44, -50, 65)
    view_marker(markers, "via-he", (12, -42.2, 1.763), (12, -16, 1.763))
    view_marker(markers, "san-nho", (7.6, -15.5, 1.76), (7.6, -4, 1.76))
    view_marker(markers, "san-cay", (5.85, 17, 1.76), (0, 33, 2.1))
    empty("Nền âm sân nhỏ", court, (0, -12.6, 2.1), zoneSound="insects")
    configure_walk_surfaces(root, hand)
    set_preview(scene, preview)


if __name__ == "__main__":
    build()
