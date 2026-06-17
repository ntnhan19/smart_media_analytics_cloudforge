# Hướng Dẫn Đồng Bộ Backend - Trang Chi Tiết Asset (Frontend-Ready)

Tài liệu này tổng hợp chi tiết các yêu cầu điều chỉnh, bổ sung cấu trúc Database, API Schemas, và API Endpoints ở phía Backend liên quan đến trang chi tiết Asset (`/assets/:id`) để sẵn sàng kết nối với giao diện cải tiến của Frontend (SMA).

---

## 1. Cơ sở dữ liệu (Database Schema / Models)

Khi tích hợp pipeline AI để trích xuất Metadata cho trang chi tiết, Backend cần lưu trữ siêu dữ liệu chi tiết sau:

### A. Đối tượng được phát hiện (Detected Objects)
Lưu trữ vị trí xuất hiện (occurrences) của vật thể đó trong dòng thời gian của video:
* **Các thuộc tính cần lưu**:
  - `name`: Tên vật thể (ví dụ: `"BRIDGE"`, `"CAR"`, `"PERSON"`).
  - `occurrences`: Mảng các mốc thời gian xuất hiện của vật thể. Mỗi mốc gồm:
    - `timestamp_start`: Giây bắt đầu phát hiện (float).
    - `timestamp_end`: Giây kết thúc phát hiện (float).
    - `confidence`: Độ chính xác phát hiện (float, khoảng `0.0` - `1.0`).

### B. Nhãn phân loại (Tags)
Cần phân nhóm nhãn để Frontend áp dụng màu sắc và phân loại trực quan:
* Bổ sung cột `category` (kiểu dữ liệu string/enum):
  - `"location"`: Địa điểm (ví dụ: "SWEDEN", "STOCKHOLM").
  - `"content_type"`: Loại nội dung (ví dụ: "VLOG", "DRONE").
  - `"theme"`: Chủ đề (ví dụ: "TRAVEL", "NATURE").
* Bổ sung cột `source` (kiểu dữ liệu string/enum):
  - `"auto"`: AI tự động nhận diện.
  - `"user_confirmed"`: User đã xác nhận hoặc tự thêm thủ công.

---

## 2. API Response Schemas (Pydantic / FastAPI Models)

Cập nhật hoặc thêm mới trong file `backend/schemas/asset.py` các models sau:

```python
from pydantic import BaseModel, Field
from typing import Optional

# 1. Schema cho các mốc xuất hiện của vật thể
class OccurrenceSchema(BaseModel):
    timestamp_start: float = Field(..., description="Giây bắt đầu xuất hiện trong video")
    timestamp_end: float = Field(..., description="Giây kết thúc xuất hiện trong video")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Độ tin cậy của AI (0 đến 1)")

# 2. Schema trả về thông tin vật thể được phát hiện
class DetectedObjectResponse(BaseModel):
    name: str = Field(..., description="Tên viết hoa của vật thể, ví dụ: 'BRIDGE'")
    occurrences: list[OccurrenceSchema]

# 3. Schema trả về thông tin nhãn phân loại
class TagResponse(BaseModel):
    name: str
    category: str = Field(..., description="Thuộc nhóm: 'location', 'content_type', hoặc 'theme'")
    source: str = Field(..., description="Nguồn gốc nhãn: 'auto' hoặc 'user_confirmed'")

# 4. Schema trả về phần tử kết quả tìm kiếm ngữ nghĩa
class SearchResultItem(BaseModel):
    scene_id: str
    timestamp_start: float
    timestamp_end: float
    thumbnail_url: Optional[str] = None
    caption: str = Field(..., description="Mô tả cụ thể của cảnh đó (caption riêng, không được trùng lặp)")
    match_score: float = Field(..., description="Tỷ lệ trùng khớp thực tế từ 0-1")
    matched_snippet: str = Field(..., description="Đoạn văn bản/phụ đề thực sự khớp dùng để tô sáng (highlight)")
```

---

## 3. Các API Endpoints cần cung cấp

### In-Video Semantic Search (Tìm kiếm ngữ nghĩa trong 1 Video)
Dành cho tính năng tìm kiếm nhanh ở thanh công cụ bên phải trang chi tiết Asset.
* **Route**: `GET /api/v1/assets/{asset_id}/search`
* **Query Params**: `q` (từ khóa tìm kiếm)
* **Response Model**: `list[SearchResultItem]`
* **Yêu cầu thuật toán**: 
  - Backend thực hiện vector similarity search dựa trên mô tả cảnh (`caption`) và phụ đề (`transcript`) của riêng video có `asset_id` tương ứng.
  - Trả về `match_score` biến thiên thực tế dựa trên điểm tương đồng (Cosine Similarity).

---

## 4. Pipeline xử lý background (Khi click "Detect more")
Khi người dùng kích hoạt **Detect more scenes**, Frontend sẽ gửi request yêu cầu Backend chạy phân tích bổ sung:
* API Endpoint: `POST /api/v1/assets/{asset_id}/detect-scenes` (trả về 202 Accepted kèm Task ID).
* Backend chạy một background task để:
  1. Trích xuất thêm các frame hình ảnh chi tiết của video.
  2. Phân tích thêm vật thể (YOLO/Multimodal AI) và cập nhật lại mảng `detected_objects`.
  3. Cắt nhỏ các scene chi tiết hơn (nhỏ hơn 1.6s) dựa trên thay đổi khung hình.
