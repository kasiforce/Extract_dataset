import os
import json
from openai import OpenAI
import pandas as pd
from pathlib import Path

# --- 1. 配置 ---
DEEPSEEK_API_KEY = "your_deepseek_api_key_here"  # 请替换为你的 DeepSeek API Key

client = OpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com"
)

# --- 2. 核心函数：构建查找 *详细* 基准信息的提示 (已更新) ---
def build_benchmark_finder_prompt(text_content: str) -> tuple[str, str]:
    """
    构建一个精确的提示，指导大模型从论文文本中查找代码评测基准的 *详细* 信息。
    返回系统提示和用户提示。
    """
    system_prompt = """
    你是一位专门研究AI代码能力评测的科研助理。
    你的任务是从提供的学术论文文本（通常是摘要、引言或方法部分）中，找出其中描述或引入的代码能力评测基准（Benchmark）。
    请提取该基准的官方名称、官网或代码仓库URL、主要任务描述，以及尽可能提取以下附加信息：
    - 评测维度 (Dimension/Focus)
    - 主要语言 (Language)
    - 数据来源 (Source)
    - 数据规模 (Data Size)
    - 更新或发布时间 (Update/Release Time)
    - 构建类型 (Type, 例如：官方构建, 社区贡献等)

    严格按照指定的JSON格式返回，只返回JSON对象，不要添加任何解释。

    **需要提取的JSON结构 (已更新):**
    {
      "benchmark_name": "评测基准的官方名称 (例如 'HumanEval', 'MBPP', 'RMCBench')",
      "dataset_url": "官网链接或代码仓库URL (例如 'https://github.com/...', 如果文中未明确提及则为 null)",
      "task_description": "【请用中文描述】该评测基准的主要任务或目标",
      "dimension": "【请用中文描述】评测维度或关注点 (例如 '代码生成正确性', '恶意代码生成抵抗力', 如果未提及则为 null)",
      "language": "【请用中文描述】涉及的主要编程语言 (例如 'Python', '多语言', 'English' 如果是通用描述, 如果未提及则为 null)",
      "source_type": "【请用中文描述】数据来源描述 (例如 '手动构建', 'GitHub开源代码', '竞赛题目', 如果未提及则为 null)",
      "data_size": "【请用中文描述】数据集规模描述 (例如 '164个问题', '473条提示', '约1000个样本', 如果未提及则为 null)",
      "last_updated": "最后更新或发布时间 (例如 '2021', '2024.09', 如果未提及则为 null)",
      "build_type": "【请用中文描述】构建类型 (例如 '官方自建', '社区贡献', '学术研究项目', 如果未提及则为 null)"
    }

    如果文本中没有明确提到某个字段的信息，请将其值设为 null。
    """

    user_prompt = f"**请分析以下论文文本，并提取其中描述的代码评测基准详细信息:**\n---\n{text_content}\n---"

    return system_prompt, user_prompt

# --- 3. 核心函数：调用API提取基准信息 (保持不变) ---
# 这个函数无需修改，因为它只是调用API和解析JSON
def find_benchmark_info_in_text(text: str) -> dict:
    """
    使用 DeepSeek 模型从论文文本中查找代码评测基准详细信息。
    """
    if not text.strip():
        print("警告：输入的文本为空。")
        return {}

    system_prompt, user_prompt = build_benchmark_finder_prompt(text) # 调用更新后的prompt构建函数

    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0,
            stream=False
        )
        response_content = response.choices[0].message.content
        cleaned_response = response_content.strip().replace('```json', '').replace('```', '').strip()
        if cleaned_response.startswith('"') and cleaned_response.endswith('"'):
             cleaned_response = cleaned_response[1:-1].replace('\\"', '"')

        extracted_json = json.loads(cleaned_response)
        if not extracted_json.get("benchmark_name"):
             print("警告：未能从文本中明确提取到 benchmark_name。")
        return extracted_json

    except json.JSONDecodeError as json_err:
        print(f"JSON解析错误: {json_err}")
        print("--- 原始模型输出 ---")
        print(response_content if 'response_content' in locals() else "N/A")
        print("--------------------")
        return {"error": "JSONDecodeError", "original_response": response_content if 'response_content' in locals() else "N/A"}
    except Exception as e:
        print(f"处理文本时发生API或其他错误: {e}")
        error_response_text = "N/A"
        if 'response_content' in locals():
            error_response_text = response_content
        elif 'response' in locals() and hasattr(response, 'text'):
             error_response_text = response.text
        return {"error": str(e), "original_response": error_response_text}


