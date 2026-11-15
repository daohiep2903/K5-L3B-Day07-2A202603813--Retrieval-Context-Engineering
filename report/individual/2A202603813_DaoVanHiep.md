# Báo cáo Day 7

**Học viên:** Đào Văn Hiệp · **MSSV:** 2A202603813 · **Lớp:** L3B

**Chủ đề:** Agentic RAG trên RFC 6749, tiếp nối corpus Day 6.

**Repo:** https://github.com/daohiep2903/K5-L3B-Day07-2A202603813--Retrieval-Context-Engineering

## Dữ liệu và benchmark

**Nguồn, quyền sử dụng, số trang và số chunk:** IETF RFC 6749, *The OAuth 2.0 Authorization Framework*, D. Hardt (Ed.), October 2012; chọn mục 2–7 từ file TXT của Day 6. Corpus có **41 đơn vị nguồn**, mỗi đơn vị ít nhất 1.502 ký tự sau chuẩn hóa, không nhân bản nội dung. Đây không phải 41 trang PDF; trường `page` là số đơn vị nguồn. Dùng **116 chunk cấu hình B** đã chọn ở Day 6, giữ ID, text, nguồn, mục và vị trí ký tự. Schema Day 7 đổi `chunk_id` thành `id`, `document_id` thành `source_id`.

Nguồn chính thức: https://www.rfc-editor.org/rfc/rfc6749.txt . Thông tin và hash ở `data/day6_import.json`, `data/manifest.json`. Điều kiện trích đoạn theo IETF Trust TLP 4.0 được đối chiếu tại `data/RIGHTS_REVIEW.md`; thông báo tác giả/bản quyền nằm trong `data/RFC6749_NOTICES.txt` và `results/RFC6749_NOTICES.txt`. Giữ các thông báo này khi chia sẻ corpus, benchmark hoặc trace. Không trình bày bản chuẩn hóa là bản RFC chính thức hoặc gán quyền sở hữu RFC cho học viên.

**Vector store, embedding model, phiên bản và số chiều:** Qdrant local, collection `day7_dense`, lưu tại `local_vectors/`, tìm kiếm cosine exact. Dùng lại vector thật từ `day6_B`; sai số sao chép do chuẩn hóa float được kiểm tra trong dung sai 1e-6. Model `sentence-transformers/all-MiniLM-L6-v2`, commit `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`, **384 chiều**, normalize embeddings. Model tạo query và index tương thích. Phiên bản đã chạy: sentence-transformers 6.3.0, qdrant-client 1.20.0; toàn bộ môi trường tại `results/dependencies.txt`. Kiểm tra nguồn/text, metadata, vector và mở lại store nằm trong `results/dense_connection_check.json`.

**Agent model, cách chạy và phân chia dev/test:** OpenAI `gpt-4.1-mini-2025-04-14`, Chat Completions với function calling, temperature 0, tối đa 768 completion token/lượt. API key chỉ lưu ở `.env`, được Git bỏ qua. Benchmark `benchmark/questions.json` có **24 câu**: dev 15 câu có đáp án + 2 câu thiếu evidence; test 5 câu có đáp án + 2 câu thiếu evidence. 15 câu dev có đáp án kế thừa Day 6 dev và rà soát lại gold; 5 câu test có đáp án soạn mới, không dùng lại test Day 6. Người chuẩn bị đã thấy nhãn; dev/test cùng một RFC nên không coi đây là kiểm tra mù trên tài liệu ngoài.

**Cách xác định câu có/thiếu evidence và tiêu chí chấm:** câu có đáp án được kiểm tra quote nguyên văn, nguồn, đơn vị và chunk chứa đầy đủ evidence. Loại alternative sai ngữ cảnh của q05/q06 và rút q08 về câu trọn vẹn. Câu thiếu evidence được đối chiếu trên toàn corpus đã chọn, kèm lý do và kiểm tra từ khóa tại `benchmark/absence_review.json`; không suy ra thiếu thông tin chỉ vì top-k không thấy. Không đưa gold, đáp án, `answerable` hoặc hành vi chuẩn cho model/tool. Bốn câu thiếu evidence không nằm trong mẫu số Hit@1, Hit@3 và Context Evidence Rate.

