"""Rebuild Zone E from the supplied aerial and ground-level references."""
import math
import random
import sys
import tempfile
from pathlib import Path

import bpy
from mathutils import Vector

HERE = Path(__file__).resolve().parent
sys.dont_write_bytecode = True
sys.path.insert(0,str(HERE))
from campus_mesh import Mesh, arc, collection, empty, foliage_material, grid_net, leaf_spray, strip, surface, text, tiled, view_marker, walk_limits

ROOT = HERE.parent
MAP = ROOT/'maps'/'khu-e'
rng = random.Random(63114)
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.unit_settings.system = 'METRIC'

land = collection('01 · Đường nội bộ, xưởng và lối vào')
faculty = collection('02 · Khoa Cơ khí Chế tạo máy')
garden = collection('03 · Vườn, ghế đá và lối gạch màu')
sports = collection('04 · Nhà thể thao · tennis và bóng chuyền')
neighbors = collection('05 · Cụm nhà và đường bao')
physics = collection('06 · Va chạm, bậc và điểm vào')

white = surface('Viền trắng và sơn vạch',(.81,.846,.845))
cream = tiled('Vữa sáng ấm',(.826,.807,.745),'paint',3.3)
blue_wall = tiled('Sơn xanh xám Khoa Cơ khí',(.635,.699,.754),'paint',3.1)
brick = tiled('Gạch ốp cam so le',(.687,.354,.224),'brick',1.68,size=640)
concrete = tiled('Bê tông xám bậc thềm',(.498,.472,.432),'granite',1.48)
tiles = tiled('Gạch sân và vỉa hè ê đê',(.69,.659,.596),'paving',1.68,size=640)
bitumen = tiled('Nhựa đường xám pha đất',(.425,.406,.381),'asphalt',4.4,size=640)
grass = tiled('Đất cỏ và rêu',(.429,.475,.271),'lawn',4.3)
roof = surface('Tôn xanh mint',(.224,.443,.393),.51,metal=.28,double=True)
silvery = surface('Tôn kẽm nhà thể thao',(.425,.486,.473),.39,metal=.46,double=True)
lintel = surface('Vì kèo thép xám sáng',(.605,.647,.624),.58,metal=.31)
dark = surface('Thép tối, cao su và bóng sâu',(.043,.061,.064),.68)
aluminum = surface('Khung nhôm và lưới cửa',(.522,.607,.602),.38,metal=.46)
glasses = [surface('Kính lam '+str(i),c,.27,metal=.21,coat=.23) for i,c in enumerate(
    [(.16,.26,.29),(.19,.31,.38),(.29,.397,.431),(.098,.168,.19)])]
plexi = surface('Tấm lấy sáng mờ',(.61,.748,.778),.37,emit=.20,double=True)
teal = surface('Sơn xanh cửa chớp',(.104,.336,.307),.63)
cobalt = surface('Biển xanh cobalt',(.035,.13,.342),.45)
gold = surface('Chữ nhôm vàng trên biển khoa',(.955,.674,.084),.49)
turf_blue = tiled('Sơn xanh dương mặt sân',(.240,.393,.530),'paint',3.7)
turf_green = tiled('Biên sân màu rêu',(.36,.453,.305),'paint',3.3)
net_mat = surface('Sợi lưới đen',(.032,.060,.053),.93,double=True)
day_lamp = surface('Chụp đèn kính trắng',(.78,.862,.82),.42,emit=.22)
terracotta = surface('Ngói đỏ cổng vườn',(.62,.216,.081),.74)
bark = tiled('Vỏ cây và thân cau xám',(.47,.407,.334),'bark',2.1)
greens = [surface('Lá vườn '+str(i),c,double=True) for i,c in enumerate([
    (.038,.104,.031),(.077,.170,.037),(.109,.227,.059),(.168,.304,.067),(.229,.375,.10)])]
paint_yellow = surface('Sơn vàng cũ trên sân xưởng',(.64,.49,.19))
pavers = [tiled('Gạch đường màu '+str(i),c,'paving',1.14,size=320) for i,c in enumerate([
    (.49,.66,.606),(.68,.738,.642),(.76,.645,.414),(.692,.515,.418),(.49,.637,.699)])]
car_paints = [surface('Sơn xe '+str(i),c,.28,metal=.35,coat=.38) for i,c in enumerate([
    (.42,.033,.026),(.70,.737,.706),(.173,.22,.263)])]
font_root = Path('/System/Library/Fonts/Supplemental')
bold_path = font_root/'Arial Bold.ttf'
regular_path = font_root/'Arial.ttf'
bold = bpy.data.fonts.load(str(bold_path)) if bold_path.is_file() else bpy.data.fonts.get('Bfont Regular')
regular = bpy.data.fonts.load(str(regular_path)) if regular_path.is_file() else bold


def bounds(x0,x1,y0,y1):
    empty('Va chạm',physics,((x0+x1)/2,(y0+y1)/2,.7),
          ((x1-x0)/2,(y1-y0)/2,.7),walkCollider=True)


def height(x0,x1,y0,y1,start,end):
    empty('Cao độ lối đi',physics,((x0+x1)/2,(y0+y1)/2,0),
          ((x1-x0)/2,(y1-y0)/2,.03),floorStart=start,floorEnd=end,floorAxis='depth')


def slab(mesh,x0,x1,y0,y1,z,material):
    mesh.span(((x0,x1),(y0,y1),(z-.076,z)),material)


def plaque(mesh,group,x,y,z,width,title,subtitle):
    mesh.box((x,y,z),(width,.16,.89),aluminum)
    mesh.box((x,y-.097,z),(width-.074,.057,.814),cobalt)
    text(title,title,(x,y-.135,z+.016),gold,group,bold,width*.9,.29,depth=.008)
    text(subtitle,subtitle,(x,y-.135,z-.277),white,group,regular,width*.86,.115,depth=.002)


