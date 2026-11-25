"""Geometry and texture helpers for the Central Building Blender scene."""
import math
import random
import struct
import tempfile
import zlib
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector

NOISE = np.random.default_rng(51033)
FACE_BOX = ((3, 2, 1, 0), (4, 5, 6, 7), (0, 1, 5, 4),
            (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7))


def collection(name, parent=None):
    group = bpy.data.collections.new(name)
    (parent or bpy.context.scene.collection).children.link(group)
    return group


def empty(name, group, position=(0, 0, 0), scale=(1, 1, 1), **properties):
    ob = bpy.data.objects.new(name, None)
    group.objects.link(ob)
    ob.location = position
    ob.scale = scale
    ob.empty_display_type = 'CUBE'
    for key, value in properties.items():
        ob[key] = value
    return ob


def walk_limits(group, x0, x1, y0, y1):
    return empty('Giới hạn bản đồ', group, ((x0+x1)/2, (y0+y1)/2, 0),
                 ((x1-x0)/2, (y1-y0)/2, 1), walkLimits=True)


def view_marker(group, key, eye, target):
    dx, dy, dz = (b-a for a, b in zip(eye, target))
    return empty('Điểm quan sát '+key, group, eye, viewKey=key,
                 viewYaw=math.atan2(-dx,dy), viewPitch=math.atan2(dz,math.hypot(dx,dy)))


def strip(mesh, points, width, material, *, z=.018, offset=0):
    """A horizontal ribbon with rounded-path joints and a constant width."""
    vertices = []
    for i, (x, y) in enumerate(points):
        a = points[max(i-1,0)]
        b = points[min(i+1,len(points)-1)]
        dx, dy = b[0]-a[0], b[1]-a[1]
        length = math.hypot(dx,dy)
        for edge in (-width/2,width/2):
            side = (offset+edge)/length
            vertices.append((x-dy*side,y+dx*side,z))
    mesh.add(vertices, [(2*i,2*i+2,2*i+3,2*i+1) for i in range(len(points)-1)], material)


def arc(x, y, radius, start, end, segments=32):
    return [(x+radius*math.cos(t),y+radius*math.sin(t))
            for t in (start+(end-start)*i/segments for i in range(segments+1))]


def grid_net(mesh, corners, spacing, thread, material):
    """Two sets of crossed flat threads avoid a cylinder at every knot."""
    a, b, c, d = (Vector(p) for p in corners)
    for start, end, opposite_start, opposite_end in ((a,b,d,c),(a,d,b,c)):
        direction = (end-start).normalized()*thread*.5
        cells = max(1,round((end-start).length/spacing))
        for i in range(cells+1):
            t = i/cells
            p, q = start.lerp(end,t), opposite_start.lerp(opposite_end,t)
            mesh.sheet((p-direction,p+direction,q+direction,q-direction),material)


def packed_image(name, pixels):
    rgb = np.clip(pixels * 255, 0, 255).astype('uint8')
    height, width, channels = rgb.shape

    def chunk(tag, data):
        return struct.pack('>I', len(data)) + tag + data + struct.pack('>I', zlib.crc32(tag + data))

    raw = b''.join(b'\0' + row.tobytes() for row in rgb)
    header = struct.pack('>IIBBBBB', width, height, 8, 6 if channels == 4 else 2, 0, 0, 0)
    png = b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', header) + chunk(b'IDAT', zlib.compress(raw, 5)) + chunk(b'IEND', b'')
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / (name + '.png')
        path.write_bytes(png)
        image = bpy.data.images.load(str(path))
        image.pack()
        image.filepath = '//' + path.name
    return image


def noise(size, cols, rows):
    grid = NOISE.random((rows, cols)) - .5
    x = np.arange(size) * cols / size
    y = np.arange(size) * rows / size
    ix, iy = x.astype(int), y.astype(int)
    dx, dy = x-ix, y-iy
    dx, dy = dx*dx*(3-2*dx), dy*dy*(3-2*dy)
    start = grid[iy[:, None], ix] * (1-dx) + grid[iy[:, None], (ix+1) % cols] * dx
    end = grid[((iy+1) % rows)[:, None], ix] * (1-dx) + grid[((iy+1) % rows)[:, None], (ix+1) % cols] * dx
    return start * (1-dy[:, None]) + end * dy[:, None]


