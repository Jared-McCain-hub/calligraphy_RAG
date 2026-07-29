"""Generate training data for embedding fine-tuning from existing knowledge."""

import json
import random
from pathlib import Path
from typing import List, Dict

BACKEND_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = BACKEND_ROOT / "data"
OUTPUT_DIR = BACKEND_ROOT / "training_data"


def load_json_data(filename: str) -> List[Dict]:
    """Load JSON data from data directory."""
    filepath = DATA_DIR / filename
    if not filepath.exists():
        return []
    with open(filepath, encoding="utf-8") as f:
        return json.load(f)


def generate_calligrapher_questions(calligrapher: Dict) -> List[Dict]:
    """Generate question-answer pairs for a calligrapher."""
    qa_pairs = []
    name = calligrapher.get("name_cn", "")
    era = calligrapher.get("era", "")
    biography = calligrapher.get("biography", "")
    achievements = calligrapher.get("achievements", "")
    works = calligrapher.get("representative_works", [])
    
    # 1. 定义类问题
    if biography:
        qa_pairs.append({
            "query": f"谁是{name}？",
            "positive": f"{name}是{era}书法家。{biography}",
            "type": "definition"
        })
    
    # 2. 特点类问题
    if achievements:
        qa_pairs.append({
            "query": f"{name}的书法特点是什么？",
            "positive": f"{name}的书法特点：{achievements}",
            "type": "characteristic"
        })
    
    # 3. 代表作类问题
    if works:
        works_str = "、".join(works)
        qa_pairs.append({
            "query": f"{name}的代表作有哪些？",
            "positive": f"{name}的代表作包括：{works_str}。",
            "type": "works"
        })
    
    # 4. 朝代类问题
    if era:
        qa_pairs.append({
            "query": f"{name}是哪个朝代的书法家？",
            "positive": f"{name}是{era}书法家。",
            "type": "era"
        })
    
    return qa_pairs


def generate_term_questions(term: Dict) -> List[Dict]:
    """Generate question-answer pairs for a term."""
    qa_pairs = []
    name = term.get("name_cn", "")
    name_en = term.get("name_en", "")
    definition = term.get("definition", "")
    usage_notes = term.get("usage_notes", "")
    category = term.get("category", "")
    
    # 1. 定义类问题
    if definition:
        qa_pairs.append({
            "query": f"什么是{name}？",
            "positive": f"{name}是书法术语。{definition}",
            "type": "definition"
        })
        
        qa_pairs.append({
            "query": f"{name}的定义是什么？",
            "positive": definition,
            "type": "definition"
        })
    
    # 2. 英文名称问题
    if name_en:
        qa_pairs.append({
            "query": f"{name}的英文名称是什么？",
            "positive": f"{name}的英文名称是{name_en}。",
            "type": "translation"
        })
    
    # 3. 用法类问题
    if usage_notes:
        qa_pairs.append({
            "query": f"{name}在书法中如何应用？",
            "positive": usage_notes,
            "type": "usage"
        })
    
    return qa_pairs


def generate_work_questions(work: Dict) -> List[Dict]:
    """Generate question-answer pairs for a work."""
    qa_pairs = []
    title = work.get("title_cn", "")
    title_en = work.get("title_en", "")
    calligrapher = work.get("calligrapher", "")
    era = work.get("era", "")
    style = work.get("style", "")
    description = work.get("description", "")
    significance = work.get("significance", "")
    
    # 1. 作者类问题
    if calligrapher:
        qa_pairs.append({
            "query": f"《{title}》是谁写的？",
            "positive": f"《{title}》是{calligrapher}的作品。",
            "type": "author"
        })
    
    # 2. 朝代类问题
    if era:
        qa_pairs.append({
            "query": f"《{title}》是哪个朝代的作品？",
            "positive": f"《{title}》是{era}的作品。",
            "type": "era"
        })
    
    # 3. 书体类问题
    if style:
        qa_pairs.append({
            "query": f"《{title}》是什么书体？",
            "positive": f"《{title}》是{style}。",
            "type": "style"
        })
    
    # 4. 描述类问题
    if description:
        qa_pairs.append({
            "query": f"《{title}》是什么样的作品？",
            "positive": description,
            "type": "description"
        })
    
    return qa_pairs