def window(mesh,x,y,z,w,h,*,bars=False):
    mesh.box((x,y,z),(w+.105,.15,h+.105),white)
    mesh.box((x,y-.097,z),(w,.085,h),dark)
    for i in range(4):
        xx=x+(i-1.5)*w/4
        mesh.box((xx,y-.15,z),(w/4-.045,.037,h-.09),glasses[(round(x)+i)%4])
    for i in range(5):
        mesh.box((x+(i-2)*w/4,y-.18,z),(.043,.055,h),aluminum)
    if bars:
        for i in range(1,9):
            mesh.box((x,y-.253,z+(i-4.5)*h/9),(w+.012,.028,.026),aluminum)
        for i in range(5):
            mesh.box((x+(i-2)*w*.19,y-.254,z),(.024,.026,h),aluminum)
    mesh.box((x,y-.105,z-h/2-.081),(w+.21,.37,.086),concrete)


terrain = Mesh('Đất cỏ và các sân lát',land)
terrain.span(((-110,100),(-45,101),(-.29,-.060)),grass)
for x0,x1,y0,y1 in [(-101,93,-4.6,3.5),(-101,-22,3.49,25.98),
                     (-92,-65,25.99,74),(66,73,3.5,81),(-95,81,79,86),
                     (-19,41,40.65,45.1),(-19,42,3.51,5.2)]:
    slab(terrain,x0,x1,y0,y1,.011,bitumen)
for x0,x1,y0,y1 in [(-21,41,39.52,45.12),(-24,-18,5.16,40.65),
                     (36.1,40.5,5.16,40.65),(-90,-21,-8.74,-4.58),
                     (35,68,-8.74,-4.58),(-63,-22,24.2,26.25)]:
    slab(terrain,x0,x1,y0,y1,.043,tiles)
for y in (-4.63,3.61):
    for a,b in [(-94,-28),(-22,2.6),(8.1,65),(73,87)]:
        terrain.box(((a+b)/2,y,.033),(b-a,.14,.116),concrete)
for pos in (-14,54,74):
    for i in range(7):
        terrain.box((pos+(i-3)*.48,.14,.017),(.222,3.65,.010),white)
for x in range(-77,-23,9):
    strip(terrain,[(x,7.7),(x,11.25),(x+6.34,11.25),(x+6.34,7.7)],.076,paint_yellow,z=.017)
for x in (-50.5,-42.4):
    strip(terrain,arc(x,15.2,3.85,0,math.tau,42),.091,white,z=.019)
for x,y in [(-33.8,2.4),(-45.55,16.32),(26.8,.63),(58.9,-1.71)]:
    terrain.box((x,y,.014),(.77,.78,.026),concrete)
    terrain.tube([(x,y,.023),(x,y,.038)],.318,dark,24)
    for j in range(7):
        terrain.box((x,y+(j-3)*.073,.040),(.45,.017,.009),aluminum)
terrain.finish(noShadow=True)

# Two classroom wings frame a recessed four-storey stair and gallery block.
front,back,base,storey = 45.2,70.2,.93,3.56
middle_a,middle_b = 0,16.4
body = Mesh('Cánh phòng học, mái, hành lang và tam cấp',faculty)
facade = Mesh('Khung cửa, lam trắng, điều hòa và mảng gạch',faculty)
arrival = Mesh('Mái đón xanh và giàn thép tam giác',faculty)
for x0,x1 in [(-22,0),(16.4,39.4)]:
    bounds(x0,x1,front,back)
    body.span(((x0,x1),(front,back),(0,base+4*storey)),blue_wall)
    body.span(((x0-.53,x1+.53),(front-.73,back+.43),
               (base+4*storey-.10,base+4*storey+.315)),cream)
    for fl in range(4):
        z = base+fl*storey
        body.span(((x0-.20,x1+.20),(front-.59,front+.045),(z-.08,z+.13)),white)
        body.span(((x0,x1),(front-.029,front+.026),(z+.16,z+1.01)),brick)
        for bay in range(5):
            xx=x0+(bay+.5)*(x1-x0)/5
            window(facade,xx,front-.061,z+1.91,3.59,1.54,bars=fl<3)
            facade.box((xx+1.27,front-.31,z+1.05),(.67,.433,.513),cream)
            facade.tube([(xx+1.27,front-.534,z+1.05),(xx+1.27,front-.551,z+1.05)],.151,aluminum,14)
            facade.tube([(xx+1.27,front-.555,z+1.05),(xx+1.27,front-.575,z+1.05)],.112,dark,13)
            facade.tube([(xx+1.61,front-.58,z+.94),(xx+1.75,front-.16,z+1.49),
                         (xx+1.75,front-.155,z+2.96)],.019,cream,6)
        for x in [x0+i*(x1-x0)/5 for i in range(6)]:
            facade.box((x,front-.075,z+storey/2),(.47,.60,storey),blue_wall)
        side = x1 if x1==0 else x0
        for i in range(3):
            yy=front+1.95+3.16*i
            facade.box((side,yy,z+1.14),(.093,2.57,.77),brick)
            facade.box((side+(.062 if side==0 else -.062),yy,z+1.97),(.102,2.38,1.39),glasses[(i+fl)%4])
            for off in (-.87,-.43,0,.43,.87):
                facade.box((side+(.122 if side==0 else -.122),yy+off,z+1.97),(.052,.036,1.41),aluminum)
        for i in range(6):
            yy=front+2.2+i*4
            xx=x0-.055 if x0<0 else x1+.055
            facade.box((xx,yy,z+1.83),(.127,3.0,1.45),glasses[(i+fl)%4])
            for off in (-1,0,1):
                facade.box((xx,yy+off,z+1.83),(.17,.044,1.46),aluminum)
    for i in range(13):
        xx=x0+.71+i*(x1-x0-1.38)/12
        facade.box((xx,back+.081,9.04),(.08,.125,8.20),aluminum)
    for y in (front+.67,back-.61):
        facade.box(((x0+x1)/2,y,base+4*storey+.33),(x1-x0,.16,.47),cream)
    for x in (x0+.65,x1-.65):
        facade.box((x,(back+front)/2,base+4*storey+.33),(.17,back-front,.47),cream)

center=(middle_a+middle_b)/2
for fl in range(1,4):
    z=base+fl*storey
    body.span(((middle_a,middle_b),(front+4.4,back),(z-.18,z+.07)),cream)
    body.span(((middle_a,middle_b),(front+4.37,front+4.60),(z+.035,z+1.02)),brick)
    facade.box((center,front+4.344,z+1.043),(middle_b,.14,.084),white)
    for x in (1.0,4.55,8.2,11.85,15.4):
        body.box((x,front+9.45,z+storey/2),(.37,.43,storey),blue_wall)
        window(facade,x,front+10.05,z+1.64,2.72,1.94)