def surface(name, color, roughness=.75, *, metal=0, image=None, metres=1, opacity=1,
            emit=0, double=False, coat=0):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, opacity)
    mat.use_nodes = True
    mat.use_backface_culling = not double
    bsdf = mat.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = (*color, 1)
    bsdf.inputs['Roughness'].default_value = roughness
    bsdf.inputs['Metallic'].default_value = metal
    bsdf.inputs['Alpha'].default_value = opacity
    bsdf.inputs['Coat Weight'].default_value = coat
    if opacity < 1:
        mat.surface_render_method = 'BLENDED'
    if emit:
        bsdf.inputs['Emission Color'].default_value = (*color, 1)
        bsdf.inputs['Emission Strength'].default_value = emit
    if image:
        tex = mat.node_tree.nodes.new('ShaderNodeTexImage')
        tex.image = image
        mat.node_tree.links.new(tex.outputs['Color'], bsdf.inputs['Base Color'])
    mat['metres'] = metres
    return mat


def tiled(name, base, pattern, metres, roughness=.85, *, metal=0, size=512):
    y, x = np.mgrid[:size, :size] / size
    large = noise(size, 8, 9)
    dither = NOISE.random((size, size)) - .5
    mid = noise(size, 44, 39)
    value = large*.088 + mid*.062 + dither*.039
    if pattern == 'brick':
        # Forty-two millimetre courses on the photographed gate, with staggered joints.
        bx = x*8 + (np.floor(y*26) % 2)*.5
        by = y*26
        u = abs(bx % 1 - .5)
        v = abs(by % 1 - .5)
        grout = np.clip(np.maximum((u-.462)/.031, (v-.402)/.080), 0, 1)
        bevel = np.exp(-((v-.37)/.042)**2)*.038
        variations = NOISE.uniform(-.083, .077, (26, 8))
        value += variations[by.astype(int), bx.astype(int)%8] + bevel + noise(size, 11, 27)*.09
        rgb = (np.array(base) + value[:, :, None])*(1-grout[:, :, None]) + grout[:, :, None]*(.394,.309,.238)
    elif pattern == 'paving':
        px, py = x*4, y*4
        u, v = abs(px % 1 - .5), abs(py % 1 - .5)
        seam = np.clip((np.maximum(u, v)-.472)/.023, 0, 1)
        corners = np.hypot(np.maximum(u-.179, 0), np.maximum(v-.112, 0))
        waves = np.exp(-((corners-.133)/.021)**2)
        inside = np.exp(-((corners-.062)/.025)**2)
        value += -.11*seam - .09*waves - .043*inside
        rgb = np.array(base) + value[:, :, None]
    elif pattern in ('granite', 'asphalt', 'marble'):
        grad = dither*.15 + mid*.067 + large*.026
        if pattern == 'granite':
            grad *= .66
            grad += (NOISE.random((size,size))>.92)*.079
        if pattern == 'marble':
            grad *= .58
            grad += np.exp(-((np.sin((x + y*2 + noise(size,4,4)*.36)*math.tau*2))/.14)**2)*.087
        rgb = np.array(base) + grad[:, :, None]
    elif pattern == 'lawn':
        blades = noise(size, 110, 90)*.14
        warm = np.maximum(0, large+.11)*.13
        rgb = np.array(base)+ (blades+large*.11+mid*.116+dither*.05)[:, :, None] + warm[:, :, None]*np.array((1,.5,.14))
    elif pattern == 'artificial turf':
        fibres = noise(size,180,90)*.067 + mid*.031 + dither*.04
        rgb = np.array(base) + fibres[:, :, None]
    elif pattern == 'bark':
        streaks = noise(size, 57, 5)*.23 + noise(size, 112, 25)*.12
        rgb = np.array(base)+(value+streaks)[:, :, None]
    elif pattern == 'paint':
        streaks = noise(size, 67, 5)*np.maximum(.015, (large+.28)*.18)
        rgb = np.array(base)+(value*.61+streaks)[:, :, None]
    else:
        rgb = np.array(base)+value[:, :, None]
    image = packed_image(name, rgb)
    return surface(name, tuple(c**2.2 for c in base), roughness, metal=metal, image=image, metres=metres)


