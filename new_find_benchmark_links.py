import os
import json
import re  # 导入正则表达式库
from openai import OpenAI
import pandas as pd
from pathlib import Path

# --- 1. 配置 (已改进) ---
# 最佳实践：从环境变量读取API Key，而不是硬编码。
# 请在运行脚本前在终端设置环境变量：
# (PowerShell): $env:DEEPSEEK_API_KEY="sk-..."
# (CMD): set DEEPSEEK_API_KEY=sk-...
# (Linux/macOS): export DEEPSEEK_API_KEY="sk-..."
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
if not DEEPSEEK_API_KEY:
    raise ValueError("错误：请设置 'DEEPSEEK_API_KEY' 环境变量。")

client = OpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com"
)


# --- 2. 新增函数 (实现请求 2：减少Token) ---
def preprocess_text(full_text: str) -> str:
    """
    在将文本发送给LLM之前对其进行预处理。
    1. 删除参考文献、附录等噪音部分。
    2. 截取核心部分（例如前5000字符）以节省Token。
    """
    # 定义停止词/章节标题，匹配到这些词时，后续内容将被截断
    # 使用正则表达式，(?im) 标志表示忽略大小写(i)和多行模式(m)
    # \s* 表示匹配任意空白符（包括换行）
    stop_patterns = [
        r"^\s*References\s*$",
        r"^\s*Bibliography\s*$",
        r"^\s*Acknowledgements\s*$",
        r"^\s*Acknowledgments\s*$",
        r"^\s*Appendix\s*$",
        r"^\s*附录\s*$",
        r"^\s*参考文献\s*$"
    ]
    
    # 将所有模式合并为一个正则表达式
    # (?:...) 是一个非捕获组
    stop_regex = re.compile(r"(\n\s*(?:" + "|".join(stop_patterns) + r")\s*\n)", re.IGNORECASE | re.MULTILINE)
    
    # 按第一个匹配到的停止词分割文本，只保留[0]（即停止词之前的内容）
    cleaned_text = stop_regex.split(full_text, maxsplit=1)[0]
    
    # 截取前16000个字符，这通常足以覆盖摘要、引言和方法部分
    # 16000字符大约对应 3000-4000 个Token，是一个合理的范围
    snippet = cleaned_text[:16000]  # 这里使用16000字符以适应更长的文本需求
    
    if len(snippet) < len(full_text) and len(snippet) > 0:
        print(f"文本已预处理：从 {len(full_text)} 字符缩减到 {len(snippet)} 字符 (已移除参考文献等)。")
    elif len(snippet) == 0 and len(full_text) > 0:
         print(f"警告：预处理后文本为空！可能切分逻辑有误。将使用原始文本的前5000字符。")
         snippet = full_text[:5000] # Fallback
    else:
        print(f"文本已预处理：保留原文 {len(snippet)} 字符。")
    
    return snippet


