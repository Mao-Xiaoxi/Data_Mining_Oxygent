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

def create_oxy_space():
    """Create a fresh OxyGent space configuration."""
    return [
       # 注册 LLM
       oxy.HttpLLM(
          name="default_llm",
          api_key=os.getenv("DEFAULT_LLM_API_KEY"),
          base_url=os.getenv("DEFAULT_LLM_BASE_URL"),
          model_name=os.getenv("DEFAULT_LLM_MODEL_NAME"),
          is_multimodal_supported=True,
          is_convert_url_to_base64=True,
       ),
       # 数学工具 (MCP)
       oxy.StdioMCPClient(
          name="math_tools",
          params={
             "command": "python",
             "args": ["mcp_servers/math_tools.py"],
          },
       ),
       # Metaso 工具
       metaso_tools,
       # Master Agent
       oxy.ReActAgent(
          is_master=True,
          name="master_agent",
          tools=["math_tools", "metaso_tools"],
          llm_model="default_llm",
          max_react_rounds=5, # Limit the number of reasoning steps
          prompt="""You are a smart answering assistant with access to Metaso AI tools.

AVAILABLE TOOLS:
1. metaso_chat: Use this for ALMOST ALL questions. It is a smart search-enhanced answering tool.
2. metaso_reader: Use this ONLY when you have a specific URL that you need to read in full detail.
3. math_tools: Use this for pure math calculations.

STRATEGY FOR CHOOSING TOOLS:
- ALWAYS start by using `metaso_chat` to ask the question. It has built-in search capabilities.
- Only use `metaso_reader` if `metaso_chat` returns a specific URL and tells you to read it for more details.

CRITICAL INSTRUCTIONS:
1. Output ONLY the final answer. Do NOT include any explanation, reasoning, steps, thinking process, or text like "Answer:".
2. If the answer is a number, output ONLY the number (e.g., "3").
3. Output in Chinese unless the question explicitly asks for English.
4. Do not loop. If you are stuck, guess and finish.
5. STRICT LIMIT: You can use `metaso_chat` AT MOST ONCE. If you get an error, STOP and output the answer.
6. TOOL CALL FORMAT: You MUST use the following JSON format to call a tool:
```json
{
    "tool_name": "metaso_chat",
    "arguments": {
        "message": "your question here"
    }
}
```
DO NOT use "action" or "action_input". Use "tool_name" and "arguments".

Examples:
User: "1+1=?"
You: "2"

User: "中国的首都是哪里？"
You: "北京"
"""
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
    problem_file = 'Datasets/valid/simple.jsonl'
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