Hit@1/Hit@3 yêu cầu đúng nguồn/đơn vị và có đủ quote sau chuẩn hóa khoảng trắng. Context Evidence Rate đo evidence trong context cuối thực sự gửi model; kiểm tra quote tự động được báo riêng với nhận xét evidence tương đương. Câu trả lời chấm 0/1/2: sai hoặc thiếu evidence/từ chối câu có đáp án; đúng một phần; đúng và đủ. Citation phải có trong context và hỗ trợ khẳng định liên quan, không chỉ đúng ID. Abstention tính trên câu thiếu bằng chứng, báo kèm từ chối nhầm trên câu có đáp án.

## Retrieval và thử nghiệm

Triển khai ba phương pháp khác nhau: dense trên Qdrant; lexical TF-IDF; hybrid Reciprocal Rank Fusion (RRF). Hybrid cộng 1/(60 + rank) của tối thiểu 10 candidate từ mỗi nhánh, không cộng trực tiếp cosine và TF-IDF score. Không dùng reranker. Filter `top_level_section`/`language` chỉ từ phạm vi người dùng cung cấp; áp cùng chính sách cho ba phương pháp và trước cutoff ở lexical.

Context giữ nguyên chunk theo thứ hạng, loại ID trùng và bỏ chunk không vừa budget, tính cả header nguồn. Runtime agent dùng alias `C001`… có ánh xạ về ID gốc; alias chỉ đổi nhãn citation, không đổi nguồn/text. Số lượt search tối đa là 2 cho mọi cấu hình agent.

| Cấu hình | Phương pháp, top-k, filter, rerank, context budget | Giả thuyết / thay đổi | Split | Hit@1 | Evidence Hit@3 | Context Evidence Rate | Thời gian / chi phí |
|---|---|---|---|---|---|---|---|
| Baseline | dense; k=3; filter from query; no rerank; 800 chars | Dense baseline with starter context budget. | dev | 7/15 (46.7%) | 11/15 (73.3%) | 5/15 (33.3%) * | median 2.365 s; $0.008587 |
| Lexical | lexical; k=3; filter from query; no rerank; 800 chars | Exact protocol names may favor lexical matching. | dev | 9/15 (60.0%) | 13/15 (86.7%) | 6/15 (40.0%) * | median 2.501 s; $0.008995 |
| Hybrid RRF | hybrid; k=3; filter from query; no rerank; 800 chars | RRF can combine semantic and exact-term rankings. | dev | 10/15 (66.7%) | 14/15 (93.3%) | 6/15 (40.0%) * | median 2.282 s; $0.008856 |
| Dense budget 3000 | dense; k=3; filter from query; no rerank; 3000 chars | Larger context may retain complete retrieved evidence; only budget changes from dense baseline. | dev | 7/15 (46.7%) | 11/15 (73.3%) | 12/15 (80.0%) * | median 2.093 s; $0.010201 |
| Hybrid top6/budget3000 | hybrid; k=6; filter from query; no rerank; 3000 chars | More candidates and a larger context may improve coverage. Two factors change together; not a causal isolation. | dev | 10/15 (66.7%) | 14/15 (93.3%) | 13/15 (86.7%) * | median 2.082 s; $0.011336 |
| Hybrid top6/budget3000 + formatter | hybrid; k=6; filter from query; no rerank; 3000 chars | Render only model-declared context-valid citations; compare after observed dev formatting errors. | dev | 10/15 (66.7%) | 14/15 (93.3%) | 13/15 (86.7%) * | median 2.124 s; $0.011408 |
| Baseline | dense; k=3; filter from query; no rerank; 800 chars | Dense baseline with starter context budget. | test | 4/5 (80.0%) | 5/5 (100.0%) | 3/5 (60.0%) | median 2.797 s; $0.003632 |
| Hybrid top6/budget3000 + formatter | hybrid; k=6; filter from query; no rerank; 3000 chars | Render only model-declared context-valid citations; compare after observed dev formatting errors. | test | 4/5 (80.0%) | 5/5 (100.0%) | 5/5 (100.0%) | median 2.139 s; $0.004844 |

