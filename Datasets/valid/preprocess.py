import json


def extract_and_save_data(input_file_path, query_output_file="query_task_id.jsonl",
                          answer_output_file="answer_task_id.jsonl"):
    """
    从JSONL文件中提取query和task_id、answer和task_id，并分别保存到两个JSONL文件中

    参数:
        input_file_path (str): 输入JSONL文件的路径
        query_output_file (str): 保存query和task_id的输出文件路径
        answer_output_file (str): 保存answer和task_id的输出文件路径

    返回:
        tuple: (query_count, answer_count) 提取的记录数量
    """
    query_count = 0
    answer_count = 0

    try:
        with open(input_file_path, 'r', encoding='utf-8') as infile, \
                open(query_output_file, 'w', encoding='utf-8') as query_outfile, \
                open(answer_output_file, 'w', encoding='utf-8') as answer_outfile:

            for line_num, line in enumerate(infile, 1):
                line = line.strip()
                if not line:  # 跳过空行
                    continue

                try:
                    data = json.loads(line)

                    # 提取task_id和query
                    if 'task_id' in data and 'query' in data:
                        query_item = {
                            'task_id': data['task_id'],
                            'query': data['query']
                        }
                        query_outfile.write(json.dumps(query_item, ensure_ascii=False) + '\n')
                        query_count += 1

                    # 提取task_id和answer（如果存在）
                    if 'task_id' in data and 'answer' in data:
                        # 检查answer是否为空或只有空格
                        if data['answer'] and str(data['answer']).strip():
                            answer_item = {
                                'task_id': data['task_id'],
                                'answer': data['answer']
                            }
                            answer_outfile.write(json.dumps(answer_item, ensure_ascii=False) + '\n')
                            answer_count += 1
                        else:
                            print(f"警告: 第{line_num}行的answer为空或空白，已跳过")

                except json.JSONDecodeError as e:
                    print(f"警告: 第{line_num}行JSON解析错误: {e}")
                    continue

        print(f"成功处理 {line_num} 行数据")
        print(f"提取了 {query_count} 条query-task_id记录到 '{query_output_file}'")
        print(f"提取了 {answer_count} 条answer-task_id记录到 '{answer_output_file}'")

        return query_count, answer_count

    except FileNotFoundError:
        print(f"错误: 输入文件 '{input_file_path}' 未找到")
        return 0, 0
    except Exception as e:
        print(f"错误: 处理文件时发生意外错误 - {e}")
        return 0, 0


# 如果需要更详细的控制，这里是一个更灵活的版本
def extract_data_separately(input_file_path,
                            query_output_file="query_task_id.jsonl",
                            answer_output_file="answer_task_id.jsonl",
                            include_fields=None):
    """
    灵活版本：从JSONL文件中提取数据到两个不同的JSONL文件

    参数:
        input_file_path (str): 输入JSONL文件的路径
        query_output_file (str): 保存query和task_id的输出文件路径
        answer_output_file (str): 保存answer和task_id的输出文件路径
        include_fields (list, optional): 需要提取的其他字段列表

    返回:
        dict: 提取结果的统计信息
    """
    stats = {
        'total_lines': 0,
        'query_records': 0,
        'answer_records': 0,
        'error_lines': 0,
        'skipped_empty_answer': 0
    }

    try:
        with open(input_file_path, 'r', encoding='utf-8') as infile:
            lines = infile.readlines()

        query_items = []
        answer_items = []

        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if not line:  # 跳过空行
                continue

            stats['total_lines'] += 1

            try:
                data = json.loads(line)

                # 提取query和task_id
                if 'task_id' in data and 'query' in data:
                    query_item = {'task_id': data['task_id'], 'query': data['query']}

                    # 如果需要其他字段
                    if include_fields:
                        for field in include_fields:
                            if field in data and field not in ['task_id', 'query']:
                                query_item[field] = data[field]

                    query_items.append(query_item)
                    stats['query_records'] += 1

                # 提取answer和task_id
                if 'task_id' in data and 'answer' in data:
                    answer_value = data['answer']
                    if answer_value and str(answer_value).strip():
                        answer_item = {'task_id': data['task_id'], 'answer': answer_value}

                        # 如果需要其他字段
                        if include_fields:
                            for field in include_fields:
                                if field in data and field not in ['task_id', 'answer']:
                                    answer_item[field] = data[field]

                        answer_items.append(answer_item)
                        stats['answer_records'] += 1
                    else:
                        stats['skipped_empty_answer'] += 1

            except json.JSONDecodeError as e:
                print(f"警告: 第{line_num}行JSON解析错误: {e}")
                stats['error_lines'] += 1
                continue

        # 写入query-task_id文件
        if query_items:
            with open(query_output_file, 'w', encoding='utf-8') as outfile:
                for item in query_items:
                    outfile.write(json.dumps(item, ensure_ascii=False) + '\n')

        # 写入answer-task_id文件
        if answer_items:
            with open(answer_output_file, 'w', encoding='utf-8') as outfile:
                for item in answer_items:
                    outfile.write(json.dumps(item, ensure_ascii=False) + '\n')

        # 打印统计信息
        print("=" * 60)
        print("数据提取统计:")
        print(f"总处理行数: {stats['total_lines']}")
        print(f"提取的query记录: {stats['query_records']}")
        print(f"提取的answer记录: {stats['answer_records']}")
        print(f"跳过的空answer: {stats['skipped_empty_answer']}")
        print(f"解析错误行数: {stats['error_lines']}")
        print(f"query记录已保存到: {query_output_file}")
        print(f"answer记录已保存到: {answer_output_file}")
        print("=" * 60)

        return stats

    except FileNotFoundError:
        print(f"错误: 输入文件 '{input_file_path}' 未找到")
        return stats
    except Exception as e:
        print(f"错误: 处理文件时发生意外错误 - {e}")
        return stats


