# Kết quả agent trên dev

## Phạm vi thực nghiệm

Model thật: `gpt-4.1-mini-2025-04-14`. Dùng cùng corpus 116 chunk, embedding và Qdrant từ bước trước. Mỗi cấu hình chạy 17 câu dev, tối đa 2 lượt search. Không chạy 7 câu test. Học viên Đào Văn Hiệp đã duyệt toàn bộ nhãn dev ngày 15/11/2026. Phương pháp ban đầu có AI hỗ trợ; lịch sử và xác nhận được giữ tại `results/student_dev_review_confirmation.json` và `results/review_history/`.

Đầu tiên chạy 5 cấu hình theo ma trận retrieval đã có: dense, lexical, hybrid, dense budget 3.000 và hybrid top-6/budget 3.000. Sau khi đọc lỗi dev, thử thêm cấu hình hybrid có formatter citation. Tổng cộng **102 trace thật**, không dùng mock để báo chất lượng.

Formatter chỉ gắn `[Cxxx]` từ danh sách nguồn mà model đã khai báo, sau khi kiểm tra ID có trong context. Không tạo nguồn mới, không sửa nội dung câu trả lời và không tự xác minh ngữ nghĩa. Phản hồi model trước formatter được giữ trong trace. Cấu hình bổ sung được chạy mới qua API trên cùng 17 câu dev, không thay thế hoặc sửa 85 kết quả trước.

## Bảng so sánh

Thang câu trả lời: 0 sai/thiếu bằng chứng hoặc từ chối câu có đáp án; 1 đúng một phần; 2 đúng và đủ. Trung bình tính trên 15 câu có đáp án. Hai câu thiếu evidence được chấm từ chối riêng.

| Cấu hình | Số câu mức 0/1/2 | TB /2 | Citation hỗ trợ | Từ chối đúng | Từ chối nhầm |
|---|---|---:|---:|---:|---:|
| Dense baseline | 14 / 1 / 0 | 0,067 | 0/2 | 2/2 | 13/15 |
| Lexical baseline | 14 / 1 / 0 | 0,067 | 0/1 | 2/2 | 14/15 |
| Hybrid baseline | 15 / 0 / 0 | 0,000 | 0/1 | 2/2 | 14/15 |
| Dense budget 3.000 | 14 / 0 / 1 | 0,133 | 2/2 | 2/2 | 14/15 |
| Hybrid top-6/budget 3.000 | 11 / 1 / 3 | 0,467 | 4/4 | 2/2 | 11/15 |
| Hybrid top-6/budget 3.000 + formatter | 1 / 2 / 12 | 1,733 | 15/17 | 2/2 | 0/15 |

Tất cả 17/17 câu ở mỗi cấu hình có gọi retrieval tool; không có lỗi provider trong các lần chạy này. Phân bố số lượt gọi, thời gian, token và chi phí nằm ở `results/agent_dev_comparison.json`.

Citation được đọc đối chiếu từng nguồn và phần khẳng định liên quan, không chỉ xét ID. Một nguồn hỗ trợ một phần đáp án không chứng minh mọi câu bổ sung đều đúng. Vì vậy vẫn có câu mức 1 dù citation chính hỗ trợ được ý chính. Không dùng tỷ lệ citation để thay thế điểm câu trả lời.

Tổng chi phí API ước tính của bước này: **0,0593828 USD**, chưa trừ giảm giá cache, chưa tính máy local; không phải hóa đơn. Lấy đơn giá chuẩn đã đối chiếu ngày 14/11/2026, token từ API. Các lần demo trước không cộng trong con số này.

## Context thực tế và query gốc

Đã kiểm tra context trong trace khớp context ở request cuối thực sự gửi model. Cấu hình formatter có 13/15 câu khớp trọn gold quote trong context. Khi đọc evidence tương đương, q09 được hỗ trợ bởi C091/mục 4.2 thay vì quote gold ở 4.2.2: tỷ lệ context đủ evidence theo nhận xét AI là **14/15**. q05 còn sai phạm vi nguồn. Xem `results/agent_dev_formatted/context_review_summary.json`.

Agent có viết lại query tìm kiếm; không trộn ranking của query viết lại với ranking query gốc. Số liệu query gốc giữ tại `results/retrieval_dev/`; trace agent lưu từng query thực tế. Bảng tổng hợp tách `original_query_hit1/hit3` với `agent_first_search_hit1/hit3`. Các metric Hit dùng cùng cutoff 1 và 3 dù cấu hình lấy 6 chunk.

