import os
import json
import re
import pandas as pd
from openai import OpenAI
from pathlib import Path
import time
from typing import Dict, Any

# --- 1. 配置  ---
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
if not DEEPSEEK_API_KEY:
    raise ValueError("错误：请设置 'DEEPSEEK_API_KEY' 环境变量。")

client = OpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com"
)

# --- 2. 核心函数：一次性规范化一行中的多个字段 ---

def build_normalization_prompt(raw_data: Dict[str, Any]) -> tuple[str, str]:
    """
    构建一个动态的提示，要求LLM规范化一个字典中所有需要规范化的字段。
    """
    system_prompt = """
    你是一个高精度的中文数据规范化引擎。你的唯一任务是将用户提供的JSON对象中，所有“raw_”开头的字段，转换成结构化的中文输出。
    严格按照指定的JSON格式返回，只返回JSON对象，不要有任何其他解释。

    **规范化规则 (必须严格遵守):**

    1.  **"raw_data_size"** (例如: "164个问题", "约1000+", "N/A"):
        - 规范为 `{"quantity": <number | null>, "unit": "<string | null>"}`
        - `quantity` 是核心数值 (例如 164, 1000, 3135.95)。
        - `unit` **仅仅**是 **quantity 的直接计量单位** (例如 "个问题", "条提示", "GB", "TB", "个样本")。
        - **[重要!]** `unit` 字段**绝不能**包含除直接计量单位之外的任何其他描述性信息（例如 "的30种编程语言代码" 这种信息是无关的，必须丢弃）。
        - 如果没有数值，`quantity` 必须为 null。

    2.  **"raw_last_updated"** (例如: "2024.09", "July 2021", "2021"):
        - 规范为 `{"year": <number | null>, "month": <number | null>, "day": <number | null>}`
        - 如果某部分未知，将其设为 null (例如 "2021" -> {"year": 2021, "month": null, "day": null})。

    3.  **"raw_language"**, **"raw_dimension"**, **"raw_evaluation_method"**, **"raw_problem_domain"**, **"raw_source_type"**:
        - 这些字段是“多选”字段。
        - 规范为 **JSON列表 (Array)**，包含所有提取到的中文关键词。
        - 例如: "Python, C++ 和多语言" -> `["Python", "C++", "多语言"]`
        - 例如: "pass@k 和 CodeBLEU" -> `["pass@k", "CodeBLEU"]`
        - 如果找不到，返回空列表 `[]`。

    4.  **"raw_problem_difficulty"** (任务难度):
        - 这是一个“单选”分类字段。
        - 必须从以下 **中文枚举值** 中选择一个最接近的：
          `"入门级"`, `"竞赛级"`, `"工程级"`, `"未知"`
        - 如果无法分类，返回 `"未知"`。

    5.  **"raw_context_dependency"** (上下文依赖):
        - 这是一个“单选”分类字段。
        - 必须从以下 **中文枚举值** 中选择一个最接近的：
          `"单函数"`, `"单文件"`, `"多文件/项目级"`, `"未知"`

    6.  **"raw_dataset_license"** (数据集许可证):
        - 这是一个“单选”分类字段。
        - 必须从以下 **标准标识符** 中选择一个最接近的：
          `"MIT"`, `"Apache 2.0"`, `"GPL-3.0"`, `"BSD"`, `"CC-BY-SA 4.0"`, `"仅供学术研究"`, `"未知"`

    **输出JSON结构 (必须严格遵守):**
    {
      "data_size": {"quantity": <number | null>, "unit": "<string | null>"},
      "last_updated": {"year": <number | null>, "month": <number | null>, "day": <number | null>},
      "language": ["<string>", "..."],
      "dimension": ["<string>", "..."],
      "evaluation_method": ["<string>", "..."],
      "problem_domain": ["<string>", "..."],
      "source_type": ["<string>", "..."],
      "problem_difficulty": "<'入门级' | '竞赛级' | '工程级' | '未知'>",
      "context_dependency": "<'单函数' | '单文件' | '多文件/项目级' | '未知'>",
      "dataset_license": "<'MIT' | 'Apache 2.0' | 'GPL-3.0' | ... | '未知'>"
    }
    """
    
    # 将原始数据字典转换为JSON字符串作为用户输入
    user_prompt = json.dumps(raw_data, ensure_ascii=False)
    
    return system_prompt, user_prompt

def normalize_row_fields(row: pd.Series, fields_to_normalize: list) -> Dict[str, Any]:
    """
    为DataFrame的 *每一行* 调用LLM，规范化所有指定的字段。
    """
    
    # 1. 准备要发送给LLM的原始数据
    data_to_normalize = {}
    for field in fields_to_normalize:
        raw_value = row.get(field)
        if pd.isna(raw_value) or str(raw_value).strip() == "":
            raw_value = None # 将空的/NaN值设为None
        data_to_normalize[f"raw_{field}"] = raw_value

    # 2. 构建提示
    system_prompt, user_prompt = build_normalization_prompt(data_to_normalize)

    # 3. 调用API
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0,
            stream=False,
            response_format={"type": "json_object"} # 使用JSON模式
        )
        
        response_content = response.choices[0].message.content
        normalized_data = json.loads(response_content)
        
        # 4. 扁平化LLM的返回结果，以便加入DataFrame
        flat_result = {}
        for main_key, value in normalized_data.items():
            if main_key in ["data_size", "last_updated"] and isinstance(value, dict):
                # 规范化 "data_size" -> "data_size_quantity", "data_size_unit"
                # 规范化 "last_updated" -> "last_updated_year", "last_updated_month", ...
                for sub_key, sub_value in value.items():
                    flat_result[f"{main_key}_{sub_key}"] = sub_value
            elif isinstance(value, list):
                # 规范化 "language" -> "language_normalized" (保存为列表的字符串形式)
                flat_result[f"{main_key}_normalized"] = str(value) # 保存为 '["Python", "C++"]'
            else:
                # 规范化 "problem_difficulty" -> "problem_difficulty_normalized" (保存为 "入门级")
                flat_result[f"{main_key}_normalized"] = value

        return flat_result

    except Exception as e:
        print(f"  规范化失败 (输入: {user_prompt}): {e}")
        return {"error": str(e)}

