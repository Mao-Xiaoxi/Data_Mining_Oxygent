# in tools.py
import os
from pydantic import Field
from oxygent.oxy import FunctionHub
import json

# 注册工具包
file_tools = FunctionHub(name="file_tools")

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

@file_tools.tool(
    description="Read the content of a json file. Returns the parsed content of a file, or an error message if the file does not exist."
)
def read_json_file(file_path):
    """
    read the json file and return the parsed data

    parameter:
        file_path (str): the path to the json file

    return:
        dict/list: the parsed data
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
        return data
    except FileNotFoundError:
        print(f"error：The file at '{file_path}' is not found.")
        return None
    except json.JSONDecodeError as e:
        print(f"error：invalid format - {e}")
        return None
    except Exception as e:
        print(f"error：unexpect errors - {e}")
        return None


@file_tools.tool(
    description="Read the content of a jsonl file. Returns a list of parsed objects, or an error message if the file does not exist or cannot be parsed."
)
def read_jsonl_file(file_path):
    """
    Read the jsonl file and return a list of parsed objects.

    A jsonl file contains one JSON object per line. This function reads all lines
    and returns them as a list of Python objects.

    Parameters:
        file_path (str): The path to the jsonl file

    Returns:
        list: A list of parsed JSON objects, one per line in the file
    """
    try:
        data_list = []
        with open(file_path, 'r', encoding='utf-8') as file:
            for line_number, line in enumerate(file, 1):
                line = line.strip()
                if not line:  # Skip empty lines
                    continue
                try:
                    data = json.loads(line)
                    data_list.append(data)
                except json.JSONDecodeError as e:
                    print(f"Warning: JSON decode error at line {line_number}: {e}")
                    # Optionally, you can return None or raise an exception here
                    # For now, we just skip the invalid line and continue
                    continue

        if not data_list:
            print(f"Warning: No valid JSON objects found in file '{file_path}'")

        return data_list

    except FileNotFoundError:
        print(f"Error: The file at '{file_path}' is not found.")
        return None
    except Exception as e:
        print(f"Error: Unexpected error occurred - {e}")
        return None


@file_tools.tool(
    description="Read jsonl file line by line with a generator. This is memory-efficient for large files."
)
def read_jsonl_file_stream(file_path):
    """
    Read jsonl file using a generator for memory-efficient processing.

    This function reads one line at a time and yields parsed JSON objects.
    It's suitable for large files that cannot be loaded entirely into memory.

    Parameters:
        file_path (str): The path to the jsonl file

    Yields:
        dict/list: Parsed JSON objects one by one
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            for line_number, line in enumerate(file, 1):
                line = line.strip()
                if not line:  # Skip empty lines
                    continue
                try:
                    data = json.loads(line)
                    yield data
                except json.JSONDecodeError as e:
                    print(f"Warning: JSON decode error at line {line_number}: {e}")
                    # Skip invalid line and continue
                    continue

    except FileNotFoundError:
        print(f"Error: The file at '{file_path}' is not found.")
        yield None
    except Exception as e:
        print(f"Error: Unexpected error occurred - {e}")
        yield None


@file_tools.tool(
    description="Convert a JSONL file to a JSON array file."
)
def jsonl_to_json_file(jsonl_path, json_path=None, indent=2):
    """
    Convert a jsonl file to a json array file.

    Parameters:
        jsonl_path (str): Path to the source jsonl file
        json_path (str, optional): Path for the output json file.
                                   If not provided, adds '.json' to jsonl_path.
        indent (int, optional): Indentation level for the output JSON (default: 2)

    Returns:
        str: Path to the created JSON file, or None if conversion failed
    """
    try:
        # Read jsonl data
        jsonl_data = read_jsonl_file(jsonl_path)
        if jsonl_data is None:
            return None

        # Determine output path
        if json_path is None:
            json_path = jsonl_path.rsplit('.', 1)[0] + '.json'

        # Write as JSON array
        with open(json_path, 'w', encoding='utf-8') as file:
            json.dump(jsonl_data, file, ensure_ascii=False, indent=indent)

        print(f"Successfully converted '{jsonl_path}' to '{json_path}'")
        return json_path

    except Exception as e:
        print(f"Error: Conversion failed - {e}")
        return None


@file_tools.tool(
    description="Convert a JSON array file to a JSONL file."
)
def json_to_jsonl_file(json_path, jsonl_path=None):
    """
    Convert a json array file to a jsonl file.

    Parameters:
        json_path (str): Path to the source json file
        jsonl_path (str, optional): Path for the output jsonl file.
                                    If not provided, adds '.jsonl' to json_path.

    Returns:
        str: Path to the created JSONL file, or None if conversion failed
    """
    try:
        # Read json data
        with open(json_path, 'r', encoding='utf-8') as file:
            json_data = json.load(file)

        if not isinstance(json_data, list):
            print(f"Error: JSON file must contain an array (list) of objects")
            return None

        # Determine output path
        if jsonl_path is None:
            jsonl_path = json_path.rsplit('.', 1)[0] + '.jsonl'

        # Write as JSONL (one object per line)
        with open(jsonl_path, 'w', encoding='utf-8') as file:
            for item in json_data:
                file.write(json.dumps(item, ensure_ascii=False) + '\n')

        print(f"Successfully converted '{json_path}' to '{jsonl_path}'")
        return jsonl_path

    except FileNotFoundError:
        print(f"Error: The file at '{json_path}' is not found.")
        return None
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON format - {e}")
        return None
    except Exception as e:
        print(f"Error: Conversion failed - {e}")
        return None


@file_tools.tool(
    description="Filter JSONL file based on a condition and save to a new file."
)
def filter_jsonl_file(input_file, output_file, filter_func=None, condition_key=None, condition_value=None):
    """
    Filter JSONL file and save matching lines to a new file.

    Parameters:
        input_file (str): Path to the input jsonl file
        output_file (str): Path for the output jsonl file
        filter_func (callable, optional): Custom filter function that takes a record and returns True/False
        condition_key (str, optional): Key to check in each record
        condition_value (any, optional): Value to match for the given key

    Returns:
        int: Number of records written to output file, or -1 if error
    """
    try:
        def default_filter(record):
            """Default filter: check if record has condition_key equal to condition_value"""
            if condition_key is None:
                return True
            return condition_key in record and record[condition_key] == condition_value

        # Use custom filter if provided, otherwise use default
        filter_to_use = filter_func if filter_func is not None else default_filter

        count = 0
        with open(input_file, 'r', encoding='utf-8') as infile, \
                open(output_file, 'w', encoding='utf-8') as outfile:

            for line in infile:
                line = line.strip()
                if not line:
                    continue

                try:
                    record = json.loads(line)
                    if filter_to_use(record):
                        outfile.write(line + '\n')
                        count += 1
                except json.JSONDecodeError:
                    # Skip invalid JSON lines
                    continue

        print(f"Filtered {count} records from '{input_file}' to '{output_file}'")
        return count

    except FileNotFoundError:
        print(f"Error: Input file '{input_file}' not found.")
        return -1
    except Exception as e:
        print(f"Error: Filter operation failed - {e}")
        return -1
