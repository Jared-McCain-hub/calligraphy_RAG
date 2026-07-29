"""Fine-tune embedding model for calligraphy domain."""

import json
import sys
from pathlib import Path

# Add backend to path
BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

import torch
from torch.utils.data import DataLoader
from sentence_transformers import SentenceTransformer, InputExample, losses
from sentence_transformers.evaluation import EmbeddingSimilarityEvaluator


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


def finetune_embedding_model(
    train_data_path: str,
    output_model_path: str,
    base_model: str = 'paraphrase-multilingual-MiniLM-L12-v2',
    epochs: int = 5,
    batch_size: int = 16,
    warmup_steps: int = 100,
    learning_rate: float = 2e-5,
):
    """Fine-tune embedding model.
    
    Args:
        train_data_path: Path to training data JSON
        output_model_path: Path to save fine-tuned model
        base_model: Base model name or path
        epochs: Number of training epochs
        batch_size: Training batch size
        warmup_steps: Warmup steps for scheduler
        learning_rate: Learning rate
    """
    print("=" * 60)
    print("微调 Embedding 模型")
    print("=" * 60)
    
    # Load model
    print(f"\n[1/5] 加载基础模型: {base_model}")
    model = SentenceTransformer(base_model)
    print(f"  模型维度: {model.get_sentence_embedding_dimension()}")
    
    # Load training data
    print(f"\n[2/5] 加载训练数据: {train_data_path}")
    data = load_training_data(train_data_path)
    print(f"  原始样本数: {len(data)}")
    
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
    print("\n[3/5] 配置训练参数")
    train_loss = losses.CosineSimilarityLoss(model)
    print(f"  损失函数: CosineSimilarityLoss")
    print(f"  训练轮数: {epochs}")
    print(f"  批次大小: {batch_size}")
    print(f"  学习率: {learning_rate}")
    
    # Train
    print("\n[4/5] 开始训练...")
    model.fit(
        train_objectives=[(train_dataloader, train_loss)],
        epochs=epochs,
        warmup_steps=warmup_steps,
        optimizer_params={'lr': learning_rate},
        show_progress_bar=True,
    )
    
    # Save model
    print(f"\n[5/5] 保存模型到: {output_model_path}")
    model.save(output_model_path)
    
    print("\n" + "=" * 60)
    print("✅ 微调完成！")
    print("=" * 60)
    print(f"模型已保存到: {output_model_path}")
    
    return model


def evaluate_model(model, test_data_path: str):
    """Evaluate fine-tuned model."""
    print("\n" + "=" * 60)
    print("评估模型")
    print("=" * 60)
    
    # Load test data (use part of training data for demo)
    data = load_training_data(test_data_path)[:50]  # Use first 50 samples
    
    # Create evaluator
    sentences1 = [item['query'] for item in data]
    sentences2 = [item['positive'] for item in data]
    labels = [1.0] * len(data)  # All positive samples
    
    evaluator = EmbeddingSimilarityEvaluator(
        sentences1,
        sentences2,
        labels,
        show_progress_bar=True,
    )
    
    # Evaluate
    score = model.evaluate(evaluator)
    print(f"\n相似度得分: {score:.4f}")
    
    return score


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Fine-tune embedding model")
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
        "--base-model",
        type=str,
        default="paraphrase-multilingual-MiniLM-L12-v2",
        help="Base model name",
    )
    parser.add_argument(
        "--epochs",
        type=int,
        default=5,
        help="Number of training epochs",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=16,
        help="Training batch size",
    )
    
    args = parser.parse_args()
    
    # Fine-tune
    model = finetune_embedding_model(
        train_data_path=args.train_data,
        output_model_path=args.output,
        base_model=args.base_model,
        epochs=args.epochs,
        batch_size=args.batch_size,
    )
    
    # Evaluate
    evaluate_model(model, args.train_data)
