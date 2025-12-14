import os

from pydantic import Field
from oxygent.oxy import FunctionHub

mysterious_tools=FunctionHub(name="mysterious_tools")

@mysterious_tools.tool(
    description="It is what the mysterious information is.",
)
def print_mysterious_information():
    print("2025 Data Mining Project")
    return "Successfully be called"
# def print_mysterious_info(
#         path: str = Field(description="")
# )->str:
#     with open(path, "r", encoding="utf-8") as f:
#         f.write("this is a mysterious info!")
#     return "Successfully printed mysterious info!"+path