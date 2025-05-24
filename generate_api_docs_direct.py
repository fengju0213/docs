#!/usr/bin/env python3
import os
import subprocess
import sys
import glob
import importlib
import re
from pathlib import Path
import shutil
import argparse

def create_config_file(output_path="pydoc-markdown.yml"):
    """创建pydoc-markdown配置文件"""
    config = """loader:
  type: python
  search_path: ["."]

renderer:
  type: markdown
  render_toc: false
  descriptive_class_title: true
  classifiers_at_top: false
  render_module_header: false
  insert_header_anchors: true
  use_fixed_header_levels: true
  header_level_by_type:
    Module: 1
    Class: 2
    Function: 3
    Method: 3
    ClassMethod: 3
    StaticMethod: 3
    Property: 3
  add_method_class_prefix: false
  add_member_class_prefix: false
  signature_with_short_description: true

processors:
  - type: smart
  - type: filter
    documented_only: false
  - type: crossref
"""
    with open(output_path, "w") as f:
        f.write(config)
    return output_path

def add_frontmatter(mdx_file, module_name):
    """添加前置元数据到MDX文件"""
    with open(mdx_file, "r", encoding="utf-8") as f:
        content = f.read()
    
    
    # 检查是否已有前置元数据
    if content.startswith("---"):
        # 如果已有，则不添加
        return
    
    # 添加前置元数据
    with open(mdx_file, "w", encoding="utf-8") as f:
        f.write(content)

def get_all_modules(package_name="camel", recursive=True):
    """获取包中的所有模块"""
    modules = []
    
    try:
        # 导入主包
        package = importlib.import_module(package_name)
        modules.append(package_name)
        
        # 获取包的路径
        package_path = os.path.dirname(package.__file__)
        
        # 遍历包中的所有Python文件
        for root, dirs, files in os.walk(package_path):
            if not recursive and root != package_path:
                continue
                
            for file in files:
                if file.endswith(".py") and file != "__init__.py":
                    # 计算模块的相对路径
                    rel_path = os.path.relpath(os.path.join(root, file), os.path.dirname(package_path))
                    # 转换为模块名称
                    module_name = os.path.splitext(rel_path)[0].replace(os.sep, ".")
                    modules.append(module_name)
            
            # 处理子包
            for dir_name in dirs:
                if os.path.isfile(os.path.join(root, dir_name, "__init__.py")):
                    # 计算子包的相对路径
                    rel_path = os.path.relpath(os.path.join(root, dir_name), os.path.dirname(package_path))
                    # 转换为包名称
                    subpackage_name = rel_path.replace(os.sep, ".")
                    modules.append(subpackage_name)
    
    except ImportError as e:
        print(f"Error importing {package_name}: {e}")
    
    return sorted(modules)

def post_process_mdx(file_path):
    """处理生成的MDX文件，改进格式"""
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # # 添加空行使标题更易读
    # content = re.sub(r'(#+\s+.*?)\n', r'\1\n\n', content)
    
    # # 改进代码块格式
    # content = re.sub(r'```\n', r'```python\n', content)
    
    # # 为函数和类添加水平线分隔
    # content = re.sub(r'\n(##\s+.*?)\n', r'\n\n---\n\n\1\n', content)
    
    # # 删除多余的水平线
    # content = re.sub(r'\n---\s*\n---\s*\n', r'\n---\n', content)
    
    # 保存更新后的内容
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

def generate_mdx_docs(module_name, output_dir):
    """为指定模块生成MDX文档"""
    os.makedirs(output_dir, exist_ok=True)
    
    # 输出文件路径
    output_file = os.path.join(output_dir, f"{module_name}.mdx")
    
    # 使用pydoc-markdown生成文档
    try:
        result = subprocess.run(
            ["pydoc-markdown", "-I", ".", "-m", module_name],
            capture_output=True,
            text=True,
            check=True
        )
        
        # 将输出写入文件
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(result.stdout)
        
        # 处理生成的文件
        post_process_mdx(output_file)
        
        # 添加前置元数据
        add_frontmatter(output_file, module_name)
        
        return output_file
    except subprocess.CalledProcessError as e:
        print(f"Error generating docs for {module_name}: {e}")
        print(f"STDERR: {e.stderr}")
        return None

def main():
    parser = argparse.ArgumentParser(description="Generate API documentation directly from Python sources")
    parser.add_argument("--output_dir", type=str, default="mintlify/reference",
                       help="Output directory for MDX files")
    parser.add_argument("--package", type=str, default="camel",
                       help="Package name to generate documentation for")
    parser.add_argument("--clean", action="store_true",
                       help="Clean output directory before generating new files")
    args = parser.parse_args()
    
    # 检查pydoc-markdown是否已安装
    try:
        subprocess.run(["pydoc-markdown", "--version"], 
                     stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("ERROR: pydoc-markdown is not installed. Please install it with:")
        print("  pip install pydoc-markdown")
        sys.exit(1)
    
    # 创建配置文件
    config_file = create_config_file()
    
    # 创建输出目录
    os.makedirs(args.output_dir, exist_ok=True)
    
    # 清理输出目录（如有需要）
    if args.clean:
        print(f"Cleaning output directory: {args.output_dir}")
        for file in glob.glob(os.path.join(args.output_dir, "*.mdx")):
            os.remove(file)
    
    # 获取所有模块
    print(f"Discovering modules in {args.package}...")
    modules = get_all_modules(args.package)
    
    # 生成文档
    print(f"Generating documentation for {len(modules)} modules...")
    for i, module in enumerate(modules):
        print(f"  [{i+1}/{len(modules)}] Processing {module}...")
        output_file = generate_mdx_docs(module, args.output_dir)
        if output_file:
            print(f"    Generated {os.path.basename(output_file)}")
    
    # 清理配置文件
    if os.path.exists(config_file):
        os.remove(config_file)
    
    print(f"\nAPI documentation generated successfully in {args.output_dir}")
    print("\nTo preview your Mintlify documentation, run:")
    print("  cd mintlify && npx mintlify dev")

if __name__ == "__main__":
    main() 