z=base+4*storey
body.span(((middle_a,middle_b),(front+3.91,back+.43),(z-.10,z+.31)),cream)
for x in (2.85,4.64,6.42,8.2,9.98,11.76,13.55):
    facade.box((x,front+4.17,(z+base+3.45)/2),(.235,.338,z-base-3.45),white)
plaque(facade,faculty,center,front+3.92,base+6.15,10.2,'KHOA CƠ KHÍ CHẾ TẠO MÁY','FACULTY OF MECHANICAL ENGINEERING')
slab(body,0,16.4,front-.05,front+13.0,base,tiles)
height(0,16.4,front,front+13,base,base)
body.span(((0,16.4),(front+13.0,back),(0,z)),blue_wall)
bounds(0,16.4,front+13.0,back)
for x in (1.0,5.6,10.7,15.4):
    body.box((x,front+2.98,2.27),(.375,.555,2.74),blue_wall)
    bounds(x-.18,x+.18,front+2.70,front+3.26)
for x0,x1 in [(1.07,5.47),(5.88,10.52),(10.93,15.31)]:
    for i in range(6):
        y0=front-2.52+i*.42
        slab(body,x0,x1,y0,y0+.42,base*(i+1)/6,concrete)
        body.span(((x0,x1),(y0,y0+.42),(0,base*(i+1)/6-.072)),concrete)
    height(x0,x1,front-2.52,front,0,base)
for x in (.75,5.67,10.72,15.62):
    body.box((x,front-1.4,.44),(.36,2.80,.88),brick)
    body.box((x,front-1.40,.89),(.43,2.82,.09),concrete)
    bounds(x-.20,x+.20,front-2.8,front)
for x0,x1 in [(1.12,5.42),(5.96,10.44),(10.97,15.27)]:
    y=front+7.77
    body.box(((x0+x1)/2,y,base+2.15),(x1-x0,.21,.36),blue_wall)
    for xx in (x0,x1):
        facade.box((xx,y,base+1.11),(.095,.12,2.25),aluminum)
    if x1<6 or x0>10:
        for i in range(3):
            xx=x0+(i+.5)*(x1-x0)/3
            facade.box((xx,y,base+1.1),(.058,.12,2.21),aluminum)
            facade.box((xx,y+.017,base+1.08),((x1-x0)/3-.064,.057,2.14),glasses[i])
        bounds(x0,x1,y-.08,y+.08)
for x,y in [(2.5,front+6.25),(13.9,front+6.25),(8.2,front+11)]:
    empty('Đèn mái đón',physics,(x,y,3.16),centralLight=16)
for i in range(12):
    x0=.42+i*1.30
    arrival.sheet([(x0,front-.56,4.87),(x0+1.28,front-.56,4.87),
                   (x0+1.28,front+4.28,5.13),(x0,front+4.28,5.13)],teal)
    for y in (front-.56,front+1.88,front+4.30):
        arrival.tube([(x0,y,4.69),(x0+1.30,y,4.69)],.043,teal,7)
    for y,d in [(front-.56,2.44),(front+1.88,2.42)]:
        arrival.tube([(x0,y,4.82),(x0+.65,y+d*.5,4.30),(x0+1.30,y+d,4.99)],.041,teal,7)
        arrival.tube([(x0+1.30,y,4.82),(x0+.65,y+d*.5,4.30),(x0,y+d,4.99)],.041,teal,7)
    arrival.tube([(x0,front-.56,4.84),(x0,front+4.3,5.11)],.031,teal,7)
body.finish()
facade.finish()
arrival.finish()

# The mint sports building has a continuous barrel vault and two playable courts.
hall_x0,hall_x1,hall_y0,hall_y1 = -61,-24,26.25,70.2
hall_mid = (hall_x0+hall_x1)/2
def roof_z(x):
    return 10.5+3.55*(1-((x-hall_mid)/18.5)**2)

hall = Mesh('Mái vòm tôn, tường chân và dải sáng',sports)
truss = Mesh('Vì kèo cong, xà dọc, đèn pha và cửa',sports)
court = Mesh('Hai mặt sân xanh với vạch trắng',sports)
sports_net = Mesh('Lưới tennis, bóng chuyền và lưới ngăn',sports)
for i in range(60):
    a=hall_x0+i*(hall_x1-hall_x0)/60
    b=a+(hall_x1-hall_x0)/60
    hall.sheet([(a,hall_y0-.42,roof_z(a)),(b,hall_y0-.42,roof_z(b)),
                (b,hall_y1+.36,roof_z(b)),(a,hall_y1+.36,roof_z(a))],roof if i%5 else silvery)
    hall.sheet([(a,hall_y1+.30,roof_z(a)-.092),(b,hall_y1+.30,roof_z(b)-.092),
                (b,hall_y0-.32,roof_z(b)-.092),(a,hall_y0-.32,roof_z(a)-.092)],
               plexi if i in (7,8,23,24,37,38,52,53) else silvery)
    truss.tube([(a,hall_y0-.41,roof_z(a)-.06),(a,hall_y1+.36,roof_z(a)-.06)],.019,lintel,5)
    if i%3==0:
        truss.tube([(a,hall_y0,roof_z(a)-.21),(a,hall_y1,roof_z(a)-.21)],.048,dark,7)
for i in range(8):
    y=hall_y0+i*(hall_y1-hall_y0)/7
    truss.tube([(x,y,roof_z(x)-.23) for x in (hall_x0+j*37/22 for j in range(23))],.143,lintel,10)
    for x,delta in ((hall_x0,1),(hall_x1,-1)):
        truss.box((x,y,5.28),(.33,.50,10.55),lintel)
        truss.box((x+.62*delta,y,8.45),(.46,.29,.143),dark)
        truss.box((x+.63*delta,y,8.36),(.36,.22,.046),day_lamp)