Trong bảng, Hit@1/Hit@3 dùng **query gốc** để so sánh ranking cùng cutoff. Context là context cuối của agent; median thời gian gồm vòng lặp agent, không phải chỉ vector search. Các lượt query model viết lại và ranking riêng được giữ trong trace và trường `agent_first_search_hit1/hit3`, không trộn với ranking query gốc. Dấu * chỉ mức context tự động theo trọn quote: ở cấu hình chọn, dev có 13/15 quote đầy đủ; sau đọc evidence tương đương, q09 được hỗ trợ tại C091/mục 4.2 nên context đủ evidence là **14/15**. Nhãn context từng câu nằm tại `results/agent_dev_formatted/reviews.json`.

Ba baseline cùng budget 800; hai cải thiện theo kế hoạch là dense budget 3.000 và hybrid top-6/budget 3.000. Hybrid cải thiện đổi hai yếu tố cùng lúc nên không cô lập tác động top-k. Sau khi đọc lỗi dev, chạy thêm cấu hình formatter trên đúng 17 câu dev; đây là lần chạy API thật mới, không sửa kết quả lỗi cũ. Tổng: 85 trace dev ban đầu + 17 trace bổ sung = **102 trace agent dev**. Ngoài ra có 85 trace retrieval-only trước khi nối model; các trace này không được gọi là đánh giá câu trả lời agent.

**Hai lỗi dev, nguyên nhân và thử cải thiện:**

1. `d7-dev-q03`: model có đáp án HTTP Basic và danh sách citation nhưng thiếu `[ID]` trong thân answer, nên code từ chối. Formatter kiểm tra ID có trong context rồi hiển thị citation model đã khai báo; cấu hình bổ sung trả lời với C048 và đạt mức 2. Formatter không thêm nguồn mới hoặc sửa nội dung đáp án.
2. `d7-dev-q02`: dense baseline trả rằng không có giới hạn rõ ràng, cite C090 nói phương thức xác thực khác; nguồn này không chứa quy định số phương thức. Cấu hình chọn giữ C059 trong context và trả đúng MUST NOT dùng nhiều hơn một phương thức/request, đạt mức 2. Context quá nhỏ và ranking chưa phù hợp có thể dẫn đến suy luận sai.

Ở retrieval-only, q02 đã tìm được chunk đúng dài 834 ký tự nhưng không vừa budget 800; q04 có lúc context rỗng dù top-3 có evidence. Tăng budget giúp giữ chunk đúng, nhưng không tự giải quyết citation hoặc nội dung model sinh.

**Lý do chọn:** trước chạy dev đã ghi quy tắc ưu tiên điểm câu trả lời, rồi abstention, citation, context và chi phí. Chọn `hybrid_top6_context_3000_formatted`, lưu model/runtime/hash tại `results/dev_selection.json`; học viên duyệt nhãn dev trước khi chạy test. Baseline test giữ dense/top-3/budget800, không thêm formatter sau khi nhìn test. Gói cấu hình chọn khác baseline ở nhiều yếu tố, nên không quy toàn bộ mức tăng cho hybrid.

## Agent và đánh giá

**Tool, số lượt gọi, điều kiện dừng, chọn context và xử lý lỗi:** model gọi `search` để tìm và `finish` để trả lời hoặc từ chối. Lần đầu được yêu cầu gọi search; model chọn query và quyết định có tìm tiếp hay kết thúc ở các lượt sau. Vì vậy tỷ lệ tool use 100% phản ánh thiết kế bắt buộc truy xuất, không chứng minh model tự nhận biết nhu cầu dùng tool. Tối đa 2 search; nếu model tiếp tục tìm quá giới hạn hoặc output/citation không hợp lệ, hệ thống trả từ chối. Các request quyết định dùng context tích lũy mới nhất, không phát lại lịch sử tool không giới hạn. Tài liệu và kết quả tool là dữ liệu, không phải chỉ dẫn.

Formatter chỉ gắn các citation ID model đã khai báo và được kiểm tra có trong context. ID hợp lệ không chứng minh ngữ nghĩa được hỗ trợ. Giữ phản hồi model gốc, answer sau formatter, mapping và sự kiện định dạng. Lỗi provider/retrieval được báo riêng, không thay bằng câu trả lời giả. Không có lỗi provider trong các lượt dev/test đã báo; các lỗi citation/giới hạn search là lỗi pipeline/đầu ra, không bị loại khỏi điểm câu trả lời.