def generate_negative_samples(positive: str, all_texts: List[str], num_negatives: int = 1) -> List[str]:
    """Generate negative samples from other texts."""
    # 简单策略：随机选择其他文本作为负样本
    negatives = []
    for _ in range(num_negatives):
        negative = random.choice(all_texts)
        if negative != positive:
            negatives.append(negative)
    return negatives


def generate_training_data():
    """Generate complete training dataset."""
    print("=" * 60)
    print("生成微调训练数据")
    print("=" * 60)
    
    # 加载所有数据
    print("\n[1/4] 加载知识数据...")
    calligraphers = load_json_data("calligraphers.json")
    terms = load_json_data("terms.json")
    works = load_json_data("works.json")
    eras = load_json_data("eras.json")
    styles = load_json_data("styles.json")
    
    print(f"  书法家: {len(calligraphers)} 位")
    print(f"  术语: {len(terms)} 个")
    print(f"  作品: {len(works)} 件")
    print(f"  朝代: {len(eras)} 个")
    print(f"  书体: {len(styles)} 种")
    
    # 生成问答对
    print("\n[2/4] 生成问答对...")
    qa_pairs = []
    
    for c in calligraphers:
        qa_pairs.extend(generate_calligrapher_questions(c))
    
    for t in terms:
        qa_pairs.extend(generate_term_questions(t))
    
    for w in works:
        qa_pairs.extend(generate_work_questions(w))
    
    print(f"  生成问答对: {len(qa_pairs)} 条")
    
    # 收集所有文本用于负采样
    all_texts = []
    for qa in qa_pairs:
        all_texts.append(qa["positive"])
    
    # 生成训练数据（添加负样本）
    print("\n[3/4] 生成训练数据（添加负样本）...")
    training_data = []
    
    for qa in qa_pairs:
        # 每个正样本配1个负样本
        negatives = generate_negative_samples(qa["positive"], all_texts, num_negatives=1)
        
        training_data.append({
            "query": qa["query"],
            "positive": qa["positive"],
            "negative": negatives[0] if negatives else "",
            "type": qa["type"]
        })
    
    print(f"  训练样本: {len(training_data)} 条")
    
    # 统计类型分布
    type_counts = {}
    for item in training_data:
        t = item["type"]
        type_counts[t] = type_counts.get(t, 0) + 1
    
    print("\n  类型分布:")
    for t, count in sorted(type_counts.items(), key=lambda x: -x[1]):
        print(f"    {t}: {count} 条")
    
    # 保存数据
    print("\n[4/4] 保存训练数据...")
    OUTPUT_DIR.mkdir(exist_ok=True)
    
    # 保存完整训练数据
    output_file = OUTPUT_DIR / "embedding_training_data.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(training_data, f, ensure_ascii=False, indent=2)
    print(f"  保存到: {output_file}")
    
    # 保存为 HuggingFace 格式
    hf_data = []
    for item in training_data:
        hf_data.append({
            "query": item["query"],
            "pos": [item["positive"]],
            "neg": [item["negative"]]
        })
    
    hf_file = OUTPUT_DIR / "hf_format_data.json"
    with open(hf_file, "w", encoding="utf-8") as f:
        json.dump(hf_data, f, ensure_ascii=False, indent=2)
    print(f"  HuggingFace格式: {hf_file}")
    
    # 保存纯文本格式（用于其他框架）
    txt_file = OUTPUT_DIR / "training_data.txt"
    with open(txt_file, "w", encoding="utf-8") as f:
        for item in training_data:
            f.write(f"QUERY: {item['query']}\n")
            f.write(f"POS: {item['positive']}\n")
            f.write(f"NEG: {item['negative']}\n")
            f.write("\n")
    print(f"  文本格式: {txt_file}")
    
    print("\n" + "=" * 60)
    print("✅ 训练数据生成完成！")
    print("=" * 60)
    print(f"总计: {len(training_data)} 条训练样本")
    print(f"输出目录: {OUTPUT_DIR}")
    
    return training_data


if __name__ == "__main__":
    random.seed(42)  # 保证可重复性
    generate_training_data()
