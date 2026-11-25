"""Dựng cổng Võ Văn Ngân và tòa nhà Trung tâm. Blender 5.3, mét, trục Z lên."""
import math
import random
import sys
import tempfile
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector

HERE = Path(__file__).resolve().parent
sys.dont_write_bytecode = True
sys.path.insert(0, str(HERE))
from campus_mesh import Mesh, collection, empty, packed_image, surface, text, tiled

ROOT = HERE.parent
MAP = ROOT/'maps'/'trung-tam'
rng = random.Random(20733)
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.unit_settings.system = 'METRIC'

gate_group = collection('01 · Cổng số 1 Võ Văn Ngân')
gate_signs = collection('Chữ nổi, phù hiệu và LED', gate_group)
gate_wings = collection('Hàng rào, cửa hàng và vỉa hè', gate_group)
gate_flags = collection('Mười hai lá cờ trên mái', gate_group)
tower_group = collection('02 · Tòa nhà Trung tâm')
tower_front = collection('Tháp kính và lam mặt trước', tower_group)
tower_rear = collection('Mặt hậu, mái và thiết bị', tower_group)
classrooms = collection('Hai cánh nhà hành lang', tower_group)
portico_group = collection('Mái đón, bậc và ba cụm cửa', tower_group)
lobby_group = collection('03 · Sảnh hành chính')
land_group = collection('04 · Khuôn viên và đường nội bộ')
greenery = collection('05 · Cây xanh, cọ và bồn hoa')
street_group = collection('06 · Biển, đèn đường và xe đỗ')
physics = collection('07 · Va chạm, cao độ và vị trí vào')
preview_group = collection('08 · Camera và ánh sáng Blender')

brick = tiled('Gạch thẻ cổng màu đất nung', (.62,.315,.190), 'brick', 1.48, size=768)
stone = tiled('Đá chân cổng xanh đen', (.121,.158,.176), 'granite', 1.27, .59)
wall_stone = tiled('Đá nâu ghi hàng rào', (.44,.388,.337), 'marble', 1.93, .62)
plaster = tiled('Bê tông ngà có vệt mưa', (.83,.806,.734), 'paint', 5.3)
cement = tiled('Bậc bê tông xám sáng', (.61,.623,.599), 'granite', 1.67)
gray_granite = tiled('Đá granite xám hạt mịn', (.395,.383,.357), 'granite', 1.57, .48)
lobby_stone = tiled('Đá bóng sảnh màu be', (.68,.624,.561), 'marble', 1.43, .22)
granite_black = tiled('Đá đen bóng của sảnh và tam cấp', (.108,.131,.145), 'granite', 1.22, .27)
granite_rose = tiled('Đá nâu hồng sân trước', (.51,.302,.236), 'granite', 1.51, .43)
street = tiled('Nhựa đường xám', (.319,.313,.300), 'asphalt', 4.8)
pavers = tiled('Gạch lát sân trước màu vàng kem', (.764,.655,.534), 'paving', 1.64)
turf = tiled('Sân cỏ xen đất nắng', (.291,.379,.173), 'lawn', 4.35)
bark = tiled('Vỏ cây xám nứt dọc', (.37,.31,.238), 'bark', 1.68)
palm_bark = tiled('Thân cau xám nâu', (.508,.458,.365), 'bark', 1.06)
gray_paint = surface('Xám cột sảnh', (.31,.278,.214), .72)
cream = surface('Trắng ngà sơn mái', (.78,.746,.652), .65)
panel = surface('Tấm gân đứng ngà hơi xanh ở cổng', (.67,.698,.581), .69)
panel_seam = surface('Rãnh giữa các tấm cổng', (.40,.432,.351), .91)
black = surface('Chữ nổi xanh than', (.035,.050,.055), .4, metal=.20)
steel = surface('Inox xước', (.53,.58,.60), .32, metal=.60)
white_metal = surface('Khung nhôm sáng', (.53,.594,.602), .41, metal=.34)
frame = surface('Nhôm tối khung kính', (.077,.103,.104), .51, metal=.23)
roof_mint = surface('Tôn mái xanh bạc hà', (.431,.645,.584), .57, metal=.25)
roof_gray = tiled('Mái bê tông có đốm cũ', (.416,.418,.388), 'granite', 2.7)
recess = surface('Bóng trong khe và lam', (.041,.068,.064), .86)
asphalt_line = surface('Vạch sơn vàng đường nội bộ', (.78,.48,.11), .82)
zebra = surface('Vạch qua đường trắng', (.80,.778,.713), .89)
led = surface('LED xanh lam', (.013,.138,.465), .44, emit=.39)
led_dark = surface('Họa tiết nền LED xanh đậm', (.017,.066,.234), .49, emit=.24)
led_light = surface('Họa tiết LED xanh cyan', (.022,.235,.535), .47, emit=.42)
paper = surface('Chữ trắng ngà', (.9,.903,.858), .57)
red = surface('Đỏ bảng hiệu và dải quầy', (.59,.023,.038), .59)
blue = surface('Chữ UTE xanh cobalt', (.022,.081,.312), .4, metal=.26)
burgundy = surface('Đỏ rượu Agribank', (.325,.035,.082), .64)
shop_blue = surface('Biển GS25 xanh', (.01,.202,.473), .53)
terracotta = surface('Chậu đất nung', (.41,.139,.061), .75)
gold = surface('Chữ đồng mặt bia', (.72,.414,.126), .36, metal=.4)
mark_red = tiled('Sơn đỏ trên gạch sân kỷ niệm', (.89,.222,.117), 'paving', 1.64)
glass_clear = surface('Kính thật cửa sảnh', (.449,.731,.702), .18, opacity=.23, metal=.2, double=True)
glass_fence = surface('Kính hàng rào ánh xanh', (.39,.66,.54), .22, opacity=.36, metal=.15, double=True)
glass_strip = surface('Dải mờ xanh trên cửa sảnh', (.28,.67,.69), .38, opacity=.76, double=True)
glass_dark = surface('Kính cửa hàng', (.071,.133,.143), .24, metal=.46)
glass = [surface(f'Kính xanh tòa tháp {i+1}', tone, .25, metal=.49, coat=.16) for i,tone in enumerate([
    (.084,.326,.404),(.079,.283,.347),(.125,.417,.489),(.102,.373,.437),
    (.133,.445,.474),(.066,.255,.339),(.116,.343,.403),(.139,.449,.512)
])]
warm_lamp = surface('Chóa đèn sảnh', (.98,.935,.79), .4, emit=1.4)
cloth = {name:surface(f'Cờ · {name}', c, .79, double=True) for name,c in {
    'đỏ':(.66,.023,.046),'vàng':(.91,.686,.043),'lam':(.049,.12,.53),
    'lục':(.043,.382,.329),'lơ':(.015,.328,.632),'trắng':(.88,.882,.80),
    'cam':(.90,.28,.038),'đen':(.066,.072,.086)
}.items()}
FONT_DIR = Path('/System/Library/Fonts/Supplemental')
bold = bpy.data.fonts.load(str(FONT_DIR/'Arial Bold.ttf'))
regular = bpy.data.fonts.load(str(FONT_DIR/'Arial.ttf'))
serif = bpy.data.fonts.load(str(FONT_DIR/'Times New Roman Bold.ttf'))
italic = bpy.data.fonts.load(str(FONT_DIR/'Arial Bold Italic.ttf'))

GATE_X, GATE_Y = -70.5, 27.0
BUILDING_FRONT, BUILDING_BACK = 47.7, 77.6
FLOOR = 1.63


def gate_point(x,y,z):
    return (GATE_X+y,GATE_Y-x,z)


def gate_mesh(name, group=gate_group):
    return Mesh(name,group,gate_point)


def bounds(x0,x1,y0,y1, *, label='Va chạm'):
    empty(label,physics,((x0+x1)/2,(y0+y1)/2,1),
          ((x1-x0)/2,(y1-y0)/2,1),walkCollider=True)


def gate_block(x0,x1,y0,y1):
    bounds(GATE_X+y0,GATE_X+y1,GATE_Y-x1,GATE_Y-x0)


def walk_height(x0,x1,y0,y1,start,end,axis='y'):
    empty('Cao độ lối đi',physics,((x0+x1)/2,(y0+y1)/2,max(start,end)),
          ((x1-x0)/2,(y1-y0)/2,.025),floorStart=start,floorEnd=end,
          floorAxis='x' if axis=='x' else 'depth')


def gate_text(name, caption, x,y,z,width,height, mat=black, font=bold,depth=.012):
    return text(name,caption,gate_point(x,y,z),mat,gate_signs,font,width,height,
                yaw=-math.pi/2,depth=depth)


def flag(mesh,x,y,z,w,h, bands, *, phase=0, star=False):
    def position(u,v,offset=0):
        bend = math.sin(u*10+v*2.5+phase)*.095*u
        fold = .53+.23*math.sin(v*math.pi*.91+phase*.34)+.23*v if h>w*2 else 1
        return (x+w*u*.82*fold, y+offset+w*(.41*u+bend), z-h*v+.18*math.sin(3.3*u+phase)*u-.14*u*u)
    divisions = max(1,len(bands))
    for i,key in enumerate(bands):
        for u in range(11):
            for v in range(3):
                v0,v1=(i+v/3)/divisions,(i+(v+1)/3)/divisions
                u0,u1=u/11,(u+1)/11
                mesh.sheet([position(u0,v0),position(u1,v0),position(u1,v1),position(u0,v1)],cloth[key])
    if star:
        for side in (-1,1):
            verts=[position(.50,.455,side*.014)]
            for j in range(10):
                a=math.pi*j/5
                l=1 if not j%2 else .43
                verts.append(position(.50+math.sin(a)*.19*l,.455-math.cos(a)*.19*l,side*.014))
            mesh.add(verts,[(0,1+j,1+(j+1)%10) for j in range(10)],cloth['vàng'])


def roof_pole(mesh,x,y,z,pole_h,flag_size,bands, *, phase=0,star=False):
    mesh.tube([(x,y,z),(x,y,z+pole_h)],(.036,.026),steel,9)
    mesh.tube([(x,y,z+pole_h),(x,y,z+pole_h+.088)],(.058,.033),steel,10)
    mesh.tube([(x,y,z),(x,y,z+.105)],.085,white_metal,12)
    flag(mesh,x+.024,y,z+pole_h-.14,*flag_size,bands,phase=phase,star=star)


def logo_texture():
    image=bpy.data.images.load(str(MAP/'hcmute-emblem.png'))
    image.pack()
    image.filepath='//hcmute-emblem.png'
    return surface('Biểu trưng HCMUTE theo mẫu trường',(.9,.9,.9),.39,image=image)


def round_badge(mesh, x, y, z, r, mat):
    mesh.tube([(x,y+.018,z),(x,y-.015,z)],r,steel,72)
    corners=[(x+r*.987*math.cos(k*math.tau/72),y-.018,z+r*.987*math.sin(k*math.tau/72)) for k in range(72)]
    uv=tuple((.5+.495*math.cos(k*math.tau/72),.5+.495*math.sin(k*math.tau/72)) for k in range(72))
    mesh.add(corners,[tuple(range(72))],mat,uv=[uv])


logo = logo_texture()
structure = gate_mesh('Kết cấu ba lối: ô tô và hai lối bộ')
for x0,x1,y0,y1,top in [(-9.18,-7.37,0,3.08,5.49),(-.48,4.98,-.024,2.92,5.48),
                          (8.94,10.03,-.01,2.92,5.48),(-14.74,-12.00,.09,2.68,4.30)]:
    structure.span(((x0,x1),(y0,y1),(.53,top)),brick)
    structure.span(((x0-.014,x1+.014),(y0-.013,y1+.013),(0,.55)),stone)
    gate_block(x0,x1,y0,y1)
