import asyncio
import os
import sys
import pandas as pd
import json
from dotenv import load_dotenv
from oxygent import MAS, Config, oxy, preset_tools
from oxygent.preset_tools.metaso_tools import metaso_tools, reset_metaso_usage
import my_first_tools

# 加载环境变量
load_dotenv()
Config.set_agent_llm_model("default_llm")

from oxygent.prompts import INTENTION_PROMPT
from oxygent.prompts import SYSTEM_PROMPT
from oxygent.prompts import SYSTEM_PROMPT_RETRIEVAL
from oxygent.prompts import MULTIMODAL_PROMPT
from prompt import METASO_PROMPT,SEARCH_PROMPT,WEB_PROMPT,TERMINAL_PROMPT,REFLECTION_PROMPT,MASTER_PROMPT


def create_oxy_space():
    """Create a fresh OxyGent space configuration."""
    return [
        # ==================================== oxygent 基本工具示例=======================================
        oxy.HttpLLM(   #注册LLM
            name="default_llm",
            api_key=os.getenv("DEFAULT_LLM_API_KEY"),
            base_url=os.getenv("DEFAULT_LLM_BASE_URL"),
            model_name=os.getenv("DEFAULT_LLM_MODEL_NAME"),
        ),
        preset_tools.time_tools,
        oxy.ReActAgent(
            name="time_agent",
            desc="A tool that can query the time",
            tools=["time_tools"],
        ),
        # preset_tools.file_tools,
        # oxy.ReActAgent(
        #    name="file_agent",
        #    desc="A tool that can operate the file system", #可以设置prompt
        #    tools=["file_tools"],
        # ),

        # 使用mcp需要删除代码中重名function call（包括master中的subagent）
        # preset_tools.math_tools,
        # oxy.ReActAgent(
        #    name="math_agent",
        #    desc="A tool that can perform mathematical calculations.",
        #    tools=["math_tools"],
        # ),

        # ====================================调用MCP工具接口=======================================
        
        oxy.StdioMCPClient(
            name="file_tools",
            params={
                "command": "npx",
            "args": [
                "-y",
                "@modelcontextprotocol/server-filesystem",
                "./Datasets/field"
            ]
            }
        ),
        oxy.StdioMCPClient(
            name="minteractive-terminal_tools",
            params={
                "command": "uvx",
                "args": ["interactive-terminal-mcp"]
            }
        ),
        oxy.StdioMCPClient(
            name="chrome-devtools",
            params={
                "command": "npx",
                "args": [
                "-y",
                "chrome-devtools-mcp@latest"
            ]
            }
        ),
        oxy.StdioMCPClient(
            name="fetch_tools",
            params={
                "command": "node",
                "args": ["D:\\APP\\Anaconda\\envs\\oxygent\\node_modules\\mcp-fetch-server\\dist\\index.js"]
            }
        ),
        oxy.StdioMCPClient(
            name="math_tools",
            params={
                "command": "uv",
                "args": ["--directory", "./mcp_servers", "run", "math_tools.py"],
            },
        ),
        
        # oxy.StdioMCPClient(
        #    name="interactive_terminal_tools",
        #    params={
        #    "command": "node",
        #    "args": [
        #      "d:\\code\\python\\agent_camel\\camel\\iterm-mcp\\build\\index.js"
        #    ]
        #    }
        # ),
        
        # ====================================function call=======================================
        # tools.file_tools,
        # oxy.ReActAgent(
        #    name="my_file_agent",
        #    tools=["file_tools"],
        #    llm_model="default_llm",
        # ),
        
        # ====================================== subagent =========================================
        my_first_tools.mysterious_tools,
        oxy.ReActAgent( # our own agent
            name="mysterious_agent",
            tools=["mysterious_tools"],
            llm_model="default_llm",
        ),
        oxy.ReActAgent(
            is_master=False,
            name='terminal_agent',
            tools=['minteractive-terminal_tools'],
            llm_model="default_llm",
            desc="An agent that allows you to operate a Windows system using the terminal command line and test running code.",
            #prompt=terminal_prompt,
        ),
        metaso_tools,
        oxy.ReActAgent(
            is_master=False,
            name='browser_interact_agent',
            tools=['chrome-devtools',"metaso_tools"],
            llm_model="default_llm",
            desc="An agent that allows you to use Chrome DevTools to browse the web and extract."
        ),
        oxy.ReActAgent(
            is_master=False,
            name='search_agent',
            tools=['fetch_tools'],
        ),
        oxy.ReActAgent(
            is_master=False,
            name='logic_agent',
            tools=['math_tools'],
            llm_model="default_llm",
            desc="An agent that can perform complex logical reasoning and calculations using math tools."
        ),
        oxy.ReActAgent(
            is_master=False,
            name='Image_audio_agent',
            tools=[],
            llm_model="default_llm",
            desc="An agent that can process images and audio files."
        ),
        oxy.ReActAgent(
            is_master=False,
            name='reflection_agent',
            tools=[],
            llm_model="default_llm",
            desc="An agent that can reflect on its own actions and improve its performance over time.",
            prompt=REFLECTION_PROMPT
        ),
        

        # ==================================== master agent =======================================
        oxy.ReActAgent(
            is_master=True,
            name="master_agent",
            tools=[],
            llm_model="default_llm",
            sub_agents=["browser_interact_agent","mysterious_agent",'terminal_agent','search_agent','logic_agent','Image_audio_agent','reflection_agent'], # ,"my_file_agent"
            #prompt=MASTER_PROMPT
            max_react_rounds=5, # Limit the number of reasoning steps
        )
    ]

