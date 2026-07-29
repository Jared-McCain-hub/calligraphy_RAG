"""Fine-tune embedding model optimized for MacBook Air (Apple Silicon)."""

import json
import sys
import os
from pathlib import Path

# Add backend to path
BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

import torch
from torch.utils.data import DataLoader
from sentence_transformers import SentenceTransformer, InputExample, losses

# Check MPS availability
def check_mps():
    """Check if MPS (Metal Performance Shaders) is available."""
    if torch.backends.mps.is_available():
        print("✅ MPS 可用（Apple Silicon GPU 加速）")
        return "mps"
    elif torch.cuda.is_available():
        print("✅ CUDA 可用")
        return "cuda"
    else:
        print("⚠️ 仅 CPU 可用（训练会较慢）")
        return "cpu"


def load_training_data(filepath: str) -> list:
    """Load training data from JSON file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def create_training_examples(data: list) -> list:
    """Create InputExample objects for training."""
    examples = []
    
    for item in data:
        # Create positive pair
        examples.append(
            InputExample(
                texts=[item['query'], item['positive']],
                label=1.0
            )
        )
        
        # Create negative pair
        examples.append(
            InputExample(
                texts=[item['query'], item['negative']],
                label=0.0
            )
        )
    
    return examples


def finetune_for_macbook(
    train_data_path: str,
    output_model_path: str,
    base_model: str = 'paraphrase-multilingual-MiniLM-L12-v2',
    epochs: int = 3,  # 减少轮数
    batch_size: int = 8,  # 减小批次大小
    warmup_steps: int = 50,  # 减少 warmup
    learning_rate: float = 2e-5,
    use_subset: bool = True,  # 使用部分数据快速测试
    subset_size: int = 200,  # 子集大小
):
    """Fine-tune embedding model optimized for MacBook Air.
    
    Args:
        train_data_path: Path to training data JSON
        output_model_path: Path to save fine-tuned model
        base_model: Base model name or path
        epochs: Number of training epochs (建议 3-5)
        batch_size: Training batch size (建议 4-8)
        warmup_steps: Warmup steps for scheduler
        learning_rate: Learning rate
        use_subset: Whether to use subset of data for quick test
        subset_size: Number of samples to use in subset mode
    """
    print("=" * 60)
    print("微调 Embedding 模型（MacBook Air 优化版）")
    print("=" * 60)
    
    # Check device
    print("\n[0/5] 检查设备...")
    device = check_mps()
    
    # Load model
    print(f"\n[1/5] 加载基础模型: {base_model}")
    model = SentenceTransformer(base_model)
    print(f"  模型维度: {model.get_sentence_embedding_dimension()}")
    
    # Move to device
    if device == "mps":
        model.to("mps")
        print("  设备: MPS (Apple Silicon GPU)")
    
    # Load training data
    print(f"\n[2/5] 加载训练数据: {train_data_path}")
    data = load_training_data(train_data_path)
    print(f"  原始样本数: {len(data)}")
    
    # Use subset for quick test
    if use_subset:
        data = data[:subset_size]
        print(f"  使用子集: {len(data)} 条（快速测试模式）")
    
    # Create training examples
    train_examples = create_training_examples(data)
    print(f"  训练样本数: {len(train_examples)}")
    
    # Create dataloader
    train_dataloader = DataLoader(
        train_examples,
        shuffle=True,
        batch_size=batch_size
    )
    
    # Define loss function
    print("\n[3/5] 配置训练参数（MacBook Air 优化）")
    train_loss = losses.CosineSimilarityLoss(model)
    print(f"  损失函数: CosineSimilarityLoss")
    print(f"  训练轮数: {epochs}")
    print(f"  批次大小: {batch_size} (适配 MacBook Air)")
    print(f"  学习率: {learning_rate}")
    
    # Estimate training time
    total_steps = len(train_dataloader) * epochs
    estimated_time = total_steps * 0.5 / 60  # 粗略估计（分钟）
    print(f"  预计训练时间: {estimated_time:.1f} 分钟")
    
    # Train
    print("\n[4/5] 开始训练...")
    print("  提示: MacBook Air 无风扇，建议在凉爽环境中运行")
    
    try:
        model.fit(
            train_objectives=[(train_dataloader, train_loss)],
            epochs=epochs,
            warmup_steps=warmup_steps,
            optimizer_params={'lr': learning_rate},
            show_progress_bar=True,
        )
    except KeyboardInterrupt:
        print("\n\n⚠️ 训练被中断")
        print("  正在保存当前模型...")
    
    # Save model
    print(f"\n[5/5] 保存模型到: {output_model_path}")
    model.save(output_model_path)
    
    print("\n" + "=" * 60)
    print("✅ 微调完成！")
    print("=" * 60)
    print(f"模型已保存到: {output_model_path}")
    
    return model


def quick_test(model_path: str):
    """Quick test of fine-tuned model."""
    print("\n" + "=" * 60)
    print("快速测试")
    print("=" * 60)
    
    # Load model
    model = SentenceTransformer(model_path)
    
    # Test queries
    test_cases = [
        ("颜体", "颜真卿创立的楷书风格"),
        ("楷书", "汉字的标准字体"),
        ("王羲之", "东晋书法家"),
    ]
    
    for query, expected in test_cases:
        vec1 = model.encode(query)
        vec2 = model.encode(expected)
        
        # Calculate cosine similarity
        import numpy as np
        similarity = np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
        
        print(f"\n  查询: {query}")
        print(f"  期望: {expected}")
        print(f"  相似度: {similarity:.4f}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Fine-tune embedding model for MacBook Air")
    parser.add_argument(
        "--train-data",
        type=str,
        default="training_data/embedding_training_data.json",
        help="Path to training data JSON",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="models/calligraphy-embedding-model",
        help="Path to save fine-tuned model",
    )
    parser.add_argument(
        "--epochs",
        type=int,
        default=3,
        help="Number of training epochs (default: 3)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=8,
        help="Training batch size (default: 8 for MacBook Air)",
    )
    parser.add_argument(
        "--full-data",
        action="store_true",
        help="Use full training data (default: use subset)",
    )
    parser.add_argument(
        "--subset-size",
        type=int,
        default=200,
        help="Number of samples in subset mode",
    )
    
    args = parser.parse_args()
    
    # Fine-tune
    model = finetune_for_macbook(
        train_data_path=args.train_data,
        output_model_path=args.output,
        epochs=args.epochs,
        batch_size=args.batch_size,
        use_subset=not args.full_data,
        subset_size=args.subset_size,
    )
    
    # Quick test
    quick_test(args.output)
