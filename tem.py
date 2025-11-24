from utils import save_last_position
# import os
# # with open("papers_metadata.jsonl", 'a') as f:
#     # position = f.tell()
#     # print(position)
#     # save_last_position(position)
# position = os.path.getsize("papers_metadata.jsonl")
# save_last_position(position)
import os
import os


def test_file_position():
    test_file = "papers_metadata.jsonl"

    # 写入一些测试数据
    # with open(test_file, 'w') as f:
    #     f.write("line1\nline2\nline3\n")

    # 测试不同方法获取的位置
    with open(test_file, 'a') as f_text:
        text_position = f_text.tell()

    with open(test_file, 'ab') as f_binary:
        binary_position = f_binary.tell()

    file_size = os.path.getsize(test_file)

    print(f"文本模式 tell(): {text_position}")
    print(f"二进制模式 tell(): {binary_position}")
    print(f"os.path.getsize(): {file_size}")




test_file_position()