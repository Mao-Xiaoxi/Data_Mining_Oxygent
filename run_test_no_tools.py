import asyncio
import os
import sys
import pandas as pd
from dotenv import load_dotenv
from oxygent import MAS, Config, oxy, preset_tools
import my_first_tools
import io

# 加载环境变量
load_dotenv()
Config.set_agent_llm_model("default_llm")

# 定义 OxyGent 空间配置 (复用 demo.py 的配置，不添加额外工具)
oxy_space = [
   # 注册 LLM
   oxy.HttpLLM(
      name="default_llm",
      api_key=os.getenv("DEFAULT_LLM_API_KEY"),
      base_url=os.getenv("DEFAULT_LLM_BASE_URL"),
      model_name=os.getenv("DEFAULT_LLM_MODEL_NAME"),
      is_multimodal_supported=True,
      is_convert_url_to_base64=True,
   ),
   # 时间工具 Agent
   preset_tools.time_tools,
   oxy.ReActAgent(
      name="time_agent",
      desc="A tool that can query the time",
      tools=["time_tools"],
   ),
   # 神秘工具 Agent
   my_first_tools.mysterious_tools,
   oxy.ReActAgent(
      name="mysterious_agent",
      tools=["mysterious_tools"],
      llm_model="default_llm",
   ),
   # Master Agent
   oxy.ReActAgent(
      is_master=True,
      name="master_agent",
      tools=[], # 不添加额外工具
      llm_model="default_llm",
      sub_agents=["time_agent", "mysterious_agent"],
   )
]

async def process_task(mas, task_id, query, file_name=None):
    """处理单个任务"""
    try:
        print(f"Processing Task ID: {task_id}")
        
        # 如果有文件名，尝试读取文件内容并附加到查询中
        # 注意：这里假设文件可能在 Datasets/test/files 或 Datasets/valid/files 下
        # 由于路径不确定且要求不加工具，这里仅做简单的路径尝试，找不到则忽略
        full_query = query
        if file_name and isinstance(file_name, str) and file_name.strip():
            file_paths = [
                f"Datasets/test/files/{file_name}",
                f"Datasets/valid/files/{file_name}",
                f"Datasets/field/{file_name}"
            ]
            file_content = None
            for path in file_paths:
                if os.path.exists(path):
                    # 图片和视频文件：使用 Markdown 格式引用，触发 BaseLLM 的多模态处理
                    if path.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.mp4', '.avi', '.mov', '.mkv')):
                        abs_path = os.path.abspath(path)
                        full_query = f"{query}\n\n![{file_name}]({abs_path})"
                        file_content = "MULTIMODAL_ATTACHED"
                        break
                    
                    # 音频文件：目前 BaseLLM 未原生支持音频转 Base64，暂时跳过或仅提供路径
                    if path.lower().endswith(('.mp3', '.wav')):
                         full_query = f"{query}\n\n(Attached audio file: {path})"
                         file_content = "AUDIO_SKIPPED"
                         break

                    try:
                        with open(path, 'r', encoding='utf-8') as f:
                            file_content = f.read()
                        break
                    except Exception:
                        pass
            
            if file_content and file_content not in ["MULTIMODAL_ATTACHED", "AUDIO_SKIPPED", "BINARY_FILE_SKIPPED"]:
                full_query = f"{query}\n\nContext File Content:\n{file_content}"
            elif not file_content:
                # 如果找不到文件，把文件名告诉 Agent 也是一种信息
                # 尝试构建一个绝对路径，即使文件不存在，也让 Agent 知道它应该在哪里
                # 优先假设在 Datasets/field/ 下
                abs_path_guess = os.path.abspath(f"Datasets/field/{file_name}")
                if file_name.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.mp4', '.avi', '.mov', '.mkv')):
                     # 检查文件是否存在，如果不存在，则不使用 Markdown 格式，避免触发 BaseLLM 的自动加载
                     if os.path.exists(abs_path_guess):
                         full_query = f"{query}\n\n![{file_name}]({abs_path_guess})"
                     else:
                         # 文件确实不存在，只提供文件名信息，不触发多模态加载
                         full_query = f"{query}\n\n(Referenced file: {file_name} - File Not Found Locally)"
                else:
                     full_query = f"{query}\n\n(Referenced file: {file_name})"

        # 发送请求给 Agent
        payload = {"query": full_query}
        response = await mas.chat_with_agent(payload=payload)
        
        return {
            "task_id": task_id,
            "query": query,
            "file_name": file_name,
            "model_answer": response.output
        }
    except Exception as e:
        print(f"Error processing task {task_id}: {e}")
        return {
            "task_id": task_id,
            "query": query,
            "file_name": file_name,
            "model_answer": f"Error: {str(e)}"
        }

async def main():
    # 1. 读取问题列表
    problem_file = 'Datasets/field/problem.csv'
    if not os.path.exists(problem_file):
        print(f"Error: {problem_file} not found.")
        return

    # 预处理 CSV 内容，修复末尾的 broken quote
    try:
        with open(problem_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 修复行尾的 ," 为 ,"" (空字符串)
        # 注意：这里假设 ," 只出现在行尾且确实是 broken 的
        fixed_content = content.replace(',"\n', ',""\n')
        
        # 如果最后一行没有换行符且以 ," 结尾
        if fixed_content.endswith(',"'):
            fixed_content = fixed_content[:-2] + ',""'

        df = pd.read_csv(io.StringIO(fixed_content), quotechar='"', on_bad_lines='warn')
    except Exception as e:
        print(f"Error reading CSV with preprocessing: {e}")
        # 回退到原来的读取方式
        try:
            df = pd.read_csv(problem_file, quotechar='"', on_bad_lines='warn')
        except Exception as e:
            print(f"Error reading CSV: {e}")
            df = pd.read_csv(problem_file, sep=',', engine='python', on_bad_lines='skip')
    
    print(f"Loaded {len(df)} tasks from {problem_file}")

    # 2. 启动 MAS 并行处理
    async with MAS(oxy_space=oxy_space) as mas:
        tasks = []
        for _, row in df.iterrows():
            # 处理 CSV 中可能的 NaN 值
            task_id = row.get('task_id', 'unknown')
            query = row.get('query', '')
            if pd.isna(query):
                query = ""
            else:
                query = str(query) # 确保是字符串
            
            file_name = row.get('file_name')
            if pd.isna(file_name):
                file_name = None
            
            tasks.append(process_task(mas, task_id, query, file_name))
        
        # 并行执行所有任务
        results = await asyncio.gather(*tasks)

    # 3. 保存结果
    result_df = pd.DataFrame(results)
    output_file = 'test_results_no_tools.csv'
    result_df.to_csv(output_file, index=False, encoding='utf-8-sig')
    print(f"Results saved to {output_file}")
    
    # 强制退出，防止子进程挂起
    os._exit(0)

if __name__ == "__main__":
    asyncio.run(main())