# --- 3. 核心函数 (实现请求 1 和 3：更丰富维度 + 溯源) ---
def build_benchmark_finder_prompt(text_content: str) -> tuple[str, str]:
    """
    构建一个精确的提示，指导LLM提取 *详细* 信息并 *附带原文位置*。
    """
    system_prompt = """
    你是一位极其细致的科研助理，专注于从学术论文中提取AI代码评测基准的元数据。
    你的任务是：针对提供的论文文本，找出其中描述的 *每一个* 字段，并同时提供：
    1. 提取的 **值 (value)**。
    2. 支持该值的 **原文引述 (source_quote)**，即你从文本中看到该信息的依据。

    严格按照指定的嵌套JSON格式返回。如果某个字段的信息在文中 *明确* 找不到，请将 "value" 和 "source_quote" 均设为 null。

    **需要提取的JSON结构 (v4 - 扩展版):**
    {
      "benchmark_name": {
        "value": "评测基准的官方名称 (例如 'HumanEval', 'MBPP')",
        "source_quote": "原文中定义或提到该名称的句子 (例如 'We introduce HumanEval, a new evaluation set...')"
      },
      "dataset_url": {
        "value": "官网链接或代码仓库URL (例如 'https://github.com/openai/human-eval')",
        "source_quote": "原文中提供该URL的句子 (例如 'The full dataset is available at https://github.com/...')"
      },
      "task_description": {
        "value": "【请用中文描述】该评测基准的主要任务",
        "source_quote": "原文中描述其任务的句子 (例如 '...measure functional correctness for synthesizing programs from docstrings.')"
      },
      "dimension": {
        "value": "【请用中文描述】评测维度或关注点 (例如 '代码生成正确性', '多语言能力')",
        "source_quote": "原文中描述其评测维度的句子"
      },
      "evaluation_method": {
        "value": "【请用中文描述】评估方法 (例如 'pass@k', '执行单元测试', '代码BLEU分数')",
        "source_quote": "原文中描述其如何评估的句子 (例如 'We use the pass@k metric, where k=1, 10, 100.')"
      },
      "context_dependency": {
        "value": "【请用中文描述】上下文依赖范围 (例如 '单函数', '多文件项目')",
        "source_quote": "原文中描述其上下文需求的句子 (例如 'The problems are single-function...')"
      },
      "problem_domain": {
        "value": "【请用中文描述】问题所属专业领域 (例如 '算法', 'Web开发', '数据科学')",
        "source_quote": "原文中描述其问题类型的句子 (例如 '...tasks are algorithmic in nature...')"
      },
      "problem_difficulty": {
        "value": "【请用中文描述】任务难度 (例如 '入门级', '竞赛级', '工程级')",
        "source_quote": "原文中描述其难度的句子 (例如 '...consists of 974 entry-level tasks...')"
      },
      "language": {
        "value": "【请用中文描述】涉及的主要编程语言",
        "source_quote": "原文中提到语言的句子 (例如 'The dataset consists of 164 Python programming problems.')"
      },
      "data_size": {
        "value": "【请用中文描述】数据集规模描述",
        "source_quote": "原文中提到数据规模的句子 (例如 'It includes 974 entry-level tasks...')"
      },
      "source_type": {
        "value": "【请用中文描述】数据来源描述",
        "source_quote": "原文中描述数据来源的句子 (例如 'Tasks were constructed manually...')"
      },
      "last_updated": {
        "value": "最后更新或发布时间 (例如 '2021', '2024.09')",
        "source_quote": "原文中提到日期的句子 (例如 'The dataset was collected in September 2024...')"
      },
      "build_type": {
        "value": "【请用中文描述】构建类型 (例如 '官方自建', '社区贡献')",
        "source_quote": "原文中描述构建者身份的句子"
      },
      "contamination_status": {
        "value": "【请用中文描述】数据污染状态 (例如 '高污染风险', '抗污染设计')",
        "source_quote": "原文中讨论数据污染或新鲜度的句子 (例如 '...designed to be contamination-free...')"
      },
      "dataset_license": {
        "value": "【请用中文描述】数据集的许可证 (例如 'MIT', '仅供学术研究')",
        "source_quote": "原文中提及许可证的句子 (例如 'The dataset is released under the MIT License.')"
      },
      "unique_features": {
        "value": "【请用中文描述】该基准的独特之处或额外信息 (即'额外列')",
        "source_quote": "原文中描述其特殊性的句子 (例如 'Unlike previous benchmarks, RMCBench focuses on malicious code generation.')"
      }
    }
    """
    user_prompt = f"**请分析以下论文文本，并严格按照JSON结构提取所有字段及其原文引述:**\n---\n{text_content}\n---"
    return system_prompt, user_prompt


# --- 4. 核心函数：调用API (保持不变) ---
def find_benchmark_info_in_text(text: str) -> dict:
    """
    使用 DeepSeek 模型从论文文本中查找代码评测基准详细信息。
    """
    if not text.strip():
        print("警告：输入的文本为空。")
        return {}

    system_prompt, user_prompt = build_benchmark_finder_prompt(text)

    try:
        response = client.chat.completions.create(
            model="deepseek-chat", # 确保你使用的是有权限且能力足够的模型
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0, # 提取任务使用低温
            stream=False
        )
        response_content = response.choices[0].message.content
        cleaned_response = response_content.strip().replace('```json', '').replace('```', '').strip()
        if cleaned_response.startswith('"') and cleaned_response.endswith('"'):
             cleaned_response = cleaned_response[1:-1].replace('\\"', '"')

        extracted_json = json.loads(cleaned_response)
        
        # 检查最关键的字段
        if not extracted_json.get("benchmark_name") or not extracted_json.get("benchmark_name").get("value"):
             print("警告：未能从文本中明确提取到 benchmark_name 的值。")
        return extracted_json

    except json.JSONDecodeError as json_err:
        print(f"JSON解析错误: {json_err}")
        print("--- 原始模型输出 ---")
        print(response_content if 'response_content' in locals() else "N/A")
        print("--------------------")
        return {"error": "JSONDecodeError", "original_response": response_content if 'response_content' in locals() else "N/A"}
    except Exception as e:
        print(f"处理文本时发生API或其他错误: {e}")
        return {"error": str(e), "original_response": "API call failed"}


