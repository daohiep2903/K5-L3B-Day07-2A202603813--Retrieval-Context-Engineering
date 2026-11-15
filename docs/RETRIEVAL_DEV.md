# So sánh retrieval trên dev

## Ba phương pháp

- Dense: embedding thật all-MiniLM-L6-v2 và tìm cosine trên Qdrant Day 7.
- Lexical: TF-IDF với tách từ đơn giản từ starter; tính IDF trên cùng corpus. Filter được áp trước khi lấy top-k.
- Hybrid: Reciprocal Rank Fusion, cộng 1/(60 + thứ hạng) của dense và lexical; lấy tối thiểu 10 candidate từ mỗi nhánh. Không cộng trực tiếp cosine với điểm TF-IDF. Trace lưu cả ranking thành phần và thứ hạng đóng góp.

Cả ba dùng câu hỏi gốc, không rewrite hoặc lấy filter từ gold. Chunk, model dense và store không đổi. Tạo context bằng cách giữ nguyên chunk theo thứ hạng, loại ID trùng, bỏ chunk không vừa budget; budget đo bằng ký tự, gồm cả header nguồn/citation.

## Ma trận cấu hình

| Cấu hình | Top-k | Budget ký tự | Vai trò |
|---|---:|---:|---|
| dense_baseline | 3 | 800 | Baseline dense |
| lexical_baseline | 3 | 800 | Phương pháp thứ hai |
| hybrid_baseline | 3 | 800 | Phương pháp thứ ba |
| dense_context_3000 | 3 | 3.000 | Cải thiện 1: chỉ tăng budget |
| hybrid_top6_context_3000 | 6 | 3.000 | Cải thiện 2: tăng top-k và budget cùng lúc |

Giả thuyết và quy tắc shortlist được ghi trong `results/retrieval_dev/plan.json` trước các lượt retrieval. Ma trận cải thiện đã lên kế hoạch trước lần chạy; phân tích lỗi bên dưới được thực hiện sau khi có trace. Không suy ra riêng tác động top-k từ cấu hình hybrid cải thiện vì nó đổi hai yếu tố.

## Kết quả đã đo

| Cấu hình | Hit@1 | Evidence Hit@3 | Evidence trong context chuẩn bị |
|---|---:|---:|---:|
| Dense baseline | 7/15 | 11/15 | 4/15 |
| Lexical baseline | 9/15 | 13/15 | 6/15 |
| Hybrid baseline | 10/15 | 14/15 | 5/15 |
| Dense budget 3.000 | 7/15 | 11/15 | 11/15 |
| Hybrid top-6, budget 3.000 | 10/15 | 14/15 | 14/15 |

Mỗi cấu hình chạy 17 câu dev, gồm 15 câu có đáp án và 2 câu thiếu bằng chứng: tổng cộng 85 trace. Hai câu thiếu bằng chứng không tính vào mẫu số retrieval/context. Chưa chấm agent, abstention, câu trả lời hoặc citation. Chỉ số context ở đây là kiểm tra trên context đã chuẩn bị, chưa phải xác nhận context cuối thực sự gửi một agent model.

Hybrid cải thiện là ứng viên retrieval tạm thời theo quy tắc ưu tiên evidence trong context, rồi Hit@3, Hit@1, context ngắn hơn và tên cấu hình. Chưa chốt cấu hình agent/test; còn phải so sánh câu trả lời thật và thời gian/chi phí trên dev.

## Phân tích lỗi dev

1. **d7-dev-q02 — budget làm rơi evidence:** dense đã đưa chunk đúng thuộc đơn vị 4 vào top-1, nhưng text dài 834 ký tự chưa tính header nên không vừa budget 800. Context bỏ chunk này và giữ đoạn khác về dùng lại authorization code, không trả lời câu hỏi số phương thức xác thực. Tăng riêng budget lên 3.000 giữ được evidence mà không thay Hit@1/Hit@3. Đây là lỗi chọn context, không phải dense không tìm ra.
2. **d7-dev-q04 — context rỗng ở hybrid baseline:** chunk đúng đơn vị 5 dài 941 ký tự; cả ba block sau cộng header đều không vừa budget 800, nên không có context dù Hit@3 đúng. Cấu hình hybrid cải thiện giữ được bằng chứng với budget lớn hơn. Không được gọi agent đúng chỉ từ việc retrieval có hit.
3. **d7-dev-q05 — lỗi ranking còn tồn tại:** hybrid top-6 vẫn chưa có evidence gold đúng ngữ cảnh client-password về chống brute force trong context. Các kết quả ưu tiên xác thực client và cả đoạn resource-owner password. Đây là hai ngữ cảnh khác nhau; không chấp nhận đoạn sai ngữ cảnh chỉ vì có từ khóa giống nhau. Cần phân tích thêm trên dev khi nối agent; không dùng test để sửa lỗi này.

Điểm Hit dùng nguồn/đơn vị và đủ quote sau chuẩn hóa khoảng trắng, chấp nhận alternative đã ghi. Không dùng gold trong query, retriever hoặc pack_context; gold chỉ dùng sau retrieval để chấm.

## Chạy lại

Từ root Day 7:

```powershell
$env:PYTHONUTF8='1'
& "<Day6>/starter/.venv/Scripts/python.exe" scripts/run_retrieval_dev.py --model-path "<Day6>/local_models/all-MiniLM-L6-v2"
python -m unittest discover -s tests -v
```

`src/retrieval.py` chứa lexical và hybrid. Runner chỉ lấy split dev. Trace, context, ranking thành phần, latency, thống kê và hash nằm tại `results/retrieval_dev/`. Chạy lại sẽ ghi đè kết quả cùng tên; lưu bản thí nghiệm trước nếu cần so sánh phiên bản.

Thời gian là một lượt tuần tự, có ảnh hưởng cache/CPU; không coi đó là benchmark tốc độ có kiểm soát. Không dùng API trả phí, chưa tính điện/phần cứng. Model đã được kiểm tra hash ở bước kết nối; giới hạn token của model Day 6 vẫn áp dụng.

Nguồn text: IETF RFC 6749, D. Hardt (Ed.), October 2012. Giữ thông báo ở `results/RFC6749_NOTICES.txt` và điều kiện tại `data/RIGHTS_REVIEW.md` khi chia sẻ trace.