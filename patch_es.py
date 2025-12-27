import os

target_file = r"C:\Users\firef\AppData\Local\Programs\Python\Python313\Lib\site-packages\elasticsearch\serializer.py"

if os.path.exists(target_file):
    try:
        with open(target_file, "r", encoding="utf-8") as f:
            content = f.read()
        
        if "np.float_" in content:
            new_content = content.replace("np.float_", "np.float64")
            with open(target_file, "w", encoding="utf-8") as f:
                f.write(new_content)
            print(f"Successfully patched {target_file}")
        else:
            print("Already patched or pattern not found.")
    except Exception as e:
        print(f"Error patching file: {e}")
else:
    print(f"File not found: {target_file}")
