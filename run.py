import argparse

from search_paper import PaperSearch
from scan_paper_list import scan_paper_jsonl
from gen_html import HTMLGenerator


def run_paper_pipeline(config_path='config.yaml'):
    """运行完整的论文处理流水线"""
    try:
        search = PaperSearch(config_path)
        paper_meta_path = search.config['papers_metadata_path']
        # 处理手动添加到jsonl文件中的论文
        scan_paper_jsonl(search)
        # 更新已处理论文
        search.get_recent_paper(paper_meta_path)

        search.search()

        html_gen = HTMLGenerator(paper_meta_path)
        html_gen.run()

    except Exception as e:
        print(f"论文处理流水线执行失败: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--config_path', type=str, default='config.yaml',
                        help='configuration file path')

    args = parser.parse_args()

    run_paper_pipeline(args.config_path)
