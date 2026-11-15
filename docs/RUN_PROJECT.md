# Hướng dẫn tái lập Day 7

## 1. Điều kiện và môi trường

Lần chạy đã ghi sử dụng Windows, PowerShell và Python 3.12.2 (đề yêu cầu Python 3.11+). Model embedding và Qdrant local từ Day 6 là đầu vào của Day 7. Các đường dẫn `<Day6>` bên dưới phải thay bằng thư mục Day 6 thực tế.

Repo Day 6: https://github.com/daohiep2903/K5-L3-Day06-2A202603813-DataIngestionEngineering . Cần có model local đã ghim commit ở `<Day6>/local_models/all-MiniLM-L6-v2` và store `<Day6>/local_vectors` chứa collection `day6_B`. Nếu chưa có hai tài nguyên local, làm theo `<Day6>/starter/RUN_CORPUS.md`, tải model bằng `<Day6>/scripts/download_model.py` và dựng vector bằng pipeline Day 6 với model đã ghim. Không dùng vector ngẫu nhiên để thay thế. Corpus và manifest nhỏ của Day 7 đã có trong `data/` để đối chiếu.

Tạo môi trường riêng từ root Day 7:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Nếu cần đúng toàn bộ phiên bản môi trường đã chạy, dùng `results/dependencies.txt` thay cho danh sách tối thiểu; các wheel phụ thuộc hệ điều hành. Các kiểm tra hash dùng byte tệp của snapshot đã ghi. Thay đổi nội dung hoặc kiểu xuống dòng có thể làm hash khác; không bỏ qua guard để âm thầm chạy test bằng code/benchmark khác. Môi trường đã kiểm chứng là Windows nêu trên, chưa xác nhận tái lập byte-for-byte trên mọi hệ điều hành.

## 2. Cấu hình API riêng

Sao chép `.env.example` thành `.env` nếu chưa có, điền `OPENAI_API_KEY` trực tiếp trên máy; không gửi hoặc commit key. Dùng cùng `AGENT_MODEL=gpt-4.1-mini-2025-04-14` cho mọi cấu hình so sánh. Nếu tài khoản không có quyền model đó, cần chuẩn bị một thí nghiệm mới có model/phiên bản rõ ràng trước khi đo; không âm thầm thay model của kết quả đã lưu.

Các runner benchmark dùng đơn giá ước tính đã ghi trong plan để tính từ usage, không phải hóa đơn. Chạy API phát sinh phí. Có thể dùng Python trong `<Day6>/starter/.venv/Scripts/python.exe` nếu đã cài đúng thư viện, như các lần đã thực hiện.

## 3. Nhập corpus và kết nối vector

```powershell
$env:PYTHONUTF8='1'
.\.venv\Scripts\python.exe scripts/import_day6.py --day6 "<Day6>"
.\.venv\Scripts\python.exe scripts/connect_day6.py --day6 "<Day6>"
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Script nhập từ chối ghi đè corpus đã sửa khác. Script kết nối kiểm tra model và payload, sao chép vector thật sang store Day 7 độc lập, kiểm tra filter và mở lại dữ liệu. Đóng tiến trình khác đang dùng Qdrant local trước khi chạy. Model/cache và vector local được Git bỏ qua; dữ liệu, cấu hình và cách tái tạo được nộp thay cho tài nguyên lớn.

Benchmark đầy đủ đã có tại `benchmark/questions.json`. Script `scripts/prepare_day7_benchmark.py --day6 "<Day6>"` chỉ để tái tạo/kiểm chứng nhãn theo nguồn; không chạy retrieval. Không ghi đè các nhãn đã được học viên sửa sau chấm bằng script tạo nhãn ban đầu.

## 4. Retrieval và agent dev

```powershell
.\.venv\Scripts\python.exe scripts/run_retrieval_dev.py --model-path "<Day6>/local_models/all-MiniLM-L6-v2"
.\.venv\Scripts\python.exe scripts/run_agent_dev.py --model-path "<Day6>/local_models/all-MiniLM-L6-v2" --max-cost-usd 1
.\.venv\Scripts\python.exe scripts/run_agent_dev_formatted.py --model-path "<Day6>/local_models/all-MiniLM-L6-v2" --max-cost-usd 0.2
.\.venv\Scripts\python.exe scripts/check_agent_dev.py
.\.venv\Scripts\python.exe scripts/check_agent_dev.py --directory agent_dev_formatted
```

Retrieval-only ghi đè output cùng tên; giữ phiên bản thí nghiệm nếu chạy lại. Runner agent checkpoint từng câu, resume chỉ bỏ qua các trace có cùng identity. Nhãn dev đã được học viên duyệt, nên các script review dev được chặn không ghi đè. Nhãn và lịch sử đã nộp có thể được kiểm tra trực tiếp; thí nghiệm/nhãn mới cần lưu thư mục phiên bản riêng.

## 5. Chốt cấu hình và chạy test

`results/dev_selection.json` là hồ sơ chốt và hash trước khi đánh giá test. Runner kiểm tra code, corpus, benchmark và model phải khớp. Test hiện đã chạy xong; lệnh sau resume sẽ dùng trace đã có, không tự tạo một lượt đánh giá độc lập mới:

```powershell
.\.venv\Scripts\python.exe scripts/run_agent_test.py --model-path "<Day6>/local_models/all-MiniLM-L6-v2" --max-cost-usd 0.2
```

14 trace và nhãn từng câu ở `results/agent_test/`. Hai câu thiếu evidence không vào mẫu số retrieval/context. Citation và nội dung đã được đọc đối chiếu; nhãn test đã được học viên duyệt ngày 15/11/2026. `scripts/review_agent_test.py` mã hóa các quyết định đã đọc từ chính trace hiện tại, không phải bộ chấm ngữ nghĩa tự động cho đầu ra mới. Không dùng để tự gán nhãn cho thí nghiệm có câu trả lời khác. Các script review dev cũng có giới hạn tương tự.

Nếu muốn chạy lại API trên toàn test, cần lưu thành lần chạy/phiên bản riêng và công bố rõ test đã được xem. Không sửa cấu hình theo test rồi gọi kết quả sau đó là holdout độc lập.

## 6. Hồ sơ đã có

- Báo cáo theo mẫu: `report/individual/2A202603813_DaoVanHiep.md`.
- Nhật ký thực nghiệm: `artifacts/experiment_log.csv`.
- Kết quả retrieval: `results/retrieval_dev/`.
- Kết quả agent dev: `results/agent_dev/`, `results/agent_dev_formatted/`, `results/agent_dev_comparison.json`.
- Kết quả test: `results/agent_test/`, `results/test_execution.json`.
- Hướng dẫn từng bước và phân tích: `docs/DENSE_SETUP.md`, `docs/RETRIEVAL_DEV.md`, `docs/AGENT_SETUP.md`, `docs/AGENT_DEV.md`, `docs/AGENT_TEST.md`.

Trước khi nộp: giữ xác nhận nhãn test, rà soát báo cáo, commit/push phần được phép chia sẻ, điền mã commit trong `STUDENT.md`, kiểm tra quyền truy cập repo và nộp link theo lớp. Giữ thông báo nguồn RFC cùng các trích đoạn; không nộp `.env`, API key, môi trường Python hoặc cache/model/store local.