structure.span(((4.98,8.94),(0,2.92),(3.86,5.49)),brick)
structure.span(((-12.00,-9.18),(.09,2.68),(3.80,4.30)),brick)
structure.span(((-14.74,-9.17),(.03,2.76),(4.30,4.74)),cream)
structure.span(((9.56,10.03),(-.058,-.020),(.91,5.48)),stone)
structure.span(((-11.20,11.20),(-.48,3.24),(5.49,7.89)),panel)
structure.span(((-11.21,11.21),(-.486,3.255),(5.46,5.55)),cream)
structure.span(((-11.21,11.21),(-.493,3.25),(7.83,7.90)),cream)
structure.span(((-.71,5.21),(-.34,3.07),(-.029,.016)),cement)
for j in range(151):
    x=-11.13+j*.1484
    structure.span(((x,x+.012),(-.493,-.482),(5.59,7.83)),panel_seam)
    structure.span(((x-.039,x+.005),(-.506,-.491),(5.58,7.83)),panel)
    structure.span(((x,x+.012),(3.242,3.254),(5.59,7.83)),panel_seam)
for x in (-6.24,-3.65,-1.05,1.22,3.4,6.0,8.22):
    structure.tube([(x,1.38,5.434),(x,1.38,5.47)],.109,warm_lamp,16)
structure.finish()

gate_text('Biển cổng · Tiếng Việt','ĐẠI HỌC CÔNG NGHỆ KỸ THUẬT TP. HỒ CHÍ MINH',0,-.537,7.11,18.60,.81,depth=.038)
gate_text('Biển cổng · Tiếng Anh','HCMC UNIVERSITY OF TECHNOLOGY AND ENGINEERING',0,-.537,6.10,15.78,.59,depth=.028)
gate_text('Địa chỉ trên trụ gạch','SỐ 1 VÕ VĂN NGÂN',2.22,-.062,4.14,3.24,.36,paper,depth=.022)
gate_text('Chữ dưới phù hiệu','HCMUTE',2.16,-.073,1.43,2.25,.39,black,depth=.023)

gate_decor=gate_mesh('Phù hiệu và khung màn hình điện tử', gate_signs)
round_badge(gate_decor,2.16,-.105,2.68,1.007,logo)
gate_decor.span(((-.505,9.55),(-.135,-.012),(4.55,5.52)),black)
gate_decor.span(((-.447,9.48),(-.146,-.131),(4.594,5.476)),led)
gate_decor.span(((-.447,9.48),(-.154,-.148),(5.274,5.476)),paper)
for x in [-.10,.28,.75,1.1,6.95,7.9,8.73,9.20]:
    gate_decor.span(((x,x+.019),(-.159,-.157),(4.62,5.23)),led_light)
for j in range(13):
    x=-.40+j*.77
    gate_decor.span(((x,x+rng.uniform(.33,.67)),(-.159,-.158),(4.63+j%4*.047,4.646+j%4*.047)),led_dark)
for x in (7.54,8.32,9.01):
    gate_decor.tube([(x,-.17,4.82),(x,-.163,4.82)],.10,led_light,18)
gate_decor.finish(noShadow=True)
gate_text('LED · Lời chào','WELCOME TO HCM-UTE !',4.45,-.166,5.376,3.04,.142,red,depth=.001)
gate_text('LED · Khóa học','TRAINING MODULE',4.45,-.168,5.181,1.56,.091,paper,depth=.001)
gate_text('LED · Tiêu đề','ARTIFICIAL INTELLIGENCE ESSENTIALS',4.45,-.168,4.944,6.73,.21,paper,depth=.001)
gate_text('LED · Địa điểm','LOCATION  ·  ROOM F1 606',5.35,-.167,4.696,1.47,.059,paper,depth=.001)

hardware=gate_mesh('Trụ inox, dây đỏ và bộ điều khiển lối bộ')
for x in (.03,4.32):
    hardware.tube([(x,-.82,0),(x,-.82,.059)],.151,steel,16)
    hardware.tube([(x,-.82,.05),(x,-.82,1.02)],.047,steel,12)
    hardware.tube([(x,-.82,1.0),(x,-.82,1.035)],.056,steel,12)
    gate_block(x-.12,x+.12,-.94,-.70)
for i in range(28):
    x=.07+i*.15
    hardware.span(((x,x+.149),(-.832,-.811),(.917,.958)),red if i%3 else paper)
gate_block(.03,4.32,-.84,-.80)
for x in (-12.66,9.83):
    hardware.box((x,.64,.58),(.39,.39,1.12),gray_granite)
    hardware.box((x,.62,1.152),(.43,.42,.073),white_metal)
    hardware.box((x,.402,.91),(.21,.034,.12),glass_dark)
    hardware.box((x,.376,.90),(.055,.019,.026),led_light)
    gate_block(x-.20,x+.20,.43,.85)
hardware.finish()

flags_mesh=gate_mesh('Cột và vải trên cổng',gate_flags)
flag_palette=['vàng','lam','đỏ','lục','lơ','đỏ','đỏ','lơ','lục','đỏ','lam','vàng']
for i,(x,name) in enumerate(zip((-10.93,-9.13,-7.24,-5.35,-3.47,-1.51,-.42,1.79,4.08,6.30,8.67,10.93),flag_palette)):
    high=i in (5,6)
    roof_pole(flags_mesh,x,.12,7.9,4.68 if high else 3.20+(i%3)*.10,
              (.89,3.35) if high else (.67,2.08),[name],phase=i*.76,star=high)
flags_mesh.finish()

fence=gate_mesh('Hàng rào đá và ô kính phía Gift Shop',gate_wings)
fence.span(((-36.1,-14.72),(.31,.62),(0,.90)),wall_stone)
fence.span(((-36.1,-14.72),(.29,.65),(2.53,2.64)),wall_stone)
for a,b in [(-36.1,-34.7),(-31.31,-30.78),(-27.53,-27.03),(-25.20,-21.19),(-18.7,-18.10),(-15.52,-14.72)]:
    fence.span(((a,b),(.31,.62),(.89,2.59)),wall_stone)
for a,b in [(-34.7,-31.31),(-30.78,-27.53),(-27.03,-25.20),(-21.19,-18.7),(-18.10,-15.52)]:
    fence.span(((a+.026,b-.026),(.443,.475),(.93,2.52)),glass_fence)
    for x in (a+.021,b-.021):
        fence.span(((x-.024,x+.024),(.397,.495),(.91,2.56)),white_metal)
    for z in (.933,2.54):
        fence.span(((a,b),(.398,.49),(z-.024,z+.024)),white_metal)
fence.span(((-16.55,-14.73),(.22,.81),(0,3.10)),stone)
gate_block(-36.1,-14.72,.22,.81)
fence.span(((10.21,18.5),(.26,.67),(0,1.10)),brick)
fence.span(((10.21,18.5),(.24,.69),(1.08,1.23)),cement)
for x in (10.24,13.37,18.41):
    fence.box((x,.42,1.40),(.34,.59,2.79),cement)
for j in range(40):
    x=10.48+j*.20
    fence.span(((x,x+.058),(.36,.447),(1.21,2.90)),white_metal)
for z in (1.42,2.60):
    fence.span(((10.31,18.48),(.34,.46),(z,z+.065)),steel)
gate_block(10.07,18.5,.21,.72)
fence.finish()
gate_text('Chữ nổi UTE trên đá','U T E',-23.21,.278,1.88,3.13,1.04,blue,depth=.024)
gate_text('Mốc thành lập','Since 1962',-23.21,.277,1.11,2.37,.29,blue,italic,depth=.016)

shops=gate_mesh('Cụm Gift Shop, Agribank, GS25 và mái hiên',gate_wings)
shops.span(((-21.3,-14.7),(1.7,7.0),(0,3.57)),wall_stone)
shops.span(((-21.55,-14.7),(1.59,7.2),(3.51,4.40)),frame)
for x0,x1,mat in [(18.8,29.02,burgundy),(29.02,38.05,shop_blue),(38.05,44.8,terracotta)]:
    shops.span(((x0,x1),(2.08,7.0),(0,5.15)),cream)
    shops.span(((x0,x1),(1.97,2.13),(3.52,5.15)),mat)
    shops.span(((x0+.12,x1-.12),(1.975,2.08),(.32,3.45)),glass_dark)
    shops.span(((x0,x1),(1.44,2.26),(3.37,3.59)),mat)
    for j in range(8):
        x=x0+(x1-x0)*j/8
        shops.span(((x,x+.085),(1.91,2.05),(.22,3.44)),frame)
    for z in (.27,2.85):
        shops.span(((x0,x1),(1.92,2.02),(z,z+.065)),white_metal)
    gate_block(x0,x1,1.94,7.0)
shops.span(((19.62,20.87),(1.88,1.94),(4.01,4.85)),gold)
shops.sheet([(19.70,1.875,4.04),(20.81,1.875,4.04),(20.81,1.875,4.80)],burgundy)
shops.span(((17.75,44.8),(1.96,2.08),(5.15,5.24)),red)
for x in (28.75,35.9):
    shops.tube([(x,.10,.2),(x,.10,2.57)],.039,frame,8)
    top=(x,.10,3.11)
    ring=[(x+1.64*math.cos(i*math.pi/4),.10+1.64*math.sin(i*math.pi/4),2.57) for i in range(8)]
    for j in range(8):
        shops.add([top,ring[j],ring[(j+1)%8]],[(0,1,2)],granite_rose if j%2 else cream)
shops.finish()
gate_text('Chữ Gift Shop','GIFT SHOP',-18.16,1.566,4.04,2.83,.37,paper,regular)
gate_text('Chữ Agribank','AGRIBANK',24.83,1.91,4.42,6.77,.729,paper,serif)
gate_text('Chữ GS25','GS25',33.38,1.91,4.43,2.04,.65,paper)
gate_text('Chữ Highlands','HIGHLANDS',41.45,1.91,4.36,4.10,.47,paper)

terrain=Mesh('Nền khuôn viên hành chính',land_group)
terrain.span(((-120,76),(-37,96),(-.25,-.061)),turf)
terrain.finish(noShadow=True)

road=Mesh('Đường Võ Văn Ngân và các nhánh nội bộ',land_group)
for x0,x1,y0,y1 in [
    (-110,-70.52,-32,84),(-70.52,-64.3,16.3,35.8),(-64.3,-54.4,-13.0,80.2),
    (54.4,64.3,-13.0,80.2),(-64.3,64.3,-22.4,-13.0),(-64.3,64.3,80.2,88.9),
    (-54.4,-9.0,28.35,35.46),(9.0,54.4,28.35,35.46),(-9.0,9.0,27.85,30.09),
]:
    road.span(((x0,x1),(y0,y1),(-.058,.001)),street)
road.finish(noShadow=True)

