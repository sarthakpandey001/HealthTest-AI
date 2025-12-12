import os
# import shutil
from git import Repo
from pathlib import Path

def repo_to_txt(repo_link):
    temp_dir = "temp"
    repo_dir = os.path.join(temp_dir, "temp_repo")
    Repo.clone_from(repo_link, repo_dir)
    SOURCE_EXTENSIONS = ['.py', '.js', '.ts', '.html', '.css', '.c', '.cpp', '.java', '.go', '.rs', '.swift', '.rb', '.php', '.md']
    EXCLUDE_DIRS = ['.git', '__pycache__', 'node_modules', '.idea', '.vscode', 'venv', 'env', '.env', 'site-packages']
    clone_path = Path()
    output_file = os.path.join(temp_dir, "source_code.txt")
    with open(output_file, 'w', encoding='utf-8') as outfile:
        for root, dirs, files in os.walk(clone_path, topdown=True):
            new_dirs = []
            for d in dirs:
                include = False
                for ed in EXCLUDE_DIRS: 
                    if ed in d: 
                        include = False
                        break
                if include: new_dirs += d
            dirs[:] = new_dirs
            for file_name in files:
                file_path = Path(root) / file_name
                if file_path.suffix.lower() in SOURCE_EXTENSIONS:
                    try:
                        relative_path = file_path.relative_to(clone_path)
                        outfile.write(f"--- START FILE: {relative_path} ---\n")
                        content = file_path.read_text(encoding='utf-8')
                        outfile.write(content.strip() + '\n') # .strip() cleans up extra leading/trailing whitespace
                        outfile.write(f"--- END FILE: {relative_path} ---\n\n")
                        # print(f"  - Included: {relative_path}")
                    except Exception as e:
                        print(f"  - Skipped (Error {e.__class__.__name__}): {file_path}")

    # print(f"\nAggregation complete. The RAG source file is: **{output_file}**")
    return output_file
    # shutil.rmtree(repo_dir)

repo_to_txt("https://github.com/dbarnett/python-helloworld")

