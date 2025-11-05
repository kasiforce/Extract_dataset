from search_paper import *
from scan_paper_list import scan_paper_jsonl


def run_paper_pipeline(config_path='config.yaml'):
    """运行完整的论文处理流水线"""
    try:

        # 加载配置
        config = load_config(config_path)
        config = {**config}

        scan_paper_jsonl(**config)

        search(**config)

    except Exception as e:
        print(f"论文处理流水线执行失败: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--config_path', type=str, default='config.yaml',
                        help='configuration file path')

    args = parser.parse_args()

    run_paper_pipeline(args.config_path)
