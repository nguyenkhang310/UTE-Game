# UTE Game

Game khám phá góc nhìn thứ nhất mô phỏng khuôn viên HCMUTE. Khu B là cảnh ban đêm có đèn pin, giọng thì thầm và tương tác ở miếu. Trung tâm, Khu E và Khu A dùng cảnh ban ngày. Khu A có sự kiện âm thanh dưới mái che.

## Chạy và tìm đúng bản đồ

- Chạy `npm run dev` từ gốc repo. Máy chủ Node phục vụ tệp tĩnh trên cổng `8000` mặc định. Dùng `PORT=8010 npm run dev` để chạy phiên kiểm tra riêng khi cổng chính đang được dùng.
- Các bản đồ dùng mô-đun ES và Three.js 0.169 được lưu sẵn ở `vendor/three/`. Các trang nạp thư viện qua import map. Có thể chạy game từ bản clone bằng Node và trình duyệt hỗ trợ WebGL2 mà không cần cài package hay mở Blender.

| Đường dẫn | Mã chạy | Tài nguyên chính |
| --- | --- | --- |
| `/` | `index.html`, `src/main.js`, `styles/main.css` | `assets/khu-b-courtyard.glb`, `mieu-tho-audio.wav` |
| `/maps/index.html` | Trang chọn bản đồ và giao diện chung trong `maps/maps.css` | Ảnh xem trước từng map |
| `/maps/trung-tam/index.html` | `maps/trung-tam/viewer.js` và `viewer.css` | `maps/trung-tam/trung-tam.glb` |
| `/maps/khu-e/index.html` | Dùng chung viewer ban ngày trong `maps/trung-tam/` | `maps/khu-e/khu-e.glb` |
| `/maps/khu-a/index.html` | Viewer ban ngày và `maps/khu-a/sound.js` | `maps/khu-a/khu-a.glb` |

Dùng URL có `index.html` cho các trang trong `/maps/` vì máy chủ chỉ tự mở `index.html` cho đường dẫn `/`.

## Khu B

- `src/config.js` giữ điểm vào, giới hạn chơi, vị trí miếu, tốc độ, thông số đèn pin và ngân sách render. `src/main.js` khởi tạo game, gắn bàn phím và cập nhật mỗi khung hình.
- `src/world/worldLoader.js` đọc GLB, va chạm, cao độ, mốc đèn và hướng mặt thờ. `walkCollider` chỉ mô tả mặt bằng, nên loader đo đỉnh vật cản từ hình học lần đầu người chơi chạm vào. Tường lửng, lan can, ghế và bồn cây thấp hơn đỉnh nhảy (khoảng 1 m, chỉnh bằng `jumpSpeed` và `gravity`) có thể nhảy qua hoặc đứng lên. Vật thể kéo cao quá 2,2 m so với sàn luôn chặn. `src/player/player.js` xử lý di chuyển, khóa chuột, bậc thềm và vòng lặp khi đi quá giới hạn.
- `src/world/shrine.js` điều khiển lửa, khói, lời thì thầm và bóng lướt qua. `src/audio/audio.js` và `src/ui/hud.js` xử lý âm thanh và giao diện nhắc tương tác.
- Bấm nút vào game, dùng WASD và chuột để đi, Shift để chạy, Space để nhảy, F để bật hoặc tắt đèn, E để thắp nhang khi có lời nhắc. Alt hoặc Esc nhả chuột.

### Mốc bố trí cần đối chiếu

- Từ điểm vào, bảng **Khoa Hóa học và Khoa học Sự sống** ở bên trái. Rẽ phải theo lối gạch rồi đi dưới cầu nối để vào sân trong có bồn cong, ghế đá và chữ **B**. Cầu thang ngoài nằm bên phải cầu nối. Giữ đường đi bên phải thông thoáng quanh cây, ghế và chân cầu thang.
- Khối B có mặt bằng chữ H, khối C chạy song song. Vườn miếu nằm giữa khối C và D, phía trái thư viện trên sơ đồ. Bãi xe máy nằm cạnh lối gạch phía vườn.
- Miếu lấy từ `hcmute-khu-b.glb`, nhận diện bằng tiền tố node `tripo_node_9f7`. Tâm miếu trong Three.js là `(-34.4, 0.03, 34.65)`. Mặt thờ quay về khe mở của hàng rào, tức hướng Z âm trong game. Đèn và khói nhang theo hướng node, nên khi xoay hoặc dời miếu hãy kiểm tra cả góc nhìn và tương tác E.
- Tư liệu tham chiếu nếu có ở máy là `src về trường/IMG_4185.MOV` và `src về trường/IMG_4187.MOV`. Đầu video 4185 có bảng khoa và bậc lên hành lang. Khoảng 1:30–2:00 của video 4187 nối bậc khoa, cầu nối và đường vào sân. Khoảng cách trong mô hình được ước lượng từ ảnh, video và sơ đồ.

