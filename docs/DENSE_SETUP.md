# Kết nối dense retrieval với Day 6

Đã sử dụng embedding thật và Qdrant lưu bền vững, không dùng vector giả. Đây là kiểm tra kết nối, chưa phải benchmark Day 7 hay agent LLM.

## Thành phần

- Adapter: `src/dense.py`, đúng giao diện `Retriever.search` trong `starter/agentic.py`.
- Model: `sentence-transformers/all-MiniLM-L6-v2`, commit `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`, 384 chiều.
- Nguồn vector: collection `day6_B` đã có từ Day 6.
- Store Day 7: `local_vectors/`, collection `day7_dense`, tìm kiếm cosine exact ở Qdrant local.
- Dùng lại trọng số model local trong Day 6; không gọi API hoặc tải model khi chạy bước này.

## Chạy lại

Từ thư mục gốc Day 7, dùng Python đã cài thư viện của Day 6, thay hai đường dẫn bên dưới:

```powershell
& "<Day6>/starter/.venv/Scripts/python.exe" scripts/connect_day6.py --day6 "<Day6>"
```

Hoặc tạo môi trường Day 7, cài `requirements.txt`, rồi chạy script bằng Python đó. Đóng các tiến trình đang dùng Qdrant Day 6 trước khi chạy vì store local chỉ cho một tiến trình mở cùng lúc.

Script đối chiếu hash model, cấu hình collection, toàn bộ text/metadata của 116 chunk và nguồn đã nhập. Vector được sao chép sang store riêng Day 7, không tính lại embedding tài liệu và không upsert/xóa collection Day 6. Kiểm tra vector dùng dung sai 1e-6 vì Qdrant có thể chuẩn hóa lại float khi ghi; sai số quan sát thực tế lưu trong JSON kết quả.

Sau đó script tạo embedding cho hai query kiểm tra, tìm top-3, thử filter mục 6, đối chiếu text với offset nguồn và mở lại store để xác nhận dữ liệu còn đủ. Kết quả: `results/dense_connection_check.json`. Lỗi kiểm tra float ban đầu và cách xử lý được ghi trong `results/connection_errors.json`.

Hai query đã được dùng kiểm tra nên không dùng làm câu test độc lập về sau. Kết quả không chứng minh độ chính xác câu trả lời, grounding hoặc citation của agent. Bước tiếp theo là chuẩn bị benchmark Day 7 trước khi thử ba phương pháp retrieval và nối model agent thật.

Nguồn text: IETF RFC 6749, D. Hardt (Ed.), October 2012. Khi chia sẻ trace cần giữ `RFC6749_NOTICES.txt` và điều kiện ở `data/RIGHTS_REVIEW.md`. `page` là số đơn vị nguồn, không phải trang RFC gốc.