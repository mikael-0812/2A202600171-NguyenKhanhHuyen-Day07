# Báo Cáo Lab 7: Embedding & Vector Store

**Họ tên:** Nguyễn Khánh Huyền
**Nhóm:** ____
**Ngày:** 10/04/2026

---

## 1. Warm-up (5 điểm)

### Cosine Similarity (Ex 1.1)

**High cosine similarity nghĩa là gì?**  
> High cosine similarity nghĩa là hai vector embedding có hướng rất gần nhau trong không gian vector. Điều đó cho thấy hai câu hoặc hai đoạn văn có ý nghĩa ngữ nghĩa tương tự nhau, dù có thể dùng từ khác nhau.

**Ví dụ HIGH similarity:**  
- Sentence A: `"The cat is sleeping on the sofa."`  
- Sentence B: `"A cat is lying asleep on the couch."`  
- **Tại sao tương đồng:** Hai câu mô tả gần như cùng một tình huống, chỉ khác cách dùng từ như *sofa/couch* và *sleeping/lying asleep*. Vì ý nghĩa rất gần nhau nên cosine similarity thường cao.

**Ví dụ LOW similarity:**  
- Sentence A: `"The cat is sleeping on the sofa."`  
- Sentence B: `"I need to submit my math assignment tomorrow."`  
- **Tại sao khác:** Hai câu nói về hai ngữ cảnh hoàn toàn khác nhau, một câu mô tả con mèo đang ngủ, câu còn lại nói về việc nộp bài tập toán. Vì không có sự liên quan ngữ nghĩa nên cosine similarity thấp.

**Tại sao cosine similarity được ưu tiên hơn Euclidean distance cho text embeddings?**  
> Cosine similarity được ưu tiên vì nó đo độ giống nhau về **hướng** của hai vector, thay vì độ lớn của chúng. Trong text embeddings, điều quan trọng nhất là hai văn bản có ý nghĩa giống nhau hay không. Hai câu có thể tạo ra vector dài ngắn khác nhau, nhưng nếu chúng cùng biểu diễn một ý nghĩa thì hướng vector vẫn gần nhau. Vì vậy, cosine similarity thường phù hợp hơn Euclidean distance khi so sánh mức độ tương đồng ngữ nghĩa giữa các văn bản.

### Chunking Math (Ex 1.2)

**Document 10,000 ký tự, `chunk_size = 500`, `overlap = 50`. Bao nhiêu chunks?**  
> `stride = 500 - 50 = 450`  
> `num_chunks = ceil((10000 - 500) / 450) + 1`  
> `= ceil(9500 / 450) + 1`  
> `= ceil(21.11) + 1 = 23`
>
> **Đáp án:** `23 chunks`

**Nếu overlap tăng lên 100, chunk count thay đổi thế nào? Tại sao muốn overlap nhiều hơn?**  
> `stride = 500 - 100 = 400`  
> `num_chunks = ceil((10000 - 500) / 400) + 1`  
> `= ceil(9500 / 400) + 1`  
> `= ceil(23.75) + 1 = 25`
>
> **Đáp án:** `25 chunks`

>Số lượng chunk tăng lên vì mỗi chunk mới dịch ít hơn, nên cần nhiều chunk hơn để phủ hết tài liệu.
>
> Chúng ta muốn overlap nhiều hơn để giữ ngữ cảnh tốt hơn ở phần ranh giới giữa hai chunk. Nếu một ý quan trọng nằm gần cuối chunk trước, phần overlap sẽ giúp nó vẫn xuất hiện ở chunk sau, từ đó giảm nguy cơ mất thông tin khi truy xuất hoặc embedding.

---

## 2. Document Selection — Nhóm (10 điểm)

### Domain & Lý Do Chọn

**Domain:** Git Fundamentals Knowledge Base

**Tại sao nhóm chọn domain này?**
> Nhóm chọn domain về Git cơ bản vì đây là một chủ đề kỹ thuật có cấu trúc rõ ràng, dễ thu thập tài liệu chính thống và thuận lợi cho việc xây dựng benchmark queries. Ngoài ra, các tài liệu Git có nhiều khái niệm dễ bị nhầm lẫn như branch, merge conflict, remote-tracking branch, hay sự khác nhau giữa `git fetch` và `git pull`, nên rất phù hợp để đánh giá chất lượng chunking, retrieval và metadata filtering.

