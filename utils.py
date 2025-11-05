def save_last_position(position):
    """保存jsonl文件当前处理位置"""
    with open("process_state.txt", 'w') as f:
        f.write(str(position))


def load_last_position():
    """加载上次处理到的文件位置"""
    try:
        with open("process_state.txt", 'r') as f:
            return int(f.read().strip())
    except (FileNotFoundError, ValueError):
        return 0