# --- 4. 主程序 (结果处理部分已更新) ---
if __name__ == "__main__":
    script_path = Path(__file__).resolve()
    project_root = script_path.parent.parent
    papers_folder = project_root / "papers_info" # 可以改成你的文件夹名
    results_folder = project_root / "results"
    results_folder.mkdir(exist_ok=True)

    print(f"正在文件夹 '{papers_folder}' 及其所有子文件夹中递归搜索 .md文件...")
    # 查找 .md文件
    input_files = list(papers_folder.glob("**/*.md")) 

    if not input_files:
        print(f"错误：在 '{papers_folder}' 及其子文件夹中没有找到任何 .md 或 .txt 文件。")
    else:
        print(f"成功找到 {len(input_files)} 个文件，准备开始处理...")

    all_found_benchmarks = []

    for file_path in input_files:
        relative_path = file_path.relative_to(papers_folder)
        
        # --- 核心修复：检查路径是否为文件 ---
        if file_path.is_file():
            print(f"\n--- 正在处理文件: {relative_path} ---")
            try:
                full_text = file_path.read_text(encoding='utf-8')
                text_snippet = full_text

                benchmark_info = find_benchmark_info_in_text(text_snippet)
                benchmark_info['source_paper'] = str(relative_path)

                print("提取结果:", json.dumps(benchmark_info, indent=2, ensure_ascii=False))

                if "error" not in benchmark_info and benchmark_info.get("benchmark_name"):
                    all_found_benchmarks.append(benchmark_info)
                elif "error" in benchmark_info:
                     print(f"处理文件 {relative_path} 时遇到错误，已跳过。")

            except Exception as e:
                # 捕获读取错误（虽然 Permission Denied 已经被 is_file 阻止了，但以防万一）
                print(f"读取或处理文件 '{relative_path}' 时发生未知错误: {e}")
        else:
            # 如果是文件夹（比如 paper3.md 本身），则跳过
            print(f"\n--- 正在跳过文件夹: {relative_path} ---")
        
        print("-" * 30)

    # --- 保存结果 (列顺序已更新) ---
    if all_found_benchmarks:
        df = pd.DataFrame(all_found_benchmarks)
        # 定义期望的列顺序，与 RMCBench 示例对应
        desired_columns = [
            'source_paper',
            'benchmark_name',
            'dimension',
            'language',
            'source_type',
            'data_size',
            'last_updated',
            'build_type',
            'dataset_url',
            'task_description'
        ]
        # 获取实际存在的列，并按期望顺序排列，不存在的列会自动忽略
        existing_columns_ordered = [col for col in desired_columns if col in df.columns]
        # 添加其他可能存在的列（比如 error 列）
        other_columns = [col for col in df.columns if col not in existing_columns_ordered]
        final_columns = existing_columns_ordered + other_columns
        df = df[final_columns]

        output_filename = results_folder / "detailed_benchmarks_info.csv"
        df.to_csv(output_filename, index=False, encoding='utf-8-sig')

        print(f"\n✅ 全部处理完成！从 {len(input_files)} 个文件中识别出 {len(all_found_benchmarks)} 条基准信息。")
        print(f"数据集已保存到: {output_filename}")
        print("\n结果预览:")
        print(df.head())
    else:
        print("\n❌ 未能从任何文件中成功识别出有效的代码评测基准信息。")