paths=Mesh('Lối lát vàng, bó vỉa và sân kỷ niệm',land_group)
# The open passages have flush paving; the sidewalk resumes beside the brickwork.
for x0,x1,y0,y1 in [
    (-75.0,-70.69,34.38,63.30),(-74.92,-70.69,-19.20,26.93),
    (-70.92,-67.35,36.39,62.80),(-70.63,-63.0,17.95,22.05),
    (-70.48,-64.31,11.0,16.3),(-75.0,-70.71,63.30,82.4),
    (-75.0,-70.71,-34.5,-19.2),(-54.36,54.36,-12.95,-10.82),
    (-54.38,54.38,19.25,28.34),(-8.95,8.95,28.34,30.10),
    (-4.05,4.05,-10.81,19.25),(-56.0,-54.38,-10.82,80.18),(54.38,56.0,-10.82,80.18),
    (-53.96,53.96,78.25,80.19),
]:
    paths.span(((x0,x1),(y0,y1),(-.056,.052)),pavers)
    if max(x1-x0,y1-y0)>4:
        if x1-x0>y1-y0:
            for y in (y0,y1):
                paths.box(((x0+x1)/2,y,.041),(x1-x0,.102,.112),cement)
        else:
            for x in (x0,x1):
                paths.box((x,(y0+y1)/2,.041),(.104,y1-y0,.112),cement)
# Paved transitions with rounded corners at the central garden axis.
for side in (-1,1):
    outer=[(side*(4.04+3.8*math.cos(t)),19.24-3.65+3.65*math.sin(t),.054)
           for t in [j*math.pi/22 for j in range(12)]]
    polygon=[(side*4.02,19.24-3.65,.054),*outer]
    paths.sheet(polygon if side>0 else list(reversed(polygon)),pavers)
paths.finish(noShadow=True)

markings=Mesh('Vạch qua đường, vạch đứt và nắp hố ga',land_group)
for x in range(-54,55,5):
    if abs(x)>8:
        markings.box((x,31.81,.009),(1.6,.086,.005),asphalt_line)
    markings.box((x,-17.65,.009),(1.8,.102,.006),asphalt_line)
    markings.box((x,84.56,.009),(1.8,.102,.006),asphalt_line)
for y in range(-12,81,5):
    for x in (-59.35,59.35):
        if abs(y-30)>3:
            markings.box((x,y,.009),(.093,1.68,.006),asphalt_line)
for x in (-59.35,59.35):
    for y in (26.65,38.38,74.1,-10.94):
        for i in range(8):
            xx=x+(i-3.5)*1.06
            markings.box((xx,y,.013),(.57,2.65,.008),zebra)
for i in range(7):
    markings.box((-67.40,27.62+i*1.12,.010),(2.12,.56,.008),zebra)
for y in (22.65,30.91,37.2):
    markings.box((-63.75,y,.011),(2.98,.094,.009),zebra)
for x,y in [(-61.45,35.80),(-76.2,30.1),(52.2,32.8),(35.5,-20.1)]:
    markings.box((x,y,.013),(.82,.82,.013),stone)
    for j in range(9):
        markings.box((x,y+(j-4)*.080,.022),(.65,.028,.011),frame)
markings.finish(noShadow=True)

pavement_letters=collection('Chữ sơn trên sân',land_group)
def painted_text(words, position, width, height):
    ob=text(words,words,position,mark_red,pavement_letters,bold,width,height,
            yaw=math.pi,tilt=0,depth=0,tracking=1.13)
    bpy.context.view_layer.update()
    bpy.ops.object.select_all(action='DESELECT')
    ob.select_set(True)
    bpy.context.view_layer.objects.active=ob
    bpy.ops.object.convert(target='MESH')
    bpy.context.view_layer.update()
    uv=ob.data.uv_layers.new(name='UVMap') if not ob.data.uv_layers else ob.data.uv_layers.active
    for loop in ob.data.loops:
        point=ob.matrix_world @ ob.data.vertices[loop.vertex_index].co
        uv.uv[loop.index].vector=(point.x/mark_red['metres'],point.y/mark_red['metres'])
    ob['noShadow']=True


painted_text('HCMUTE', (0,24,.058),27.2,3.30)
painted_text('60', (0,20.64,.058),5.45,2.69)

# Tower is divided into the recessed blue front, vertical white fins and mostly
# solid back. The rear facade was modeled from the separate aerial reference.
tower_shell=Mesh('Khối tháp trung tâm và các gờ đứng',tower_front)
tower_shell.span(((-11.85,11.85),(53.60,75.38),(8.35,52.96)),plaster)
tower_shell.span(((-11.91,11.91),(48.64,75.49),(52.78,53.15)),cream)
tower_shell.span(((-12.05,-9.78),(48.61,75.14),(8.03,50.54)),plaster)
tower_shell.span(((9.78,12.05),(48.61,75.14),(8.03,50.54)),plaster)
tower_shell.span(((-10.99,10.99),(48.61,53.87),(8.63,52.79)),recess)
for x in (-9.35,-3.3,3.30,9.35):
    tower_shell.box((x,48.27,30.56),(.69,1.16,45.03),plaster)
    tower_shell.box((x,48.23,53.11),(.73,1.22,.13),cream)
for x in (-6.26,6.26):
    tower_shell.box((x,48.27,27.37),(.38,.92,33.0),plaster)
    tower_shell.box((x,48.2,43.90),(.414,1.0,.11),cream)
for z in (9.42,11.46,13.50,15.55):
    tower_shell.box((0,48.20,z),(5.98,1.08,.27),plaster)
tower_shell.finish()

curtain=Mesh('Kính xanh mặt chính, đố và nan nhôm',tower_front)
front_ranges=[(-11.95,-9.73,2),(-8.98,-3.68,5),(-2.94,2.94,6),(3.67,8.99,5),(9.74,11.95,2)]
for a,b,count in front_ranges:
    side= abs((a+b)/2)>3.4
    end_panel=abs((a+b)/2)>10
    z0=8.10
    top=50.56 if end_panel else 52.62
    height=top-z0
    rows=30 if end_panel else 32
    spacing=(b-a)/count
    for col in range(count):
        x=a+(col+.5)*spacing
        for row in range(rows):
            z=z0+height*(row+.5)/rows
            if side and not end_panel and (z > 43.68 or z < 14.07):
                continue
            xtrim = spacing-.032
            curtain.box((x,48.535,z),(xtrim,.118,height/rows-.026),
                        rng.choices(glass,weights=(4,3,6,9,2,2,5,3))[0])
            if (row*17+col*9+int(a*11))%31==0 and row>4:
                curtain.box((x+spacing*.19,48.438,z-.035),(spacing*.49,.096,height/rows*.58),frame)
                curtain.box((x+spacing*.19,48.381,z-.031),(spacing*.41,.041,height/rows*.49),glass[5])
        curtain.box((a+col*spacing,48.455,(top+z0)/2),(.032,.055,height),frame)
    for row in range(rows+1):
        z=z0+row*height/rows
        if side and not end_panel and (z>43.71 or z<14.04):
            continue
        curtain.box(((a+b)/2,48.43,z),(b-a,.049,.033),frame)
    if side and not end_panel:
        for low,high in ((8.06,14.07),(43.68,52.65)):
            curtain.span(((a,b),(48.49,48.62),(low,high)),recess)
            for k in range(math.ceil((high-low)/.149)):
                z=low+k*.147+.038
                curtain.box(((a+b)/2,48.375,z),(b-a,.235,.045),white_metal)
        for x in (a+.05,(a+b)/2,b-.05):
            curtain.box((x,48.255,48.40),(.053,.075,9.02),steel)
curtain.finish()
text('Chữ đỏ trên đỉnh tháp','ĐẠI HỌC SƯ PHẠM KỸ THUẬT',(0,48.00,53.33),
     granite_rose,tower_front,bold,17.66,.94,depth=.065)

rear=Mesh('Mặt sau trắng, ô cửa nhỏ và lam dọc',tower_rear)
side_glass=Mesh('Mảng xanh hai hông tháp',tower_rear)
rear_top=52.88
rear.span(((-12.05,12.05),(74.92,75.94),(7.80,rear_top)),plaster)
for x,width in [(-10.74,.95),(-8.28,1.36),(-5.32,1.02),(-2.66,1.24),(0,1.93),
                (2.66,1.24),(5.32,1.02),(8.28,1.36),(10.74,.95)]:
    rear.box((x+.66,76.10,30.28),(.38,.43,45.20),cream)
    rear.box((x,76.018,30.22),(width,.13,44.76),roof_mint)
    for fl in range(14):
        z=9.35+fl*3.12
        for j in (-1,1):
            rear.box((x+j*width*.228,76.11,z),(width*.40,.07,.76),rng.choice(glass))
        rear.box((x,76.17,z),(.058,.038,.87),white_metal)
        for off in (-.39,.39):
            rear.box((x,76.18,z+off),(width,.078,.059),white_metal)
for side in (-1,1):
    x=side*12.07
    for i in range(17):
        y=49.10+i*1.47
        side_glass.box((x,y,30.68),(.121,1.41,44.90),roof_mint if i%4==2 else plaster)
        for fl in range(14):
            z=9.27+3.12*fl
            if i%4 in (0,2,3):
                side_glass.box((x+side*.10,y,z),(.091,1.24,.86),rng.choice(glass))
                side_glass.box((x+side*.16,y,z),(.05,.046,.91),white_metal)
        side_glass.box((x+side*.15,y+.71,30.70),(.19,.08,44.40),white_metal)
side_glass.finish()
rear.finish()

plinth=Mesh('Mặt sau tầng trệt: cửa kỹ thuật và bậc thềm',tower_rear)
plinth.span(((-11.87,11.87),(63.55,76.17),(0,8.36)),plaster)
plinth.span(((-11.92,11.92),(75.85,76.26),(0,1.32)),wall_stone)
for i in range(12):
    x=(i-5.5)*1.775
    plinth.box((x,76.225,3.19),(1.34,.085,2.20),white_metal)
    for dx in (-.316,.316):
        plinth.box((x+dx,76.279,3.18),(.593,.04,2.06),rng.choice(glass))
    plinth.box((x,76.32,3.57),(1.28,.046,.056),frame)
for i in range(6):
    z=(i+1)*.205
    plinth.box((0,76.25+(5.5-i)*.29,z/2),(4.36,.295,z),cement)
bounds(-11.9,11.9,63.54,76.23)
bounds(-2.19,2.19,76.20,78.0)
plinth.finish()

service=Mesh('Mái tháp, buồng kỹ thuật, bồn nước và chảo',tower_rear)
service.span(((-11.88,11.88),(48.61,75.69),(53.0,53.22)),roof_gray)
for x in (-11.76,11.76):
    service.box((x,62.06,53.62),(.217,27.10,.83),cream)
for y in (48.78,75.53):
    service.box((0,y,53.62),(23.63,.215,.83),cream)
service.span(((-4.9,5.75),(60.95,69.72),(53.22,57.34)),plaster)
service.span(((-5.08,5.93),(60.82,69.91),(57.34,57.55)),cream)
service.span(((-7.21,-4.87),(62.12,68.3),(53.22,56.41)),plaster)
service.span(((5.73,8.57),(60.96,67.71),(53.22,55.13)),plaster)
for x in (1.6,3.65):
    service.tube([(x,64.2,57.98),(x,66.89,57.98)],.56,steel,20)
    for y in (64.62,66.43):
        service.box((x,y,57.50),(1.26,.12,.28),frame)
    service.tube([(x,64.52,58.25),(x,64.52,58.87)],.075,steel,8)
service.tube([(-2.78,64.8,57.37),(-2.78,64.8,58.91)],.075,steel,9)
dish_axis=Vector((-.43,-.49,.76)).normalized()
dish_u=dish_axis.cross(Vector((0,0,1))).normalized()
dish_v=dish_axis.cross(dish_u)
pole=Vector((-2.78,64.8,58.78))
for j in range(38):
    a,b=j*math.tau/38,(j+1)*math.tau/38
    a=pole+(dish_u*math.cos(a)+dish_v*math.sin(a))*.84+dish_axis*.216
    b=pole+(dish_u*math.cos(b)+dish_v*math.sin(b))*.84+dish_axis*.216
    service.add([pole,a,b],[(0,1,2)],steel)