### Data Inventory

| # | Tên tài liệu | Nguồn | Số ký tự | Metadata đã gán |
|---|--------------|-------|----------|-----------------|
| 1 | `Git Basics - Getting a Git Repo.txt` | Pro Git / Git Basics | 4,501 | `tool: git`, `topic: basics`, `lang: vi` |
| 2 | `Basic Branching and Merging.txt` | Pro Git / Branching and Merging | 12,328 | `tool: git`, `topic: merging`, `lang: vi` |
| 3 | `Remote Branches.txt` | Pro Git / Remote Branches | 13,632 | `tool: git`, `topic: remotes`, `lang: vi` |


### Metadata Schema

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho retrieval? |
|----------------|------|---------------|-------------------------------|
| `tool` | string | `git` | Xác định bộ tài liệu đang thuộc công cụ nào, hữu ích nếu sau này mở rộng sang Python hoặc Docker. |
| `topic` | string | `remotes` | Giúp lọc trước theo chủ đề như basics, branching, merging, remotes hoặc commands để tăng độ chính xác khi truy xuất. |
| `lang` | string | `vi` | Đảm bảo kết quả trả về đúng ngôn ngữ của tài liệu và phù hợp với query tiếng Việt. |

---

## 3. Chunking Strategy — Cá nhân chọn, nhóm so sánh (15 điểm)

### Baseline Analysis

Chạy `ChunkingStrategyComparator().compare()` trên 2-3 tài liệu:

| Tài liệu | Strategy | Chunk Count | Avg Length | Preserves Context? |
|-----------|----------|-------------|------------|-------------------|
| `Git Basics - Getting a Git Repo.txt` | `fixed_size` | 17 | 293.00 | No |
| `Git Basics - Getting a Git Repo.txt` | `by_sentences` | 9 | 495.33 | Yes |
| `Git Basics - Getting a Git Repo.txt` | `recursive` | 26 | 171.42 | Partially |
| `Basic Branching and Merging.txt` | `fixed_size` | 46 | 297.35 | No |
| `Basic Branching and Merging.txt` | `by_sentences` | 29 | 420.31 | Yes |
| `Basic Branching and Merging.txt` | `recursive` | 63 | 193.70 | Partially |
| `Remote Branches.txt` | `fixed_size` | 51 | 296.71 | No |
| `Remote Branches.txt` | `by_sentences` | 31 | 435.00 | Yes |
| `Remote Branches.txt` | `recursive` | 75 | 179.88 | Partially |

**Nhận xét baseline:**
> Kết quả baseline cho thấy `fixed_size` tạo các chunk có kích thước khá đồng đều nhưng thường cắt giữa câu hoặc giữa một ý kỹ thuật, nên khả năng giữ ngữ cảnh không tốt. `by_sentences` tạo ít chunk hơn và các chunk dễ đọc hơn vì giữ được câu hoàn chỉnh, nên phù hợp với các đoạn giải thích khái niệm. Trong khi đó, `recursive` tạo nhiều chunk hơn với độ dài ngắn hơn, linh hoạt hơn khi gặp các cấu trúc tài liệu khác nhau nhưng đôi khi tạo ra các đoạn quá ngắn và thiếu ngữ cảnh.

### Strategy Của Tôi

**Loại:** RecursiveChunker (`recursive`)

**Mô tả cách hoạt động:**
> Strategy này hoạt động bằng cách chia văn bản theo thứ tự ưu tiên của các dấu phân cách, từ mức lớn xuống mức nhỏ, chẳng hạn như đoạn văn, xuống dòng, câu, rồi đến khoảng trắng. Nếu một đoạn sau khi tách vẫn vượt quá `chunk_size`, thuật toán tiếp tục chia nhỏ bằng separator tiếp theo. Nhờ đó, strategy này cố gắng giữ cho chunk vừa không quá dài, vừa không bị cắt quá thô như cách chia cố định theo số ký tự.

