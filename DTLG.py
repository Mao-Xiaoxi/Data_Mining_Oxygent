import os

from dateutil.parser import DEFAULTPARSER
from dotenv import load_dotenv

from oxygent import MAS, Config, oxy, preset_tools
from oxygent.preset_tools.metaso_tools import metaso_tools, reset_metaso_usage

import tools,my_first_tools

from oxygent.prompts import INTENTION_PROMPT
from oxygent.prompts import SYSTEM_PROMPT
from oxygent.prompts import SYSTEM_PROMPT_RETRIEVAL
from oxygent.prompts import MULTIMODAL_PROMPT
from prompt import METASO_PROMPT,SEARCH_PROMPT,WEB_PROMPT,TERMINAL_PROMPT,REFLECTION_PROMPT,MASTER_PROMPT


load_dotenv()
print(os.getenv("DEFAULT_LLM_API_KEY"))
print(os.getenv("DEFAULT_LLM_BASE_URL"))
print(os.getenv("DEFAULT_LLM_MODEL_NAME"))

Config.set_agent_llm_model("default_llm")



oxy_space = [
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
       max_react_rounds=10, # Limit the number of reasoning steps
   )
]


async def main():
   async with MAS(oxy_space=oxy_space) as mas:
      await mas.start_web_service(
      #await mas.start_web_service(
         #first_query="please,print the mysterious information"
         first_query="print the mysterious information"
      )
      # print("You: please,print the mysterious information")
      # payload = {"query": "please,print the mysterious information"}
      # oxy_response = await mas.chat_with_agent(payload=payload)
      # print("LLM: ", oxy_response.output)

if __name__ == "__main__":
   import asyncio
   asyncio.run(main())