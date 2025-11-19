import os
import json
from openai import OpenAI
import pandas as pd
from pathlib import Path

# --- 1. 配置 ---
DEEPSEEK_API_KEY = "sk"

# 检查密钥是否已填写
if not DEEPSEEK_API_KEY or DEEPSEEK_API_KEY == "sk-...":
    raise ValueError("请在代码中替换 'sk-...' 为你的真实 DeepSeek API 密钥")

# 初始化客户端，指向DeepSeek的API地址
client = OpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com"
)

# --- 2. 核心提取函数 ---
def extract_data_from_text_deepseek(text: str) -> dict:
    """
    使用 DeepSeek 模型从学术论文文本中提取元数据。
    """
    if not text.strip():
        print("警告：输入的文本为空。")
        return {}

    # 这是指导模型行为的系统提示 (System Prompt)
    system_prompt = """
    你是一位专业的学术研究助理。你的任务是从一篇学术论文的文本中，精准地提取出核心的元数据，并严格按照指定的JSON格式返回。
    请只返回一个干净的JSON对象，不要包含任何额外的解释、注释或Markdown标记。

    **需要提取的JSON结构:**
    {
      "title": "论文的完整标题",
      "authors": ["作者1的全名", "作者2的全名"],
      "abstract": "论文的完整摘要内容
      ,
      "keywords": ["关键词1", "关键词2"],
      "journal_name": "发表论文的期刊或会议名称",
      "publication_year": "发表年份 (整数)",
      "doi": "数字对象标识符 (DOI)"
    }

    如果某个字段在文本中找不到，请将其值设为 null。对于作者和关键词，如果找不到，请返回一个空列表 `[]`。
    """
    
    # 这是包含具体论文内容的用户提示 (User Prompt)
    user_prompt = f"""
    **待处理的论文文本:**
    ---
    {text}
    ---
    **提取出的JSON元数据:**
    """

    try:
        # --- 重点：在这里使用你配置好的 client 来调用 DeepSeek API ---
        response = client.chat.completions.create(
            model="deepseek-chat", # 使用DeepSeek的模型
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0, # 设置为0，让输出更稳定、更具确定性
            stream=False
        )
        
        # 从返回结果中获取模型生成的内容
        response_content = response.choices[0].message.content
        
        # 清理可能的Markdown标记
        cleaned_response = response_content.strip().replace('```json', '').replace('```', '').strip()
        
        # 解析为JSON对象
        extracted_json = json.loads(cleaned_response)
        return extracted_json
        
    except Exception as e:
        print(f"处理文本时发生错误: {e}")
        # 打印更多调试信息
        if 'response' in locals():
            print("--- API原始返回内容 ---")
            print(response)
        return {"error": str(e), "original_text_snippet": text[:300]}

# --- 3. 主程序 ---

if __name__ == "__main__":
    # --- 变化 1: 定义更智能的路径 ---
    # 获取当前脚本文件所在的路径
    script_path = Path(__file__).resolve()
    # 从脚本路径推断出项目的根目录 (脚本在agent/里，所以根目录是它的上一级的上一级)
    project_root = script_path.parent.parent
    # 定义你的.md文件所在的文件夹和输出结果的文件夹
    papers_folder = project_root / "paper3.md/2503.17502v1/auto"
    results_folder = project_root / "results"

    # --- 变化 2: 自动创建输出文件夹 ---
    # 确保输出文件夹存在，如果不存在就自动创建它
    results_folder.mkdir(exist_ok=True)
    
    # --- 变化 3: 在指定的文件夹中查找.md文件 ---
    md_files = list(papers_folder.glob("*.md"))
    
    if not md_files:
        print(f"错误：在文件夹 '{papers_folder}' 中没有找到任何 .md 文件。")
    else:
        print(f"成功找到 {len(md_files)} 个 .md 文件，准备开始处理...")

    all_extracted_data = []

    for md_file_path in md_files:
        print(f"\n--- 正在处理文件: {md_file_path.name} ---")
        try:
            text_content = md_file_path.read_text(encoding='utf-8')
            extracted_data = extract_data_from_text_deepseek(text_content)
            extracted_data['source_file'] = md_file_path.name
            print("提取结果:", json.dumps(extracted_data, indent=2, ensure_ascii=False))
            
            if "error" not in extracted_data:
                all_extracted_data.append(extracted_data)
        except Exception as e:
            print(f"处理文件 '{md_file_path.name}' 时发生未知错误: {e}")
        
        print("-" * 30)

    # --- 保存结果部分 (输出路径已更新) ---
    if all_extracted_data:
        df = pd.DataFrame(all_extracted_data)
        if 'source_file' in df.columns:
            cols = ['source_file'] + [col for col in df.columns if col != 'source_file']
            df = df[cols]
            
        # 将结果保存到指定的results文件夹中
        output_filename = results_folder / "final_dataset.csv"
        df.to_csv(output_filename, index=False, encoding='utf-8-sig')
        
        print(f"\n✅ 全部处理完成！成功提取了 {len(all_extracted_data)} 份文件的元数据。")
        print(f"数据集已保存到: {output_filename}")
        print("\n数据集预览:")
        print(df.head())
    else:
        print("\n❌ 未能从任何文件中成功提取数据。")