class Mesh:
    """Batch each architectural assembly into one editable material-indexed mesh."""
    def __init__(self, name, group, transform=None):
        self.name = name
        self.group = group
        self.transform = transform
        self.verts, self.faces, self.mats = [], [], []
        self.indices, self.smooth, self.uv = [], [], []

    def add(self, verts, faces, mat, *, uv=None, smooth=False):
        offset = len(self.verts)
        self.verts.extend(self.transform(*p) if self.transform else tuple(p) for p in verts)
        if mat not in self.mats:
            self.mats.append(mat)
        mat_index = self.mats.index(mat)
        scale = mat['metres']
        for i, face in enumerate(faces):
            self.faces.append(tuple(offset + j for j in face))
            self.indices.append(mat_index)
            self.smooth.append(smooth)
            if uv is not None:
                self.uv.extend(uv[i])
            else:
                a,b,c = (Vector(verts[j]) for j in face[:3])
                normal = (b-a).cross(c-a)
                axis = max(range(3), key=lambda k: abs(normal[k]))
                s,t = ((1,2),(0,2),(0,1))[axis]
                self.uv.extend((verts[j][s]/scale, verts[j][t]/scale) for j in face)

    def box(self, p, size, mat, *, angle=0):
        x,y,z = p
        w,d,h = (v/2 for v in size)
        cc,ss = math.cos(angle),math.sin(angle)
        corners = [(-w,-d,-h),(w,-d,-h),(w,d,-h),(-w,d,-h),
                   (-w,-d,h),(w,-d,h),(w,d,h),(-w,d,h)]
        self.add([(x+a*cc-b*ss,y+a*ss+b*cc,z+c) for a,b,c in corners], FACE_BOX, mat)

    def span(self, limits, mat):
        self.box(tuple((a+b)/2 for a,b in limits),tuple(b-a for a,b in limits),mat)

    def tube(self, points, radii, mat, sides=8, *, irregular=0):
        p = [Vector(v) for v in points]
        r = [radii]*len(p) if isinstance(radii,(int,float)) else radii
        verts,faces,uv = [],[],[]
        travel = 0
        tangent = (p[1]-p[0]).normalized()
        axis = Vector((0,0,1)) if abs(tangent.z)<.82 else Vector((0,1,0))
        scale = mat['metres']
        for i, center in enumerate(p):
            tangent = (p[min(i+1,len(p)-1)]-p[max(0,i-1)]).normalized()
            u = tangent.cross(axis).normalized()
            v = tangent.cross(u)
            for j in range(sides):
                angle = j*math.tau/sides
                radius = r[i]*(1+irregular*math.sin(j*3.7+i*.82))
                verts.append(center+radius*(u*math.cos(angle)+v*math.sin(angle)))
            if i==0:
                continue
            end = travel+(p[i]-p[i-1]).length/scale
            for j in range(sides):
                a=(j+1)%sides
                faces.append(((i-1)*sides+j,(i-1)*sides+a,i*sides+a,i*sides+j))
                x0 = j/sides*max(r)*math.tau/scale
                x1 = (j+1)/sides*max(r)*math.tau/scale
                uv.append(((x0,travel),(x1,travel),(x1,end),(x0,end)))
            travel = end
        faces += [tuple(reversed(range(sides))), tuple(range(len(verts)-sides,len(verts)))]
        disk = tuple((.5+.42*math.cos(j*math.tau/sides),.5+.42*math.sin(j*math.tau/sides)) for j in range(sides))
        uv += [tuple(reversed(disk)),disk]
        self.add(verts,faces,mat,uv=uv,smooth=True)

    def sheet(self, polygon, mat):
        self.add(polygon,[tuple(range(len(polygon)))],mat)

    def leaf(self, position, tangent, length, width, mat, *, droop=.16):
        p=Vector(position)
        d=Vector(tangent).normalized()*length
        ref=(0,0,1) if abs(d.z/length)<.97 else (0,1,0)
        w=d.cross(Vector(ref)).normalized()*width*.5
        tip=p+d+Vector((0,0,-length*droop))
        ridge=p+d*.44+Vector((0,0,width*.14))
        self.add([p,p+d*.32-w,tip,p+d*.40+w,ridge],[(0,1,4),(1,2,4),(2,3,4),(3,0,4)],mat)

    def globe(self, p, radii, mats, rng, *, sides=11, rings=7):
        x,y,z=p
        a,b,c=radii
        points=[(x,y,z+c)]
        for j in range(1,rings):
            v=j*math.pi/rings
            for k in range(sides):
                u=k*math.tau/sides
                points.append((x+a*math.sin(v)*math.cos(u),y+b*math.sin(v)*math.sin(u),z+c*math.cos(v)))
        points.append((x,y,z-c))
        faces=[]
        for j in range(rings-2):
            first=1+j*sides
            for k in range(sides):
                n=(k+1)%sides
                faces.append((first+k,first+sides+k,first+sides+n,first+n))
        for k in range(sides):
            n=(k+1)%sides
            last=1+(rings-2)*sides
            faces += [(0,1+k,1+n),(len(points)-1,last+n,last+k)]
        self.add(points,faces,rng.choice(mats),smooth=True)

    def finish(self, **properties):
        if not self.faces:
            raise ValueError(f'Empty mesh {self.name}')
        mesh = bpy.data.meshes.new(self.name)
        mesh.from_pydata(self.verts,[],self.faces)
        mesh.update()
        for mat in self.mats:
            mesh.materials.append(mat)
        mesh.polygons.foreach_set('material_index',self.indices)
        mesh.polygons.foreach_set('use_smooth',self.smooth)
        if any(mat.node_tree.nodes.get('Image Texture') for mat in self.mats):
            uv_layer = mesh.uv_layers.new(name='UVMap')
            uv_layer.uv.foreach_set('vector',[value for uv in self.uv for value in uv])
        ob=bpy.data.objects.new(self.name,mesh)
        self.group.objects.link(ob)
        for key,value in properties.items():
            ob[key]=value
        return ob