## Hai lỗi dev và kết quả trước/sau

1. **Lỗi định dạng citation — d7-dev-q03:** ở lượt hybrid top-6 ban đầu, model có thể đưa đáp án và danh sách ID nguồn nhưng thiếu `[ID]` trong thân answer. Starter từ chối nên điểm đầu ra là 0. Formatter kiểm tra nguồn rồi hiển thị citation đã khai báo; lần chạy bổ sung trả HTTP Basic và trích C048 đúng, đạt 2. Đây là thay đổi hiển thị có thể kiểm chứng, không biến citation sai thành đúng.
2. **Lỗi điều kiện xác thực — d7-dev-q02:** dense baseline trả rằng không có giới hạn rõ ràng, dựa vào C090 nói phương thức xác thực khác; nguồn này không chứa quy định số phương thức. Cấu hình chọn đưa C059 vào context và trả đúng MUST NOT dùng nhiều hơn một phương thức trong mỗi request, đạt 2. Sửa budget/retrieval không tự đảm bảo câu trả lời đúng; cần chấm câu trả lời thật.

Kết quả trên là các lượt phát sinh thực tế, không đảm bảo API trả giống nhau tuyệt đối dù cùng snapshot và temperature 0. So sánh baseline với gói cấu hình chọn đổi nhiều yếu tố (retrieval, budget, formatter), không quy toàn bộ cải thiện cho một yếu tố riêng lẻ.

## Lỗi còn lại trong cấu hình chọn

- **q01, mức 1:** trả đúng identifier không bí mật/không dùng một mình, nhưng khái quát quá rộng yêu cầu credential bí mật. C073 chỉ nói nhóm confidential hoặc client đã được cấp credentials.
- **q04, mức 1:** ý chính placement/URI đúng; thêm chi tiết form/UTF-8 chưa được các đoạn đã cite chứng minh đầy đủ.
- **q05, mức 0:** trả brute force nhưng cite C054 thuộc resource-owner password flow, khác client-password authentication được hỏi. Không chấp nhận evidence chỉ vì trùng từ khóa.

Không chỉnh theo test để chữa các lỗi này. Có thể dành thí nghiệm dev tiếp theo nếu muốn; nếu thay cấu hình đã chọn phải ghi phiên bản và chọn lại trước khi chạy test.

## Cấu hình chọn và tái lập

Theo quy tắc đã ghi trước chạy dev (điểm câu trả lời, abstention, citation, context, chi phí), chọn `hybrid_top6_context_3000_formatted`. `results/dev_selection.json` lưu cấu hình, model và hash code/corpus/benchmark. Học viên đã duyệt toàn bộ nhãn dev; xác nhận được lưu trong hồ sơ. Chưa có kết quả test và chưa thực hiện phần nâng cao.

Chạy từ root Day 7:

```powershell
$env:PYTHONUTF8='1'
& "<Day6>/starter/.venv/Scripts/python.exe" scripts/run_agent_dev.py --model-path "<Day6>/local_models/all-MiniLM-L6-v2" --max-cost-usd 1
& "<Day6>/starter/.venv/Scripts/python.exe" scripts/run_agent_dev_formatted.py --model-path "<Day6>/local_models/all-MiniLM-L6-v2" --max-cost-usd 0.2
python scripts/check_agent_dev.py
python scripts/check_agent_dev.py --directory agent_dev_formatted
python scripts/review_agent_dev.py
python scripts/review_agent_dev_formatted.py
```

Runner lưu sau từng câu và bỏ qua câu đã chạy khi resume cùng identity, không tự gọi API lại toàn bộ. Muốn thí nghiệm mới phải dùng thư mục/phiên bản riêng. Không ghi đè nhãn học viên đã sửa bằng script nhãn AI. `.env` chứa key riêng và được Git bỏ qua; không đưa gold/answerable/đáp án chuẩn vào model hoặc retrieval tool.

Nguồn trích: IETF RFC 6749, D. Hardt (Ed.), October 2012. Giữ `results/RFC6749_NOTICES.txt` và điều kiện ở `data/RIGHTS_REVIEW.md` khi chia sẻ.