for x in (hall_x0,hall_x1):
    hall.box((x,(hall_y0+hall_y1)/2,1.41),(.283,hall_y1-hall_y0,2.82),cream)
    bounds(x-.14,x+.14,hall_y0,hall_y1)
    for i in range(101):
        yy=hall_y0+(i+.5)*(hall_y1-hall_y0)/101
        m=plexi if i%19 in (8,9,10) else silvery
        hall.box((x,yy,6.63),(.123,.436,7.65),m)
        truss.box((x+.101 if x< -40 else x-.101,yy,6.63),(.10,.027,7.66),lintel)
    for z in (3.02,5.47,7.5,9.55):
        truss.tube([(x,hall_y0,z),(x,hall_y1,z)],.061,lintel,7)
for y in (hall_y0,hall_y1):
    openings=[(hall_mid-3.05,hall_mid+3.05)] if y==hall_y0 else []
    for x0,x1 in [(hall_x0,hall_mid-3.05),(hall_mid+3.05,hall_x1)] if openings else [(hall_x0,hall_x1)]:
        hall.box(((x0+x1)/2,y,1.47),(x1-x0,.24,2.94),cream)
        bounds(x0,x1,y-.13,y+.13)
    for i in range(97):
        a=hall_x0+i*37/97
        b=a+37/97
        mat=plexi if i%15 in (3,4,5,6) else roof
        hall.sheet([(a,y,2.92),(b,y,2.92),(b,y,roof_z(b)),(a,y,roof_z(a))],mat)
        truss.box(((a+b)/2,y-.035,(roof_z(a)+2.92)/2),(.033,.082,roof_z(a)-2.92),lintel if mat==plexi else roof)
    for x in (-56.9,-48.7,-36.3,-28.1):
        truss.box((x,y-.068,6.44),(2.6,.16,.58),roof)
        for i in range(7):
            truss.box((x,y-.16,6.18+i*.088),(2.57,.072,.026),lintel)
plaque(truss,sports,hall_mid,hall_y0-.20,5.06,7.5,'TRUNG TÂM THỂ THAO VÀ GIẢI TRÍ','SPORTS AND RECREATION CENTER')
truss.box((hall_mid,hall_y0-.024,2.93),(6.38,.35,.19),teal)
for x in (hall_mid-3.05,hall_mid+3.05):
    truss.box((x,hall_y0-.023,1.48),(.19,.33,2.98),teal)
slab(court,hall_x0+.12,hall_x1-.12,hall_y0-1.48,hall_y1-.12,.032,turf_green)

def blue_court(x,y,width,length):
    x0,x1=x-width/2,x+width/2
    y0,y1=y-length/2,y+length/2
    slab(court,x0,x1,y0,y1,.042,turf_blue)
    strip(court,[(x0,y0),(x1,y0),(x1,y1),(x0,y1),(x0,y0)],.06,white,z=.050)
    return x0,x1,y0,y1

tennis_x,tennis_y=-33.9,47.6
x0,x1,y0,y1=blue_court(tennis_x,tennis_y,10.97,23.77)
for x in (x0+1.37,x1-1.37):
    strip(court,[(x,y0),(x,y1)],.053,white,z=.052)
for y in (tennis_y-6.4,tennis_y+6.4):
    strip(court,[(x0+1.37,y),(x1-1.37,y)],.053,white,z=.052)
strip(court,[(tennis_x,tennis_y-6.4),(tennis_x,tennis_y+6.4)],.053,white,z=.052)

volley_x,volley_y=-51.3,47.6
u0,u1,v0,v1=blue_court(volley_x,volley_y,9.0,18.0)
for y in (volley_y-3,volley_y,volley_y+3):
    strip(court,[(u0,y),(u1,y)],.053,white,z=.052)
for x0,x1,y,bottom,top in [(x0-.42,x1+.42,tennis_y,.063,1.08),(u0-.62,u1+.62,volley_y,1.51,2.45)]:
    grid_net(sports_net,[(x0,y,bottom),(x1,y,bottom),(x1,y,top),(x0,y,top)],.075,.007,net_mat)
    truss.tube([(x0,y,top),(x1,y,top)],.027,white,7)
    for x in (x0,x1):
        truss.tube([(x,y,.045),(x,y,top+.08)],.066,teal,10)
    bounds(x0,x1,y-.04,y+.04)
grid_net(sports_net,[(-43,y0-1,.042),(-43,y1+2,.042),(-43,y1+2,4.8),(-43,y0-1,4.8)],.16,.011,net_mat)
bounds(-43.04,-42.96,y0-1,y1+2)
for x,y in [(-45.33,47.60),(-28.19,49.65)]:
    for d in (-.332,.332):
        for off in (-1,1):
            truss.tube([(x+d,y+off*.67,.035),(x+d*.74,y+off*.27,1.79)],.041,white,8)
        for z in (.28,.61,.94,1.27,1.60):
            truss.tube([(x-.33,y-.66+z*.22,z),(x+.33,y-.66+z*.22,z)],.026,white,7)
    truss.box((x,y,1.81),(.59,.46,.12),cobalt)
    truss.box((x,y+.20,2.03),(.57,.104,.37),cobalt)
    for side in (-1,1):
        xx=x+side*.36
        truss.tube([(xx,y+.23,1.84),(xx,y+.23,2.69),(xx,y+.04,2.84),(xx,y-.44,2.68)],.027,white,8)
    truss.sheet([(x-.38,y-.45,2.68),(x+.38,y-.45,2.68),(x+.38,y+.04,2.85),(x-.38,y+.04,2.85)],roof)
    truss.sheet([(x-.38,y+.04,2.85),(x+.38,y+.04,2.85),(x+.38,y+.30,2.73),(x-.38,y+.30,2.73)],roof)
    bounds(x-.38,x+.38,y-.68,y+.68)
for x,y in [(-39,43.2),(-55.77,39.68),(-31.31,55.2)]:
    court.globe((x,y,.171),(.127,.126,.126),[gold,white,cobalt],rng,sides=11,rings=8)
for x,y in [(-51.3,38),(-51.3,56),(-34.0,38),(-34.0,56)]:
    empty('Đèn nhà thể thao',physics,(x,y,7.2),centralLight=110)
hall.finish()
truss.finish()
court.finish(noShadow=True)
sports_net.finish(noShadow=True)

