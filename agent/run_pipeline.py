# 读取 md 文件（支持目录）
import datetime
import json
from pathlib import Path
from string import Template
from typing import Dict, LiteralString

from click import prompt
def split_text(text, max_len=6000):
    """按字符长度切分，避免超过 token 限制"""
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + max_len, len(text))
        chunks.append(text[start:end])
        start = end
    return chunks

def read_md_files(path: str) -> LiteralString:
    p = Path(path)
    files = []
    if p.is_dir():
        files = list(p.glob("**/*.md"))
    elif p.is_file():
        files = [p]
    else:
        raise FileNotFoundError(f"No file or directory: {path}")
    result = []
    for f in files:
        text = f.read_text(encoding="utf-8")
        result.append(text)
    return " ".join(result)

if __name__=="__main__":
    md_text=read_md_files("C:\\Users\\lmwtc\\PycharmProjects\\ChemPaperAgent\\paper1.md\\paper1\\auto\\paper1-simple.md")
    # print(md_text)


    PROMPT_TEMPLATE=Template("""你现在扮演“化学实验条件结构化抽取器”的角色。任务：从下面提供的实验文本中抽取“合成/制备”的所有条件参数，并以严格的 JSON 输出（唯一输出，且不带任何额外注释/解释）。如果某字段无法确认，请用 null、[] 或 {} 表示。不要输出非 JSON 文本。

=== 上下文开始 ===
$context
=== 上下文结束 ===

请按照以下 JSON schema 返回数据（严格遵守字段名和结构）：
{
  "document_id": "<string or null>",
  "reaction_name": "<string or null>",
  "precursors": [
     {
       "name": "<standardized name or raw name>",
       "raw": "<原文片段>",
       "amount": "<normalized string e.g. '0.5 g' or null>",
       "moles": "<e.g. '0.002 mol' or null>",
       "equivalents": "<e.g. '1.0 eq' or null>",
       "purity": "<e.g. '98%' or null>",
       "role": "<precursor/catalyst/ligand/oxidant/reductant/templating_agent/other or null>"
     }
  ],
  "solvents": [
    {"name":"", "raw":"", "volume":"", "concentration":""}
  ],
  "catalysts": [...],
  "additives": [...],
  "stoichiometry": "<string or null>",
  "apparatus": [],
  "atmosphere": "<string or null>",
  "temperature": [
    {"raw":"原文", "value": <number or null>, "unit":"°C or null", "stage":"step name or null"}
  ],
  "time": [
    {"raw":"原文", "value": <number or null>, "unit":"h/min/s or null", "step":"step name or null"}
  ],
  "pH": "<number or range or null>",
  "workup": {
    "quench": null,
    "extraction": null,
    "washing": null,
    "drying_agent": null,
    "concentration_method": null
  },
  "isolation": {
     "method": null,
     "yield": null,
     "physical_state": null,
     "purification": null
  },
  "characterization": [
      {"technique":"", "raw":"", "details":""}
  ],
  "notes": null,
  "extraction_hints": [
     {"field":"temperature", "hint":"对应上下文的 XX 段: '...'"}
  ],
  "confidence": 0.0
}

输出规范与要求（必须遵守）：
1. JSON 中每个数值字段同时提供原文片段（raw）和归一化字段（value/unit 或标准字符串）。
2. 对于化学品名称，尽可能标准化（例如 TiO2 -> "titanium dioxide" 作为 name，并在 raw 中保留原文）。
3. 如果上下文含多个步骤，务必在相关字段中用 step 或 stage 标明对应步骤（例如 heating step / calcination step）。
4. 在 extraction_hints 中列出你抽取每个关键字段的原文依据（每条不超过 30 字），便于人工审核。
5. confidence：基于上下文是否直接给出信息，估算 0.0 - 1.0 的置信度（直接给出数值为 0.9-1.0，推断/含糊为 0.4-0.7，无法确认为 <0.4）。
6. 不要生成任何 Markdown、代码块或多余文本 —— 仅输出单个 JSON 对象。

如果你理解任务，现在开始抽取并返回 JSON。
""")
    from openai import OpenAI
    # chunks = split_text(md_text, max_len=5000)

    client = OpenAI(api_key="sk-uHLcAS9HexjT263w5FcE6oHJF37LV6Tvz6SfipyOLrxJ1IYG", base_url="https://api.agicto.cn/v1")
    # for i, chunk in enumerate(chunks, 1):
    #     final_prompt = PROMPT_TEMPLATE.substitute(context=chunk)
    #     response = client.chat.completions.create(messages=[{"role": "user", "content": final_prompt, }], model="gpt-5-mini", )
    #     output = response.choices[0].message.content
    #     with open(f"llm_outputs/chunk_{i}.json", "w", encoding="utf-8") as f:
    #         f.write(output)

    final_prompt = PROMPT_TEMPLATE.substitute(context=md_text)

    # # final_prompt = prompt.format(context=md_text)
    print(final_prompt)

    chat_completion = client.chat.completions.create(messages=[{"role": "user", "content": final_prompt, }], model="gpt-5", )
    print(chat_completion.choices[0].message.content)
    # 取出内容
    output_text = chat_completion.choices[0].message.content.strip()

    # 尝试解析成 JSON
    try:
        output_json = json.loads(output_text)
    except json.JSONDecodeError:
        print("⚠️ 模型输出不是合法 JSON，先原样保存。")
        output_json = None

    # 创建输出目录
    out_dir = Path("llm_outputs")
    out_dir.mkdir(exist_ok=True)

    # 用时间戳命名文件
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    json_file = out_dir / f"chem_extract_{timestamp}.json"
    txt_file = out_dir / f"chem_extract_{timestamp}.txt"

    # 保存
    if output_json:
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(output_json, f, ensure_ascii=False, indent=2)
        print(f"✅ 已保存 JSON 输出到 {json_file}")
    else:
        with open(txt_file, "w", encoding="utf-8") as f:
            f.write(output_text)
        print(f"⚠️ 输出不是合法 JSON，已保存原始文本到 {txt_file}")