## Tòa nhà Trung tâm

- `maps/trung-tam/viewer.js` quản lý di chuyển, chiếu sáng và kiểm tra va chạm cho các map ban ngày. Từng trang chọn GLB và điểm vào qua `data-model` và `data-start-view`. Các điểm vào được lấy từ mốc trong GLB. Chọn điểm đứng, bấm **Đi bộ**, rồi dùng WASD hoặc phím mũi tên, Shift và Esc.
- Khi nhìn chính diện tòa nhà, sân bóng nằm bên phải, qua đường dọc. Có thể đi qua khe lưới ở cạnh giáp tòa nhà hoặc chọn **Sân bóng** để vào thẳng sân. Đường bên trái uốn quanh vườn và gặp đường ngang phía trước.
- Bóng nắng cập nhật khi chuyển vùng. Cảnh vẽ lại khi người chơi di chuyển, đổi góc nhìn, chọn điểm đứng hoặc đổi kích thước cửa sổ. Khi sửa render của một map, kiểm tra entry point của map đó trước.

## Khu E

- Đường nội bộ chạy dọc mép trước vườn. Lối gạch nhiều màu đưa từ đường qua vườn tới Khoa Cơ khí Chế tạo máy. Khoa có hai cánh xanh xám ốp gạch cam, lam trắng ở sảnh lõm và mái đón xanh. Có thể đi lên tam cấp và vào sảnh giữa.
- Nhà thể thao mái vòm xanh mint đứng bên trái khoa, lối vào mở ra sân xưởng. Bên trong có sân tennis và sân bóng chuyền, lưới chia ở giữa và lối đi vòng ở đầu sân.

## Khu A

- Mở `khu-a-demo.blend`. Trong **Scripting**, mở `tools/build_zone_a.py` (hoặc **Text → Reload** nếu đã mở) rồi **Run Script** để dựng lại phần tự động. Hướng trái/phải lấy theo người đứng ở vỉa hè phía Tòa nhà Trung tâm nhìn vào. Tên và vị trí mười khu có trong [sơ đồ quy ước](personal/khu-a/so-do-quy-uoc-demo-v1.png).
- Trong Outliner, đặt vật thể mới vào **Khu A · Chi tiết chỉnh tay** → Collection của mã khu. Để thay một vật sinh tự động, nhân bản vật đó sang Collection chỉnh tay, đặt thuộc tính chuỗi `ka_replaces` trên bản sao bằng giá trị `ka_id` của bản gốc, rồi chạy lại script. Vật thể có `ka_walk` bằng `wall` tạo vật cản theo mặt bằng, còn `floor` tạo mặt đứng ở cao độ đỉnh. Với mái che hoặc tán cây cần đi qua bên dưới, chỉ gắn va chạm cho cột hoặc thân.
- Lưu file Blender rồi xuất từ thư mục gốc bằng `blender -b khu-a-demo.blend --python-exit-code 1 -P tools/export_zone_a.py`. Nếu chỉnh tay trong Blender, bước xuất đọc trực tiếp cảnh vừa lưu. Bản xuất dùng màu nền của các vật liệu thủ tục trong demo.
- Mở **Chọn bản đồ → Khu A → Vỉa hè → Đi bộ**. Men theo hông phải nhà mái sáng, tới sân nhỏ rồi rẽ vào lối mái che hướng về khối nối. Đi dưới khối nối tới lối lát cạnh bồn cây dài. Các nút **Sân nhỏ** và **Sân cây** cho phép thử riêng từng đoạn.
- Âm côn trùng đặt ở sân nhỏ. Lần đầu đi từ sân vào một trong hai lối mái che, âm nền giảm và một bước chân phát từ tầng trên. Esc mở menu và ngắt âm. Tải lại trang để thử sự kiện thêm lần nữa.
- Hai ảnh đối chiếu nằm trong `maps/khu-a/preview-tren-cao.jpg` và `maps/khu-a/preview-mat-dat.jpg`. Đặt tên ảnh tư liệu mới theo mã và hướng nhìn, ví dụ `KA-05_tu-moc-tron_nhin-ve-day-lop.jpg`.

## Chỉnh cảnh và xuất từ Blender

