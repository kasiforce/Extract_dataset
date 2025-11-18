import json
import os
import arxiv
from datetime import datetime
from tempfile import NamedTemporaryFile

from utils import load_last_position, save_last_position
from search_paper import download_paper_pdf, get_authors


def scan_paper_jsonl(**config):
    """扫描papers_metadata.jsonl文件是否有手动添加的论文"""

    print("--- 正在扫描论文列表 ---")
    paper_jsonl = config['papers_metadata_path']
    if not os.path.exists(paper_jsonl):
        return
    current_position = load_last_position()
    # 创建临时文件
    with NamedTemporaryFile(mode='w', delete=False, encoding='utf-8', suffix='.jsonl') as temp_file:
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
                    if line:
                        new_lines.append(line)

                for line in new_lines:
                    data = json.loads(line)
                    if "title" in data:
                        title = data['title']
                        # 清理标题，移除可能影响搜索的字符
                        clean_title = title.replace('"', '').replace("'", "").replace(":", "")
                        query = f"ti:{clean_title}"
                        client = arxiv.Client()
                        search_engine = arxiv.Search(
                            query=query,
                            sort_by=arxiv.SortCriterion.Relevance,
                            max_results=1
                        )
                        # 遍历搜索结果中的每一篇论文
                        for result in client.results(search_engine):

                            try:
                                # 下载PDF文件
                                pdf_path = download_paper_pdf(result, config['download_papers_path'])

                                # 保存元数据到jsonl

                                # 提取论文的基本信息
                                paper_id = result.get_short_id()
                                ver_pos = paper_id.find('v')
                                paper_key = paper_id[0:ver_pos] if ver_pos != -1 else paper_id

                                paper_title = result.title
                                paper_url = f"https://arxiv.org/abs/{paper_key}"
                                paper_abstract = result.summary.replace("\n", " ")
                                paper_authors = get_authors(result.authors)
                                paper_first_author = get_authors(result.authors, first_author=True)
                                primary_category = result.primary_category
                                publish_time = result.published.date()
                                update_time = result.updated.date()
                                comments = result.comment
                                keywords = config['kv']
                                topic = list(keywords.keys())[0]

                                # 获取当前时间作为下载时间
                                download_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                                # 构建论文元数据字典
                                paper_metadata = {
                                    'paper_id': paper_key,  # 论文ID
                                    'title': paper_title,  # 标题
                                    'abstract': paper_abstract,  # 摘要
                                    'paper_url': paper_url,  # 论文URL
                                    'authors': paper_authors,  # 所有作者
                                    'first_author': paper_first_author,  # 第一作者
                                    'primary_category': primary_category,  # 主要分类
                                    'topic': topic,  # 主题
                                    'pdf_path': pdf_path if pdf_path else "",  # PDF文件路径
                                    'publish_time': str(publish_time),  # 发布日期
                                    'update_time': str(update_time),  # 更新日期
                                    'comments': comments if comments else "",  # 评论（处理None值）
                                    'download_time': download_time,  # 下载时间
                                    'query': query  # 搜索查询
                                }

                                temp_file.write(json.dumps(paper_metadata, ensure_ascii=False) + '\n')

                            except Exception as e:
                                print(f"处理{result.get_short_id()}论文时出错: {e}")
                                temp_file.write(line)
                    else:
                        # 如果原行没有title，原样写入
                        temp_file.write(line)

            # 关闭临时文件
            temp_file.close()
            # 用临时文件替换原文件
            os.replace(temp_path, paper_jsonl)

            # 保存新的文件位置
            new_position = os.path.getsize(paper_jsonl)
            save_last_position(new_position)

        except Exception as e:
            # 如果出错，删除临时文件
            os.unlink(temp_path)
            print(f"处理文件时出错: {e}")

    print("--- 扫描结束 ---")