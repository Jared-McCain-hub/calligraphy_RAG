#!/bin/bash

# MacBook Air 微调脚本运行指南

echo "======================================"
echo "MacBook Air 微调准备"
echo "======================================"

# 1. 检查 Python 环境
echo ""
echo "1. 检查 Python 环境..."
which python3 || echo "请先安装 Python 3"

# 2. 检查依赖
echo ""
echo "2. 检查依赖..."
python3 -c "import torch; print(f'PyTorch: {torch.__version__}')" || echo "需要安装 PyTorch"
python3 -c "import sentence_transformers; print('sentence-transformers: OK')" || echo "需要安装 sentence-transformers"

echo ""
echo "======================================"
echo "安装依赖（如果缺失）"
echo "======================================"
echo "pip install torch sentence-transformers"

echo ""
echo "======================================"
echo "运行微调（推荐配置）"
echo "======================================"
echo "cd backend"
echo "python scripts/finetune_embedding_mps.py \\"
echo "  --epochs 3 \\"
echo "  --batch-size 8 \\"
echo "  --subset-size 200"

echo ""
echo "======================================"
echo "完整数据训练（耗时较长）"
echo "======================================"
echo "python scripts/finetune_embedding_mps.py \\"
echo "  --epochs 5 \\"
echo "  --batch-size 8 \\"
echo "  --full-data"

echo ""
echo "======================================"
echo "注意事项"
echo "======================================"
echo "1. MacBook Air 无风扇，建议在凉爽环境运行"
echo "2. 训练时间约 5-15 分钟（取决于配置）"
echo "3. 如遇过热警告，可减少 batch-size 到 4"
echo "4. 推荐先用 --subset-size 200 快速测试"