**Tại sao tôi chọn strategy này cho domain nhóm?**
> Tôi chọn `RecursiveChunker` vì bộ dữ liệu Git của nhóm gồm nhiều loại nội dung kỹ thuật khác nhau: có file mang tính giới thiệu khái niệm, có file trình bày quy trình thao tác, và có file giải thích chi tiết các lệnh. Với kiểu dữ liệu này, `RecursiveChunker` linh hoạt hơn `FixedSizeChunker` vì không cắt văn bản thuần theo số ký tự, đồng thời cũng linh hoạt hơn `SentenceChunker` khi gặp các đoạn liệt kê lệnh, ví dụ hoặc block giải thích dài. Tôi kỳ vọng strategy này sẽ cân bằng tốt giữa việc giữ ngữ nghĩa và tạo chunk đủ nhỏ để retrieval hiệu quả.

### So Sánh: Strategy của tôi vs Baseline

| Tài liệu | Strategy | Chunk Count | Avg Length | Retrieval Quality? |
|-----------|----------|-------------|------------|--------------------|
| `Remote Branches.txt` | `fixed_size` (baseline) | 51 | 296.71 | Medium |
| `Remote Branches.txt` | `recursive` (của tôi) | 75 | 179.88 | High |

**Vì sao tôi đánh giá `recursive` tốt hơn baseline?**
> Trên tài liệu `Remote Branches.txt`, `recursive` tạo nhiều chunk nhỏ hơn nên dễ cô lập các khái niệm như remote references, remote-tracking branches và tracking branches thành các đoạn riêng biệt. Trong khi đó, `fixed_size` giữ độ dài chunk ổn định nhưng dễ cắt ngang phần giải thích giữa chừng. Với các tài liệu Git có nhiều định nghĩa kỹ thuật và ví dụ lệnh, việc giữ được các đơn vị ý nghĩa ngắn nhưng trọn vẹn giúp retrieval chính xác hơn.

### So Sánh Với Thành Viên Khác

| Trường hợp | Strategy | Cấu hình | Retrieval Score (/10) | Điểm mạnh | Điểm yếu |
|-----------|----------|----------|------------------------|-----------|----------|
| TH1 | Fixed Size | `chunk_size=300, overlap=50` | 6/10 | Đơn giản, kích thước chunk đồng đều, dễ kiểm soát | Dễ cắt ngang câu và cắt giữa ý kỹ thuật |
| TH2 | Sentence | `max_sentences_per_chunk=2` | 7/10 | Giữ câu trọn vẹn, chunk dễ đọc, phù hợp với định nghĩa kỹ thuật | Một số chunk khá dài, đôi khi gộp nhiều ý |
| TH3 | Recursive | `chunk_size=300` | 8/10 | Linh hoạt theo cấu trúc văn bản, giữ ngữ nghĩa tốt hơn, phù hợp với tài liệu Git | Tạo nhiều chunk ngắn, cần chọn separator hợp lý |
| TH4 | Recursive + metadata filter | `chunk_size=300` + `topic filter` | 9/10 | Retrieval chính xác hơn với các query theo chủ đề như remotes hoặc commands | Phụ thuộc vào việc metadata được gán đúng và đủ chi tiết |

**Trường hợp nào tốt nhất? Tại sao?**
> Trong các thử nghiệm, `RecursiveChunker` kết hợp với metadata filtering cho kết quả tốt nhất. Lý do là tài liệu Git có cấu trúc không đồng đều: có đoạn là định nghĩa ngắn, có đoạn là ví dụ lệnh, có đoạn là giải thích quy trình dài hơn. `RecursiveChunker` giúp chia văn bản linh hoạt hơn so với `FixedSizeChunker`, còn metadata filtering giúp thu hẹp không gian tìm kiếm khi query thuộc một chủ đề cụ thể như `remotes`, `branching` hoặc `commands`.

---

## 4. My Approach — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi implement các phần chính trong package `src`.

### Chunking Functions

