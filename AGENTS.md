# UTE Game

Game khám phá góc nhìn thứ nhất mô phỏng khuôn viên HCMUTE. Khu B là cảnh ban đêm có đèn pin, giọng thì thầm và tương tác ở miếu. Tòa nhà Trung tâm và Khu E là hai bản đồ ban ngày.

## Chạy và tìm đúng bản đồ

- Chạy `npm run dev` từ gốc repo. Máy chủ Node phục vụ tệp tĩnh trên cổng `8000` mặc định. Dùng `PORT=8010 npm run dev` để chạy phiên kiểm tra riêng khi cổng chính đang được dùng.
- Các bản đồ dùng mô-đun ES và Three.js 0.169 được lưu sẵn ở `vendor/three/`. Các trang nạp thư viện qua import map. Có thể chạy game từ bản clone bằng Node và trình duyệt hỗ trợ WebGL2 mà không cần cài package hay mở Blender.

| Đường dẫn | Mã chạy | Tài nguyên chính |
| --- | --- | --- |
| `/` | `index.html`, `src/main.js`, `styles/main.css` | `assets/khu-b-courtyard.glb`, `mieu-tho-audio.wav` |
| `/maps/index.html` | Trang chọn bản đồ và giao diện chung trong `maps/maps.css` | Ảnh xem trước từng map |
| `/maps/trung-tam/index.html` | `maps/trung-tam/viewer.js` và `viewer.css` | `maps/trung-tam/trung-tam.glb` |
| `/maps/khu-e/index.html` | Dùng chung viewer ban ngày trong `maps/trung-tam/` | `maps/khu-e/khu-e.glb` |

Dùng URL có `index.html` cho các trang trong `/maps/` vì máy chủ chỉ tự mở `index.html` cho đường dẫn `/`.

## Khu B

- `src/config.js` giữ điểm vào, giới hạn chơi, vị trí miếu, tốc độ, thông số đèn pin và ngân sách render. `src/main.js` khởi tạo game, gắn bàn phím và cập nhật mỗi khung hình.
- `src/world/worldLoader.js` đọc GLB, va chạm, cao độ, mốc đèn và hướng mặt thờ. `src/player/player.js` xử lý di chuyển, khóa chuột, bậc thềm và vòng lặp khi đi quá giới hạn.
- `src/world/shrine.js` điều khiển lửa, khói, lời thì thầm và bóng lướt qua. `src/audio/audio.js` và `src/ui/hud.js` xử lý âm thanh và giao diện nhắc tương tác.
- Bấm nút vào game, dùng WASD và chuột để đi, Shift để chạy, F để bật hoặc tắt đèn, E để thắp nhang khi có lời nhắc. Alt hoặc Esc nhả chuột.

### Mốc bố trí cần đối chiếu

- Từ điểm vào, bảng **Khoa Hóa học và Khoa học Sự sống** ở bên trái. Rẽ phải theo lối gạch rồi đi dưới cầu nối để vào sân trong có bồn cong, ghế đá và chữ **B**. Cầu thang ngoài nằm bên phải cầu nối. Giữ đường đi bên phải thông thoáng quanh cây, ghế và chân cầu thang.
- Khối B có mặt bằng chữ H, khối C chạy song song. Vườn miếu nằm giữa khối C và D, phía trái thư viện trên sơ đồ. Bãi xe máy nằm cạnh lối gạch phía vườn.
- Miếu lấy từ `hcmute-khu-b.glb`, nhận diện bằng tiền tố node `tripo_node_9f7`. Tâm miếu trong Three.js là `(-34.4, 0.03, 34.65)`. Mặt thờ quay về khe mở của hàng rào, tức hướng Z âm trong game. Đèn và khói nhang theo hướng node, nên khi xoay hoặc dời miếu hãy kiểm tra cả góc nhìn và tương tác E.
- Tư liệu tham chiếu nếu có ở máy là `src về trường/IMG_4185.MOV` và `src về trường/IMG_4187.MOV`. Đầu video 4185 có bảng khoa và bậc lên hành lang. Khoảng 1:30–2:00 của video 4187 nối bậc khoa, cầu nối và đường vào sân. Khoảng cách trong mô hình được ước lượng từ ảnh, video và sơ đồ.

## Tòa nhà Trung tâm

- `maps/trung-tam/viewer.js` quản lý di chuyển, chiếu sáng và kiểm tra va chạm cho hai map ban ngày. Từng trang chọn GLB và điểm vào qua `data-model` và `data-start-view`. Các điểm vào được lấy từ mốc trong GLB. Chọn điểm đứng, bấm **Đi bộ**, rồi dùng WASD hoặc phím mũi tên, Shift và Esc.
- Khi nhìn chính diện tòa nhà, sân bóng nằm bên phải, qua đường dọc. Có thể đi qua khe lưới ở cạnh giáp tòa nhà hoặc chọn **Sân bóng** để vào thẳng sân. Đường bên trái uốn quanh vườn và gặp đường ngang phía trước.
- Bóng nắng cập nhật khi chuyển vùng. Cảnh vẽ lại khi người chơi di chuyển, đổi góc nhìn, chọn điểm đứng hoặc đổi kích thước cửa sổ. Khi sửa render của một map, kiểm tra entry point của map đó trước.

## Khu E

- Đường nội bộ chạy dọc mép trước vườn. Lối gạch nhiều màu đưa từ đường qua vườn tới Khoa Cơ khí Chế tạo máy. Khoa có hai cánh xanh xám ốp gạch cam, lam trắng ở sảnh lõm và mái đón xanh. Có thể đi lên tam cấp và vào sảnh giữa.
- Nhà thể thao mái vòm xanh mint đứng bên trái khoa, lối vào mở ra sân xưởng. Bên trong có sân tennis và sân bóng chuyền, lưới chia ở giữa và lối đi vòng ở đầu sân.

## Chỉnh cảnh và xuất từ Blender

| Bản đồ | Script nguồn | Kết quả |
| --- | --- | --- |
| Khu B | `tools/build_courtyard.py` | `khu-b-mo-rong.blend`, `assets/khu-b-courtyard.glb` |
| Trung tâm | `tools/build_central_campus.py`, `tools/campus_pitch.py` | `toa-nha-trung-tam.blend`, `maps/trung-tam/trung-tam.glb` |
| Khu E | `tools/build_zone_e.py` | `khu-e.blend`, `maps/khu-e/khu-e.glb` |

Hai builder ban ngày dùng chung các helper hình học và vật liệu trong `tools/campus_mesh.py`.

Dùng Blender nền để dựng lại cảnh khi thay đổi hình học. Các script dùng `bpy` và `numpy` trong Blender. Dự án đã được dựng bằng Blender 5.3. Trên macOS, nếu lệnh `blender` chưa có trên PATH, dùng `/Applications/Blender.app/Contents/MacOS/Blender`. Builder Trung tâm hiện đọc font từ `/System/Library/Fonts/Supplemental` và dùng ảnh phù hiệu trong `maps/trung-tam/`. Khi chạy trên hệ điều hành khác, kiểm tra lại đường dẫn font.

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
