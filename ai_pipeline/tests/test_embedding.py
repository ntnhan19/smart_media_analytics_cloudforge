"""
Test Embedding Model - Production Grade Testing
Kiểm tra chi tiết Ollama Embedding (BGE-M3)
"""

import numpy as np
from pathlib import Path
import time
from ai_pipeline.embeddings.embedding_models import (
    EmbeddingModel, 
    EmbeddingManager,
    create_embedding_model
)
from utils.logger import logger


def test_embedding_model():
    """Test toàn diện Embedding Model"""
    print("="*80)
    print(" EMBEDDING MODEL COMPREHENSIVE TEST")
    print("="*80)

    try:
        # 1. Khởi tạo model
        print("\n[1] Khởi tạo EmbeddingModel...")
        embedding_model = create_embedding_model()
        
        if not embedding_model.is_ready:
            print(" Embedding model không ready!")
            return False
            
        print(f" Model ready: {embedding_model.model_name} | Dim: {embedding_model.embedding_dim}")

        # 2. Test single text
        print("\n[2] Test single text embedding...")
        single_text = "Đây là một câu tiếng Việt để kiểm tra embedding model"
        emb_single = embedding_model.encode(single_text)
        
        print(f"   Shape: {emb_single.shape}")
        print(f"   Mean: {emb_single.mean():.6f} | Std: {emb_single.std():.6f}")
        print(f"   Min: {emb_single.min():.6f} | Max: {emb_single.max():.6f}")
        print(f"   Is zero vector: {np.allclose(emb_single, 0, atol=1e-5)}")

        # 3. Test multiple texts (batch)
        print("\n[3] Test batch embedding...")
        test_texts = [
            "Cảnh núi non hùng vĩ vào lúc bình minh",
            "Người phụ nữ mặc áo đỏ đang đi dạo trên bãi biển",
            "Drone fly over beautiful rice terraces in Vietnam",
            "This is a test sentence in English",
            "Kỹ thuật AI đang phát triển rất nhanh chóng"
        ]
        
        start_time = time.time()
        embeddings = embedding_model.encode(test_texts, batch_size=4)
        elapsed = time.time() - start_time
        
        print(f"   Batch size: {len(test_texts)} texts")
        print(f"   Output shape: {embeddings.shape}")
        print(f"   Time: {elapsed:.3f} seconds")
        print(f"   Avg time per text: {(elapsed/len(test_texts))*1000:.2f} ms")

        # 4. Kiểm tra cosine similarity (độ tương đồng)
        print("\n[4] Test semantic similarity...")
        sim12 = np.dot(embeddings[0], embeddings[1]) / (np.linalg.norm(embeddings[0]) * np.linalg.norm(embeddings[1]))
        sim13 = np.dot(embeddings[0], embeddings[2]) / (np.linalg.norm(embeddings[0]) * np.linalg.norm(embeddings[2]))
        
        print(f"   Similarity giữa câu 1 và 2: {sim12:.4f}")
        print(f"   Similarity giữa câu 1 và 3: {sim13:.4f}")
        
        if sim12 > 0.3:
            print("    Semantic understanding hoạt động tốt")
        else:
            print("     Similarity thấp, cần kiểm tra")

        # 5. Test EmbeddingManager
        print("\n[5] Test EmbeddingManager...")
        manager = EmbeddingManager()
        manager.load_all()
        
        manager_emb = manager.encode("Test qua EmbeddingManager")
        print(f"   Manager encode thành công | Shape: {manager_emb.shape}")

        print("\n" + "="*80)
        print(" TẤT CẢ TEST EMBEDDING ĐÃ PASS!")
        print("="*80)
        
        return True

    except Exception as e:
        logger.error(f"Embedding test failed: {e}")
        print(f" Test thất bại: {e}")
        return False


if __name__ == "__main__":
    test_embedding_model()