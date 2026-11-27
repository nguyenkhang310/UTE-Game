# Khu A · Kế hoạch từ demo Blender đến bản đi thử

**Mục tiêu của vòng này:** từ màn chọn bản đồ, người chơi vào Khu A, đi từ vỉa hè qua sân nhỏ tới sân cây dài, nghe một sự kiện âm thanh trên đường rồi đi ngược về điểm đầu. Nhóm có thể bắt đầu với tư liệu hiện tại. Kích thước khối chính khoảng 30 × 60 m, chiều cao tầng và chi tiết mặt đứng vẫn là ước lượng.

**Trước khi triển khai:** [cảnh Blender](khu-a-demo.blend) đã có ngoại cảnh và hai camera. [Script dựng Khu A](tools/build_zone_a.py) khi đó gom vật thể vào sáu Collection theo loại và dựng lại phần do script quản lý mỗi lần bấm **Run Script**. Repo đã có bộ điều khiển đi bộ ban ngày dùng chung cho Trung tâm và Khu E. Khu A khi đó mới có bản xem trong Blender.

**Trạng thái ngày 27/11/2026:** Khu A đã chơi được. Chạy `npm run dev` rồi mở [Khu A trên máy](http://localhost:8000/maps/khu-a/index.html). Các mốc dưới đây ghi lại phạm vi đã triển khai và cách nghiệm thu.

## 1. Tổ chức cảnh để bổ sung chi tiết an toàn

- [x] Dùng mã trên [sơ đồ Khu A](personal/khu-a/so-do-quy-uoc-demo-v1.png) trong Blender và khi ghi góp ý. Hướng trái/phải luôn tính từ đường phía Tòa nhà Trung tâm nhìn vào.

  | Mã | Vị trí | Mã | Vị trí |
  |---|---|---|---|
  | KA-01 | Đường, vỉa hè và cây vòng ngoài | KA-06 | Khối nối trước, phía sân nhỏ |
  | KA-02 | Nhà mái sáng sát đường | KA-07 | Dãy lớp học trái |
  | KA-03 | Nhà mái bạc đỏ bên trái | KA-08 | Sân cây dài giữa hai dãy |
  | KA-04 | Nhà mái đỏ bên phải | KA-09 | Dãy lớp học phải |
  | KA-05 | Sân nhỏ, mốc tròn và các mái che | KA-10 | Khối nối sau, cuối sân cây |

- [x] Mở bản sao của cảnh hiện tại. Đối chiếu với cảnh dựng mới từ script, tìm vật thể được thêm hoặc chỉnh tay và giữ lại các chỉnh sửa trước lần dựng lại đầu tiên. Với vật thể đã sửa trực tiếp, lưu một bản độc lập của hình học và vật liệu để so sánh.
- [x] Trong phần do script quản lý, chia nhà, cột, đường và cây theo mã khu. Đặt nền chung và mái xanh liền khối vào Collection dùng chung, giữ hai camera trong Collection góc xem. Tạo một Collection gốc riêng cho chi tiết chỉnh tay, với các Collection con theo mã khu. Nếu một chi tiết tay thay thế vật thể sinh tự động, ghi nhận vật thể cần bỏ khi dựng để tránh hai lớp trùng nhau.
- [x] Cập nhật phần dọn cảnh để xử lý được cả sáu Collection cũ và cấu trúc mới. Giữ thao tác quen thuộc trong Blender: **Scripting → Open → Run Script**. Khi có bản script mới, nạp lại file từ đĩa trước khi chạy.

**Đạt khi** chạy hai lần trên bản sao cho cùng số vật thể sinh tự động, vật mẫu đặt tay ở KA-05 vẫn giữ vị trí và vật liệu sau khi lưu rồi mở lại. Hai góc camera còn dùng được và có thể ẩn riêng từng khu trong Outliner.

## 2. Dựng tuyến đi bộ và xuất bản đồ

- [x] Đặt điểm đứng mặc định trên vỉa hè KA-01, nhìn về lối đi bên phải nhà mái sáng KA-02. Từ đây người chơi đi men hông nhà vào KA-05, qua mái che và khoảng trống dưới KA-06 rồi tới lối lát dọc bồn cây KA-08.
- [x] Gắn mốc nhìn cho **Vỉa hè**, **Sân nhỏ** và **Sân cây**. Dùng quy ước hiện có trong [helper dựng map](tools/campus_mesh.py) cho hướng nhìn, giới hạn đi bộ và cao độ. Dựng va chạm sát tường, cột và thân cây. Chừa khoảng đi dưới mái và khối nối tầng trên vì viewer xét va chạm theo mặt bằng.
- [x] Lưu cảnh đã kiểm tra vào `khu-a-demo.blend`. Xuất hình học demo, chi tiết tay dùng trong game và metadata sang `maps/khu-a/khu-a.glb` với glTF extras. Giữ camera và đèn phục vụ render ở bản Blender. Đối chiếu màu mái và nền lát trong trình duyệt vì vật liệu có node Noise của Blender có thể cần màu thay thế hoặc texture đã bake.

**Đạt khi** GLB nạp được bằng loader của repo, đủ ba mốc nhìn, giới hạn, va chạm và mặt sàn. Góc nhìn ban đầu hướng đúng lối đi. Hai dãy mái xanh, mốc tròn và hai mái đỏ vẫn nhận ra được sau khi xuất.

## 3. Đưa Khu A vào game và đi thử

- [x] Tạo trang `maps/khu-a/index.html` theo [trang Khu E](maps/khu-e/index.html), dùng lại viewer và CSS ban ngày. Khớp `data-model`, `data-start-view` và ba nút chọn điểm đứng với các mốc trong GLB. Thêm thẻ **Khu A** cùng ảnh render tổng thể vào [màn chọn bản đồ](maps/index.html).
- [x] Từ gốc repo, chạy `npm run dev` rồi mở `http://localhost:8000/maps/index.html`. Vào Khu A bằng thẻ bản đồ, bấm **Đi bộ** và đi trọn tuyến ở mốc 2 theo cả hai chiều. Thử đi thường, giữ Shift chạy và áp sát góc tường, cột, bồn cây.
- [x] Thử từng điểm đứng, nhấn Esc mở menu, tiếp tục đi rồi quay lại màn chọn bản đồ. Ghi lỗi bằng mã khu, hướng di chuyển và ảnh màn hình, chẳng hạn “KA-06, từ sân nhỏ vào sân dài, mắc ở cột bên phải”.

**Đạt khi** hoàn thành tuyến từ vỉa hè và quay về bằng bàn phím, đi qua được dưới khối nối, không xuyên tường hoặc rơi khỏi sàn. Ba điểm đứng hoạt động và trình duyệt tải đủ mô hình, ảnh, JS và CSS.

## 4. Thử một sự kiện kinh dị trên tuyến đã đi thông

- [x] Giữ cảnh ban ngày cho lần thử đầu để đánh giá riêng tác dụng của âm thanh. Sau khi người chơi bấm **Đi bộ**, phát nền tiếng côn trùng nhẹ ở sân nhỏ. Khi đi từ KA-05 vào vùng dưới mái che gần KA-06, hạ âm nền dần và phát một tiếng bước chân từ phía hành lang tầng trên.
- [x] Đặt mốc nguồn âm và vùng kích hoạt trong cảnh Khu A để chúng đi cùng vị trí mái che khi sửa map. Sự kiện kích hoạt một lần mỗi lượt tải trang. Tạm dừng âm khi mở menu, tiếp tục âm nền khi trở lại. Chức năng đi bộ vẫn dùng được khi trình duyệt chặn âm.
- [x] Đi qua vị trí đó hai lần, dừng giữa vùng kích hoạt, mở menu rồi tiếp tục và thử tải lại trang. Kiểm tra Trung tâm và Khu E vẫn chọn điểm đứng và đi bộ được sau các thay đổi ở viewer dùng chung.

**Đạt khi** lần đi vào đầu tiên nghe được bước chân đúng hướng, đứng yên hoặc quay lại không làm âm thanh phát chồng. Cả tuyến vẫn đi được khi tắt tiếng.

## 5. Ghi kết quả trước khi nhận thêm tư liệu

- [x] Lưu ảnh đối chiếu từ trên cao và ngang tầm mắt. Ghi theo mã khu những điểm cần xác minh ngoài thực tế, ưu tiên bề rộng lối quanh KA-02, vị trí mái che KA-05, khoảng trống qua KA-06 và cao độ sân KA-08.
- Quy ước cho vòng sau: khi có ảnh mới, đặt tên theo mẫu `KA-05_tu-moc-tron_nhin-ve-day-lop.jpg`. Với mỗi lần sửa, đối chiếu góc ảnh trong Blender, xuất lại GLB và đi lại đoạn chịu ảnh hưởng.
- [x] Cập nhật hướng dẫn chạy Khu A trong [AGENTS.md](AGENTS.md). Chạy `node --check` cho các file JavaScript đã sửa và `git diff --check`. Ghi kết quả đi thử, lỗi còn mở và kích thước GLB để nhóm so sánh ở vòng sau.


## Kết quả đi thử ngày 27/11/2026

- **Blender 5.3.** So sánh bản lưu cũ với cảnh dựng từ script cũ cho cùng danh sách vật thể, hình học, vị trí và vật liệu. Trên bản sao, chạy script mới hai lần cho cùng 761 vật thể tự động. Vật mẫu ở Collection tay KA-05 giữ được vị trí và vật liệu sau khi mở lại. Đã xuất thử một vật thay thế bằng `ka_replaces` và kiểm tra GLB chỉ chứa bản thay thế.
- **Bản web.** [GLB Khu A](maps/khu-a/khu-a.glb) nặng 869.816 byte, có ba điểm đứng, 101 vùng va chạm, 13 mặt sàn và giới hạn di chuyển. Đã mở GLB bằng Three.js để đối chiếu hai dãy mái, hai khối đỏ và sân nhỏ với [góc trên cao](maps/khu-a/preview-tren-cao.jpg) và [góc mặt đất](maps/khu-a/preview-mat-dat.jpg).
- **Tuyến chính.** Từ thẻ Khu A, thử cả ba điểm đứng. Dùng WASD và Shift từ KA-01 vòng hông phải KA-02, qua KA-05, dưới KA-06, đi tới lối cạnh bồn cây KA-08 rồi quay về vỉa hè. Tường KA-02, chân cột mái che KA-05 và bồn cây KA-08 đều chặn người chơi. Esc về menu, tiếp tục và trở lại màn chọn map đều hoạt động.
- **Âm thanh và tương thích.** Kiểm tra trên Chrome cho thấy bộ phát bước chân kích hoạt ở cả lối mái che trái và phải trong hai lượt thử riêng. Trong cùng lượt, đổi điểm đứng và đi vào lần nữa vẫn chỉ có một lần phát. Tải lại trang khởi tạo lượt mới. Chặn Web Audio vẫn đi được. Trung tâm và Khu E tải, đổi điểm đứng, đi bộ và trở về menu được. Đã kiểm tra cú pháp JavaScript và `git diff --check`.
- **Đối chiếu ở trường trong vòng sau.** KA-02 cần kích thước lối hông. KA-05 cần ảnh chân cột và hướng mái che. KA-06 cần chiều rộng thông thủy. KA-08 cần độ cao bồn cây và bề rộng lối lát. Nhóm có thể nghe thử bằng tai nghe để góp ý âm lượng bước chân so với tiếng côn trùng.
