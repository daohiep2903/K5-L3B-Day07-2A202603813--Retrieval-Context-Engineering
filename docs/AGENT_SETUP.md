# Agent OpenAI: cấu hình và chạy demo

## Cấu hình riêng

File `.env` ở root Day 7 chứa `OPENAI_API_KEY`; file được Git bỏ qua. Không đưa key vào code, trace, báo cáo hoặc nội dung chat. `.env.example` chỉ chứa tên biến và giá trị mặc định không có secret.

Model mặc định ghim phiên bản `gpt-4.1-mini-2025-04-14`, dùng Chat Completions và function calling. Thông số lấy từ tài liệu chính thức: https://developers.openai.com/api/docs/models/gpt-4.1-mini và https://developers.openai.com/api/docs/guides/function-calling . Trang model hiện đánh dấu deprecated; nếu tài khoản không còn truy cập được, chọn model thay thế trước khi chạy thí nghiệm so sánh, ghi phiên bản và kiểm tra tương thích. Không âm thầm đổi model giữa cấu hình.

Các biến tùy chọn: `AGENT_TIMEOUT_SECONDS`, `AGENT_INPUT_USD_PER_MILLION`, `AGENT_OUTPUT_USD_PER_MILLION`. Nếu chưa điền đơn giá, trace ghi chi phí chưa tính, không ghi 0. Nếu có đơn giá thì ước tính từ usage; chưa trừ chiết khấu cache. Token thực tế do API trả về được lưu.

## Luồng thực hiện

`src/openai_controller.py` gửi câu hỏi, filter do người dùng cung cấp và context mới nhất cho model. Model gọi function `search` hoặc `finish`; function call đầu được yêu cầu là search. Kết quả quyết định được chuẩn hóa theo giao diện Controller của starter.

Runner dùng `starter/agentic.py` để thực thi retrieval, tích lũy chunk, bỏ ID trùng và đóng gói context. Mỗi lần quyết định model nhận context tích lũy mới nhất trong một request độc lập, không phát lại một chuỗi tool message dài không giới hạn. Gold, đáp án dự kiến và nhãn có/thiếu evidence không được gửi model. Tài liệu được coi là dữ liệu, không phải chỉ dẫn.

Mặc định demo: hybrid, top-k 6, budget 3.000 ký tự, tối đa 2 lượt search. Model có thể kết thúc với đáp án và citation `[chunk-id]`, hoặc từ chối. Code kiểm tra ID citation nằm trong context và có trong answer; kiểm tra này chưa chứng minh nguồn hỗ trợ ngữ nghĩa, cần đọc đánh giá sau đó.

Lỗi API, quota, model hoặc retrieval được ghi riêng, không thay bằng kết quả giả. Request dùng `store: false`; API vẫn nhận câu hỏi và context RFC theo cấu hình dịch vụ của nhà cung cấp.

## Chạy một câu demo thật

Từ root Day 7, dùng Python đã cài model embedding và Qdrant:

```powershell
$env:PYTHONUTF8='1'
& "<Day6>/starter/.venv/Scripts/python.exe" scripts/run_agent_demo.py --model-path "<Day6>/local_models/all-MiniLM-L6-v2"
```

Có thể thêm `--query`, `--method dense|lexical|hybrid`, `--top-k`, `--budget`, `--max-searches`, `--section`. Không cần cài SDK OpenAI riêng: HTTP request dùng thư viện chuẩn Python.

Kết quả thành công lưu `results/agent_demo/trace.json`: tool call của model, query tìm kiếm, ranking, context thực tế, answer, citation, usage và thời gian. Nếu lỗi, xem `results/agent_demo/error.json`. Chạy lại có thể ghi đè file demo cùng tên.

Đây là một câu phát triển đã thấy, không phải benchmark test độc lập. Chưa dùng kết quả demo để công bố chất lượng agent toàn bộ. Bước tiếp theo là chạy và đánh giá các cấu hình trên dev, sau đó mới chốt baseline/cấu hình chọn để đánh giá test.
## Citation ngắn và các lần thử demo

Để tránh model chép sai ID hash 64 ký tự, runtime dùng alias `C001`… có bảng ánh xạ về ID chunk gốc. `src/citation_aliases.py` chỉ đổi nhãn trong context gửi model; nội dung, nguồn, vị trí và ID trong corpus/Qdrant không đổi. Trace chứa `original_chunk_id` và bảng `citation_aliases` để truy ngược. Khi đánh giá citation phải kiểm tra cả alias trong context và nội dung nguồn hỗ trợ câu trả lời.

Hai lần demo đầu đã bị code từ chối: lần 1 gộp nhiều ID trong một cặp ngoặc; lần 2 chép sai ký tự ID dài. Các trace được giữ tại `attempt_01_invalid_citation.json` và `attempt_02_mistyped_long_id.json`; không ghi chúng thành đáp án đúng. Đây là sửa lỗi trong phát triển trước benchmark agent, không chỉnh theo test.

Header alias ngắn hơn header ID gốc nên cùng budget ký tự có thể giữ được nhiều text hơn. Không lấy nguyên điểm context đã chuẩn bị ở bước retrieval làm điểm context cuối của agent; cần tính lại từ context thực sự gửi model trong từng trace.