| Bản đồ | Script nguồn | Kết quả |
| --- | --- | --- |
| Khu B | `tools/build_courtyard.py` | `khu-b-mo-rong.blend`, `assets/khu-b-courtyard.glb` |
| Trung tâm | `tools/build_central_campus.py`, `tools/campus_pitch.py` | `toa-nha-trung-tam.blend`, `maps/trung-tam/trung-tam.glb` |
| Khu E | `tools/build_zone_e.py` | `khu-e.blend`, `maps/khu-e/khu-e.glb` |
| Khu A | `tools/build_zone_a.py`, `tools/export_zone_a.py` | `khu-a-demo.blend`, `maps/khu-a/khu-a.glb` |

Trung tâm và Khu E dùng chung các helper hình học và vật liệu trong `tools/campus_mesh.py`.

Dùng Blender nền để dựng lại cảnh khi thay đổi hình học. Các script dùng `bpy` và `numpy` trong Blender. Dự án đã được dựng bằng Blender 5.3. Trên macOS, nếu lệnh `blender` chưa có trên PATH, dùng `/Applications/Blender.app/Contents/MacOS/Blender`. Trên Windows, dùng `"C:\Program Files\Blender Foundation\Blender 5.3\blender.exe"`. Hai builder đọc font Arial và Times từ `/System/Library/Fonts/Supplemental` trên macOS hoặc `C:\Windows\Fonts` trên Windows. Builder Trung tâm dùng ảnh phù hiệu trong `maps/trung-tam/`.

```bash
blender --background --python-exit-code 1 --python tools/build_courtyard.py
blender --background --python-exit-code 1 --python tools/build_central_campus.py
blender --background --python-exit-code 1 --python tools/build_zone_e.py
```

Để đối chiếu Khu B với ảnh, thêm `-- --preview /tmp/ute-khu-b cua-khoa re-phai san-trong mat-bang` vào lệnh đầu. Tham số đầu là tiền tố đường dẫn ảnh. Với Trung tâm và Khu E, thêm `-- --preview` để render các ảnh `preview-*.jpg` vào thư mục map. Có thể truyền các tên góc sau `--preview` để chỉ dựng các ảnh cần dùng.

- Các cảnh dùng mét. Blender có trục Z hướng lên, xuất GLB sang Three.js theo `(x, y, z) -> (x, z, -y)`. Dùng đúng hệ trục khi phối hợp điểm đặt trong builder và `src/config.js`.
- Giữ tùy chọn xuất glTF extras. `walkCollider` đánh dấu thể tích chặn, `floorStart`, `floorEnd` và `floorAxis` mô tả cao độ sàn hoặc dốc. Đường dốc theo `depth` đọc từ Z lớn về Z nhỏ trong Three.js. `courtyardLight` và `centralLight` là mốc đèn của từng map. Trung tâm có thêm `viewKey`, `viewYaw`, `viewPitch`. Các helper trong builder đã tạo metadata theo dạng loader cần.
- Khi thay hình học, cập nhật builder và xuất lại cả cặp `.blend` và `.glb` tương ứng. Mở trang game để kiểm tra bản GLB vì camera và đèn render trong Blender có thiết lập riêng.

## Kiểm tra thay đổi và hiệu năng

- Repo hiện chưa có bộ test tự động. Chạy `node --check <tệp-js>` cho các tệp JS đã sửa và `git diff --check`. Mở trang chọn bản đồ và các entry point liên quan khi thay đường dẫn hoặc tài nguyên dùng chung.
- Với Khu B, thử vào game, di chuyển từ bảng khoa tới sân trong, qua lối gạch tới miếu và bấm E ở mặt thờ. Kiểm tra va chạm khi lên bậc hoặc áp sát bồn cây. Bật F, thử đứng yên, quay nhìn và đi bộ.
- Với Trung tâm, thử đi qua cổng, bậc sảnh và cửa, theo đường dọc qua khe lưới vào sân bóng. Với Khu E, thử đi dọc lối gạch từ đường vào sảnh khoa và từ sân xưởng vào nhà thể thao. Thử đổi điểm đứng và Esc để mở lại menu ở cả hai map.
- Khu B dùng tối đa 6 đèn sân gần người chơi. Bóng đèn pin chỉ được tạo khi bật đèn và cập nhật theo vị trí hoặc góc nhìn. Độ phân giải render có giới hạn riêng cho màn hình mật độ cao. Khi chỉnh chất lượng, đo trong cùng trình duyệt, cùng kích thước cửa sổ, cùng vị trí và thử cả lúc bật lẫn tắt đèn. `window.__demo` cho phép xem camera, trạng thái game và `renderer.info.render` trong DevTools.
- Trước khi commit, xem danh sách tệp đã stage. Các video tham chiếu lớn phục vụ dựng cảnh cục bộ. Bản chơi chỉ cần tài nguyên được trang và loader nạp. Viết commit tiếng Việt nêu rõ thay đổi.
