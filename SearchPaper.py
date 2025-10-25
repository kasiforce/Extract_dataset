import csv
import os
import re
import json
import arxiv
import yaml
import logging
import argparse
from datetime import datetime
import requests

logging.basicConfig(format='[%(asctime)s %(levelname)s] %(message)s',
                    datefmt='%m/%d/%Y %H:%M:%S',
                    level=logging.INFO)

base_url = "https://arxiv.paperswithcode.com/api/v0/papers/"
github_url = "https://api.github.com/search/repositories"
arxiv_url = "http://arxiv.org/"


def load_config(config_file: str) -> dict:
    '''
    config_file: input config file path
    return: a dict of configuration
    '''

    def pretty_filters(**config) -> dict:
        keywords = dict()
        OR = ' OR '
        AND = ' AND '

        def parse_filters(filters: list) -> str:
            ret = []
            for filter_item in filters:
                # 如果filter_item是列表，则用OR连接每个术语，并将包含空格的术语用双引号括起来
                if isinstance(filter_item, list):
                    terms = []
                    for term in filter_item:
                        if ' ' in term:
                            terms.append(f'"{term}"')
                        else:
                            terms.append(term)
                    ret.append('(' + OR.join(terms) + ')')
                # 如果filter_item是字符串，则直接使用（为了向后兼容，但不建议）
                else:
                    # 注意：这里假设字符串已经格式正确，但最好还是用列表的列表
                    ret.append(filter_item)
            return AND.join(ret)

        for k, v in config['keywords'].items():
            keywords[k] = parse_filters(v['filters'])
        return keywords

    with open(config_file, 'r') as f:
        config = yaml.load(f, Loader=yaml.FullLoader)
        config['kv'] = pretty_filters(**config)
        logging.info(f'config = {config}')
    return config


def get_authors(authors, first_author=False):
    output = str()
    if first_author == False:
        output = ", ".join(str(author) for author in authors)
    else:
        output = authors[0]
    return output


def sort_papers(papers):
    output = dict()
    keys = list(papers.keys())
    keys.sort(reverse=True)
    for key in keys:
        output[key] = papers[key]
    return output


import requests


def download_paper_pdf(result, download_dir="./papers"):
    """
    下载论文的PDF文件

    @param result: arxiv.Result - arXiv论文结果对象
    @param download_dir: str - PDF下载目录路径
    @return: tuple - (成功状态, PDF文件路径, 错误信息)
    """
    try:
        # 获取论文ID（移除版本后缀）
        paper_id = result.get_short_id()
        ver_pos = paper_id.find('v')
        paper_key = paper_id[0:ver_pos] if ver_pos != -1 else paper_id

        # 创建下载目录（如果不存在）
        os.makedirs(download_dir, exist_ok=True)

        # 构建PDF文件路径
        pdf_filename = f"{paper_key}.pdf"
        pdf_path = os.path.join(download_dir, pdf_filename)

        # 检查PDF是否已存在，避免重复下载
        if not os.path.exists(pdf_path):
            # 使用arxiv库的download_pdf方法下载PDF
            result.download_pdf(dirpath=download_dir, filename=pdf_filename)
            logging.info(f"下载PDF: {pdf_filename}")
            return pdf_path
        else:
            logging.info(f"PDF已存在: {pdf_filename}")
            return None

    except Exception as e:
        logging.error(f"下载{result.get_short_id()} PDF失败: {e}")
        return None


def save_paper_metadata(result, topic, query, pdf_path=None, csv_file="papers_metadata.csv"):
    """
    保存论文元数据到CSV文件

    @param result: arxiv.Result - arXiv论文结果对象
    @param topic: str - 论文主题/类别名称
    @param query: str - 搜索查询字符串
    @param pdf_path: str - PDF文件路径（可选）
    @param csv_file: str - CSV元数据文件路径
    @return: tuple - (成功状态, 错误信息)
    """
    try:
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

        # 获取当前时间作为下载时间
        download_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 初始化CSV文件（如果不存在）
        if not os.path.exists(csv_file):
            with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                # 写入CSV表头
                writer.writerow([
                    'topic', 'paper_id', 'title', 'authors', 'first_author',
                    'primary_category', 'publish_time', 'update_time',
                    'comments', 'abstract', 'pdf_path', 'paper_url',
                    'download_time', 'query'
                ])

        # 准备CSV行数据
        csv_row = [
            topic,  # 主题
            paper_key,  # 论文ID
            paper_title,  # 标题
            paper_authors,  # 所有作者
            paper_first_author,  # 第一作者
            primary_category,  # 主要分类
            str(publish_time),  # 发布日期
            str(update_time),  # 更新日期
            comments if comments else "",  # 评论（处理None值）
            paper_abstract,  # 摘要
            pdf_path if pdf_path else "",  # PDF文件路径
            paper_url,  # 论文URL
            download_time,  # 下载时间
            query  # 搜索查询
        ]

        # 写入CSV文件
        with open(csv_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(csv_row)

        logging.info(f"保存元数据: {paper_key} - {paper_title}")

    except Exception as e:
        logging.error(f"保存元数据失败: {e}")


def get_daily_papers(topic, query, max_results=2, download_dir="./papers", csv_file="papers_metadata.csv"):
    """
    @param topic: str
    @param query: str
    """

    success = 0
    client = arxiv.Client()
    search_engine = arxiv.Search(
        query=query,
        sort_by=arxiv.SortCriterion.Relevance,
        max_results=max_results
    )

    # 遍历搜索结果中的每一篇论文
    for result in client.results(search_engine):

        try:
            # 下载PDF文件
            pdf_path = download_paper_pdf(result, download_dir)

            # 保存元数据到CSV
            if pdf_path is not None:
                save_paper_metadata(result, topic, query, pdf_path, csv_file)
                success += 1
                if success >= max_results:
                    break

        except Exception as e:
            logging.error(f"处理{result.get_short_id()}论文时出错: {e}")

    return success

def demo(**config):

    keywords = config['kv']
    max_results = config['max_results']
    download_papers_path = config['download_papers_path']
    papers_metadata_path = config['papers_metadata_path']

    logging.info(f"GET daily papers begin")
    for topic, keyword in keywords.items():
        logging.info(f"Keyword: {topic}")
        success_download = get_daily_papers(topic, query=keyword, max_results=max_results,
                         download_dir=download_papers_path, csv_file=papers_metadata_path)
        logging.info(f"Download {success_download} new papers")
    logging.info(f"GET daily papers end")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--config_path', type=str, default='config.yaml',
                        help='configuration file path')
    args = parser.parse_args()
    config = load_config(args.config_path)
    config = {**config}
    demo(**config)
