"""Export the saved Khu A scene, including hand edits. Run in background Blender."""
import sys
import tempfile
from pathlib import Path

import bpy
from mathutils import Vector

HERE = Path(__file__).resolve().parent
sys.dont_write_bytecode = True
sys.path.insert(0, str(HERE))
from campus_mesh import empty

MAP = HERE.parent / 'maps' / 'khu-a'


def render_objects(group):
    if group.hide_render:
        return
    for obj in group.objects:
        if obj.type in {'MESH', 'EMPTY'} and not obj.hide_render:
            yield obj
    for child in group.children:
        yield from render_objects(child)


def walk_proxy(group, obj, graph):
    surface = obj.get('ka_walk')
    if surface not in {'wall', 'floor'}:
        return
    evaluated = obj.evaluated_get(graph)
    corners = [evaluated.matrix_world @ Vector(v) for v in evaluated.bound_box]
    x0, x1 = min(p.x for p in corners), max(p.x for p in corners)
    y0, y1 = min(p.y for p in corners), max(p.y for p in corners)
    top = max(p.z for p in corners)
    props = ({'walkCollider': True} if surface == 'wall'
             else {'floorStart': top, 'floorEnd': top, 'floorAxis': 'depth'})
    return empty('Walk · ' + obj.name, group, ((x0+x1)/2, (y0+y1)/2, 0),
                 ((x1-x0)/2, (y1-y0)/2, 1), **props)


def export():
    scene = bpy.context.scene
    root = next(c for c in scene.collection.children if c.get('ute_zone_a_demo'))
    hand = next(c for c in scene.collection.children if c.get('ka_manual'))
    objects = list(dict.fromkeys((*render_objects(root), *render_objects(hand))))
    # A temporary scene makes export independent of Outliner selection and isolated views.
    stage = bpy.data.scenes.new('Khu A · Export')
    proxies = []
    links = []
    try:
        for obj in objects:
            stage.collection.objects.link(obj)
        bpy.context.window.scene = stage
        graph = bpy.context.evaluated_depsgraph_get()
        for obj in objects:
            proxy = walk_proxy(stage.collection, obj, graph)
            if proxy:
                proxies.append(proxy)

        # glTF cannot encode the procedural Noise ramps. Use the builder's base colours.
        materials = {slot.material for obj in objects for slot in obj.material_slots if slot.material}
        for mat in materials:
            if not mat.get('ute_zone_a_demo') or not mat.node_tree:
                continue
            shader = mat.node_tree.nodes.get('Principled BSDF')
            if shader:
                base = shader.inputs['Base Color']
                for link in list(base.links):
                    if link.from_node.type == 'VALTORGB':
                        links.append((mat, link.from_socket, base))
                        mat.node_tree.links.remove(link)
        MAP.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=MAP) as directory:
            path = Path(directory) / 'khu-a.glb'
            bpy.ops.export_scene.gltf(filepath=str(path), export_format='GLB', use_active_scene=True,
                                      export_extras=True, export_yup=True, export_cameras=False,
                                      export_lights=False, export_animations=False)
            path.replace(MAP / path.name)
    finally:
        for mat, output, base in links:
            mat.node_tree.links.new(output, base)
        bpy.context.window.scene = scene
        for proxy in proxies:
            bpy.data.objects.remove(proxy, do_unlink=True)
        bpy.data.scenes.remove(stage)


if __name__ == '__main__':
    export()
