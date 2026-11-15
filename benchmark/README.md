# Benchmark Day 7 — RFC 6749

## Phạm vi và phân chia

Corpus: IETF RFC 6749 mục 2–7, 116 chunk cấu hình B từ Day 6. `page` là đơn vị nguồn, không phải trang vật lý RFC. Có AI hỗ trợ soạn và đối chiếu nhãn; học viên cần duyệt trước khi nộp.

| Loại | Dev | Test | Tổng |
|---|---:|---:|---:|
| Có đáp án | 15 | 5 | 20 |
| Thiếu bằng chứng | 2 | 2 | 4 |
| Tổng | 17 | 7 | 24 |

15 câu dev có đáp án kế thừa bộ dev Day 6, đã rà soát gold theo ngữ cảnh. Bỏ alternative sai phạm vi của q05/q06; q08 chỉ giữ câu hoàn chỉnh về khuyến nghị thời hạn authorization code. Các câu test có đáp án được soạn mới, không sao chép 5 câu test cũ. Test mới vẫn cùng một tài liệu và chia sẻ chủ đề với nội dung đã biết; người soạn đã thấy nhãn nên không coi là đánh giá mù trên dữ liệu ngoài.

Bốn câu thiếu bằng chứng hỏi về yêu cầu PKCE, thuật toán ký JWT, DPoP và thời hạn refresh token cố định. Chỉ kết luận thiếu trong corpus mục 2–7 đã chọn, không khẳng định cả hệ sinh thái OAuth không có thông tin đó. `absence_review.json` ghi cách đọc kiểm tra và tìm từ khóa trên toàn corpus. Không dùng việc top-k tìm không ra để khẳng định không có đáp án. Không nhầm thời hạn authorization code hoặc ví dụ expires_in của access token thành thời hạn refresh token.

## Các file

- `questions.json`: bộ nhãn đầy đủ; mỗi câu có `answerable`, đáp án/hành vi mong đợi, gold hoặc lý do thiếu bằng chứng.
- `cases.json`: ID, split, loại câu, câu hỏi và hành vi mong đợi để nối với script tổng hợp agent metrics. Đây vẫn là file nhãn đánh giá, không truyền nguyên object cho model.
- `absence_review.json`: cơ sở đánh giá 4 câu thiếu evidence.
- `validation.json`: số lượng, hash bộ câu hỏi và kết quả kiểm chứng nguồn/chunk/filter. Không phải điểm retrieval.

Gold là các evidence thay thế, không phải tập evidence bắt buộc kết hợp nhiều đoạn. Mỗi evidence khớp nguồn và nằm trọn trong chunk đúng đơn vị. Các câu nêu mục 2/3 có filter `top_level_section` tương ứng; phạm vi được lấy từ chính câu hỏi, không từ gold. Bộ này chưa đánh giá multi-hop.

## Chạy lại kiểm chứng

Từ root Day 7, thay đường dẫn Day 6:

```powershell
$env:PYTHONUTF8='1'
python scripts/prepare_day7_benchmark.py --day6 "<đường-dẫn-Day6>"
```

Script không truy vấn vector store hoặc model; không ghi đè bộ benchmark đã bị sửa khác. Khi cần sửa nhãn sau thí nghiệm, tạo phiên bản và công bố tác động, không âm thầm thay nhãn gốc.

## Quy tắc chạy thí nghiệm tiếp theo

Chỉ đưa `question` và filter nếu có cho agent/tool. Không đưa `gold`, `expected_answer`, `answerable`, `absence_reason`, `expected_behavior`, evidence hoặc offset chuẩn vào query/context chạy thật. Chọn các cấu hình trên dev; chốt cấu hình và tiêu chí trước khi chạy baseline/cấu hình chọn trên test. Không dùng 4 câu thiếu evidence vào mẫu số Hit@1, Hit@3 hoặc Context Evidence Rate.

Bước hiện tại chỉ chuẩn bị và kiểm chứng dữ liệu: chưa chạy retrieval trên benchmark, chưa tạo câu trả lời agent hoặc điểm benchmark. Hai query kiểm tra kết nối trước đó là query phát triển đã thấy, không được coi là test độc lập.

Nguồn trích đoạn: IETF RFC 6749, D. Hardt (Ed.), October 2012, https://www.rfc-editor.org/rfc/rfc6749.txt . Khi chia sẻ bộ này, giữ `data/RFC6749_NOTICES.txt` và điều kiện tại `data/RIGHTS_REVIEW.md` đi kèm.