import os

from dateutil.parser import DEFAULTPARSER

from oxygent import MAS, Config, oxy, preset_tools

from dotenv import load_dotenv

import tools,my_first_tools


load_dotenv()
print(os.getenv("DEFAULT_LLM_API_KEY"))
print(os.getenv("DEFAULT_LLM_BASE_URL"))
print(os.getenv("DEFAULT_LLM_MODEL_NAME"))

Config.set_agent_llm_model("default_llm")

mathematician_prompt="""
你是一个聪明的数学家，你需要仔细思考，发现问题中的数学本质，最终计算解决问题。
"""

oxy_space = [
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
   preset_tools.file_tools,
   oxy.ReActAgent(
      name="file_agent",
      desc="A tool that can operate the file system", #可以设置prompt
      tools=["file_tools"],
   ),
   preset_tools.math_tools,
   oxy.ReActAgent(
      name="math_agent",
      desc="A tool that can perform mathematical calculations.",
      tools=["math_tools"],
   ),
   tools.file_tools,
   oxy.ReActAgent(
      name="new_file_agent",
      tools=["new_tools"],
      llm_model="default_llm",
   ),
   my_first_tools.mysterious_tools,
   oxy.ReActAgent( # our own agent
      name="mysterious_agent",
      tools=["mysterious_tools"],
      llm_model="default_llm",
   ),
   oxy.ReActAgent(
      is_master=True,
      name="master_agent",
      sub_agents=["time_agent", "file_agent", "math_agent","new_file_agent","mysterious_agent"],
   )
]

async def main():
   async with MAS(oxy_space=oxy_space) as mas:
      await mas.start_cli_mode(
         first_query="please,print the mysterious information."
      )

if __name__ == "__main__":
   import asyncio
   asyncio.run(main())