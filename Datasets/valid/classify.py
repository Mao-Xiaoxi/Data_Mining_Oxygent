import json
import pandas as pd
from collections import defaultdict

def process_jsonl_to_csv(input_file, output_file):
    """
    处理JSONL文件，按难度等级划分数据并存储到CSV表格中
    
    Args:
        input_file: 输入的JSONL文件路径
        output_file: 输出的CSV文件路径
    """
    # 用于存储不同难度等级的数据
    level_data = defaultdict(list)
    
    # 读取JSONL文件
    with open(input_file, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            
            try:
                # 解析JSON行
                data = json.loads(line)
                
                # 提取字段
                task_id = data.get('task_id', '')
                query = data.get('query', '')
                level = data.get('level', '')
                file_name = data.get('file_name', '')
                answer = data.get('answer', '')
                steps = data.get('steps', '')
                
                # 将数据添加到对应难度等级
                level_data[level].append({
                    'task_id': task_id,
                    'query': query,
                    'level': level,
                    'file_name': file_name,
                    'answer': answer,
                    'steps': steps
                })
                
            except json.JSONDecodeError as e:
                print(f"第{line_num}行JSON解析错误: {e}")
                continue
            except Exception as e:
                print(f"处理第{line_num}行时发生错误: {e}")
                continue
    
    # 将所有数据合并到一个DataFrame中，添加难度等级列
    all_data = []
    for level, records in level_data.items():
        all_data.extend(records)
    
    # 创建DataFrame
    df = pd.DataFrame(all_data)
    
    # 按照难度等级排序
    df = df.sort_values(by='level')
    
    # 保存到CSV文件
    df.to_csv(output_file, index=False, encoding='utf-8-sig')
    
    # 输出统计信息
    print(f"处理完成！共处理{len(all_data)}条记录")
    for level in sorted(level_data.keys()):
        print(f"难度等级 {level}: {len(level_data[level])} 条记录")
    
    return df

def create_separate_csv_by_level(input_file, output_prefix):
    """
    为每个难度等级创建单独的CSV文件
    
    Args:
        input_file: 输入的JSONL文件路径
        output_prefix: 输出文件的前缀
    """
    # 用于存储不同难度等级的数据
    level_data = defaultdict(list)
    
    # 读取JSONL文件
    with open(input_file, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            
            try:
                # 解析JSON行
                data = json.loads(line)
                
                # 提取字段
                task_id = data.get('task_id', '')
                query = data.get('query', '')
                level = data.get('level', '')
                file_name = data.get('file_name', '')
                answer = data.get('answer', '')
                steps = data.get('steps', '')
                
                # 将数据添加到对应难度等级
                level_data[level].append({
                    'task_id': task_id,
                    'query': query,
                    'level': level,
                    'file_name': file_name,
                    'answer': answer,
                    'steps': steps
                })
                
            except json.JSONDecodeError as e:
                print(f"第{line_num}行JSON解析错误: {e}")
                continue
            except Exception as e:
                print(f"处理第{line_num}行时发生错误: {e}")
                continue
    
    # 为每个难度等级创建单独的CSV文件
    total_records = 0
    for level, records in level_data.items():
        df = pd.DataFrame(records)
        output_file = f"{output_prefix}_level_{level}.csv"
        df.to_csv(output_file, index=False, encoding='utf-8-sig')
        print(f"难度等级 {level} 的 {len(records)} 条记录已保存到 {output_file}")
        total_records += len(records)
    
    print(f"处理完成！共处理{total_records}条记录")
    for level in sorted(level_data.keys()):
        print(f"难度等级 {level}: {len(level_data[level])} 条记录")

def main():
    # 示例使用
    input_file = "data.jsonl"  # 输入JSONL文件路径
    output_file = "output.csv"  # 输出CSV文件路径
    output_prefix = "output_by_level"  # 按等级分开输出的文件前缀
    
    print("选择处理方式:")
    print("1. 将所有数据保存到一个CSV文件")
    print("2. 按难度等级分别保存到不同CSV文件")
    
    choice = input("请输入选择 (1 或 2): ")
    
    if choice == "1":
        df = process_jsonl_to_csv(input_file, output_file)
        print(f"数据已保存到 {output_file}")
    elif choice == "2":
        create_separate_csv_by_level(input_file, output_prefix)
    else:
        print("无效选择")

if __name__ == "__main__":
    main()
