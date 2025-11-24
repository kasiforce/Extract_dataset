import json
import os
import arxiv
import yaml
from datetime import datetime
from tempfile import NamedTemporaryFile

from utils import load_last_position, save_last_position
from search_paper import *


def scan_paper_jsonl(paper_search):
    """扫描papers_metadata.jsonl文件是否有手动添加的论文"""
    print("--- 正在扫描论文列表 ---")
    paper_jsonl = paper_search.config['papers_metadata_path']
    current_position = load_last_position()
    target_dir = os.path.dirname(paper_jsonl)

    # 创建临时文件
    with NamedTemporaryFile(mode='a', delete=False, suffix='.jsonl',
                            dir=target_dir, encoding='utf-8') as temp_file:
        temp_path = temp_file.name

        try:
            # 读取原文件
            with open(paper_jsonl, 'r', encoding='utf-8') as f:
                # 复制已处理的部分到临时文件
                f.seek(0)
                content_before = f.read(current_position)
                temp_file.write(content_before)

                # 处理新添加的行
                new_lines = []
                for line in f:
                    line = line.strip()
                    print(line)
                    if line:
                        new_lines.append(line)

                for line in new_lines:
                    if not line:
                        continue
                    data = json.loads(line)
                    if "id" in data:
                        id = data['id']
                        client = arxiv.Client()
                        search_engine = arxiv.Search(
                            query=id,
                            sort_by=arxiv.SortCriterion.Relevance,
                            max_results=1
                        )
                        # 遍历搜索结果中的每一篇论文
                        for result in client.results(search_engine):

                            try:
                                # 判断是否有重复论文
                                paper_id = result.get_short_id()
                                ver_pos = paper_id.find('v')
                                paper_key = paper_id[0:ver_pos] if ver_pos != -1 else paper_id
                                if paper_key in paper_search.paper:
                                    break

                                # 判断论文是否为LLM4SE
                                paper_title = result.title
                                print(paper_title)
                                paper_abstract = result.summary
                                content = paper_title + '\n' + paper_abstract
                                system_prompt, user_prompt = paper_search.build_benchmark_finder_prompt(content)
                                messages = [
                                    {"role": "system", "content": system_prompt},
                                    {"role": "user", "content": user_prompt}
                                ]
                                # print(messages)
                                resp = call_chatgpt(messages)
                                print(resp)
                                if resp['topic']:
                                    # 下载PDF文件
                                    pdf_path = paper_search.download_paper_pdf(result, paper_search.config[
                                        'download_papers_path'])

                                    # 保存元数据到jsonl
                                    # 提取论文的基本信息
                                    paper_title = result.title
                                    paper_url = f"https://arxiv.org/abs/{paper_key}"
                                    paper_abstract = result.summary.replace("\n", " ")
                                    paper_authors = [author.name for author in result.authors]
                                    paper_first_author = paper_search.get_authors(result.authors, first_author=True)
                                    primary_category = result.primary_category
                                    publish_time = result.published.date()
                                    update_time = result.updated.date()
                                    comment = result.comment if result.comment else None
                                    journal_ref = result.journal_ref if hasattr(result,
                                                                                'journal_ref') and result.journal_ref else None
                                    conference = paper_search.extract_venue_from_journal_ref(journal_ref) or \
                                                 paper_search.extract_venue_from_comment(comment)

                                    # 获取当前时间作为下载时间
                                    download_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                                    # 构建论文元数据字典
                                    paper_metadata = {
                                        'id': paper_key,  # 论文ID
                                        'title': paper_title,  # 标题
                                        'abstract': paper_abstract,  # 摘要
                                        'arxiv_url': paper_url,  # 论文URL
                                        'authors': paper_authors,  # 所有作者
                                        'first_author': paper_first_author,  # 第一作者
                                        'primary_category': primary_category,  # 主要分类
                                        'tag': [resp['topic']],  # 主题
                                        "benchmark": resp['benchmark'],  # 是否benchmark相关
                                        "conference": conference,  # 会议/期刊
                                        'pdf_url': result.pdf_url,  # PDF路径
                                        'published': str(publish_time),  # 发布日期
                                        'update_time': str(update_time),  # 更新日期
                                        'download_time': download_time,  # 下载时间
                                    }

                                    temp_file.write(json.dumps(paper_metadata, ensure_ascii=False) + '\n')
                                    temp_file.flush()
                                    current_position = temp_file.tell()
                                    save_last_position(current_position)

                            except Exception as e:
                                print(f"处理{result.get_short_id()}论文时出错: {e}")
                                temp_file.write(line + '\n')
                                temp_file.flush()
                    else:
                        # 如果原行没有title，原样写入
                        temp_file.write(line + '\n')
                        temp_file.flush()

            # new_position = temp_file.tell()
            # save_last_position(new_position)
            # 关闭临时文件
            temp_file.close()
            # 用临时文件替换原文件
            os.replace(temp_path, paper_jsonl)

            if os.path.exists(temp_path):
                os.remove(temp_path)
            #
            # position = os.path.getsize(paper_jsonl)
            # save_last_position(position)

        except Exception as e:
            # 如果出错，删除临时文件
            os.unlink(temp_path)
            print(f"处理文件时出错: {e}")

    print("--- 扫描结束 ---")


if __name__ == "__main__":
    config_path = "config.yaml"
    search = PaperSearch(config_path)
    scan_paper_jsonl(search)