service.tube([pole,pole+dish_axis*.68],.025,steel,8)
for x in (5.13,5.62):
    service.tube([(x,69.84,53.25),(x,69.84,57.93)],.035,steel,7)
for i in range(15):
    z=53.38+i*.30
    service.tube([(5.13,69.82,z),(5.62,69.82,z)],.023,steel,7)
for i in range(8):
    x=-8.82+i*.93
    service.box((x,72.13,53.65),(.78,1.32,.83),cream)
    service.box((x,71.45,53.66),(.63,.08,.62),recess)
    for fin in range(5):
        service.box((x,71.412,53.40+fin*.114),(.63,.06,.027),white_metal)
service.finish()


def safety_rail(mesh,start,end,h=.90):
    a,b=Vector(start),Vector(end)
    z=Vector((0,0,h))
    mesh.tube([a+z,b+z],.026,steel,8)
    mesh.tube([a+z*.37,b+z*.37],.018,steel,7)
    steps=max(1,math.ceil((b-a).length/1.27))
    for i in range(steps+1):
        p=a.lerp(b,i/steps)
        mesh.tube([p,p+z],.022,steel,7)


def wing(side):
    name='Cánh Tây' if side<0 else 'Cánh Đông'
    body=Mesh(name+' · dầm, cột và các sàn hành lang',classrooms)
    glazing=Mesh(name+' · cửa sổ, cửa phòng và lam chắn nắng',classrooms)
    roof=Mesh(name+' · mái tôn xanh và sân mái',classrooms)
    a,b=sorted((side*11.98,side*52.92))
    center=(a+b)/2
    width=b-a
    body.span(((a,b),(53.76,72.68),(.4,18.49)),plaster)
    body.span(((a,b),(48.97,76.89),(0,1.46)),wall_stone)
    body.span(((a,b),(51.52,75.13),(17.36,18.26)),cream)
    outer=side*52.70
    body.box((outer,62.88,9.735),(.82,28.6,19.47),plaster)
    steps=8
    pitch=width/steps
    for level in range(4):
        z=1.46+level*4.02
        for y in (50.86,74.59):
            body.box((center,y,z-.10),(width,4.54,.289),plaster)
        body.box((center,48.63,z+.49),(width,.20,1.01),plaster)
        body.box((center,76.87,z+.50),(width,.195,1.019),plaster)
        body.box((center,48.51,z+.98),(width,.277,.08),cream)
        for bay in range(steps):
            x=a+(bay+.5)*pitch
            for dest,sign in ((53.72,-1),(72.72,1)):
                glazing.box((x,dest,z+1.96),(pitch-.67,.095,2.05),frame)
                for cell in range(6):
                    xx=x+(cell-2.5)*(pitch-.70)/6
                    height=1.34 if cell in (1,4) else 1.45
                    glazing.box((xx,dest+sign*.060,z+1.98),((pitch-.70)/6-.056,.084,height),rng.choice(glass))
                    glazing.box((xx,dest+sign*.106,z+2.27),((pitch-.70)/6-.019,.036,.037),white_metal)
                glazing.box((x,dest+sign*.03,z+.47),(.78,.08,.95),glass[5])
            if level in (1,2,3) and bay%2==side%2:
                glazing.box((x+.44,53.46,z+.55),(.69,.31,.48),cream)
                glazing.box((x+.44,53.28,z+.55),(.48,.063,.36),recess)
                for k in range(6):
                    glazing.box((x+.44,53.233,z+.385+k*.058),(.47,.038,.023),white_metal)
            for y in (48.87,76.64):
                for k in range(4):
                    glazing.box((x,y,z+1.08+k*.132),(pitch-.73,.061,.033),steel)
                for offset in (-pitch*.43,0,pitch*.43):
                    glazing.box((x+offset,y,z+1.265),(.041,.075,.68),steel)
            for k in range(6):
                glazing.box((x,48.79,z+2.83+k*.109),(pitch-.68,.42,.038),white_metal)
        for j in range(steps+1):
            x=a+j*pitch
            body.box((x,48.66,z+1.98),(.57,.78,4.13),plaster)
            body.box((x,76.63,z+1.98),(.39,.43,4.12),plaster)
    roof.span(((a-.37,b+.36),(48.25,77.43),(17.63,18.03)),roof_gray)
    roof.span(((a-.37,b+.36),(48.25,48.49),(17.92,18.69)),cream)
    roof.span(((a-.37,b+.36),(77.18,77.43),(17.92,18.71)),cream)
    roof.span(((a-.37,b+.36),(50.25,58.05),(20.03,20.255)),roof_mint)
    for x in (a-.32,b+.32):
        roof.box((x,62.81,18.27),(.24,28.89,.75),cream)
    for i in range(steps+1):
        x=a+i*pitch
        for y in (50.45,57.66):
            roof.box((x,y,19.02),(.126,.139,2.2),white_metal)
        roof.box((x,54.2,20.05),(.13,7.82,.32),frame)
    for i in range(round(width/.35)):
        x=a+i*.35
        roof.box((x,54.18,20.263),(.037,7.84,.037),roof_mint)
    for x in (a+3.15,b-3.15):
        for offset in (-.63,.63):
            roof.tube([(x+offset,74.01,18.54),(x+offset,75.67,18.54)],.41,steel,14)
    roof.box((a+.85,73.28,18.75),(1.62,3.56,1.48),roof_mint)
    for j in range(5):
        roof.box((b-2.1-j*.78,70.14,18.42),(.61,.77,.67),cream)
    # The rear service stairs and front corner stair visible from the adjoining roads.
    stairs=Mesh(name+' · thang ngoài và tay vịn',classrooms)
    x=side*39.9
    for front,facing in [(48.37,-1),(77.03,1)]:
        for row in range(9):
            height=FLOOR*(row+1)/9
            y=front+facing*((8-row+.5)*.297)
            stairs.box((x,y,height/2),(2.45,.299,height),granite_black if facing<0 else granite_rose)
            stairs.box((x,y+facing*.133,height-.015),(2.47,.044,.033),cement)
        for offset in (-1.29,1.29):
            safety_rail(stairs,(x+offset,front+facing*2.67,0),(x+offset,front,FLOOR))
        bounds(x-1.24,x+1.24,min(front,front+facing*2.67),max(front,front+facing*2.67))
    bounds(a,b,48.49,77.44,label='Cánh nhà hành chính')
    for mesh in (body,glazing,roof,stairs):
        mesh.finish()


wing(-1)
wing(1)

entry_arch=Mesh('Mái đón hai lớp, cửa lấy sáng và bốn trụ',portico_group)
for x in (-10.32,10.32):
    entry_arch.box((x,41.05,7.25),(1.20,14.11,.77),cream)
for y in (34.22,47.81):
    entry_arch.box((0,y,7.25),(22.24,1.30,.78),plaster)
entry_arch.box((0,43.12,7.31),(20.16,8.17,.60),cream)
entry_arch.box((0,35.86,7.31),(20.17,2.54,.60),cream)
for x in (-8.11,8.11):
    entry_arch.box((x,38.50,7.25),(4.12,2.91,.73),cream)
for x in (-3.59,0,3.59):
    entry_arch.box((x,38.50,7.25),(.113,2.86,.35),white_metal)
entry_arch.box((0,38.50,7.40),(12.14,2.82,.038),glass_clear)
for x in (-9.53,9.53,-4.79,4.79):
    y=36.92 if abs(x)>9 else 47.16
    width=1.12 if abs(x)>9 else 1.24
    entry_arch.box((x,y,(FLOOR+7.04)/2),(width,width,7.04-FLOOR),gray_paint)
    entry_arch.box((x,y,6.92),(width+.04,width+.04,.48),cream)
    entry_arch.box((x,y,FLOOR+.089),(width+.05,width+.05,.19),granite_black)
    bounds(x-width/2,x+width/2,y-width/2,y+width/2)
for x in (-8.54,-4.27,0,4.27,8.54):
    for y in (35.80,40.23,42.12,44.03,45.94):
        entry_arch.tube([(x,y,6.989),(x,y,7.018)],.088,warm_lamp,15)
entry_arch.finish()

entry_stairs=Mesh('Tam cấp rộng ốp đá đen và hai đường dốc',portico_group)
entry_stairs.span(((-10.85,10.85),(33.60,47.74),(0,FLOOR)),lobby_stone)
entry_stairs.span(((-6.38,6.38),(33.52,34.25),(FLOOR-.061,FLOOR+.008)),granite_black)
for step in range(10):
    top=FLOOR*(step+1)/10
    y=30.29+(step+.5)*.338
    entry_stairs.box((0,y,top/2),(12.75,.339,top),granite_black)
    entry_stairs.box((0,y-.153,top-.018),(12.76,.047,.044),cement)
    for x in (-5.11,-3.86,-2.57,-1.3,0,1.3,2.57,3.86,5.11):
        entry_stairs.box((x,y,top+.002),(.015,.320,.003),gray_granite)
walk_height(-6.38,6.38,30.29,33.67,0,FLOOR)
walk_height(-10.85,10.85,33.60,61.25,FLOOR,FLOOR)
for side in (-1,1):
    lo,hi=sorted((side*10.85,side*29.2))
    vertices=[(lo,37.55,0),(hi,37.55,0),(hi,41.0,0),(lo,41.0,0),
              (lo,37.55,FLOOR if side>0 else .052),(hi,37.55,.052 if side>0 else FLOOR),
              (hi,41.0,.052 if side>0 else FLOOR),(lo,41.0,FLOOR if side>0 else .052)]
    entry_stairs.add(vertices,[(3,2,1,0),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],pavers)
    walk_height(lo,hi,37.55,41.0,FLOOR if side>0 else 0,0 if side>0 else FLOOR,axis='x')
    for y in (37.57,40.98):
        safety_rail(entry_stairs,(side*10.90,y,FLOOR),(side*29.12,y,.053))
        bounds(lo+.20,hi-.20,y-.028,y+.028)
    x=side*6.76
    entry_stairs.box((x,32.08,.68),(.76,3.6,1.36),plaster)
    entry_stairs.box((x,32.08,1.37),(.80,3.60,.056),granite_black)
    bounds(x-.39,x+.39,30.28,33.89)
    bounds(min(side*6.37,side*10.85),max(side*6.37,side*10.85),33.56,33.73)
    for ya,yb in [(33.62,37.55),(41.0,47.67)]:
        bounds(side*10.83-.08,side*10.83+.08,ya,yb)
entry_stairs.finish()

facade=Mesh('Kính nguyên tầng, tay kéo và dải xanh',portico_group)
def glazing_wall(mesh,x0,x1,y,low,high,count,*,profile='full'):
    pitch=(x1-x0)/count
    for i in range(count+1):
        x=x0+i*pitch
        mesh.box((x,y,(low+high)/2),(.055,.086,high-low),frame)
    levels = (low+.044,low+1.27,low+3.34,high-.058) if profile == "full" else (low+.044,low+.76,high-.058)
    for z in (value for value in levels if value<high):
        mesh.box(((x0+x1)/2,y,z),(x1-x0,.082,.058),white_metal)
    if profile=='full':
        mesh.sheet([(x0,y,low),(x1,y,low),(x1,y,high),(x0,y,high)],glass_clear)
        mesh.sheet([(x0,y-.009,low+.94),(x1,y-.009,low+.94),
                    (x1,y-.009,low+1.095),(x0,y-.009,low+1.095)],glass_strip)
    else:
        z=low
        mesh.sheet([(x0,y,z),(x1,y,z),(x1,y,high),(x0,y,high)],glass_clear)