| Cấu hình / split | Tool use | Số lượt gọi | Grounded answer 0/1/2 và trung bình | Citation hợp lệ | Câu có citation | Abstention đúng | Từ chối nhầm |
|---|---|---|---|---|---|---|---|
| Baseline / dev | 17/17 (100.0%) | model 40; 1 search: 11, 2 search: 6 | 14/1/0; TB 0.067/2 | 0/2 (0.0%) | 2/2 (100.0%) | 2/2 (100.0%) | 13/15 (86.7%) |
| Lexical / dev | 17/17 (100.0%) | model 41; 1 search: 10, 2 search: 7 | 14/1/0; TB 0.067/2 | 0/1 (0.0%) | 1/1 (100.0%) | 2/2 (100.0%) | 14/15 (93.3%) |
| Hybrid RRF / dev | 17/17 (100.0%) | model 40; 1 search: 11, 2 search: 6 | 15/0/0; TB 0.000/2 | 0/1 (0.0%) | 1/1 (100.0%) | 2/2 (100.0%) | 14/15 (93.3%) |
| Dense budget 3000 / dev | 17/17 (100.0%) | model 34; 1 search: 17 | 14/0/1; TB 0.133/2 | 2/2 (100.0%) | 1/1 (100.0%) | 2/2 (100.0%) | 14/15 (93.3%) |
| Hybrid top6/budget3000 / dev | 17/17 (100.0%) | model 34; 1 search: 17 | 11/1/3; TB 0.467/2 | 4/4 (100.0%) | 4/4 (100.0%) | 2/2 (100.0%) | 11/15 (73.3%) |
| Hybrid top6/budget3000 + formatter / dev | 17/17 (100.0%) | model 34; 1 search: 17 | 1/2/12; TB 1.733/2 | 15/17 (88.2%) | 15/15 (100.0%) | 2/2 (100.0%) | 0/15 (0.0%) |
| Baseline / test | 7/7 (100.0%) | model 16; 1 search: 5, 2 search: 2 | 5/0/0; TB 0.000/2 | 0/0 (N/A) | 0/0 (N/A) | 2/2 (100.0%) | 5/5 (100.0%) |
| Hybrid top6/budget3000 + formatter / test | 7/7 (100.0%) | model 14; 1 search: 7 | 0/2/3; TB 1.600/2 | 5/7 (71.4%) | 5/5 (100.0%) | 2/2 (100.0%) | 0/5 (0.0%) |

Mẫu số `Câu có citation` là số câu trả lời thực sự được trả ra; baseline test không trả lời nên 0/0 là không áp dụng. Baseline từ chối đúng 2/2 câu thiếu evidence nhưng từ chối nhầm 5/5 câu có đáp án, nên không coi 2/2 là bằng chứng abstention tốt. Nhãn chấm câu trả lời cuối người dùng nhận, không lấy raw answer đã bị chặn để tính đúng.

| Query ID | Loại câu | Tool call và kết quả | Câu trả lời và citation | Nhãn, lý do |
|---|---|---|---|---|
| d7-dev-q03, cấu hình chọn | Có đáp án | Search lấy C048 | HTTP Basic cho client được cấp password; cite C048 | 2; điều kiện và nguồn trực tiếp đúng. |
| d7-dev-q05, cấu hình chọn | Có đáp án | Search lấy đoạn C054 | Brute force nhưng cite resource-owner password flow | 0; không chứng minh đúng ngữ cảnh client-password được hỏi. |
| d7-test-01, cấu hình chọn | Có đáp án | Context có C041 đúng điều kiện và C002 mô tả chung | Trả đúng scope nhưng cite C002 | 1; citation không chứng minh MUST khi scope thay đổi. |
| d7-test-02, cấu hình chọn | Có đáp án | Search lấy C028 | SHOULD thông báo, MUST NOT tự redirect tới URI lỗi | 2; đủ điều kiện và citation hỗ trợ. |
| d7-test-04, cấu hình chọn | Có đáp án | Context có C035/C031 và C015 khác flow | Trả đúng state, thêm lý do CSRF và cite thêm C015 | 1; CSRF không trong context, C015 thuộc implicit-error flow. |
| d7-test-abs-03, cấu hình chọn | Thiếu evidence | Search không cung cấp yêu cầu DPoP typ | Từ chối, không suy đoán giá trị | Từ chối đúng. |
| d7-test-abs-04, cấu hình chọn | Thiếu evidence | Có ví dụ thời hạn access token, không có số ngày cố định của refresh token | Từ chối, không nhầm hai loại token | Từ chối đúng. |