**`SentenceChunker.chunk`** — approach:
> Xử lý trường hợp chuỗi rỗng trước, sau đó dùng `re.split()` để tách văn bản theo các mẫu kết thúc câu như `. `, `! `, `? ` hoặc `.
`. Sau khi loại bỏ khoảng trắng thừa, các câu được gom lại theo kích thước `max_sentences_per_chunk`. Cách làm này đơn giản, dễ kiểm soát và đủ tốt cho các tài liệu kỹ thuật có câu khá rõ ràng, dù nó có thể làm mất dấu câu ở ranh giới tách.

**`RecursiveChunker.chunk` / `_split`** — approach:
> Triển khai theo hướng đệ quy. Hàm `chunk()` chuẩn hóa đầu vào rồi gọi `_split()` với danh sách separator ưu tiên. Trong `_split()`, nếu đoạn hiện tại đã ngắn hơn `chunk_size` thì trả về luôn. Nếu chưa, thuật toán thử tách theo separator hiện tại; nếu vẫn quá dài thì tiếp tục đệ quy với separator ở mức nhỏ hơn. Khi đến separator rỗng, văn bản được cắt theo cửa sổ ký tự cố định. Cách này giúp strategy tận dụng được cấu trúc tự nhiên của văn bản trước khi phải rơi về chia cứng theo độ dài.

### EmbeddingStore

**`add_documents` + `search`** — approach:
> Thiết kế `EmbeddingStore` theo kiểu có fallback. Nếu ChromaDB khả dụng thì collection được khởi tạo và dùng để lưu embeddings; nếu không thì hệ thống dùng một list in-memory. Trong `add_documents()`, mỗi `Document` được chuyển thành một record chuẩn hóa gồm `id`, `content`, `metadata`, và `embedding`. Trong `search()`, nếu dùng in-memory thì query được embed rồi so sánh với toàn bộ records bằng dot product, sau đó sắp xếp giảm dần theo score và trả về top-k.

**`search_with_filter` + `delete_document`** — approach:
> `search_with_filter()` được cài theo đúng thứ tự là lọc metadata trước rồi mới search. Nếu có `metadata_filter`, store chỉ giữ lại các records thỏa điều kiện rồi mới tính similarity, giúp tránh nhiễu và đúng yêu cầu của bài lab. `delete_document()` xóa toàn bộ chunk có `metadata["doc_id"]` trùng với document cần xóa, và trả về `True/False` tùy việc có xóa được record nào hay không.

### KnowledgeBaseAgent

**`answer`** — approach:
> Trong `KnowledgeBaseAgent.answer()`, gọi `store.search()` để lấy top-k chunks liên quan, sau đó ghép nội dung các chunk thành phần `Context` trong prompt. Prompt được viết theo hướng yêu cầu mô hình chỉ trả lời dựa trên context, và nếu context không đủ thì phải nói rõ điều đó. Cuối cùng prompt được truyền vào `llm_fn`. Cách làm này bám đúng RAG pattern cơ bản: retrieve → build prompt → generate answer.


### Test Results

**Số tests pass:** 42 / 42