for a,b in [(-11.92,-4.25),(4.25,11.92)]:
    glazing_wall(facade,a,b,BUILDING_FRONT,FLOOR,7.04,6)
    bounds(a,b,BUILDING_FRONT-.043,BUILDING_FRONT+.047)
glazing_wall(facade,-4.23,4.23,BUILDING_FRONT,FLOOR+2.70,7.04,7,profile="transom")
# Four glass leaves held open inward on the photographed central entrance.
for x in (-3.81,-2.48,2.48,3.81):
    edge=x+(.37 if x<0 else -.37)
    front=BUILDING_FRONT+.052
    rear=BUILDING_FRONT+1.12
    facade.sheet([(x,front,FLOOR+.035),(edge,rear,FLOOR+.035),
                  (edge,rear,FLOOR+2.68),(x,front,FLOOR+2.68)],glass_clear)
    facade.sheet([(x,front-.008,FLOOR+.95),(edge,rear-.008,FLOOR+.95),
                  (edge,rear-.008,FLOOR+1.08),(x,front-.008,FLOOR+1.08)],glass_strip)
    facade.tube([(edge,rear,FLOOR+.75),(edge,rear,FLOOR+1.59)],.025,steel,9)
    for z in (FLOOR+.06,FLOOR+2.67):
        facade.box((x,front,z),(.12,.11,.088),steel)
    bounds(min(x,edge)-.016,max(x,edge)+.016,front,rear)
for a,b in [(-11.97,-10.89),(10.89,11.97)]:
    facade.span(((a,b),(47.35,48.43),(0,8.28)),plaster)
    for z in (FLOOR+.113,7.29):
        facade.box(((a+b)/2,47.32,z),(b-a,.055,.12),stone)
