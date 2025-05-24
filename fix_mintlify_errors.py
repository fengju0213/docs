#!/usr/bin/env python3
import json
import subprocess
import re
import os
import time
from pathlib import Path
import sys

def run_mintlify_dev_check():
    """运行mintlify dev并捕获解析错误"""
    print("Running mintlify dev to check for parsing errors...")
    
    try:
        # 运行mintlify dev命令，设置超时避免长时间运行
        result = subprocess.run(
            ["npx", "mintlify", "dev", "--port", "3002"],  # 使用不同端口避免冲突
            capture_output=True,
            text=True,
            timeout=30,  # 30秒超时
            cwd="."
        )
        
        return result.stderr + result.stdout
        
    except subprocess.TimeoutExpired:
        print("Mintlify dev timed out (which is expected), checking captured output...")
        # 尝试用另一种方式获取错误信息
        try:
            result = subprocess.run(
                ["mint", "dev", "--check"],  # 只检查不启动服务器
                capture_output=True,
                text=True,
                timeout=60,
                cwd="."
            )
            return result.stderr + result.stdout
        except:
            pass
    
    except Exception as e:
        print(f"Error running mintlify dev: {e}")
        return ""

def parse_error_files(output):
    """从mintlify输出中解析出有错误的文件路径"""
    error_files = set()
    
    # 匹配解析错误的模式
    patterns = [
        r"Parsing error: \./([^:]+\.mdx):",
        r"⚠️.*?Parsing error: \./([^:]+\.mdx):",
        r"Could not parse.*?([^\s]+\.mdx)",
        r"Unexpected.*?([^\s]+\.mdx)",
        r"Expected.*?([^\s]+\.mdx)",
        r"Invalid import path.*?in /([^\.]+\.mdx)",
    ]
    
    lines = output.split('\n')
    for line in lines:
        # 跳过非错误行
        if not ('⚠️' in line or 'Parsing error' in line or 'Invalid import' in line):
            continue
            
        for pattern in patterns:
            matches = re.findall(pattern, line, re.IGNORECASE)
            for match in matches:
                # 清理路径
                file_path = match.strip()
                # 确保以./开头的路径被正确处理
                if file_path.startswith('./'):
                    file_path = file_path[2:]
                if file_path.endswith('.mdx'):
                    error_files.add(file_path)
                    print(f"Found error file: {file_path}")
    
    return list(error_files)

def file_path_to_page_path(file_path):
    """将文件路径转换为docs.json中的页面路径"""
    # 移除.mdx扩展名
    page_path = file_path.replace('.mdx', '')
    
    # 处理特殊字符
    page_path = page_path.replace('&', '')  # 移除&字符
    
    return page_path

def remove_pages_from_navigation(docs_data, error_files):
    """从docs.json的navigation中移除有错误的页面"""
    removed_pages = []
    
    # 将文件路径转换为页面路径
    error_page_paths = [file_path_to_page_path(f) for f in error_files]
    
    def remove_from_groups(groups):
        """递归地从groups中移除页面"""
        if isinstance(groups, list):
            new_groups = []
            for item in groups:
                if isinstance(item, str):
                    # 直接的页面路径
                    if item not in error_page_paths:
                        new_groups.append(item)
                    else:
                        removed_pages.append(item)
                        print(f"  Removed page: {item}")
                elif isinstance(item, dict):
                    # 页面组
                    if 'pages' in item:
                        item['pages'] = remove_from_groups(item['pages'])
                    if 'groups' in item:
                        item['groups'] = remove_from_groups(item['groups'])
                    # 只保留非空的组
                    if (item.get('pages') and len(item['pages']) > 0) or \
                       (item.get('groups') and len(item['groups']) > 0):
                        new_groups.append(item)
                    else:
                        print(f"  Removed empty group: {item.get('group', 'Unknown')}")
            return new_groups
        return groups
    
    # 处理navigation中的tabs
    if 'navigation' in docs_data and 'tabs' in docs_data['navigation']:
        for tab in docs_data['navigation']['tabs']:
            if 'groups' in tab:
                tab['groups'] = remove_from_groups(tab['groups'])
    
    return removed_pages