# The yard and central garden share the asphalt approach in the aerial view.
props = Mesh('Ghế đá, đèn ba nhánh, bồn và dải viền',garden)
paths = Mesh('Lối gạch nhiều màu và đá dạo quanh vườn',garden)
foliage = Mesh('Lá thấp, hàng rào xanh và hoa giấy',garden)
tree_wood = Mesh('Thân cau, cây tán rộng và cành nhỏ',garden)
crowns = Mesh('Tán lá lớp dày',garden)
leaf_cards = foliage_material()
lamp_black = surface('Sơn cột đèn đen',(.049,.064,.06),.56,metal=.21)
flower = surface('Hoa giấy đỏ hồng',(.63,.14,.212),.78,double=True)
red = surface('Sơn đỏ đồ trưng bày',(.62,.039,.028),.48,metal=.16)

slab(paths,3.36,8.46,3.52,40.06,.048,tiles)
for i in range(48):
    yy=3.57+i*.758
    palette=[1,0,4,1,2,3,2,4,0,3,2,1]
    for j in range(6):
        x=3.56+j*.80
        slab(paths,x,x+.788,yy,yy+.741,.056,pavers[palette[(i+j//3)%len(palette)]])
for x in (3.32,8.48):
    paths.box((x,21.7,.045),(.16,36.5,.119),concrete)
for center_x,center_y in [(-5.7,21.4),(21.5,21.8),(23.9,31.8)]:
    for i in range(17):
        t=i*math.tau/17
        x,y=center_x+4.87*math.cos(t),center_y+3.16*math.sin(t)
        paths.box((x,y,.023),(.41,.63,.073),concrete,angle=t)
for x0,x1,y0,y1 in [(-18,3.20,5.02,5.60),(8.58,35.91,5.02,5.60),
                     (3.06,3.35,6.12,39.32),(8.47,8.78,6.12,39.32),
                     (-18,1.45,39.03,39.46),(10.0,35.92,39.03,39.46),
                     (-18.0,-17.55,8.0,38.79),(35.59,36.02,7.3,39.43)]:
    props.span(((x0,x1),(y0,y1),(-.01,.19)),concrete)
    foliage.span(((x0+.015,x1-.015),(y0+.015,y1-.015),(.13,.40)),greens[1])
    steps=math.ceil(max(x1-x0,y1-y0)/.29)
    for i in range(steps):
        t=(i+.5)/steps
        x=x0+(x1-x0)*t if x1-x0>y1-y0 else (x0+x1)/2
        y=y0+(y1-y0)*t if y1-y0>x1-x0 else (y0+y1)/2
        foliage.globe((x,y,.365),(.185,.168,.14),greens[1:5],rng,sides=7,rings=4)
    bounds(x0,x1,y0,y1)
paths.finish(noShadow=True)

def bench(x,y,angle=0):
    ca,sa=math.cos(angle),math.sin(angle)
    def part(a,b,z,w,d,h,mat):
        props.box((x+a*ca-b*sa,y+a*sa+b*ca,z),(w,d,h),mat,angle=angle)
    part(0,0,.465,1.63,.51,.095,white)
    part(0,.225,.781,1.64,.105,.33,cream)
    for a in (-.52,.52):
        part(a,0,.227,.135,.37,.454,concrete)
        part(a,.225,.624,.085,.095,.51,concrete)
    radius_x=.82*abs(ca)+.26*abs(sa)
    radius_y=.82*abs(sa)+.26*abs(ca)
    bounds(x-radius_x,x+radius_x,y-radius_y,y+radius_y)


for i,(x,y) in enumerate([(-13.9,9.3),(-8.0,13.6),(-4.8,27.9),(-13,34.4),
                           (-.5,33),(13.2,8.9),(15.3,16.1),(20.9,12.45),
                           (26.8,16.74),(29.6,22),(14.0,27.5),(19,36.05),
                           (31.4,33),(25.65,30.1),(31.8,38),(-15,41.2),(35.5,42.3)]):
    bench(x,y,math.pi*.23*(i%4))
for x,y in [(-9.72,21.5),(16.8,20.3),(26.6,36.02)]:
    props.box((x,y,.69),(1.31,.79,.119),cream)
    props.box((x,y,.355),(.26,.28,.62),concrete)
    bench(x,y-1.09,0)
    bench(x,y+1.09,math.pi)
    bounds(x-.67,x+.67,y-.42,y+.42)

for i,(x,y) in enumerate([(-15.8,8),(-15.4,27.7),(-10.7,37.9),(.64,8.5),(11.58,11.6),
                           (10.18,28.6),(31.5,10.9),(31.7,30.8),(33.65,38.1)]):
    props.tube([(x,y,.035),(x,y,2.83)],(.041,.029),lamp_black,10)
    props.tube([(x,y,.04),(x,y,.29)],(.124,.074),lamp_black,10)
    for d in (-1,0,1):
        z=3.23 if d==0 else 3.01
        xx=x+d*.345
        arm=[(x,y,2.68),(x+d*.23,y,2.68),(xx,y,z-.16)] if d else [(x,y,2.69),(x,y,z-.16)]
        props.tube(arm,.022,lamp_black,7)
        props.globe((xx,y,z),(.112,.113,.231),[day_lamp],rng,sides=10,rings=8)
    bounds(x-.082,x+.082,y-.082,y+.082)
for i,y in enumerate((8.36,14.5,21.9,29.25,36.0)):
    x=2.66 if i%2==0 else 9.12
    color=pavers[4] if i%2==0 else gold
    props.tube([(x,y,.04),(x,y,3.65)],.045,cobalt,10)
    props.box((x+.37,y,3.57),(.76,.033,.042),cobalt)
    pos=x+.42
    props.sheet([(pos-.36,y,3.55),(pos-.36,y,2.51),(pos,y,2.71),
                 (pos+.36,y,2.51),(pos+.36,y,3.55)],color)
    text('Cờ đón Khu E','CƠ KHÍ',(pos,y-.019,3.16),dark,garden,bold,.55,.115,depth=.001)
    text('Cờ đón Khu E','HCMUTE',(pos,y-.019,2.97),dark,garden,regular,.43,.081,depth=.001)
for x,y in [(-18.6,4.8),(-12.05,18.5),(12.44,24.3),(30.5,40.2),(61.8,-4.8)]:
    for shift,mat in [(-.23,teal),(.23,red)]:
        props.box((x+shift,y,.43),(.365,.39,.78),mat)
        props.box((x+shift,y,.843),(.41,.43,.105),dark)
    bounds(x-.46,x+.46,y-.26,y+.26)

# Terracotta gateway and lattice on the west corner of the garden.
for y,w,h in [(7.5,4.2,2.85),(9.7,3.21,2.52)]:
    cx=-20.65
    for x in (cx-w*.45,cx+w*.45):
        for dx in (-.145,.145):
            for dy in (-.173,.173):
                props.tube([(x+dx,y+dy,.05),(x+dx,y+dy,h)],.034,lamp_black,8)
        for i in range(8):
            z=.24+i*.295
            for dy in (-.176,.176):
                props.tube([(x-.14,y+dy,z),(x+.14,y+dy,z+.225)],.018,lamp_black,6)
                props.tube([(x+.14,y+dy,z),(x-.14,y+dy,z+.225)],.018,lamp_black,6)
        bounds(x-.21,x+.21,y-.23,y+.23)
    for a,b,za,zb in [(y-.75,y,h,h+.57),(y,y+.75,h+.57,h)]:
        props.sheet([(cx-w/2,a,za),(cx+w/2,a,za),(cx+w/2,b,zb),(cx-w/2,b,zb)],terracotta)
        for i in range(24):
            xx=cx-w/2+(i+.5)*w/24
            props.tube([(xx,a,za+.024),(xx,b,zb+.024)],.035,terracotta,7)
props.box((19.8,22.65,.19),(4.71,1.14,.37),concrete,angle=.11)
for i,(letter,mat) in enumerate(zip('UTE',(teal,gold,red))):
    text('Chữ nổi trong vườn '+letter,letter,(18.48+i*1.26,22.62,1.20),
         mat,garden,bold,1.16,1.79,depth=.13)
    bounds(17.95+i*1.26,19.01+i*1.26,22.11,23.25)
props.finish()

def tree(x,y,h,spread,trunk,*,count=110):
    base=Vector((x,y,0))
    crown=base+Vector((rng.uniform(-.60,.60),rng.uniform(-.40,.40),h*.82))
    branch_base=base.lerp(crown,.55)
    tree_wood.tube([base-Vector((0,0,.07)),base+Vector((0,0,.39)),branch_base,crown],
                  (trunk*1.50,trunk,trunk*.63,trunk*.13),bark,9,irregular=.13)
    for j in range(8):
        t=j*2.39996
        axis=Vector((math.cos(t),math.sin(t),0))
        tail=crown+axis*spread*rng.uniform(.52,.96)+Vector((0,0,rng.uniform(-.19,.26)*h))
        mid=branch_base.lerp(tail,.6)+Vector((0,0,h*.07))
        tree_wood.tube([branch_base,mid,tail],(trunk*.42,trunk*.23,.014),bark,6)
        for k in range(4):
            center = mid.lerp(tail,.31+k*.20)
            center += Vector((-axis.y,axis.x,.16)) * spread * (0.14 if k%2 else -.14)
            leaf_spray(crowns,center,spread*(.42-k*.04),t+k*.76,leaf_cards)
        for i in range(count):
            az=rng.uniform(0,math.tau)
            theta=rng.uniform(-1,1)
            radius=rng.uniform(.08,1)**.5*spread*.44
            pos=mid.lerp(tail,rng.uniform(.36,1.14))+Vector((math.cos(az)*radius,math.sin(az)*radius,theta*radius*.76))
            size=rng.uniform(.19,.41)*(1 if h>7 else .73)
            foliage.leaf(pos,(math.cos(az),math.sin(az),rng.uniform(-.54,.39)),
                         size,size*rng.uniform(.43,.64),rng.choice(greens))
    bounds(x-trunk,x+trunk,y-trunk,y+trunk)

for i,(x,y) in enumerate([(-23.0,4.47),(-18.3,10.4),(-14.3,17.75),(-5.4,8.96),(-10.9,31.5),
                           (-.03,27.4),(-1.68,38.1),(12.4,6.66),(16.2,12.2),(25.9,8.11),
                           (28.2,17.3),(18.0,27.6),(30.6,28.1),(27.8,37.3),(34.5,9.2),
                           (34.1,36.4),(13.36,34.4),(12.3,31.5),(-74.1,25.8),(-67,49),
                           (-65.3,68.7),(-34.5,-7.0),(-57.9,-6.47),(41.9,6.4),(51.3,6.35),
                           (65.6,24.1),(63.5,41.2),(48.5,72.5),(-20.2,77.5),(15.9,74.4)]):
    big=i in (0,1,14,15,18,19,20,21,22,23,24,25,26)
    tree(x,y,rng.uniform(9.8,14) if big else rng.uniform(5.5,8.2),
         rng.uniform(3.7,5.8) if big else rng.uniform(2.1,3.7),.36 if big else .20,count=138 if big else 76)
for i,x in enumerate((-19.2,-14.2,-9.1,-3.4,19.15,24.4,29.4,35.1)):
    y=42.75-(i%2)*.53
    h=7.0+rng.random()*2.4
    stem=[(x+.21*t*t,y+.23*t*t,h*t) for t in (0,.12,.30,.5,.72,1)]
    tree_wood.tube(stem,[.33,.27,.25,.24,.228,.25],bark,11)
    for j in range(23):
        t=.04+j*.039
        xx,yy,z=x+.21*t*t,y+.23*t*t,h*t
        tree_wood.tube([(xx,yy,z),(xx,yy,z+.019)],.27-.04*t,bark,10)
    tree_wood.tube([stem[-1],(x+.25,y+.29,h+1.03)],(.23,.115),greens[2],9)
    for j in range(14):
        theta=j*2.39996
        a=Vector((math.cos(theta),math.sin(theta),0))
        b=Vector((-a.y,a.x,0))
        root=Vector(stem[-1])+Vector((0,0,.58))
        reach=rng.uniform(2.28,3.23)
        points=[root+a*reach*t+Vector((0,0,reach*(.68*math.sin(t*2.42)-.69*t)))
                for t in (0,.13,.29,.49,.72,1)]
        tree_wood.tube(points,[.042,.039,.033,.024,.014,.006],greens[2],5)
        for k in range(17):
            t=(k+.9)/19
            at=root+a*reach*t+Vector((0,0,reach*(.68*math.sin(t*2.42)-.69*t)))
            for d in (-1,1):
                length=.12+reach*.33*math.sin(t*math.pi)
                foliage.leaf(at,b*d*.83+a*.45+Vector((0,0,-.39)),length,length*.149,
                             rng.choice(greens[1:]),droop=.24)
    bounds(x-.30,x+.30,y-.30,y+.30)

for x,y in [(-19,7.7),(-21.9,9.4),(-18.12,11),(9.05,6.17),(13.3,15.5),
            (17.2,9.02),(13.6,33.8),(24.3,27.1),(-10.8,24.9),(28.2,20.6)]:
    for j in range(11):
        t=rng.random()*math.tau
        r=rng.uniform(.12,1.05)
        px,py=x+math.cos(t)*r,y+math.sin(t)*r
        z=rng.uniform(.31,.87)
        foliage.globe((px,py,z),(.36,.32,.26),greens[1:],rng,sides=8,rings=5)
        if x<-18 or y<8:
            foliage.leaf((px,py,z+.22),(math.cos(t),math.sin(t),.32),.153,.093,flower)
foliage.finish(noShadow=True)
tree_wood.finish()
crowns.finish()

# Low blue-roof shops border the open workshop yard and the internal road.
utility = Mesh('Xưởng cơ khí, cửa lá sách và mái xanh',land)
blue_roof=surface('Tôn xanh dương ngoài xưởng',(.185,.42,.56),.62,metal=.23)
for x0,x1,y0,y1,face_y in [(-93,-65,22,70,22),(-61,-25,70.2,77.0,70.2),
                            (-89,-28,-17.3,-9.0,-9.0),(16.5,61.2,-19.1,-9.3,-9.3)]:
    utility.span(((x0,x1),(y0,y1),(0,4.26)),cream)
    for i in range(1+int((x1-x0)/5)):
        left=x0+i*5
        right=min(left+4.96,x1)
        if right-left<.1:
            continue
        ridge=(y0+y1)/2
        width=right-left
        for a,b,za,zb in [(y0-.36,ridge,4.34,5.23),(ridge,y1+.39,5.23,4.34)]:
            utility.sheet([(left-.19,a,za),(right+.19,a,za),(right+.19,b,zb),(left-.19,b,zb)],blue_roof)
        x=(left+right)/2
        direction=-1 if face_y==y0 else 1
        y=face_y+direction*.088
        utility.box((x,y,2.52),(width*.78,.21,1.54),teal)
        utility.box((x,y+direction*.135,2.52),(width*.69,.067,1.32),dark)
        for j in range(7):
            utility.box((x,y+direction*.176,1.98+j*.178),(width*.66,.122,.07),teal)
        for j in range(4):
            utility.box((x+(j-1.5)*width*.19,y+direction*.20,2.52),(.047,.078,1.38),teal)
    bounds(x0,x1,y0,y1)
plaque(utility,land,-78.2,21.81,3.74,7.63,'XƯỞNG CƠ KHÍ','KHU THỰC HÀNH')
plaque(utility,land,-43.9,-17.48,3.76,7.92,'TRUNG TÂM TIN HỌC','HCMUTE')
utility.box((49.4,-6.33,2.26),(1.47,.103,.76),cobalt,angle=.12)
utility.tube([(48.91,-6.22,.04),(49.02,-6.27,2.42)],.045,cobalt,9)
text('Biển hướng dẫn Tin học','TRUNG TÂM TIN HỌC',(49.37,-6.39,2.29),white,land,bold,1.26,.22,depth=.003)
utility.finish()

context = Mesh('Nhà mái ngói, mặt kính kỹ thuật và khối nhà phía sau',neighbors)
for x0,x1,y0,y1,h,mat,roof_mat in [(41,62,15,42,6.6,blue_wall,terracotta),
    (41.1,64.1,7.11,14.7,4.7,cream,silvery),(41.25,61.8,45.05,64.0,9.9,cream,terracotta),
    (-92,-75,73,78.7,8.9,blue_wall,blue_roof),(42,66,69,77.9,13.1,blue_wall,cream),
    (-16.7,-4,74,83,11.9,cream,terracotta),(12.4,32.5,74,81,9.0,cream,silvery)]:
    context.span(((x0,x1),(y0,y1),(0,h)),mat)
    bounds(x0,x1,y0,y1)
    mid=(y0+y1)/2
    rise=.34 if roof_mat!=terracotta else 1.55
    for a,b,za,zb in [(y0-.28,mid,h+.11,h+rise),(mid,y1+.28,h+rise,h+.11)]:
        context.sheet([(x0-.24,a,za),(x1+.24,a,za),(x1+.24,b,zb),(x0-.24,b,zb)],roof_mat)
    for i in range(round((x1-x0)/2.44)):
        x=x0+1.22+i*2.44
        for fl in range(int(h/3)):
            window(context,x,y0,z=1.72+fl*3.05,w=1.87,h=1.53)
plaque(context,neighbors,54.6,6.97,4.09,13.5,'HCMUTE TECHNICAL SPACE','KHÔNG GIAN KỸ THUẬT')
for i in range(10):
    x=42.87+i*2.14
    context.box((x,7.022,1.88),(2.07,.103,2.84),glasses[i%4])
    context.box((x-1.043,6.948,1.88),(.071,.16,2.89),aluminum)
    context.box((x,6.935,2.65),(2.07,.092,.055),aluminum)
for x,y in [(-33.2,-3.45),(65.9,3.7),(56.9,-4.48),(-24.2,24.9)]:
    context.tube([(x,y,.034),(x,y,6.55)],(.13,.08),concrete,9)
    context.tube([(x,y,5.88),(x+.34,y,6.47),(x+.90,y,6.61)],.026,aluminum,8)
    context.box((x+.94,y,6.576),(.30,.185,.089),day_lamp)
    bounds(x-.12,x+.12,y-.12,y+.12)
for j in range(4):
    context.tube([(-33.2+((65.9+33.2)*i/12),-3.45+j*.14+((3.7+3.45)*i/12),
                   6.07-1.02*math.sin(math.pi*i/12)) for i in range(13)],.012,dark,5)

for i,(x,y) in enumerate([(-27.3,-3.2),(68.3,10.1),(-69.4,18.72)]):
    paint=car_paints[i]
    context.box((x,y,.63),(4.27,1.76,.78),paint)
    a,b=x-1.46,x+.78
    verts=[(a,y-.81,1.0),(b,y-.81,1.0),(b,y+.81,1.0),(a,y+.81,1.0),
           (a+.36,y-.67,1.52),(b-.44,y-.67,1.52),(b-.44,y+.67,1.52),(a+.36,y+.67,1.52)]
    context.add(verts,[(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],glasses[3])
    context.add(verts,[(4,5,6,7)],paint)
    for d in (-1,1):
        yy=y+d*.84
        for xx in (x-1.34,x+1.33):
            context.tube([(xx,yy,.345),(xx,yy+d*.13,.345)],.323,dark,16)
            context.tube([(xx,yy+d*.13,.345),(xx,yy+d*.158,.345)],.178,aluminum,13)
        context.box((x+2.14,y+d*.56,.748),(.071,.47,.117),day_lamp)
        context.box((x-2.14,y+d*.58,.758),(.071,.39,.133),red)
    context.box((x-2.181,y,.575),(.035,.43,.113),white)
    bounds(x-2.13,x+2.13,y-.92,y+.92)
context.finish()

houses=Mesh('Dãy nhà phố ngoài rìa bản đồ',neighbors)
urban=[cream,blue_wall,white]
for row,y in enumerate((88.6,96.05)):
    x=-105.8+row*1.65
    while x<92:
        width=rng.uniform(3.8,7.1)
        depth=rng.uniform(4.7,6.6)
        levels=rng.choice((2,2,3,3,4))
        h=levels*2.75
        houses.box((x,y,h*.5),(width,depth,h),rng.choice(urban))
        houses.box((x,y,h+.14),(width+.18,depth+.12,.28),rng.choice((cream,blue_roof,terracotta)))
        for level in range(levels):
            z=1.74+level*2.75
            for xx in (x-width*.245,x+width*.245):
                houses.box((xx,y-depth*.5-.055,z),(width*.32,.117,1.19),glasses[(level+row)%4])
                houses.box((xx,y-depth*.5-.18,z-.665),(width*.35,.37,.091),concrete)
        if levels>2:
            houses.tube([(x,y,h+.28),(x,y,h+1.14)],.286,aluminum,10)
        x+=width+1.11
houses.finish()

VIEWS={
    'loi-vao':((-29,-1.14,1.72),(-9.8,19.7,2.5),21),
    'khoa':((7.73,32.4,1.74),(8.2,51.7,6.75),16.8),
    'vuon':((6.05,8.20,1.71),(6.8,37.0,3.24),22),
    'nha-the-thao':((-34.3,36.72,1.72),(-41.8,63.2,4.7),18),
    'xuong':((-76.9,12.1,1.72),(-42.0,30.7,4.25),21),
    'tren-cao':((-9,-80,124),(-12,33,2),34),
}
walk_limits(physics,-98,85,-28,83)
for key,(eye,target,_) in VIEWS.items():
    if key!='tren-cao':
        view_marker(physics,key,eye,target)

MAP.mkdir(parents=True,exist_ok=True)
asset=MAP/'khu-e.glb'
with tempfile.TemporaryDirectory(dir=MAP) as directory:
    scratch=Path(directory)/asset.name
    bpy.ops.export_scene.gltf(filepath=str(scratch),export_format='GLB',export_extras=True,export_yup=True,
                             export_cameras=False,export_lights=False,export_animations=False,export_apply=True)
    scratch.replace(asset)

studio=collection('07 · Góc máy đối chiếu')
world=bpy.data.worlds.new('Trời Khu E')
scene.world=world
world.use_nodes=True
bg=world.node_tree.nodes.get('Background')
bg.inputs['Color'].default_value=(.54,.69,.88,1)
bg.inputs['Strength'].default_value=.72
sun_data=bpy.data.lights.new('Nắng ngày','SUN')
sun_data.energy=2.55
sun_data.angle=math.radians(7)
sun=bpy.data.objects.new(sun_data.name,sun_data)
studio.objects.link(sun)
sun.rotation_euler=Vector((.39,.56,-.78)).to_track_quat('-Z','Y').to_euler()
for x,y,power,radius in [(-34.3,40,1800,4.2),(-34.3,57,1800,4.2),(-51.7,48,1620,4.2),(8.2,50,700,2.0)]:
    light_data=bpy.data.lights.new('Ánh sáng tán xạ','POINT')
    light_data.energy=power
    light_data.shadow_soft_size=radius
    light=bpy.data.objects.new(light_data.name,light_data)
    studio.objects.link(light)
    light.location=(x,y,8.53 if x<0 else 3.8)

cameras={}
for key,(eye,target,lens) in VIEWS.items():
    data=bpy.data.cameras.new(key)
    ob=bpy.data.objects.new(key,data)
    studio.objects.link(ob)
    ob.location=eye
    ob.rotation_euler=(Vector(target)-Vector(eye)).to_track_quat('-Z','Y').to_euler()
    data.lens=lens
    data.clip_end=370
    cameras[key]=ob
scene.camera=cameras['khoa']
scene.render.engine='CYCLES'
scene.cycles.samples=12
scene.cycles.use_denoising=True
scene.cycles.max_bounces=6
scene.render.resolution_x=1420
scene.render.resolution_y=830
scene.render.image_settings.file_format='JPEG'
scene.render.image_settings.quality=91
scene.view_settings.view_transform='AgX'
scene.view_settings.exposure=.42
bpy.ops.file.pack_all()
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            view=area.spaces.active
            view.clip_end=480
            view.region_3d.view_location=(-13,34,0)
            view.region_3d.view_rotation=cameras['tren-cao'].rotation_euler.to_quaternion()
            view.region_3d.view_distance=160
            view.shading.color_type='MATERIAL'
            view.overlay.show_extras=False
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'khu-e.blend'),compress=True)
if '--preview' in sys.argv:
    selected=sys.argv[sys.argv.index('--preview')+1:]
    for key,view in cameras.items():
        if selected and key not in selected:
            continue
        scene.camera=view
        scene.render.filepath=str(MAP/f'preview-{key}.jpg')
        bpy.ops.render.render(write_still=True)