**Đường dẫn trace, nhãn, cách chạy, thời gian và chi phí:**

- Benchmark, cách kiểm chứng và absence review: `benchmark/`.
- Ranking query gốc/retrieval-only: `results/retrieval_dev/`.
- 85 lượt agent dev ban đầu: `results/agent_dev/traces.jsonl`; nhãn theo thư mục cấu hình.
- 17 lượt dev formatter: `results/agent_dev_formatted/traces.jsonl`, `reviews.json`.
- Tổng hợp dev: `results/agent_dev_comparison.json`; xác nhận của học viên: `results/student_dev_review_confirmation.json`.
- 14 lượt test: `results/agent_test/traces.jsonl`; mỗi cấu hình có `reviews.json`, `summary.json`. Đã đọc 5 câu có đáp án + 2 câu thiếu evidence cho cả baseline và cấu hình chọn. Học viên đã xác nhận duyệt toàn bộ nhãn test ngày 15/11/2026; hồ sơ tại `results/student_test_review_confirmation.json`.
- Snapshot trước test: `results/agent_test/dev_selection_snapshot.json`; trạng thái sau test: `results/test_execution.json`.
- Hướng dẫn tái lập: `docs/RUN_PROJECT.md`; phân tích dev/test: `docs/AGENT_DEV.md`, `docs/AGENT_TEST.md`.

Chi phí dùng usage thực tế và đơn giá chuẩn đã lưu ngày 14/11/2026, chưa trừ giảm giá cache, không phải hóa đơn; chưa tính điện/phần cứng hoặc tải model. Nguồn đơn giá: https://developers.openai.com/api/docs/models/gpt-4.1-mini .

Agent dev: **0.0593828 USD**; agent test: **0.0084760 USD**; demo ba lần: **0.0034404 USD**. Tổng API ước tính đã ghi: **0.0712992 USD**. Retrieval/embedding local không gọi API trả phí.

**Kết quả trước/sau và giới hạn:** cấu hình chọn có test Context Evidence Rate 5/5 nhưng chỉ 3/5 câu đúng đủ, hai câu đúng một phần; ví dụ này cho thấy retrieval tốt chưa bảo đảm citation/answer đúng. Baseline test có ranking tốt nhưng đầu ra đều bị từ chối, chủ yếu do ràng buộc citation. Mẫu test chỉ 5 câu có đáp án và cùng RFC; không tuyên bố tốt nhất tổng quát hoặc khác biệt có ý nghĩa thống kê. Model API có thể thay đổi đầu ra giữa các lần gọi dù cùng snapshot/temperature. Chỉ chạy một lượt test đã chốt; không điều chỉnh hoặc chọn kết quả đẹp sau khi xem test.

B/C Day 6 có 2 chunk vượt giới hạn 256 token của embedding model, tối đa 271 token; Day 7 dùng lại vector đó, không coi đây là lỗi đã được giải quyết. Context dạng giữ nguyên chunk có thể cắt danh sách hoặc bỏ đoạn quá lớn; filter sai có thể loại evidence đúng. TF-IDF dùng tách từ đơn giản. Những nhãn được hỗ trợ đọc nguồn vẫn có nguy cơ thiên lệch; dev và test đã được học viên duyệt; vẫn có nguy cơ thiên lệch và không phải chấm mù độc lập. Chưa đánh giá multi-hop hoặc nội dung trực quan. Nếu cải thiện tiếp, thử trên dev, lưu phiên bản mới và cần test mới để đánh giá độc lập nếu đã dùng test này để chỉnh.

## Thử thách nâng cao (nếu thực hiện)

**Không thực hiện.** Corpus hiện tại là TXT trích RFC, không đáp ứng thử thách một tài liệu từ 100 trang có bảng, ảnh và biểu đồ; không đăng ký 15 điểm bonus và không sử dụng kết quả test cơ bản để tuyên bố đạt ngưỡng nâng cao. Phần cơ bản tối đa 85 điểm; báo cáo không tự chấm điểm môn học.