def backup_docs_json(docs_json_path):
    """备份原始的docs.json文件"""
    backup_path = f"{docs_json_path}.backup"
    with open(docs_json_path, 'r', encoding='utf-8') as f:
        data = f.read()
    
    with open(backup_path, 'w', encoding='utf-8') as f:
        f.write(data)
    
    print(f"Backup created: {backup_path}")
    return backup_path

def get_manual_error_input():
    """手动输入错误信息"""
    print("\nPlease run 'npx mintlify dev' in another terminal and copy the error messages here.")
    print("Paste the error output (press Enter twice when done):")
    
    lines = []
    empty_line_count = 0
    
    while True:
        try:
            line = input()
            if not line.strip():
                empty_line_count += 1
                if empty_line_count >= 2:
                    break
            else:
                empty_line_count = 0
                lines.append(line)
        except KeyboardInterrupt:
            print("\nInput cancelled.")
            return ""
    
    return '\n'.join(lines)

def read_error_file(file_path):
    """从文件读取错误信息"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return ""

def main():
    docs_json_path = "docs.json"
    
    if not os.path.exists(docs_json_path):
        print(f"Error: {docs_json_path} not found!")
        return
    
    print("=== Mintlify Error Fixer ===\n")
    
    # 1. 备份原始文件
    backup_path = backup_docs_json(docs_json_path)
    
    # 2. 获取错误信息
    output = ""
    
    # 检查是否有命令行参数
    if len(sys.argv) > 1:
        if sys.argv[1] == "--manual":
            output = get_manual_error_input()
        elif sys.argv[1] == "--file" and len(sys.argv) > 2:
            output = read_error_file(sys.argv[2])
        elif os.path.exists(sys.argv[1]):
            # 直接提供文件路径
            output = read_error_file(sys.argv[1])
    else:
        # 默认读取sample_errors.txt文件
        if os.path.exists("sample_errors.txt"):
            output = read_error_file("sample_errors.txt")
            print("Reading errors from sample_errors.txt")
        else:
            print("No error file found. Please provide error information.")
            print("Usage: python3 fix_mintlify_errors.py [error_file.txt|--manual]")
            return
    
    if not output:
        print("No error information provided. Exiting.")
        return
    
    # 3. 解析错误文件
    print("Parsing error files...")
    error_files = parse_error_files(output)
    
    if not error_files:
        print("No parsing errors found in the provided output!")
        print("The output was:")
        print(output[:500] + "..." if len(output) > 500 else output)
        return
    
    print(f"\nFound {len(error_files)} files with parsing errors:")
    for file in sorted(error_files):
        print(f"  - {file}")
    
    # 4. 读取docs.json
    with open(docs_json_path, 'r', encoding='utf-8') as f:
        docs_data = json.load(f)
    
    # 5. 移除有问题的页面
    print(f"\nRemoving problematic pages from {docs_json_path}...")
    removed_pages = remove_pages_from_navigation(docs_data, error_files)
    
    # 6. 保存修改后的docs.json
    with open(docs_json_path, 'w', encoding='utf-8') as f:
        json.dump(docs_data, f, indent=2, ensure_ascii=False)
    
    print(f"\nSummary:")
    print(f"  - Total error files found: {len(error_files)}")
    print(f"  - Pages removed from navigation: {len(removed_pages)}")
    print(f"  - Updated: {docs_json_path}")
    print(f"  - Backup: {backup_path}")
    
    print(f"\nYou can now run 'npx mintlify dev' to test the fixed configuration.")
    print(f"To restore the original configuration, copy {backup_path} back to {docs_json_path}")

    # 7. 输出错误文件的详细信息
    if output and error_files:
        print(f"\nDetailed error information (first 10 errors):")
        lines = output.split('\n')
        count = 0
        for line in lines:
            if ('parsing error' in line.lower() or '⚠️' in line) and count < 10:
                print(f"  {line.strip()}")
                count += 1

if __name__ == "__main__":
    main() 