```
============================= test session starts =============================
collecting ... collected 42 items

test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED [  2%]
test_solution.py::TestProjectStructure::test_src_package_exists PASSED   [  4%]
test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED [  7%]
test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED [  9%]
test_solution.py::TestFixedSizeChunker::test_chunks_respect_size PASSED  [ 11%]
test_solution.py::TestFixedSizeChunker::test_correct_number_of_chunks_no_overlap PASSED [ 14%]
test_solution.py::TestFixedSizeChunker::test_empty_text_returns_empty_list PASSED [ 16%]
test_solution.py::TestFixedSizeChunker::test_no_overlap_no_shared_content PASSED [ 19%]
test_solution.py::TestFixedSizeChunker::test_overlap_creates_shared_content PASSED [ 21%]
test_solution.py::TestFixedSizeChunker::test_returns_list PASSED         [ 23%]
test_solution.py::TestFixedSizeChunker::test_single_chunk_if_text_shorter PASSED [ 26%]
test_solution.py::TestSentenceChunker::test_chunks_are_strings PASSED    [ 28%]
test_solution.py::TestSentenceChunker::test_respects_max_sentences PASSED [ 30%]
test_solution.py::TestSentenceChunker::test_returns_list PASSED          [ 33%]
test_solution.py::TestSentenceChunker::test_single_sentence_max_gives_many_chunks PASSED [ 35%]
test_solution.py::TestRecursiveChunker::test_chunks_within_size_when_possible PASSED [ 38%]
test_solution.py::TestRecursiveChunker::test_empty_separators_falls_back_gracefully PASSED [ 40%]
test_solution.py::TestRecursiveChunker::test_handles_double_newline_separator PASSED [ 42%]
test_solution.py::TestRecursiveChunker::test_returns_list PASSED         [ 45%]
test_solution.py::TestEmbeddingStore::test_add_documents_increases_size PASSED [ 47%]
test_solution.py::TestEmbeddingStore::test_add_more_increases_further PASSED [ 50%]
test_solution.py::TestEmbeddingStore::test_initial_size_is_zero PASSED   [ 52%]
test_solution.py::TestEmbeddingStore::test_search_results_have_content_key PASSED [ 54%]
test_solution.py::TestEmbeddingStore::test_search_results_have_score_key PASSED [ 57%]
test_solution.py::TestEmbeddingStore::test_search_results_sorted_by_score_descending PASSED [ 59%]
test_solution.py::TestEmbeddingStore::test_search_returns_at_most_top_k PASSED [ 61%]
test_solution.py::TestEmbeddingStore::test_search_returns_list PASSED    [ 64%]
test_solution.py::TestKnowledgeBaseAgent::test_answer_non_empty PASSED   [ 66%]
test_solution.py::TestKnowledgeBaseAgent::test_answer_returns_string PASSED [ 69%]
test_solution.py::TestComputeSimilarity::test_identical_vectors_return_1 PASSED [ 71%]
test_solution.py::TestComputeSimilarity::test_opposite_vectors_return_minus_1 PASSED [ 73%]
test_solution.py::TestComputeSimilarity::test_orthogonal_vectors_return_0 PASSED [ 76%]
test_solution.py::TestComputeSimilarity::test_zero_vector_returns_0 PASSED [ 78%]
test_solution.py::TestCompareChunkingStrategies::test_counts_are_positive PASSED [ 80%]
test_solution.py::TestCompareChunkingStrategies::test_each_strategy_has_count_and_avg_length PASSED [ 83%]
test_solution.py::TestCompareChunkingStrategies::test_returns_three_strategies PASSED [ 85%]
test_solution.py::TestEmbeddingStoreSearchWithFilter::test_filter_by_department PASSED [ 88%]
test_solution.py::TestEmbeddingStoreSearchWithFilter::test_no_filter_returns_all_candidates PASSED [ 90%]
test_solution.py::TestEmbeddingStoreSearchWithFilter::test_returns_at_most_top_k PASSED [ 92%]
test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_reduces_collection_size PASSED [ 95%]
test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_false_for_nonexistent_doc PASSED [ 97%]
test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_true_for_existing_doc PASSED [100%]

============================= 42 passed in 0.08s ==============================

```

---
## 5. Similarity Predictions — Cá nhân (5 điểm)

| Pair | Sentence A | Sentence B | Dự đoán | Actual Score | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | A Git branch is a lightweight pointer to a commit. | In Git, a branch is just a movable reference to a commit. | high | -0.1792 | No |
| 2 | `git fetch` only downloads changes from the remote repository. | `git pull` downloads changes and then integrates them into the current branch. | medium | -0.2708 | No |
| 3 | Merge conflict happens when two branches modify the same part of a file differently. | Remote-tracking branches reflect the state of branches on a remote server. | low | -0.2307 | Yes |
| 4 | `git init` creates a new Git repository in an existing folder. | `git clone` copies an existing Git repository to the local machine. | medium | 0.0594 | Yes |
| 5 | `origin/master` is a remote-tracking branch. | Tracking branches are local branches that have a direct relationship with a remote branch. | high | -0.0267 | No |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn nghĩa?**
> Kết quả bất ngờ nhất là cặp 1 và cặp 5. Về mặt ngữ nghĩa, đây đều là các cặp câu khá gần nhau, nhưng điểm similarity thực tế lại âm hoặc gần 0. Điều này cho thấy `MockEmbedder` không thực sự học ý nghĩa ngôn ngữ mà chỉ tạo vector theo cơ chế hashing, nên điểm similarity không phản ánh tốt mức độ tương đồng ngữ nghĩa. Vì vậy, nếu muốn đánh giá semantic similarity đáng tin cậy hơn, cần dùng embedding model thực tế như `all-MiniLM-L6-v2` hoặc OpenAI embeddings.

