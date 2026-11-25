"""Artificial-turf football pitches next to the Central Building."""
import math

from campus_mesh import Mesh, arc, collection, grid_net, strip, surface, tiled


def build_pitch(bounds):
    group = collection('09 · Sân bóng cạnh Tòa nhà Trung tâm')
    white = surface('Sơn vạch sân trắng',(.85,.874,.813))
    orange = surface('Vạch vàng cam chia sân nhỏ',(.68,.367,.097))
    concrete = surface('Bê tông chân cột',(.41,.442,.394))
    pole_blue = surface('Cột sân sơn xanh da trời',(.15,.40,.51),.58,metal=.19)
    steel = surface('Thép lưới sân mạ xám',(.26,.32,.31),.52,metal=.34)
    net_green = surface('Sợi lưới chắn bóng xanh đen',(.029,.083,.074),.93,double=True)
    net_white = surface('Sợi lưới thành bạc trắng',(.67,.729,.709),.92,double=True)
    turf = [tiled('Cỏ nhân tạo sân bóng '+str(i),c,'artificial turf',1.8,size=512)
            for i,c in enumerate(((.19,.35,.205),(.29,.445,.241)))]
    field = Mesh('Thảm cỏ hai hướng chải và vạch thi đấu',group)
    field.span(((69,124),(-10,76),(-.06,.022)),turf[0])
    for i in range(18):
        y = -9.6+i*4.73
        field.span(((69.18,123.82),(y,y+4.73),(.023,.032)),turf[i%2])

    left,right,near,far = 71.1,121.9,-7.9,73.9
    cx,cy = (left+right)/2,(near+far)/2
    strip(field,[(left,near),(right,near),(right,far),(left,far),(left,near)],.112,white,z=.039)
    strip(field,[(left,cy),(right,cy)],.112,white,z=.039)
    strip(field,arc(cx,cy,6.9,0,math.tau,74),.115,white,z=.042)
    field.tube([(cx,cy,.033),(cx,cy,.043)],.116,white,14)
    for end,direction in ((near,1),(far,-1)):
        for width,depth in ((31.7,13.1),(14.1,4.5)):
            x0,x1,y = cx-width/2,cx+width/2,end+depth*direction
            strip(field,[(x0,end),(x0,y),(x1,y),(x1,end)],.111,white,z=.040)
        y = end+9.12*direction
        field.tube([(cx,y,.033),(cx,y,.043)],.103,white,12)
        start,stop = (.73,2.41) if direction>0 else (3.87,5.55)
        strip(field,arc(cx,y,6.03,start,stop,30),.105,white,z=.041)

    for y0,y1 in [(-5.75,30.85),(35.15,71.75)]:
        x0,x1,middle = 73.4,119.6,(y0+y1)/2
        strip(field,[(x0,y0),(x1,y0),(x1,y1),(x0,y1),(x0,y0)],.079,orange,z=.046)
        strip(field,[(cx,y0),(cx,y1)],.079,orange,z=.046)
        strip(field,arc(cx,middle,4.08,0,math.tau,52),.078,orange,z=.045)
        for x,d in ((x0,1),(x1,-1)):
            strip(field,[(x,middle-6.1),(x+5.9*d,middle-6.1),
                         (x+5.9*d,middle+6.1),(x,middle+6.1)],.078,orange,z=.045)
    field.finish(noShadow=True)

    frames = Mesh('Cột lưới, đèn pha và khung thành trắng',group)
    net = Mesh('Lưới bao sân, lưới chia sân và lưới thành',group)
    for x in (68.98,124.0):
        portions = [(-10,16.0),(20.0,76)] if x<70 else [(-10,76)]
        for a,b in portions:
            grid_net(net,[(x,a,.08),(x,b,.08),(x,b,6.14),(x,a,6.14)],.24,.010,net_green)
            for z in (.07,2.8,6.15):
                frames.tube([(x,a,z),(x,b,z)],.019,steel,6)
            bounds(x-.065,x+.065,a,b,label='Va chạm · Lưới sân bóng')
            bays = math.ceil((b-a)/9.5)
            for i in range(bays+1):
                y = a+(b-a)*i/bays
                frames.tube([(x,y,.025),(x,y,6.32)],(.077,.055),pole_blue,9)
                frames.box((x,y,.091),(.32,.36,.17),concrete)
        for y in (6.3,35.5,65.3):
            d = 1 if x<70 else -1
            frames.tube([(x,y,0),(x,y,10.1),(x+d*.44,y,10.25)],(.11,.077,.061),pole_blue,10)
            frames.box((x+d*.47,y,10.12),(.37,1.07,.14),steel)
            for j in range(3):
                yy = y+(j-1)*.375
                frames.box((x+d*.59,yy,10.13),(.28,.29,.175),steel)
                frames.box((x+d*.743,yy,10.11),(.019,.251,.137),white)
    for y in (-10,76):
        grid_net(net,[(69,y,.095),(124,y,.095),(124,y,6.14),(69,y,6.14)],.24,.010,net_green)
        bounds(69,124,y-.065,y+.065,label='Va chạm · Lưới sau gôn')
        for x in range(69,125,9):
            frames.tube([(x,y,.02),(x,y,6.3)],(.067,.051),pole_blue,8)
        frames.tube([(69,y,6.16),(124,y,6.16)],.021,steel,6)
    grid_net(net,[(73.2,33,.049),(119.1,33,.049),(119.1,33,3.05),(73.2,33,3.05)],.16,.009,net_green)
    frames.tube([(73.2,33,3.06),(119.1,33,3.06)],.018,steel,7)
    for x in (73.2,88.5,104,119.1):
        frames.tube([(x,33,.029),(x,33,3.17)],.047,pole_blue,8)
    bounds(73.2,119.1,32.94,33.06,label='Va chạm · Lưới giữa hai sân')

    def goal(x,y,width,height,depth,along_y):
        def point(a,b,z):
            return (x+a,y+b,z) if along_y else (x+b,y+a,z)

        half = width/2
        a,b = point(-half,0,.04),point(half,0,.04)
        c,d = point(-half,0,height),point(half,0,height)
        e,f = point(-half,depth,.04),point(half,depth,.04)
        g,h = point(-half,depth*.52,height*.89),point(half,depth*.52,height*.89)
        for bar in ((a,c,d,b),(a,e,f,b),(c,g,e),(d,h,f)):
            frames.tube(bar,.046,white,9)
        for corners in [(c,d,h,g),(e,f,h,g),(a,e,g,c),(b,f,h,d)]:
            grid_net(net,corners,.132,.010,net_white)
        for px,py,_ in (a,b):
            bounds(px-.075,px+.075,py-.075,py+.075)

    goal(cx,near,6.8,2.28,-1.62,True)
    goal(cx,far,6.8,2.28,1.62,True)
    for y in (12.55,53.45):
        goal(73.4,y,3.57,1.91,-1.17,False)
        goal(119.6,y,3.57,1.91,1.17,False)
    frames.finish()
    net.finish(noShadow=True)

    sheds = Mesh('Dãy mái tôn xanh và mái pin mặt trời dọc sân',group)
    blue_roof = surface('Tôn mái xanh bạc cạnh sân',(.274,.493,.493),.68,metal=.16)
    solar = surface('Pin mặt trời xanh lam xẫm',(.045,.095,.18),.35,metal=.22,coat=.29)
    cream = surface('Tường kem quanh sân',(.61,.621,.565))
    for x0,x1 in [(-32,19),(20,64),(65,117.6)]:
        sheds.span(((x0,x1),(-32.5,-25.25),(0,3.25)),cream)
        for y0,y1,z0,z1 in [(-32.9,-28.9,3.35,4.75),(-28.9,-24.85,4.75,3.35)]:
            sheds.sheet([(x0-.25,y0,z0),(x1+.25,y0,z0),(x1+.25,y1,z1),(x0-.25,y1,z1)],blue_roof)
        for x in range(math.ceil(x0),math.floor(x1),2):
            sheds.tube([(x,-32.9,3.37),(x,-28.9,4.77),(x,-24.85,3.37)],.022,white,5)
        bounds(x0,x1,-32.5,-25.25)
    sheds.span(((132.9,154),(-4,76),(0,4.08)),cream)
    sheds.span(((132.6,154.33),(-4.28,76.28),(4.06,4.28)),blue_roof)
    bounds(132.9,154,-4,76)
    for y in range(0,73,4):
        for x in range(134,153,3):
            sheds.box((x,y,4.34),(2.77,3.74,.087),solar)
            for j in range(5):
                sheds.box((x-1.12+j*.56,y,4.39),(.013,3.64,.012),white)
            for j in range(6):
                sheds.box((x,y-1.55+j*.62,4.392),(2.68,.012,.01),white)
    for x in (66.1,122.8):
        for y in (5.2,24.6,49.2,68.7):
            sheds.box((x,y,.32),(.44,1.57,.15),concrete)
            for dy in (-.51,.51):
                sheds.box((x,y+dy,.14),(.33,.14,.29),concrete)
    sheds.finish()
