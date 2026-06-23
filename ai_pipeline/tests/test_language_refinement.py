# -*- coding: utf-8 -*-
"""
test_pipeline_language_output_on_real_video.py

Integration Test cho toàn bộ AI Pipeline
Kiểm tra chất lượng Refinement LLM (tiếng Việt) + Semantic output
"""

import uuid
from pathlib import Path

import pytest
from sqlalchemy import text

from schemas.ingest import IngestOptions
from services.ingest_service import run_ingest_pipeline
from database import SessionLocal


@pytest.mark.asyncio
async def test_pipeline_language_output_on_real_video():
    """
    Test tích hợp toàn pipeline trên video thực tế.
    Chỉ kiểm tra asset + scenes mới nhất để tránh lẫn dữ liệu cũ.
    """
    video_path = Path("/app/data/my_video.mp4")
    file_name = "my_video.mp4"

    assert video_path.exists(), f"Không tìm thấy video test: {video_path}"

    job_id = str(uuid.uuid4())
    options = IngestOptions(processing_mode="fast")

    print(f"\n[1/4] Bắt đầu pipeline trên video thực: {video_path}")
    print(f"Job ID: {job_id}")

    # Tạo job trước
    async with SessionLocal() as db:
        await db.execute(
            text("""
                INSERT INTO ingest_jobs (job_id, status, progress)
                VALUES (:job_id, 'processing', 0)
                ON CONFLICT (job_id) DO NOTHING
            """),
            {"job_id": job_id},
        )
        await db.commit()

    # Chạy pipeline
    try:
        await run_ingest_pipeline(
            job_id_str=job_id,
            source_path=str(video_path),
            options=options,
        )
        print("\n[2/4] Pipeline hoàn thành thành công thành công! Đang tiến hành bóc tách dữ liệu từ DB...")
    except Exception as e:
        pytest.fail(f"Pipeline thất bại: {e}")

    print("\n[3/4] Truy vấn asset mới nhất từ PostgreSQL...")

    async with SessionLocal() as db:
        # Lấy asset mới nhất theo file_name
        asset_query = text("""
            SELECT id, file_name, ingested_at
            FROM assets
            WHERE file_name = :file_name
            ORDER BY ingested_at DESC, id DESC
            LIMIT 1
        """)

        asset_row = (await db.execute(asset_query, {"file_name": file_name})).first()
        assert asset_row, f"Không tìm thấy asset cho file {file_name}!"

        asset_id = asset_row[0]
        print(f"   → Asset ID tìm thấy: {asset_id}")
        print(f"   → Thời gian Ingest: {asset_row[2]}")

        print("\n[4/4] Đang nạp và hiển thị báo cáo chi tiết từng Scene...")

        scenes_query = text("""
            SELECT scene_index, transcript_snippet, caption, searchable_text
            FROM scenes
            WHERE asset_id = :asset_id
            ORDER BY scene_index ASC
        """)

        scenes = (await db.execute(scenes_query, {"asset_id": asset_id})).fetchall()
        assert scenes, f"Không có scene nào cho asset {asset_id}!"

        print("\n" + "=" * 100)
        print("BÁO CÁO KẾT QUẢ SEMANTIC OUTPUT (ASSET MỚI NHẤT)")
        print("=" * 100)

        forbidden_phrases = [
            "main subjects", "visible objects", "scene type", "location cues",
            "shot type", "camera movement", "dominant color", "action:"
        ]

        # 🟢 ĐÃ SỬA: Thụt lề (4 spaces) chuẩn xác cho vòng lặp for bên dưới
        for scene_idx, transcript, caption, searchable_text in scenes:
            caption = caption or ""
            transcript = transcript or ""
            searchable = searchable_text or ""

            print(f"\n🎬 Scene {scene_idx:2d}")
            print(f"   • Lời thoại bóc tách       : {transcript if transcript.strip() else '[Không có lời thoại]'}")
            print(f"   • Tóm tắt cảnh (Caption)   : {caption}")
            print(f"   • Từ khóa tìm kiếm (Search) : {searchable}")

            # Assertions kiểm tra chất lượng dữ liệu
            assert caption and caption.strip(), f"Scene {scene_idx}: Caption bị rỗng!"
            lowered = caption.lower()

            for phrase in forbidden_phrases:
                assert phrase not in lowered, (
                    f"Scene {scene_idx}: Phát hiện output rác tiếng Anh → '{phrase}'\n"
                    f"Caption: {caption}"
                )

            # Nếu bị dính câu hướng dẫn mẫu, fail test để biết đường sửa prompt
            assert "mô tả ngắn gọn" not in lowered, f"Scene {scene_idx}: LLM bị học vẹt chuỗi hướng dẫn mẫu!"

            assert len(caption.strip()) >= 12, (
                f"Scene {scene_idx}: Caption quá ngắn, thiếu giá trị semantic!"
            )
            assert searchable.strip(), f"Scene {scene_idx}: searchable_text bị rỗng!"

        print("\n" + "=" * 100)
        print(f" TEST ĐẠT — ĐÃ XÁC MINH THÀNH CÔNG {len(scenes)} PHÂN CẢNH CỦA ASSET {asset_id}")
        print("=" * 100 + "\n")