---

## 6. Results — Cá nhân (10 điểm)

Chạy 5 benchmark queries của nhóm trên implementation cá nhân của bạn trong package `src`.

### Benchmark Queries & Gold Answers

| # | Query | Gold Answer |
|---|-------|-------------|
| 1 | Git repository có thể được tạo bằng git init hay git clone như thế nào? | Có hai cách chính: khởi tạo một thư mục cục bộ bằng `git init`, hoặc sao chép một repository hiện có bằng `git clone`. |
| 2 | Branch trong Git là gì? | Branch trong Git là một con trỏ nhẹ, có thể di chuyển, trỏ tới một commit. |
| 3 | Khi nào xảy ra merge conflict và cần làm gì sau đó? | Merge conflict xảy ra khi hai nhánh sửa cùng một phần của cùng một file theo những cách khác nhau. Sau đó cần mở file để resolve conflict, chạy `git add`, rồi `git commit` để hoàn tất merge. |
| 4 | Remote-tracking branch là gì? | Remote-tracking branch là tham chiếu cục bộ phản ánh trạng thái của một nhánh trên remote, ví dụ `origin/master`. |
| 5 | `git pull` khác `git fetch` ở điểm nào? | `git fetch` chỉ tải thay đổi từ remote về local và cập nhật thông tin tracking, còn `git pull` về cơ bản là `git fetch` rồi tích hợp thay đổi đó vào nhánh hiện tại, thường bằng merge hoặc rebase. |

### Kết Quả Của Tôi

| # | Query | Top-1 Retrieved Chunk (tóm tắt) | Score | Relevant? | Agent Answer (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Git repository có thể được tạo bằng git init hay git clone như thế nào? | Top-1 là đoạn trong `Git Basics - Getting a Git Repo.txt` nói về việc bắt đầu theo dõi file và tạo commit ban đầu; top-2 đã chứa đúng ý chính rằng có hai cách để có một Git repository: biến thư mục cục bộ thành repository hoặc sao chép một repository hiện có | 0.2494 | Yes| Agent trả lời dựa trên context truy xuất được; dù top-1 chưa phải đoạn tốt nhất, top-2 đã rất sát với gold answer nên câu trả lời có thể được cải thiện nếu ưu tiên đúng chunk hơn. |
| 2 | Branch trong Git là gì? | Top-1 là đoạn trong `Phân nhánh trong Git.txt` nói về cách hiển thị lịch sử commit bằng `git log`; top-2 đã nêu ý rất sát rằng nhánh trong Git thực chất là một tệp đơn giản chứa mã SHA-1 của commit mà nó trỏ tới | 0.2144 | Yes | Agent trả lời dựa trên context truy xuất được; dù top-1 chưa đúng trực tiếp, top-2 đã khá sát với gold answer nên câu trả lời có thể đúng một phần nếu mô hình tận dụng được chunk phù hợp hơn. |
| 3 | Khi nào xảy ra merge conflict và cần làm gì sau đó? | Top-1 chỉ là tiêu đề “Hợp nhất cơ bản” trong `Basic Branching and Merging.txt`; top-2 và top-3 nói về workflow phân nhánh và trạng thái thư mục làm việc, chưa nêu trực tiếp khi nào xảy ra merge conflict và cách xử lý | 0.2175 | No | Agent trả lời dựa trên context truy xuất được, nhưng context chưa chứa phần định nghĩa merge conflict và các bước resolve nên câu trả lời chưa đủ chính xác. |
| 4 | Remote-tracking branch là gì? | Top-1 là chú thích hình trong `Remote Branches.txt` về kho lưu trữ sau khi sao chép; top-2 đã nêu ý gần đúng rằng `origin/serverfix` là một con trỏ mà người dùng không thể sửa trực tiếp | 0.3724 | Yes | Agent trả lời dựa trên context truy xuất được; top-1 chưa đúng trực tiếp, nhưng top-2 đã phần nào phản ánh bản chất của remote-tracking branch là một tham chiếu cục bộ theo dõi trạng thái nhánh trên remote. |
| 5 | `git pull` khác `git fetch` ở điểm nào? | Top-1 là đoạn trong `git-pull.txt` nói về thuật toán diff khi merge; top-2 chỉ là tùy chọn `--prune`, còn top-3 nói về submodule và `fetch`, chưa giải thích trực tiếp sự khác nhau giữa `git pull` và `git fetch` | 0.3504 | No | Agent trả lời dựa trên context truy xuất được, nhưng context không chứa phần giải thích đúng về `git fetch` và `git pull` nên câu trả lời chưa đủ chính xác. |

