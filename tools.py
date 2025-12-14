# in tools.py
import os
from pydantic import Field
from oxygent.oxy import FunctionHub

# 注册工具包
file_tools = FunctionHub(name="new_tools")

@file_tools.tool(
    description="Create a new file or completely overwrite an existing file with new content. Use with caution as it will overwrite existing files without warning. Handles text content with proper encoding. Only works within allowed directories."
)
def new_write_file(
    path: str = Field(description=""), content: str = Field(description="")
) -> str:
    with open(path, "w", encoding="utf-8") as file:
        file.write(content)
    return "Successfully wrote to " + path

@file_tools.tool(
    description="Read the content of a file. Returns an error message if the file does not exist."
)
def new_read_file(path: str = Field(description="Path to the file to read")) -> str:
    if not os.path.exists(path):
        return f"Error: The file at {path} does not exist."
    with open(path, "r", encoding="utf-8") as file:
        return file.read()


@file_tools.tool(
    description="Delete a file. Returns a success message if the file is deleted, or an error if the file does not exist."
)
def new_delete_file(path: str = Field(description="Path to the file to delete")) -> str:
    if not os.path.exists(path):
        return f"Error: The file at {path} does not exist."
    os.remove(path)
    return f"Successfully deleted the file at {path}"


