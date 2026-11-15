# Kết quả test Day 7

Đã chạy **baseline và cấu hình đã chọn trên cùng 7 câu test**: 5 câu có đáp án, 2 câu thiếu bằng chứng. Tổng 14 trace thật. Model, prompt, chunk, embedding, runtime code và benchmark được kiểm tra hash khớp bản chốt dev trước khi gọi API. Không sửa hoặc chọn lại cấu hình theo test.

Có AI hỗ trợ đọc toàn bộ câu trả lời, context và citation; **học viên Đào Văn Hiệp đã xác nhận duyệt toàn bộ nhãn test ngày 15/11/2026**. Xác nhận riêng lưu tại `results/student_test_review_confirmation.json`.

## Kết quả tổng hợp

| Chỉ số | Dense baseline | Hybrid top-6/budget 3.000 + formatter |
|---|---:|---:|
| Hit@1 query gốc | 4/5 (80%) | 4/5 (80%) |
| Evidence Hit@3 query gốc | 5/5 (100%) | 5/5 (100%) |
| Context đủ evidence | 3/5 (60%) | 5/5 (100%) |
| Context mức 0/1/2 | 1 / 1 / 3 | 0 / 0 / 5 |
| Context trung bình /2 | 1,4 | 2,0 |
| Câu trả lời mức 0/1/2 | 5 / 0 / 0 | 0 / 2 / 3 |
| Câu trả lời trung bình /2 | 0,0 | 1,6 |
| Citation hỗ trợ | 0/0, không áp dụng | 5/7 |
| Câu trả lời có citation | 0/0, không áp dụng | 5/5 |
| Từ chối đúng câu thiếu evidence | 2/2 | 2/2 |
| Từ chối nhầm câu có đáp án | 5/5 | 0/5 |
| Có gọi retrieval tool | 7/7 | 7/7 |
| Tổng lượt gọi model | 16 | 14 |
| Lỗi provider | 0 | 0 |
| Chi phí API ước tính USD | 0,0036324 | 0,0048436 |

Chi phí chung của bước test khoảng **0,008476 USD**; theo đơn giá chuẩn đã lưu, chưa trừ giảm giá cache, chưa tính máy local, không phải hóa đơn. Thời gian và phân bố số search của từng câu nằm trong `results/agent_test/summary.json`.

## Nhận xét từng câu của cấu hình chọn

| Query ID | Điểm đáp án /2 | Nhận xét nguồn và citation |
|---|---:|---|
| d7-test-01 | 1 | Đáp án scope đúng; cite C002 chỉ mô tả scope chung, thiếu điều kiện MUST khi scope thay đổi. C041 có đúng evidence trong context nhưng không được cite. |
| d7-test-02 | 2 | C028 hỗ trợ đủ điều kiện URI lỗi, SHOULD thông báo và MUST NOT tự redirect. |
| d7-test-03 | 2 | C055 hỗ trợ absolute URI làm grant_type và bổ sung tham số cần thiết. |
| d7-test-04 | 1 | C035 hỗ trợ state bắt buộc nếu đã gửi và phải trả đúng giá trị; C031 hỗ trợ bối cảnh trả code. C015 thuộc lỗi implicit flow; phần lý do CSRF thêm vào không có trong context đã gửi. |
| d7-test-05 | 2 | C063 trực tiếp định nghĩa unauthorized_client trong yêu cầu authorization code. |
| d7-test-abs-03 | Từ chối đúng | Không suy đoán giá trị typ cho DPoP khi corpus không cung cấp. |
| d7-test-abs-04 | Từ chối đúng | Không lấy ví dụ expires_in của access token thành thời hạn refresh token cố định. |

Đáp án có thể đúng nhưng citation chưa chứng minh đủ điều kiện. Có evidence trong context cũng chưa bảo đảm model chọn đúng nguồn để cite. Vì vậy không báo 5/5 đúng và đủ dù cả 5 câu có đáp án đều được agent trả lời.

## Vì sao baseline thấp?

Baseline từ chối cả 7 câu. Bốn câu có đáp án đầu bị kiểm tra output từ chối vì thiếu/không đúng citation trong thân câu; câu thứ năm chạm giới hạn search. Context của ba câu thực sự đủ evidence, nhưng đầu ra cuối vẫn là từ chối nên điểm câu trả lời là 0. Giữ nguyên kết quả này thay vì dùng raw answer chưa qua kiểm tra để tính đúng.

Tỷ lệ từ chối đúng 2/2 của baseline không chứng minh agent phân biệt tốt câu thiếu evidence: baseline cũng từ chối nhầm 5/5 câu có đáp án. Cần đọc hai chỉ số cùng nhau.

## Phạm vi kết luận

Đây là gói cải thiện nhiều yếu tố so với baseline: hybrid thay dense, tăng budget/top-k và thêm formatter. Không quy toàn bộ lợi ích cho riêng thuật toán hybrid. Test có 5 câu có đáp án, cùng tài liệu và chủ đề đã biết; không suy rộng kết quả 100% retrieval thành độ chính xác tổng quát. Model có thể phát sinh khác biệt giữa các lần gọi; chỉ chạy một lượt test đã chốt, không chọn kết quả đẹp.

`results/dev_selection.json` là hồ sơ chốt trước test; `results/agent_test/dev_selection_snapshot.json` giữ bản đó. Trạng thái test hiện tại nằm ở `results/test_execution.json`, không sửa lịch sử chốt dev để che việc đã xem test.

## File và tái lập

- `scripts/run_agent_test.py`: kiểm tra identity rồi chạy baseline/cấu hình chọn, lưu sau từng câu, resume không gọi lại câu đã có.
- `results/agent_test/plan.json`, `run_manifest.json`: cấu hình và hash trước/chạy test.
- `results/agent_test/traces.jsonl`: đủ 14 trace, có query gốc và query model chọn, kết quả, context, answer, citation, token và thời gian.
- `results/agent_test/<cấu hình>/reviews.json`: nhãn test từng câu/context/citation và lý do.
- `results/agent_test/summary.json`: số liệu tổng hợp.

```powershell
$env:PYTHONUTF8='1'
& "<Day6>/starter/.venv/Scripts/python.exe" scripts/run_agent_test.py --model-path "<Day6>/local_models/all-MiniLM-L6-v2" --max-cost-usd 0.2
python scripts/review_agent_test.py
python -m unittest discover -s tests -v
```

Không chạy script chấm lại để ghi đè nhãn học viên đã sửa; cần lưu phiên bản review riêng. Sau khi test đã được xem, mọi điều chỉnh dùng test phải được công bố và không coi chính test đó là đánh giá độc lập cho cấu hình đã chỉnh.

Nguồn: IETF RFC 6749, D. Hardt (Ed.), October 2012; giữ các thông báo tại `results/RFC6749_NOTICES.txt` và điều kiện trong `data/RIGHTS_REVIEW.md` khi chia sẻ.