async def process_task(sem, task_id, query, file_name=None, level='unknown', answer=''):
    """处理单个任务"""
    async with sem:
        # Reset usage for this specific task context
        reset_metaso_usage()
        
        try:
            print(f"Processing Task ID: {task_id}")
            
            full_query = query
            if file_name and isinstance(file_name, str) and file_name.strip():
                 full_query = f"{query}\n\n(Referenced file: {file_name})"

            # Create a fresh MAS environment for each task to ensure no memory leakage
            oxy_space = create_oxy_space()
            
            # Use try-finally to ensure proper cleanup if MAS doesn't handle it perfectly
            try:
                async with MAS(oxy_space=oxy_space) as mas:
                    # 发送请求给 Agent
                    payload = {"query": full_query}
                    response = await mas.chat_with_agent(payload=payload)
                    
                    result = {
                        "task_id": task_id,
                        "query": query,
                        "file_name": file_name,
                        "model_answer": response.output,
                        "level": level,
                        "ground_truth": answer
                    }
            except Exception as e:
                raise e
        except Exception as e:
            print(f"Error processing task {task_id}: {e}")
            result = {
                "task_id": task_id,
                "query": query,
                "file_name": file_name,
                "model_answer": f"Error: {str(e)}",
                "level": level,
                "ground_truth": answer
            }
        
        # Calculate correctness immediately
        model_ans = str(result.get('model_answer', '')).strip()
        ground_truth = str(answer).strip()
        is_correct = False
        if ground_truth and model_ans:
             # Remove common punctuation for comparison
             clean_gt = ground_truth.replace('。', '').replace('.', '').strip()
             clean_model = model_ans.replace('。', '').replace('.', '').strip()
             if clean_gt in clean_model or clean_model in clean_gt:
                 is_correct = True
        result['is_correct'] = is_correct
        
        return result

async def main():
    # 1. 读取问题列表 (JSONL)
    problem_file = 'Datasets/valid/data.jsonl'
    if not os.path.exists(problem_file):
        print(f"Error: {problem_file} not found.")
        return

    try:
        df = pd.read_json(problem_file, lines=True)
    except Exception as e:
        print(f"Error reading JSONL: {e}")
        return
    
    print(f"Loaded {len(df)} tasks from {problem_file}")

    # 2. 并发处理所有任务
    # Limit concurrency to 5 to avoid rate limits
    sem = asyncio.Semaphore(5)
    tasks = []
    
    for _, row in df.iterrows():
        task_id = row.get('task_id', 'unknown')
        query = row.get('query', '')
        file_name = row.get('file_name')
        level = row.get('level', 'unknown')
        answer = row.get('answer', '')
        
        task = asyncio.create_task(process_task(sem, task_id, query, file_name, level, answer))
        tasks.append(task)

    # Wait for all tasks to complete
    results = await asyncio.gather(*tasks)

    # 3. 保存结果
    result_df = pd.DataFrame(results)
    output_file = 'test_results_data.csv'
    result_df.to_csv(output_file, index=False, encoding='utf-8-sig')
    print(f"Results saved to {output_file}")

    # 4. Calculate and print statistics
    total_tasks = len(results)
    correct_count = 0
    level_stats = {} # {level: {'total': 0, 'correct': 0}}

    for res in results:
        is_correct = res.get('is_correct', False)
        lvl = str(res.get('level', 'unknown'))
        
        if is_correct:
            correct_count += 1
            
        if lvl not in level_stats:
            level_stats[lvl] = {'total': 0, 'correct': 0}
        level_stats[lvl]['total'] += 1
        if is_correct:
            level_stats[lvl]['correct'] += 1

    overall_accuracy = (correct_count / total_tasks * 100) if total_tasks > 0 else 0

    print("=" * 30)
    print(f"Total Tasks: {total_tasks}")
    print(f"Correct Answers: {correct_count}")
    print(f"Overall Accuracy: {overall_accuracy:.2f}%")
    print("=" * 30)
    print("Accuracy by Level:")
    
    sorted_levels = sorted(level_stats.keys())
    for lvl in sorted_levels:
        stats = level_stats[lvl]
        acc = (stats['correct'] / stats['total'] * 100) if stats['total'] > 0 else 0
        print(f"  Level {lvl}: {acc:.2f}% ({stats['correct']}/{stats['total']})")
    print("=" * 30)
    
    os._exit(0)

if __name__ == "__main__":
    asyncio.run(main())