# --- 3. 主程序 ---
def main():
    script_path = Path(__file__).resolve()
    project_root = script_path.parent
    
    results_folder = project_root / "results"
    # 输入文件
    input_csv_path = results_folder / "new_detailed_benchmarks_info.csv"
    # 输出文件
    output_csv_path = results_folder / "new_detailed_benchmarks_standardized_info.csv"

    if not input_csv_path.exists():
        print(f"错误：未找到输入文件 {input_csv_path}")
        print("请先运行 'new_find_benchmark_links.py' 脚本来生成原始CSV。")
        return

    print(f"正在读取原始CSV文件: {input_csv_path}")
    df = pd.read_csv(input_csv_path)

    # --- 核心改进 ---
    # 定义我们希望LLM规范化的所有列
    fields_to_normalize = [
        'data_size', 'last_updated', 'language', 'dimension',
        'evaluation_method', 'problem_domain', 'source_type',
        'problem_difficulty', 'context_dependency', 'dataset_license'
    ]
    
    # 检查这些列是否存在
    missing_cols = [col for col in fields_to_normalize if col not in df.columns]
    if missing_cols:
        print(f"警告：原始CSV文件中缺少以下列，将跳过对它们的规范化: {missing_cols}")
        fields_to_normalize = [col for col in fields_to_normalize if col in df.columns]

    if not fields_to_normalize:
        print("没有找到任何可以规范化的列。程序退出。")
        return

    print(f"开始规范化以下列: {fields_to_normalize}")
    print(f"总共需要处理 {len(df)} 行数据... (这将调用 {len(df)} 次API，请耐心等待)")

    normalized_data_list = []
    
    total_rows = len(df)
    for index, row in df.iterrows():
        print(f"\n--- 正在处理第 {index + 1}/{total_rows} 行 (Benchmark: {row.get('benchmark_name')}) ---")
        raw_values = {field: row.get(field) for field in fields_to_normalize}
        print(f"原始数据: {raw_values}")
        
        normalized_result_dict = normalize_row_fields(row, fields_to_normalize)
        print(f"规范化结果: {normalized_result_dict}")
        
        normalized_data_list.append(normalized_result_dict)
        
        # 速率限制
        time.sleep(1) # 1秒/次调用。如果你的API限制更宽松，可以调低

    # --- 整合数据 ---
    print("\n--- 规范化完成，正在整合数据 ---")
    
    normalized_df = pd.DataFrame(normalized_data_list, index=df.index)
    df_combined = pd.concat([df, normalized_df], axis=1)

    # --- 动态构建最终列顺序 ---
    final_cols = ['source_paper', 'benchmark_name', 'dataset_url', 'task_description']
    
    # 规范化的字段
    normalized_map = {
        'data_size': ['data_size_quantity', 'data_size_unit'],
        'last_updated': ['last_updated_year', 'last_updated_month', 'last_updated_day'],
        'language': ['language_normalized'],
        'dimension': ['dimension_normalized'],
        'evaluation_method': ['evaluation_method_normalized'],
        'problem_domain': ['problem_domain_normalized'],
        'source_type': ['source_type_normalized'],
        'problem_difficulty': ['problem_difficulty_normalized'],
        'context_dependency': ['context_dependency_normalized'],
        'dataset_license': ['dataset_license_normalized']
    }
    
    # 先添加原始列和规范化后的列
    for raw_col in fields_to_normalize:
        if raw_col in df_combined.columns:
            final_cols.append(raw_col) # 添加原始列 (例如 "164个问题")
            for norm_col in normalized_map.get(raw_col, []):
                if norm_col in df_combined.columns:
                    final_cols.append(norm_col) # 添加规范化列 (例如 164)
    
    # 添加所有带 _quote 的溯源列
    quote_cols = [col for col in df_combined.columns if col.endswith('_quote')]
    final_cols.extend(quote_cols)
    
    # 添加任何剩余的列 (例如 error, unique_features 等)
    other_cols = [col for col in df_combined.columns if col not in final_cols]
    final_cols.extend(other_cols)
    
    # 确保没有重复的列
    final_cols_dedup = list(dict.fromkeys(final_cols))
    df_combined = df_combined[final_cols_dedup]

    # 5. 保存到新的CSV文件
    df_combined.to_csv(output_csv_path, index=False, encoding='utf-8-sig')

    print(f"\n✅ 全部处理完成！")
    print(f"已将规范化后的数据库保存到: {output_csv_path}")
    
    print("\n规范化数据预览 (相关列):")
    preview_cols = [
        'data_size', 'data_size_quantity', 'data_size_unit', 
        'last_updated', 'last_updated_year',
        'problem_difficulty', 'problem_difficulty_normalized',
        'language', 'language_normalized'
    ]
    preview_cols_exist = [col for col in preview_cols if col in df_combined.columns]
    print(df_combined[preview_cols_exist].head().to_markdown(index=False))


if __name__ == "__main__":
    main()