facade.box((0,47.51,5.26),(8.18,.16,1.08),granite_rose)
facade.box((0,47.408,5.26),(8.10,.046,1.00),led_light)
for i in range(12):
    x=(i%6-2.5)*1.20
    z=5.14-(i//6)*.239
    facade.box((x,47.377,z),(.98,.02,.188),led if i%2 else paper)
facade.finish(noShadow=True)
text('LED phía trước sảnh','Happy Birthday to you',(1.28,47.373,5.60),blue,portico_group,italic,3.32,.26,depth=.002)
text('LED · Tên trường','TRƯỜNG ĐẠI HỌC SƯ PHẠM KỸ THUẬT TP. HCM',(-2.58,47.371,5.60),
     blue,portico_group,bold,2.39,.137,depth=.002)

interior=Mesh('Sảnh thông tầng, nền đá và cầu hành lang',lobby_group)
interior.span(((-11.85,11.85),(47.70,61.40),(FLOOR-.21,FLOOR)),lobby_stone)
for y in (48.28,56.75,60.9):
    interior.box((0,y,FLOOR+.005),(23.45,.70,.012),gray_granite)
for x in (-9.96,9.96):
    interior.box((x,54.42,FLOOR+.003),(1.29,13.43,.011),gray_granite)
for i in range(19):
    interior.box(((i-9)*1.22,54.52,FLOOR+.0008),(.011,13.6,.002),gray_granite)
for j in range(15):
    interior.box((0,47.80+j*.947,FLOOR+.001),(23.66,.011,.002),gray_granite)
interior.span(((-11.99,11.99),(48.02,61.65),(7.82,8.42)),cream)
for x in (-11.98,11.98):
    interior.box((x,54.59,4.88),(.32,14.1,6.51),plaster)
    interior.box((x,54.59,FLOOR+.081),(.45,14.1,.162),granite_black)
    bounds(x-.22,x+.22,47.74,61.65)
interior.span(((-12.02,12.02),(61.27,63.48),(FLOOR,8.43)),plaster)
bounds(-12.04,12.04,61.15,63.60)
walk_height(-11.98,11.98,47.68,61.28,FLOOR,FLOOR)
for i in range(2):
    y=53.72+i*5.58
    for x in (-4.70,4.70):
        interior.box((x,y,4.53),(1.11,1.20,5.81),gray_paint)
        interior.box((x,y,FLOOR+.077),(1.16,1.25,.154),granite_black)
        interior.box((x,y,7.48),(1.17,1.27,.66),cream)
        bounds(x-.56,x+.56,y-.60,y+.60)
for x in (-8.14,8.14):
    interior.box((x,57.97,5.19),(7.25,6.5,.48),cream)
    interior.box((x+(.55 if x<0 else -.55),54.62,5.22),(6.8,.27,.62),paper)
interior.box((0,56.13,5.28),(8.34,2.66,.54),cream)
interior.box((0,54.72,5.24),(8.61,.248,.65),paper)
for x0,x1,y in [(-11.78,-5.34,54.55),(-4.1,4.1,54.59),(5.34,11.78,54.55)]:
    safety_rail(interior,(x0,y,5.58),(x1,y,5.58),.89)
    interior.sheet([(x0,y,5.62),(x1,y,5.62),(x1,y,6.36),(x0,y,6.36)],glass_clear)
for side in (-1,1):
    for x in (side*10.99,side*7.03):
        for y in (55.96,57.7,59.45):
            interior.tube([(x,y,4.932),(x,y,4.954)],.093,warm_lamp,13)
for x in (-2.74,0,2.74):
    for y in (55.18,56.45,57.8,59.10):
        interior.tube([(x,y,5.002),(x,y,5.027)],.090,warm_lamp,13)
for y in (48.74,50.22,51.72,53.05):
    interior.box((0,y,7.78),(3.31,.31,.10),plaster)
    for x in (-1.08,0,1.08):
        interior.tube([(x,y,7.715),(x,y,7.74)],.094,warm_lamp,14)
interior.finish()

medallion=Mesh('Hoa gió lát đá tròn trong sảnh',lobby_group)
cx,cy=0,51.11
for j in range(120):
    a,b=j*math.tau/120,(j+1)*math.tau/120
    for inner,outer,mat in [(0,2.77,granite_black),(2.77,3.25,gray_granite),
                            (3.25,3.44,granite_rose),(3.44,3.82,gray_granite)]:
        points=[(cx+rad*math.cos(theta),cy+rad*math.sin(theta),FLOOR+.014)
                for rad,theta in ((inner,a),(outer,a),(outer,b),(inner,b))]
        if inner==0:
            points.pop()
        medallion.sheet(points,mat)
for j in range(16):
    angle=j*math.tau/16
    points=[(cx+r*math.cos(a),cy+r*math.sin(a),FLOOR+.01435) for a,r in [
        (angle-.167,1.89),(angle,2.73),(angle+.167,1.89)]]
    medallion.sheet(points,granite_rose)
medallion.finish(noShadow=True)

reception=Mesh('Quầy thông tin cong trắng đỏ, ghế và bảng chỉ dẫn',lobby_group)
desk_x,desk_y=-5.9,51.25
def desk_outline(theta, z):
    return (desk_x+2.34*math.cos(theta),desk_y+.87*math.sin(theta),z)


for j in range(54):
    a,b=j*math.tau/54,(j+1)*math.tau/54
    for z0,z1,material in [(0,.09,steel),(.09,.45,red if j<13 or 38<j<52 else paper),
                           (.45,.47,red),(.47,.68,paper),(.68,.70,red),
                           (.70,1.0,red if j<13 or 38<j<52 else paper),(1.0,1.085,granite_black)]:
        reception.sheet([desk_outline(a,FLOOR+z0),desk_outline(b,FLOOR+z0),
                         desk_outline(b,FLOOR+z1),desk_outline(a,FLOOR+z1)],material)
    reception.add([(desk_x,desk_y,FLOOR+1.085),desk_outline(a,FLOOR+1.085),
                   desk_outline(b,FLOOR+1.085)],[(0,1,2)],granite_black)
bounds(-8.16,-3.62,50.4,52.11)
for x in (-6.85,-6.28):
    reception.tube([(x,51.83,FLOOR+.058),(x,51.83,FLOOR+.51)],.052,frame,8)
reception.box((-6.55,51.83,FLOOR+.52),(.61,.49,.109),recess)
reception.box((-6.55,52.03,FLOOR+.79),(.61,.084,.62),recess)
reception.box((-6.37,50.83,FLOOR+1.147),(.72,.12,.12),gold)
for x in (-2.51,0,2.51):
    reception.box((x,60.98,FLOOR+1.34),(1.93,.47,2.69),granite_black)
    reception.box((x,60.711,FLOOR+1.31),(1.48,.09,2.58),steel)
    reception.box((x,60.648,FLOOR+1.31),(.017,.035,2.55),frame)
    reception.box((x,60.694,FLOOR+2.87),(.421,.08,.114),led_light)
    reception.box((x+.925,60.682,FLOOR+1.03),(.139,.084,.354),steel)
    reception.box((x+.928,60.633,FLOOR+1.11),(.084,.047,.052),warm_lamp)
for side in (-1,1):
    center=side*8.13
    reception.box((center,60.89,FLOOR+1.22),(5.26,.49,2.29),plaster)
    for j in range(5):
        x=center+(j-2)*.97
        reception.box((x,60.606,FLOOR+1.72),(.943,.14,1.10),wall_stone)
        reception.box((x,60.519,FLOOR+1.72),(.824,.058,.961),glass_clear)
        reception.box((x,60.491,FLOOR+1.77),(.797,.045,.027),frame)
    reception.box((center,60.567,FLOOR+2.69),(2.63,.09,.222),blue)
    for y in (51.83,55.72):
        for j in range(4):
            x=side*(8.18+j*.69)
            reception.box((x,y,FLOOR+.53),(.59,.54,.085),steel)
            reception.box((x,y+.215,FLOOR+.82),(.57,.074,.49),steel)
            for dx in (-.245,.245):
                reception.tube([(x+dx,y-.13,FLOOR+.013),(x+dx,y,FLOOR+.48)],.025,frame,7)
                reception.tube([(x+dx,y+.14,FLOOR+.013),(x+dx,y,FLOOR+.48)],.025,frame,7)
        bounds(min(side*7.87,side*10.56),max(side*7.87,side*10.56),y-.27,y+.27)
reception.box((0,57.11,4.785),(3.21,.13,.34),blue)
reception.finish()
text('Chữ Information','INFORMATION',(-6.38,50.754,FLOOR+1.147),black,lobby_group,bold,.60,.084,depth=.002)
text('Phương châm trên quầy','INNOVATIVE UNIVERSITY',
     (desk_x,desk_y-.878,FLOOR+.565),black,lobby_group,bold,2.17,.115,depth=.002)
text('Biển thang máy','THANG MÁY  ↑',(0,57.033,4.783),paper,lobby_group,bold,2.10,.163,depth=.002)

def point_preview(name,position,power,radius):
    data=bpy.data.lights.new(name,'POINT')
    data.energy=power
    data.shadow_soft_size=radius
    node=bpy.data.objects.new(name,data)
    preview_group.objects.link(node)
    node.location=position


for x,y,z,intensity in [(0,51.5,6.9,170),(0,57.1,4.66,115),(-7.9,56.86,4.54,85),
                        (7.9,56.86,4.54,85),(0,41.8,6.64,84)]:
    empty('Đèn sảnh',physics,(x,y,z),centralLight=intensity)
    point_preview('Đèn sảnh',(x,y,z),intensity*3.2,.46)

greens=[surface(f'Lá xanh {i+1}',c,.82,double=True) for i,c in enumerate([
    (.036,.095,.028),(.056,.140,.035),(.076,.178,.049),(.105,.230,.055),
    (.149,.274,.062),(.190,.303,.081),(.246,.336,.105)
])]
petals=[surface(f'Hoa giấy {i+1}',c,.78,double=True) for i,c in enumerate([
    (.56,.057,.19),(.73,.138,.289),(.86,.275,.394),(.69,.084,.276),(.92,.447,.507)
])]
dirt=tiled('Đất gốc cây',(.372,.302,.225),'granite',2.4)
fauna_floor=Mesh('Đất chân cây và sỏi trong chậu',greenery)


def detailed_leaf_material():
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
    mat=surface('Cụm lá chi tiết quanh cổng',(.13,.22,.06),.79,image=image,opacity=.99,double=True)
    nodes=mat.node_tree.nodes
    mat.node_tree.links.new(nodes.get('Image Texture').outputs['Alpha'],nodes.get('Principled BSDF').inputs['Alpha'])
    mat.surface_render_method='DITHERED'
    mat['leafCutout']=True
    return mat


leaf_cards=detailed_leaf_material()


def add_leaf_spray(mesh, center, radius, angle):
    for turn in (-.91,.18,1.23):
        az=angle+turn
        u=Vector((math.cos(az),math.sin(az),0))*radius
        v=Vector((-.41*math.sin(az),.41*math.cos(az),.91))*radius*.94
        mesh.add([center-u-v,center+u-v,center+u+v,center-u+v],
                 [(0,1,2,3)],leaf_cards,uv=[((0,0),(1,0),(1,1),(0,1))])


def broadleaf(name,x,y,h,spread,radius, *, sparse=False):
    wood=Mesh(name+' · thân, rễ và cành',greenery)
    leaves=Mesh(name+' · tán lá',greenery)
    p=Vector((x,y,0))
    dip=Vector((rng.uniform(-.5,.5),rng.uniform(-.5,.5),0))
    root=p+Vector((0,0,-.1))
    trunk=[root+Vector((0,0,h*t))+dip*math.sin(t*3) for t in (0,.046,.22,.39,.56,.72,.86,.96)]
    wood.tube(trunk,[radius*f for f in (1.24,.89,.76,.65,.52,.39,.26,.06)],bark,12,irregular=.14)
    for i in range(6):
        angle=i*math.tau/6+rng.uniform(-.34,.34)
        a=Vector((math.cos(angle),math.sin(angle),0))
        reach=radius*rng.uniform(1.28,2.7)
        wood.tube([p+Vector((0,0,radius*.32)),p+a*reach*.53+Vector((0,0,radius*.075)),
                   p+a*reach+Vector((0,0,-.052))],[radius*.29,radius*.13,.012],bark,7)
    for j in range(8):
        angle=j*2.39996+rng.uniform(-.42,.42)
        a=Vector((math.cos(angle),math.sin(angle),0))
        b=Vector((-a.y,a.x,0))
        origin=trunk[2+j%4]
        tip=p+a*spread*rng.uniform(.53,.98)+Vector((0,0,h*rng.uniform(.72,.97)))
        bend=origin.lerp(tip,.56)-Vector((0,0,h*.065))
        wood.tube([origin,origin.lerp(bend,.47),bend,tip],[radius*.46,radius*.30,radius*.14,.017],bark,8,irregular=.13)
        for k in range(6):
            start=bend.lerp(tip,(k+.5)/6)
            end=start+a*rng.uniform(.28,.91)+b*((-1)**k)*spread*rng.uniform(.16,.42)+Vector((0,0,rng.uniform(.15,.85)))
            wood.tube([start,start.lerp(end,.55),end],[radius*.069,radius*.041,.008],bark,6)
            n=16 if sparse else 26
            for i in range(n):
                f=rng.uniform(.06,1.20)
                r=spread*rng.uniform(.021,.11)
                az=rng.uniform(0,math.tau)
                base=start.lerp(end,f)+Vector((r*math.cos(az),r*math.sin(az),rng.uniform(-.32,.43)))
                length=rng.uniform(.17,.41)*(1.22 if not sparse else .94)
                leaves.leaf(base,(math.cos(az),math.sin(az),rng.uniform(-.54,.58)),length,
                            length*rng.uniform(.37,.66),rng.choice(greens))
        if not sparse:
            # Layer the silhouette at the tips, with flatter clusters below each spray.
            for k in range(5):
                origin = bend.lerp(tip,.35+k*.145)
                center = origin + b*((-1)**k)*spread*rng.uniform(.15,.32) + Vector((0,0,spread*.13))
                if x<-62 and h>13:
                    add_leaf_spray(leaves,center,spread*.27,angle+k*.84)
                for count in range(48 if x>-60 else 100):
                    latitude = rng.uniform(-1,1)
                    az = rng.uniform(0,math.tau)
                    rad = rng.uniform(.10,1)**.35*spread*.26
                    planar = math.sqrt(1-latitude*latitude)
                    point = center + Vector((math.cos(az)*rad*planar,math.sin(az)*rad*planar,latitude*rad*.79))
                    length = rng.uniform(.28,.61)
                    leaves.leaf(point,(math.cos(az),math.sin(az),rng.uniform(-.45,.58)),
                                length,length*rng.uniform(.43,.68),rng.choice(greens[1:6]))
            for i in range(19):
                base=bend.lerp(tip,rng.uniform(.45,1.14))+Vector((rng.uniform(-.66,.66),rng.uniform(-.66,.66),rng.uniform(.20,.92)))
                leaves.leaf(base,(rng.uniform(-1,1),rng.uniform(-1,1),rng.uniform(-.45,.28)),
                            rng.uniform(.31,.56),rng.uniform(.13,.28),rng.choice(greens[1:6]))
    wood.finish()
    leaves.finish()
    bounds(x-radius*.80,x+radius*.80,y-radius*.80,y+radius*.80)
    ring=[(x+math.cos(k*math.tau/13)*radius*rng.uniform(2.2,3.11),
           y+math.sin(k*math.tau/13)*radius*rng.uniform(2.2,3.11),.004) for k in range(13)]
    fauna_floor.sheet(ring,dirt)


trees=[
    (-66.61,42.6,19.5,8.18,.59),(-68.2,15.98,18.25,6.7,.48),
    (-62.31,53.6,21.1,8.55,.44),(-64.75,48.1,22.4,8.3,.51),
    (-68.05,55.71,17.1,7.31,.48),(-61.0,48.53,20.34,6.44,.48),
    (-66.07,37.48,16.25,5.55,.44),
    (-60.8,26.3,13.77,4.96,.44),(-60.71,39.6,13.68,5.46,.39),
    (-68.03,4.16,10.12,4.60,.35),(-61.6,9.08,12.2,4.85,.42),
    (-77.0,57.5,12.7,4.85,.36),(-82.8,-1.5,12.4,4.47,.37),
    (-57.2,36.93,11.5,4.5,.39),(-55.7,42.65,13.18,5.16,.45),
    (-48.5,10.4,12.88,5.3,.36),(-42.3,1.1,14.05,5.33,.41),
    (-36.3,7.27,13.47,5.26,.38),(-48.2,-5.7,13.67,5.31,.41),
    (-32.0,-4.7,14.64,6.05,.47),(-25.8,12.51,11.36,4.34,.32),
    (-18.65,3.51,13.56,5.42,.38),(-12.1,-6.64,10.84,4.19,.33),
    (-10.66,9.36,10.57,4.38,.28),(7.45,-8.37,9.3,3.46,.32),
    (27.64,12.30,10.80,3.80,.29),(37.31,5.57,10.21,4.37,.35),
    (50.01,5.85,13.1,5.38,.39),(48.81,-7.31,10.9,4.86,.33),
    (26.6,-8.8,9.6,4.01,.28),(42.6,16.0,10.5,4.74,.32),
    (-58.3,80.11,11.4,4.86,.41),(-23.2,79.0,9.06,4.00,.30),
    (27.11,78.26,8.78,3.77,.32),(47.5,79.4,10.95,4.32,.42),
    (53.7,41.91,9.8,4.27,.36),(-51.4,44.20,9.1,4.18,.35),
]
for i,(x,y,h,spread,radius) in enumerate(trees):
    broadleaf(f'Cây bóng mát {i+1:02}',x,y,h,spread,radius,sparse=(i%4==3 and x>-56))

palms=Mesh('Hai hàng cau trước cánh nhà',greenery)
palm_leaves=Mesh('Tàu lá cau và lá chét',greenery)
def palm(x,y,z,h,spread, *, thick=.21):
    base=Vector((x,y,z))
    curve=Vector((rng.uniform(-.43,.43),rng.uniform(-.35,.35),0))
    stem=[base+curve*t*t+Vector((0,0,h*t)) for t in (0,.13,.30,.48,.65,.84,1)]
    palms.tube(stem,[thick*1.16,thick,thick*.90,thick*.83,thick*.79,thick*.79,thick*.95],
               palm_bark,10,irregular=.071)
    for i in range(22):
        t=(i+.38)/22
        p=base+curve*t*t+Vector((0,0,h*t))
        palms.tube([p,p+Vector((0,0,.028))],thick*(.80+.18*(1-t)),palm_bark,9)
    center=stem[-1]
    palms.tube([center-Vector((0,0,.45)),center+Vector((0,0,.61))],(.19,.14),greens[1],8)
    phase=rng.uniform(0,math.tau)
    for j in range(13):
        theta=phase+j*2.39996
        slope=rng.uniform(.52,1.0)
        a=Vector((math.cos(theta),math.sin(theta),0))
        b=Vector((-a.y,a.x,0))
        points=[center+a*spread*slope*(t*.85)+Vector((0,0,spread*(.67*math.sin(t*2.45)-t*.48)+rng.uniform(-.045,.045)))
                for t in (0,.14,.29,.46,.65,.81,1)]
        palm_leaves.tube(points,[.038,.034,.029,.022,.017,.011,.004],greens[2],5)
        for k in range(16):
            t=.13+k*.052
            lo=min(int(t*6),5)
            leaf=points[lo].lerp(points[lo+1],t*6-lo)
            for side in (-1,1):
                direction=b*side*.80+a*.49+Vector((0,0,-.29-(t*.32)))
                length=spread*(.33*math.sin(t*math.pi)+.086)*rng.uniform(.79,1.13)
                palm_leaves.leaf(leaf,direction,length,max(.026,length*.146),rng.choice(greens[1:5]),droop=.24)


for side in (-1,1):
    for i in range(8):
        x=side*(13+i*4.95)
        y=44.00+(i%3)*.36
        palm(x,y,0,rng.uniform(7.20,9.38),rng.uniform(2.54,3.17))
        bounds(x-.22,x+.22,y-.22,y+.22)
for x,y in [(-52.7,42.1),(-50.43,40.0),(51.2,42.01),(49.25,39.97),
            (-55.5,17.6),(55.37,21.4),(34.4,-4.54),(-67.2,20.4)]:
    palm(x,y,0,rng.uniform(3.4,5.04),rng.uniform(1.52,2.04),thick=.153)
    bounds(x-.16,x+.16,y-.16,y+.16)
for x,y in [(-5.5,49.2),(5.53,49.18),(5.58,54.21),(-5.6,54.19),(10.58,50.01),(-10.79,50.03)]:
    palm(x,y,FLOOR+.29,1.10,1.15,thick=.056)
    bounds(x-.26,x+.26,y-.26,y+.26)
palms.finish()
palm_leaves.finish()
fauna_floor.finish(noShadow=True)

gardens=Mesh('Bồn hoa, bụi tròn, hàng viền và chậu đất nung',greenery)
plant_detail=Mesh('Lá chét và hoa giấy',greenery)
def mound(x,y,z,r,h, *, flowers=False):
    for j in range(9):
        angle=j*math.tau/9+rng.uniform(-.33,.29)
        grow=rng.uniform(.20,.69)
        dx,dy=math.cos(angle)*r*grow,math.sin(angle)*r*grow
        height=h*rng.uniform(.40,.64)
        gardens.globe((x+dx,y+dy,z+height), (r*.50,r*.43,height*.82), greens[2:6],rng,sides=8,rings=5)
        for k in range(25 if flowers else 10):
            a=rng.uniform(0,math.tau)
            base=(x+dx+math.cos(a)*r*rng.uniform(.22,.51),
                  y+dy+math.sin(a)*r*rng.uniform(.22,.51),z+height*rng.uniform(.90,1.80))
            mat=rng.choice(petals if flowers else greens[3:])
            length = rng.uniform(.064,.145) if flowers else rng.uniform(.105,.192)
            plant_detail.leaf(base,(math.cos(a),math.sin(a),rng.uniform(-.72,.80)),length,length*.84,mat)


def pot(x,y,z,r,h,mat=terracotta):
    gardens.tube([(x,y,z),(x,y,z+h*.13),(x,y,z+h*.84),(x,y,z+h)],
                 [r*.55,r*.64,r*.94,r],mat,16)
    gardens.tube([(x,y,z+h*.89),(x,y,z+h*.96)],r*1.029,mat,19)
    gardens.tube([(x,y,z+h+.002),(x,y,z+h+.019)],r*.89,dirt,17)


for side in (-1,1):
    for i in range(10):
        x=side*(11+i*4.15)
        y=35.81-(min(i,5)*.143)
        mound(x,y,.035,rng.uniform(.78,1.22),rng.uniform(.53,.92),flowers=i in (0,5))
    for i in range(10):
        x=side*(12.0+i*4.38)
        mound(x,45.87,.016,rng.uniform(.68,1.12),rng.uniform(.47,.89))
    for x,y,r,h in [(8.35,30.20,.62,.35),(13.3,27.5,.59,.33),(23.5,27.7,.58,.33),(37.4,27.5,.56,.32),
                    (51.7,21.45,.67,.38),(5.22,18.79,.43,.32),(9.65,36.2,.71,.49)]:
        pot(x*side,y,0,r,h)
        mound(x*side,y,h,r*1.41,1.28,flowers=True)
        bounds(x*side-r,x*side+r,y-r,y+r)
    for i in range(12):
        x=side*(6.8+i*3.83)
        y=-9.65+(i%3)*1.77
        mound(x,y,.015,.87,.63,flowers=i%5==2)
for x,y in [(-64.29,23.9),(-63.37,37.55),(-69.37,39.1),(-68.3,9.36),
            (-66.37,48.5),(-66.31,53.84),(-62.32,14.05),(-55.31,30.32),(-45.21,13.71),
            (53.25,37.68),(52.1,-7.87),(47.3,77.85),(-50.4,78.56)]:
    mound(x,y,0,rng.uniform(.71,1.22),rng.uniform(.46,.94))
for x,y in [(-5.5,49.2),(5.53,49.18),(5.58,54.21),(-5.6,54.19),(10.58,50.01),(-10.79,50.03)]:
    pot(x,y,FLOOR,.31,.30,paper)
pot(-5.27,50.84,FLOOR+1.09,.159,.12,paper)
mound(-5.27,50.84,FLOOR+1.21,.23,.21)
gardens.finish()
plant_detail.finish()

turf_blades=Mesh('Cỏ ngắn và lá rụng rải thưa',greenery)
for i in range(9600):
    x,y=rng.uniform(-53.5,53.5),rng.uniform(-11.0,19.22)
    if abs(x)<4.21 or rng.uniform(0,1)<.28:
        continue
    for j in range(2):
        a=rng.uniform(0,math.tau)
        l=rng.uniform(.045,.119)
        turf_blades.leaf((x+rng.uniform(-.10,.10),y+rng.uniform(-.10,.10),-.05),
                         (math.cos(a),math.sin(a),1.62),l,rng.uniform(.014,.028),
                         rng.choice(greens[1:]))
for i in range(360):
    x,y=rng.uniform(-52,52),rng.uniform(28.8,34.6)
    a=rng.uniform(0,math.tau)
    turf_blades.leaf((x,y,.010),(math.cos(a),math.sin(a),.04),rng.uniform(.052,.126),.037,terracotta)
turf_blades.finish(noShadow=True)

flags_plaza=Mesh('Hai dãy cờ trước sân và cờ trên mái đón',land_group)
left_flags = [
    ('đỏ','trắng'),('trắng','lam','đỏ'),('đen','đỏ','vàng'),
    ('trắng','lơ','đỏ'),('đỏ','trắng','lam'),('đỏ',)
]
right_flags = [
    ('đỏ',),('lục','vàng','đỏ'),('đỏ','trắng','đỏ','trắng','đỏ','trắng'),
    ('vàng','trắng'),('đỏ','vàng','đỏ'),('đỏ','trắng')
]
for side, sequence in [(-1,left_flags[::-1]),(1,right_flags)]:
    for i, bands in enumerate(sequence):
        x=side*(11.5+i*5.47)
        y=33.9
        z=.083
        flags_plaza.tube([(x,y,0),(x,y,.22)],.162,cement,11)
        roof_pole(flags_plaza,x,y,z,11.9 if i==0 else 10.3-(i%2)*.17,(1.96,1.21),
                  bands,phase=i*.62+side,star=i==0)
        bounds(x-.085,x+.085,y-.085,y+.085)
for i,key in enumerate(('đỏ','vàng','đỏ','lơ','cam','lục','vàng','lơ')):
    roof_pole(flags_plaza,(i-3.5)*2.02,34.80,7.62,1.40,(.31,.80),[key],phase=i*.7)
flags_plaza.finish()

plaques=Mesh('Hai bia tên ốp đá hai bên tam cấp',land_group)
for x in (-10.26,10.26):
    # Slightly reclined face and dark granite coping.
    u,v=x-2.62,x+2.62
    pts=[(u,30.23,.02),(v,30.23,.02),(v,31.23,.02),(u,31.23,.02),
         (u,30.49,1.13),(v,30.49,1.13),(v,31.18,1.13),(u,31.18,1.13)]
    plaques.add(pts,[(3,2,1,0),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],granite_rose)
    plaques.box((x,30.85,1.15),(5.34,.76,.18),granite_black)
    for u in (x-2.60,x+2.60):
        plaques.tube([(u,30.20,.035),(u,30.44,1.10)],.068,granite_black,6)
    plaques.tube([(x-2.66,30.17,.05),(x+2.66,30.17,.05)],.036,granite_black,7)
    plaques.tube([(x-2.66,30.43,1.105),(x+2.66,30.43,1.105)],.039,granite_black,7)
    round_badge(plaques,x-2.08,30.35,.75,.144,logo)
    text('Chữ HCMUTE trên bia','HCMUTE',(x,30.335,.81),gold,land_group,bold,1.45,.213,depth=.006)
    label='ĐẠI HỌC SƯ PHẠM KỸ THUẬT TP. HỒ CHÍ MINH' if x<0 else 'HCMC UNIVERSITY OF TECHNOLOGY AND EDUCATION'
    text('Dòng tên trên bia',label,(x,30.27,.56),gold,land_group,bold,4.06,.131,depth=.006)
    bounds(x-2.68,x+2.68,30.15,31.26)
plaques.finish()

fittings=Mesh('Đèn đường, biển chỉ lối và băng ghế',street_group)
for x,y,h,side in [
    (-76.4,10.62,9.0,-1),(-76.4,52.4,9.5,1),(-68.1,36.6,5.85,1),(-65.7,29.3,5.63,-1),
    (-53.75,17.4,6.36,-1),(-56.0,44.0,6.55,1),(-54.1,72.2,5.9,1),
    (54.08,18.4,6.38,1),(54.1,51.0,6.45,1),(54.1,72.7,5.88,-1),
    (15.25,-12.24,6.10,1),(-17.15,-12.3,6.10,-1),(34.8,29.1,5.5,1),
]:
    fittings.tube([(x,y,0),(x,y,h-.79),(x+side*.43,y,h-.20),(x+side*.93,y,h)],
                  [.082,.061,.050,.035],steel,10)
    fittings.box((x+side*.95,y,h-.055),(.43,.16,.095),white_metal)
    fittings.box((x+side*.97,y,h-.089),(.27,.126,.046),warm_lamp)
    fittings.tube([(x,y,.025),(x,y,.27)],.122,frame,10)
    bounds(x-.086,x+.086,y-.086,y+.086)
for x,y in [(-56.3,38),(-51.0,34.5),(-45,34.7),(-37.5,34.6),(-29.7,34.5),(-22.3,34.5)]:
    fittings.tube([(x,y,0),(x,y,3.40)],.036,white_metal,7)
    fittings.box((x,y-.05,2.57),(.54,.085,1.22),shop_blue)
    for j in range(7):
        fittings.box((x,y-.105,2.94-j*.12),(.33-(j%3)*.065,.015,.016),paper)
for x,y in [(-65.2,36.0),(-3.65,10.4),(8.9,26.6),(-43.88,27.5),(42.93,24.81)]:
    fittings.box((x,y,.275),(1.65,.43,.109),cream)
    fittings.box((x,y+.20,.595),(1.65,.108,.31),cream)
    for off in (-.56,.56):
        fittings.box((x+off,y,.144),(.134,.35,.29),cement)
        fittings.box((x+off,y+.19,.39),(.105,.10,.68),cement)
    bounds(x-.83,x+.83,y-.25,y+.25)
for x,y in [(-54.16,22.2),(-65.45,17.15),(53.91,27.18),(31.4,18.7)]:
    fittings.box((x,y,.52),(.48,.46,1.01),greens[1])
    fittings.box((x,y-.013,1.038),(.52,.52,.108),greens[2])
    bounds(x-.25,x+.25,y-.25,y+.25)
fittings.finish()

near_signs=gate_mesh('Biển lối bộ và biển cấm trước cổng',gate_wings)
for x in (-14.73,10.47):
    near_signs.tube([(x,-.75,0),(x,-.75,1.34)],.026,steel,9)
    near_signs.box((x,-.785,.92),(.54,.034,.79),shop_blue)
    near_signs.tube([(x,-.824,.98),(x,-.806,.98)],.154,paper,22)
    near_signs.tube([(x,-.838,1.055),(x,-.822,1.055)],.031,shop_blue,10)
    for off in (-1,1):
        near_signs.tube([(x,-.844,.986),(x+off*.041,-.844,.896)],.011,shop_blue,6)
    gate_text('Biển lối đi bộ','LỐI ĐI BỘ',x,-.824,.655,.426,.078,paper,depth=.001)
x=-27.4
near_signs.tube([(x,-1.38,.02),(x,-1.38,1.27)],.026,frame,8)
near_signs.box((x,-1.406,1.05),(.64,.06,.49),red)
gate_text('Biển cấm ở vỉa hè','CẤM',x,-1.438,1.125,.327,.104,cloth['vàng'],depth=.001)
gate_text('Biển cấm · dòng dưới','ĐỖ XE',x,-1.439,.969,.41,.086,cloth['vàng'],depth=.001)
near_signs.finish()

car_materials = [surface('Sơn ô tô '+name,c,.27,metal=.45) for name,c in [
    ('bạc',(.49,.53,.52)),('trắng',(.67,.686,.66)),('nâu',(.285,.172,.125)),('đen',(.046,.053,.059))
]]
rubber=surface('Lốp xe',(.022,.025,.025),.90)
def car(x,y,angle,paint, variant=0):
    ca,sa=math.cos(angle),math.sin(angle)
    def transform(a,b,z):
        return (x+ca*a-sa*b,y+sa*a+ca*b,z)
    model=Mesh('Xe đỗ ven đường',street_group,transform)
    profile=[(-2.16,.60,.35,.63),(-2.01,.89,.29,.78),(-1.46,.94,.28,.86),
             (-.55,.96,.26,.85),(.47,.93,.28,.83),(1.47,.89,.30,.74),(2.06,.81,.37,.62)]
    verts=[]
    for px,w,lo,hi in profile:
        verts.extend([(px,-w*.83,lo),(px,w*.83,lo),(px,w,hi-.10),
                      (px,w*.83,hi),(px,-w*.83,hi),(px,-w,hi-.10)])
    faces=[(5,4,3,2,1,0),tuple(range(len(verts)-6,len(verts)))]
    for i in range(len(profile)-1):
        faces.extend((6*i+j,6*i+(j+1)%6,6*(i+1)+(j+1)%6,6*(i+1)+j)
                     for j in range(6))
    model.add(verts,faces,paint,smooth=True)
    w=.80
    roof_top=1.58+variant*.06
    bl,br=(-1.55,-w,.83),(-1.55,w,.83)
    fl,fr=(1.23,-w,.81),(1.23,w,.81)
    tl,tr=(-.91,-.68,roof_top),(-.91,.68,roof_top)
    el,er=(.41,-.62,roof_top),(.41,.62,roof_top)
    model.sheet([tl,el,er,tr],paint)
    model.sheet([fl,fr,er,el],glass_dark)
    model.sheet([br,bl,tl,tr],glass_dark)
    model.add([bl,fl,el,tl,fr,br,tr,er],[(0,1,2,3),(4,5,6,7)],glass_dark)
    for s in (-1,1):
        model.tube([(-1.54,s*.8,.825),(-.91,s*.68,roof_top),(.41,s*.62,roof_top),(1.23,s*.80,.813)],
                   .041,paint,7)
        model.tube([(-.25,s*.80,.85),(-.31,s*.662,roof_top)],.032,frame,7)
        model.box((.72,s*.97,1.05),(.20,.19,.128),paint)
        model.box((1.99,s*.58,.63),(.16,.39,.158),warm_lamp)
        model.box((-2.10,s*.59,.62),(.07,.34,.145),red)
        for pos in (-1.36,1.33):
            model.tube([(pos,s*.735,.34),(pos,s*.917,.34)],.335,rubber,17)
            model.tube([(pos,s*.915,.34),(pos,s*.931,.34)],.232,white_metal,16)
            model.tube([(pos,s*.932,.34),(pos,s*.937,.34)],.091,steel,12)
            for j in range(5):
                th=j*math.tau/5
                model.tube([(pos,s*.943,.34),(pos+.204*math.cos(th),s*.943,.34+.204*math.sin(th))],.017,frame,5)
    model.box((2.036,0,.537),(.057,.61,.147),frame)
    model.box((2.071,0,.493),(.026,.40,.10),paper)
    model.box((-2.155,0,.52),(.024,.39,.11),paper)
    for i in range(4):
        model.box((2.075,0,.486+i*.024),(.024,.55,.010),steel)
    model.finish()
    extent = abs(ca)*2.14+abs(sa)*.94
    depth = abs(sa)*2.14+abs(ca)*.94
    bounds(x-extent,x+extent,y-depth,y+depth)


for i,(x,y,angle) in enumerate([
    (-61.97,46.8,math.pi/2),(-61.97,52.0,math.pi/2),(-61.97,57.17,math.pi/2),
    (-56.63,42.38,-math.pi/2),(-56.63,49.34,-math.pi/2),
    (-44.30,29.51,math.pi),(-36.84,29.52,math.pi),(-29.45,29.51,math.pi),
    (32.7,29.3,0),(39.60,29.33,0),(47.1,29.32,0),
    (61.85,59.12,math.pi/2),(61.85,66.83,math.pi/2),(-74.98,6.02,math.pi/2)
]):
    car(x,y,angle,car_materials[i%4],i%3)

context=Mesh('Nhà thấp cạnh đường và sân thể thao xa',street_group)
for x,y,w,d,h,material in [
    (-105.1,50.0,8,12,7.3,cream),(-105.2,63.0,8,10,9.0,plaster),
    (-105.1,10.3,8,10,5.2,wall_stone),(-104.9,-1.2,8,12,8.9,cream),
    (-65.7,53,5.2,8,4.2,roof_mint),
    (-55.36,89.94,16,4.1,7.2,plaster),(-27.67,91.5,17.9,5.2,5.1,cream),
    (34.0,91.87,20,7.1,7.0,roof_mint),
]:
    context.box((x,y,h/2),(w,d,h),material)
    context.box((x,y,h+.08),(w+.37,d+.34,.19),roof_gray)
    for level in range(int(h/3)):
        for j in range(4):
            yy=y+(j-1.5)*d*.223
            context.box((x+w/2+.021,yy,1.55+level*2.9),(.068,d*.17,1.31),glass_dark)
    bounds(x-w/2,x+w/2,y-d/2,y+d/2)
field=surface('Cỏ sân thể thao xanh thẫm',(.07,.195,.091),.88)
context.box((70.2,62.7,.008),(11.45,31.8,.070),field)
for x in (65.0,75.6):
    context.box((x,62.72,.047),(.069,30.05,.015),paper)
for y in (47.7,77.72,62.72):
    context.box((70.30,y,.048),(10.60,.074,.015),paper)
for y in (47.44,77.85):
    for x in (68.75,71.76):
        context.tube([(x,y,0),(x,y,1.78)],.039,paper,8)
    context.tube([(68.75,y,1.78),(71.76,y,1.78)],.039,paper,8)
context.finish()

VIEWS={
    'cong': ((-101.2,28.7,1.69),(-70.50,27.9,4.03),20),
    'cong-xien': ((-96.8,42.60,1.85),(-69.3,37.4,3.89),18.7),
    'cong-phai': ((-93.34,12.83,1.75),(-69.65,16.3,3.86),20),
    'toa-nha': ((0,-9.30,1.69),(0,48.19,19.7),18),
    'sanh': ((.81,48.20,FLOOR+1.69),(-1.85,58.04,FLOOR+1.48),14.5),
    'sanh-nhin-ra': ((.60,56.25,FLOOR+1.69),(-1.35,47.62,FLOOR+1.56),14.5),
    'tren-cao': ((9,-85,123),(0,38,21.2),29.5),
    'mat-sau': ((0,174.0,70),(0,71.2,27.2),29),
}
for key in ('cong','toa-nha','sanh'):
    eye,target,_=VIEWS[key]
    direction=Vector(target)-Vector(eye)
    empty('Điểm quan sát '+key,physics,eye,viewKey=key,
          viewYaw=math.atan2(-direction.x,direction.y),
          viewPitch=math.atan2(direction.z,math.hypot(direction.x,direction.y)))

# Export an independent game asset. Preview lights and cameras only exist in the .blend.
asset=MAP/'trung-tam.glb'
with tempfile.TemporaryDirectory(dir=MAP) as directory:
    scratch=Path(directory)/asset.name
    bpy.ops.export_scene.gltf(filepath=str(scratch),export_format='GLB',export_extras=True,
                             export_yup=True,export_cameras=False,export_lights=False,
                             export_animations=False,export_apply=True)
    scratch.replace(asset)

world=bpy.data.worlds.new('Trời xanh dịu')
scene.world=world
world.use_nodes=True
nodes=world.node_tree.nodes
links=world.node_tree.links
surface_out=nodes.get('World Output')
ambient=nodes.get('Background')
ambient.inputs['Color'].default_value=(.58,.70,.79,1)
ambient.inputs['Strength'].default_value=.38
coordinates=nodes.new('ShaderNodeTexCoord')
split=nodes.new('ShaderNodeSeparateXYZ')
links.new(coordinates.outputs['Normal'],split.inputs[0])
ramp=nodes.new('ShaderNodeValToRGB')
ramp.color_ramp.elements[0].position=.0
ramp.color_ramp.elements[0].color=(.427,.682,.886,1)
ramp.color_ramp.elements[1].position=.34
ramp.color_ramp.elements[1].color=(.074,.374,.702,1)
sky_angle=nodes.new('ShaderNodeMath')
sky_angle.operation='MULTIPLY'
sky_angle.inputs[1].default_value=-1
links.new(split.outputs['Z'],sky_angle.inputs[0])
links.new(sky_angle.outputs[0],ramp.inputs[0])
sky=nodes.new('ShaderNodeBackground')
links.new(ramp.outputs['Color'],sky.inputs['Color'])
sky.inputs['Strength'].default_value=.86
is_camera=nodes.new('ShaderNodeLightPath')
mix=nodes.new('ShaderNodeMixShader')
links.new(is_camera.outputs['Is Camera Ray'],mix.inputs[0])
links.new(ambient.outputs[0],mix.inputs[1])
links.new(sky.outputs[0],mix.inputs[2])
links.new(mix.outputs[0],surface_out.inputs['Surface'])
sun_data=bpy.data.lights.new('Nắng khuôn viên','SUN')
sun_data.color=(1.0,.946,.854)
sun_data.energy=2.67
sun_data.angle=math.radians(6)
sun=bpy.data.objects.new(sun_data.name,sun_data)
preview_group.objects.link(sun)
sun.rotation_euler=Vector((.73,.49,-.71)).to_track_quat('-Z','Y').to_euler()

def camera(key, definition):
    eye,target,lens=definition
    data=bpy.data.cameras.new(key)
    data.lens=lens
    data.clip_end=420
    ob=bpy.data.objects.new(key,data)
    preview_group.objects.link(ob)
    ob.location=eye
    ob.rotation_euler=(Vector(target)-Vector(eye)).to_track_quat('-Z','Y').to_euler()
    return ob


cameras={key:camera(key,definition) for key,definition in VIEWS.items()}
scene.camera=cameras['cong']
scene.render.engine='CYCLES'
scene.cycles.samples=15
scene.cycles.use_denoising=True
scene.cycles.max_bounces=6
scene.cycles.transparent_max_bounces=16
scene.render.resolution_x=1440
scene.render.resolution_y=810
scene.render.resolution_percentage=100
scene.render.image_settings.file_format='JPEG'
scene.render.image_settings.quality=90
scene.view_settings.view_transform='AgX'
scene.view_settings.exposure=.40
bpy.ops.file.pack_all()
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            view=area.spaces.active
            view.clip_end=600
            view.region_3d.view_location=(-59.5,27,3.4)
            view.region_3d.view_rotation=cameras['cong-xien'].rotation_euler.to_quaternion()
            view.region_3d.view_distance=36
            view.region_3d.view_perspective='PERSP'
            view.shading.color_type='MATERIAL'
            view.shading.show_cavity=True
            view.overlay.show_extras=False
bpy.ops.object.select_all(action='DESELECT')
bpy.context.view_layer.objects.active=None
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'toa-nha-trung-tam.blend'),compress=True)
if '--preview' in sys.argv:
    for key,ob in cameras.items():
        scene.camera=ob
        if key=='mat-sau':
            sun.rotation_euler=Vector((.32,-.51,-.77)).to_track_quat('-Z','Y').to_euler()
        scene.render.filepath=str(MAP/f'preview-{key}.jpg')
        bpy.ops.render.render(write_still=True)