def text(name, words, position, mat, group, font, width, height, *,
         yaw=0, tilt=math.pi/2, depth=.014, tracking=1, fit_width=True):
    shape=bpy.data.curves.new(name,'FONT')
    shape.body=words
    shape.font=font
    shape.align_x='CENTER'
    shape.align_y='CENTER'
    shape.size=1
    shape.space_character=tracking
    shape.resolution_u=6
    shape.extrude=depth
    shape.bevel_depth=.002 if depth>.003 else 0
    shape.materials.append(mat)
    ob=bpy.data.objects.new(name,shape)
    group.objects.link(ob)
    bpy.context.view_layer.update()
    sx=width/max(ob.dimensions.x,.01)
    sy=height/max(ob.dimensions.y,.01)
    ob.location=position
    ob.rotation_euler=(tilt,0,yaw)
    ob.scale = (sx if fit_width else min(sx,sy),sy,1)
    return ob


def foliage_material():
    """A clustered foliage texture fills the crown between modeled leaves."""
    size = 448
    pixels = np.zeros((size,size,4), dtype=np.float32)
    source = random.Random(9196)
    for i in range(1230):
        theta = source.uniform(0,math.tau)
        rad = (source.random() ** .72) * size*.46
        x = size*.5 + math.cos(theta)*rad
        y = size*.5 + math.sin(theta)*rad
        length = source.uniform(4.8,13.8)
        width = length*source.uniform(.22,.48)
        blade = source.uniform(0,math.tau)
        x0,x1 = max(0,int(x-length-2)),min(size,int(x+length+3))
        y0,y1 = max(0,int(y-length-2)),min(size,int(y+length+3))
        cy,cx = np.mgrid[y0:y1,x0:x1]
        u = ((cx-x)*math.cos(blade)+(cy-y)*math.sin(blade))/length
        v = (-(cx-x)*math.sin(blade)+(cy-y)*math.cos(blade))/width
        outline = abs(u)**1.7 + abs(v)**1.31 + .12*u*v
        leaf = outline<1
        tint=np.array(source.choice([(.186,.268,.072),(.216,.307,.094),(.139,.218,.071),
                                     (.211,.291,.093),(.32,.39,.112),(.267,.341,.119)]))
        rib=np.exp(-(v/.071)**2) * .052
        shading=source.uniform(-.034,.033) + .062*(.5-u)*v + rib
        patch=pixels[y0:y1,x0:x1]
        patch[:,:,:3][leaf]=(tint+shading[:,:,None])[leaf]
        patch[:,:,3][leaf]=1
    image=packed_image('Cụm lá cây',pixels)
    mat=surface('Cụm lá cây có gân',(.13,.22,.06),.79,image=image,opacity=.99,double=True)
    nodes=mat.node_tree.nodes
    mat.node_tree.links.new(nodes.get('Image Texture').outputs['Alpha'],nodes.get('Principled BSDF').inputs['Alpha'])
    mat.surface_render_method='DITHERED'
    mat['leafCutout']=True
    return mat



def leaf_spray(mesh, center, radius, angle, material):
    for turn in (-.91,.18,1.23):
        az=angle+turn
        u=Vector((math.cos(az),math.sin(az),0))*radius
        v=Vector((-.41*math.sin(az),.41*math.cos(az),.91))*radius*.94
        mesh.add([center-u-v,center+u-v,center+u+v,center-u+v],
                 [(0,1,2,3)],material,uv=[((0,0),(1,0),(1,1),(0,1))])