# --- 5. 新增函数 (加入原文位置：扁平化数据以便存入CSV) ---
def flatten_extracted_data(nested_data: dict, source_paper: str) -> dict:
    """
    将LLM返回的嵌套JSON扁平化，以便存入CSV。
    例如：{"benchmark_name": {"value": "...", "source_quote": "..."}}
    变为：{"benchmark_name": "...", "benchmark_name_quote": "..."}
    """
    flat_data = {"source_paper": source_paper}
    
    # 遍历所有在prompt中定义的键
    all_fields = [
        "benchmark_name", "dataset_url", "task_description", "dimension",
        "evaluation_method", "context_dependency", "problem_domain", 
        "problem_difficulty", "language", "data_size", "source_type",
        "last_updated", "build_type", "contamination_status", 
        "dataset_license", "unique_features"
    ]
    
    for field in all_fields:
        item = nested_data.get(field)
        
        if isinstance(item, dict):
            # 正常情况：提取 value 和 source_quote
            flat_data[field] = item.get("value")
            flat_data[f"{field}_quote"] = item.get("source_quote")
        else:
            # 异常情况：LLM可能返回了 null 或其他非字典结构
            flat_data[field] = item # 可能是 null
            flat_data[f"{field}_quote"] = None
            
    # 检查是否有错误信息
    if "error" in nested_data:
        flat_data["error"] = nested_data.get("error")
        flat_data["original_response"] = nested_data.get("original_response")

    return flat_data


# --- 6. 主程序 (已更新) ---
if __name__ == "__main__":
    script_path = Path(__file__).resolve()
    project_root = script_path.parent
    
    papers_folder = project_root / "papers_info/2102.04664v2_output" # mineru输出文件夹
    results_folder = project_root / "results"
    results_folder.mkdir(exist_ok=True)

    print(f"正在文件夹 '{papers_folder}' 及其所有子文件夹中递归搜索 .md 文件...")
    #查找 .md 文件
    input_files = list(papers_folder.glob("**/*.md")) 

    if not input_files:
        print(f"错误：在 '{papers_folder}' 及其子文件夹中没有找到任何 .md 文件。")
    else:
        print(f"成功找到 {len(input_files)} 个文件，准备开始处理...")

    all_found_benchmarks_flat = []

    for file_path in input_files:
        relative_path = file_path.relative_to(papers_folder)
        
        # 检查路径是否为文件 (避免读取mineru创建的.md结尾的文件夹)
        if file_path.is_file():
            print(f"\n--- 正在处理文件: {relative_path} ---")
            try:
                # 1. 读取完整文本
                full_text = file_path.read_text(encoding='utf-8')
                
                # 2. 预处理文本 (减少Token)
                text_snippet = preprocess_text(full_text)

                # 3. 调用LLM提取嵌套数据
                nested_benchmark_info = find_benchmark_info_in_text(text_snippet)
                
                # 4. 扁平化数据
                flat_benchmark_info = flatten_extracted_data(nested_benchmark_info, str(relative_path))
                
                print("提取结果 (扁平化):", json.dumps(flat_benchmark_info, indent=2, ensure_ascii=False))

                # 5. 添加到总列表 (只添加有基准名称的)
                if flat_benchmark_info.get("benchmark_name"):
                    all_found_benchmarks_flat.append(flat_benchmark_info)
                elif "error" in flat_benchmark_info:
                     print(f"处理文件 {relative_path} 时遇到错误，已跳过。")
                else:
                    print(f"在文件 {relative_path} 中未提取到 benchmark_name，已跳过。")
                     
            except Exception as e:
                print(f"读取或处理文件 '{relative_path}' 时发生未知错误: {e}")
        else:
            # 如果是文件夹，则跳过
            print(f"\n--- 正在跳过文件夹: {relative_path} ---")
        
        print("-" * 30)

    # --- 保存结果 (列顺序已更新) ---
    if all_found_benchmarks_flat:
        df = pd.DataFrame(all_found_benchmarks_flat)
        
        # 定义基础列 (丰富了维度)
        base_columns = [
            "benchmark_name", "dataset_url", "task_description", "dimension",
            "evaluation_method", "context_dependency", "problem_domain", 
            "problem_difficulty", "language", "data_size", "source_type",
            "last_updated", "build_type", "contamination_status", 
            "dataset_license", "unique_features" # "额外列"
        ]
        
        # 动态生成带引述的完整列列表 (实现请求 3)
        desired_columns = ['source_paper']
        for col in base_columns:
            desired_columns.append(col)
            desired_columns.append(f"{col}_quote") # 为每个字段添加引述列
        
        # 排序
        existing_columns_ordered = [col for col in desired_columns if col in df.columns]
        other_columns = [col for col in df.columns if col not in existing_columns_ordered]
        final_columns = existing_columns_ordered + other_columns
        df = df[final_columns]

        output_filename = results_folder / "new_detailed_benchmarks_info.csv"
        df.to_csv(output_filename, index=False, encoding='utf-8-sig')

        print(f"\n✅ 全部处理完成！从 {len(input_files)} 个路径中（已跳过文件夹）识别出 {len(all_found_benchmarks_flat)} 条基准信息。")
        print(f"数据集已保存到: {output_filename}")
        print("\n结果预览 (前5行，部分核心列):")
        preview_cols = ['source_paper', 'benchmark_name', 'dataset_url', 'task_description', 'evaluation_method', 'context_dependency']
        print(df.head()[preview_cols].to_markdown(index=False))
    else:
        print(f"\n❌ 未能从 {len(input_files)} 个路径中成功识别出有效的代码评测基准信息。")