# 验证提取结果的函数
def verify_extraction(query_file, answer_file):
    """
    验证提取结果，显示文件内容和统计信息

    参数:
        query_file (str): query-task_id文件路径
        answer_file (str): answer-task_id文件路径
    """
    print("验证提取结果:")
    print("=" * 60)

    # 验证query文件
    if query_file:
        try:
            with open(query_file, 'r', encoding='utf-8') as f:
                query_lines = f.readlines()

            print(f"query-task_id文件 '{query_file}' 包含 {len(query_lines)} 条记录")
            print("前3条记录示例:")
            for i, line in enumerate(query_lines[:3]):
                data = json.loads(line.strip())
                print(f"  {i + 1}. task_id: {data.get('task_id', 'N/A')[:20]}...")
                print(f"     query: {data.get('query', 'N/A')[:50]}...")
            if len(query_lines) > 3:
                print(f"  ... 还有 {len(query_lines) - 3} 条记录")
            print()

        except FileNotFoundError:
            print(f"警告: query文件 '{query_file}' 未找到")
        except Exception as e:
            print(f"验证query文件时出错: {e}")

    # 验证answer文件
    if answer_file:
        try:
            with open(answer_file, 'r', encoding='utf-8') as f:
                answer_lines = f.readlines()

            print(f"answer-task_id文件 '{answer_file}' 包含 {len(answer_lines)} 条记录")
            print("前3条记录示例:")
            for i, line in enumerate(answer_lines[:3]):
                data = json.loads(line.strip())
                print(f"  {i + 1}. task_id: {data.get('task_id', 'N/A')[:20]}...")
                print(f"     answer: {data.get('answer', 'N/A')[:50]}...")
            if len(answer_lines) > 3:
                print(f"  ... 还有 {len(answer_lines) - 3} 条记录")

        except FileNotFoundError:
            print(f"警告: answer文件 '{answer_file}' 未找到")
        except Exception as e:
            print(f"验证answer文件时出错: {e}")

    print("=" * 60)


# 使用示例
if __name__ == "__main__":
    # 设置文件路径
    input_file = "./data.jsonl"  # 替换为你的输入文件路径
    query_output = "./query_task_id.jsonl"
    answer_output = "./answer_task_id.jsonl"

    print("开始提取数据...")
    print("=" * 60)

    # 使用简单版本
    query_count, answer_count = extract_and_save_data(input_file, query_output, answer_output)

    print("\n" + "=" * 60)

    # 验证结果
    verify_extraction(query_output, answer_output)

    # 使用灵活版本（可选）
    print("\n使用灵活版本提取（包含level字段）:")
    stats = extract_data_separately(
        input_file,
        query_output_file="query_task_id_with_level.jsonl",
        answer_output_file="answer_task_id_with_level.jsonl",
        include_fields=['level']  # 除了task_id和query/answer，还提取level字段
    )

    # 验证灵活版本的结果
    verify_extraction("query_task_id_with_level.jsonl", "answer_task_id_with_level.jsonl")