**Bao nhiêu queries trả về chunk relevant trong top-3?** 3 / 5

**Nhận xét kết quả:**
> Với `RecursiveChunker` kết hợp metadata filtering theo `topic`, chất lượng retrieval đã cải thiện so với lần chạy trước, đặc biệt ở các query về branch và Git repository basics. Tuy nhiên, top-1 vẫn chưa ổn định và nhiều trường hợp thông tin đúng chỉ xuất hiện ở top-2 hoặc top-3 thay vì đứng đầu. Điều này cho thấy metadata filtering giúp thu hẹp đúng tài liệu, nhưng với `MockEmbedder`, thứ hạng similarity vẫn chưa phản ánh tốt ngữ nghĩa thật của câu hỏi. Ngoài ra, một số file như `git-pull.txt` chứa nhiều thông tin tham số và tùy chọn kỹ thuật chi tiết, khiến retrieval dễ bị kéo vào các đoạn phụ thay vì đúng đoạn định nghĩa cốt lõi.

---

## 7. What I Learned (5 điểm — Demo)

**Điều quan trọng nhất tôi rút ra từ quá trình tự thử nghiệm nhiều trường hợp:**
> Tôi nhận ra rằng chunking strategy chỉ là một phần của bài toán. Nếu document selection không khớp với benchmark queries, retrieval sẽ thất bại ngay cả khi chunking được thiết kế hợp lý. Ngược lại, khi bộ tài liệu bao phủ đúng chủ đề, chỉ cần thay đổi strategy chia chunk cũng có thể làm khác biệt rõ rệt ở top-1 retrieval.

**Điều tôi học được từ phần demo / quan sát các cách làm khác:**
> Một bài học quan trọng là metadata filtering có thể cải thiện kết quả rất rõ khi tài liệu đã được gán chủ đề hợp lý. Với domain Git, việc thêm metadata như `topic = basics`, `branching`, `merging`, `remotes`, hoặc `commands` giúp thu hẹp không gian tìm kiếm và làm cho truy xuất chính xác hơn.

**Nếu làm lại, tôi sẽ thay đổi gì trong data strategy?**
> Nếu làm lại, tôi sẽ tiếp tục giữ domain Git nhưng sẽ chuẩn hóa metadata kỹ hơn, đặc biệt là tách rõ `topic` và `source`. Ngoài ra, tôi cũng sẽ thay `MockEmbedder` bằng một embedding model thực tế để semantic similarity phản ánh đúng ngữ nghĩa hơn, từ đó cải thiện cả retrieval quality lẫn phần similarity prediction.

---
## Tự Đánh Giá

| Tiêu chí | Loại | Điểm tự đánh giá |
|----------|------|-------------------|
| Warm-up | Cá nhân | 5 / 5 |
| Document selection | Nhóm | 10 / 10 |
| Chunking strategy | Nhóm | 15 / 15 |
| My approach | Cá nhân | 10 / 10 |
| Similarity predictions | Cá nhân | 5 / 5 |
| Results | Cá nhân | 10 / 10 |
| Core implementation (tests) | Cá nhân | 30 / 30 |
| Demo | Nhóm | 5 / 5 |
| **Tổng** | | **100 / 100** |