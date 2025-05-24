#!/usr/bin/env python3
import json
import os
import subprocess
import sys
import glob
import importlib
import re
import time
from pathlib import Path
import argparse
from collections import defaultdict
import tempfile
import shutil

# 模块名到显示名称的映射
MODULE_NAME_DISPLAY = {
    "agents": "Agents",
    "configs": "Configs",
    "datagen": "Data Generation",
    "datasets": "Datasets",
    "data_collector": "Data Collector",
    "embeddings": "Embeddings",
    "environments": "Environments",
    "interpreters": "Interpreters",
    "loaders": "Loaders",
    "memories": "Memory",
    "messages": "Messages",
    "models": "Models",
    "prompts": "Prompts",
    "responses": "Responses",
    "retrievers": "Retrievers",
    "runtime": "Runtime",
    "schemas": "Schemas",
    "societies": "Societies",
    "storages": "Storage",
    "tasks": "Tasks",
    "terminators": "Terminators",
    "toolkits": "Toolkits",
    "types": "Types",
    "utils": "Utilities",
    "verifiers": "Verifiers",
    "benchmarks": "Benchmarks",
    "bots": "Bots",
    "personas": "Personas",
    "extractors": "Extractors"
}

# 自定义顺序，这决定了顶级模块的显示顺序
MODULE_ORDER = [
    "agents",
    "configs",
    "datagen",
    "datasets",
    "embeddings",
    "models",
    "interpreters",
    "memories",
    "messages",
    "prompts",
    "responses",
    "retrievers",
    "societies",
    "storages",
    "tasks",
    "terminators",
    "toolkits",
    "types",
    "verifiers",
    "bots",
    "runtime",
    "utils",
    "environments",
    "extractors",
    "personas"
]

def create_sphinx_config(source_dir, build_dir, package_name="camel"):
    """创建 Sphinx 配置文件"""
    conf_py_content = f'''# Configuration file for the Sphinx documentation builder.
import os
import sys
sys.path.insert(0, os.path.abspath('../../..'))  # Add package root to path

# Project information
project = '{package_name}'
copyright = '2024, CAMEL-AI'
author = 'CAMEL-AI'

# The full version, including alpha/beta/rc tags
release = '0.1.0'

# Extensions
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary',
    'sphinx.ext.viewcode',
    'sphinx.ext.napoleon',
]

# autodoc settings
autodoc_default_options = {{
    'members': True,
    'undoc-members': True,
    'private-members': False,
    'special-members': '__init__',
    'inherited-members': False,
    'show-inheritance': True,
}}

# Be more tolerant of errors
autodoc_warningiserror = False
suppress_warnings = ['autodoc', 'autodoc.import_object']

# autosummary settings
autosummary_generate = True
autosummary_imported_members = True

# Napoleon settings (for Google/NumPy style docstrings)
napoleon_google_docstring = True
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = False
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True
napoleon_use_admonition_for_examples = False
napoleon_use_admonition_for_notes = False
napoleon_use_admonition_for_references = False
napoleon_use_ivar = False
napoleon_use_param = True
napoleon_use_rtype = True
napoleon_type_aliases = None

# Source and build directories
source_suffix = {{
    '.rst': None,
}}

# Master document
master_doc = 'index'

# Templates path
templates_path = ['_templates']

# Exclude patterns
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# HTML output options
html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']

# More tolerant settings
nitpicky = False
'''
    
    # 创建配置文件
    conf_file = os.path.join(source_dir, 'conf.py')
    with open(conf_file, 'w', encoding='utf-8') as f:
        f.write(conf_py_content)
    
    # 创建 _static 和 _templates 目录
    static_dir = os.path.join(source_dir, '_static')
    templates_dir = os.path.join(source_dir, '_templates')
    os.makedirs(static_dir, exist_ok=True)
    os.makedirs(templates_dir, exist_ok=True)
    
    return conf_file

def create_index_rst(source_dir):
    """创建 index.rst 文件"""
    index_content = """
Welcome to API Documentation
============================

.. toctree::
   :maxdepth: 2
   :caption: Contents:

This is a temporary index file for Sphinx builds.
"""
    
    index_file = os.path.join(source_dir, 'index.rst')
    with open(index_file, 'w', encoding='utf-8') as f:
        f.write(index_content.strip())
    
    return index_file

def generate_rst_files(source_dir, package_name="camel", modules=None):
    """使用 sphinx-apidoc 生成 RST 文件"""
    try:
        # 如果指定了特定模块，我们需要手动创建 RST 文件
        if modules:
            for module in modules:
                rst_content = f"""
{module}
{'=' * len(module)}

.. automodule:: {module}
   :members:
   :undoc-members:
   :show-inheritance:
"""
                rst_file = os.path.join(source_dir, f"{module}.rst")
                with open(rst_file, 'w', encoding='utf-8') as f:
                    f.write(rst_content.strip())
        else:
            # 使用 sphinx-apidoc 生成所有模块的 RST 文件
            cmd = [
                'sphinx-apidoc',
                '-f',  # Force overwrite
                '-o', source_dir,  # Output directory
                '--separate',  # Create separate files for each module
                '--module-first',  # Put module documentation before submodule
                package_name,  # Package directory
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            print(f"Generated RST files: {result.stdout}")
        
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error generating RST files: {e}")
        if e.stderr:
            print(f"STDERR: {e.stderr}")
        return False

def sphinx_build_to_markdown(source_dir, build_dir, module_name):
    """使用 Sphinx 构建单个模块的 markdown 文档"""
    try:
        # 创建 index.rst 文件
        create_index_rst(source_dir)
        
        # 创建临时的 RST 文件用于单个模块
        rst_content = f"""
{module_name}
{'=' * len(module_name)}

.. automodule:: {module_name}
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__
   :ignore-module-all:
"""
        rst_file = os.path.join(source_dir, f"{module_name}.rst")
        with open(rst_file, 'w', encoding='utf-8') as f:
            f.write(rst_content.strip())
        
        # 首先尝试直接使用 MyST builder 生成 markdown
        markdown_build_dir = os.path.join(build_dir, 'markdown')
        try:
            cmd = [
                'sphinx-build',
                '-b', 'markdown',
                '-q',  # quiet mode
                '-W', '--keep-going',  # Convert warnings to errors but keep going
                source_dir,
                markdown_build_dir
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            # 读取生成的 markdown 文件
            markdown_file = os.path.join(markdown_build_dir, f"{module_name}.md")
            if os.path.exists(markdown_file):
                with open(markdown_file, 'r', encoding='utf-8') as f:
                    return f.read()
        except subprocess.CalledProcessError:
            print(f"    MyST markdown builder not available, falling back to HTML conversion...")
        
        # 如果 markdown builder 不可用，使用 HTML 然后转换
        html_build_dir = os.path.join(build_dir, 'html')
        cmd = [
            'sphinx-build',
            '-b', 'html',
            '-q',  # quiet mode
            '--keep-going',  # Continue on errors
            source_dir,
            html_build_dir
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        # 读取生成的 HTML 文件并转换为 markdown
        html_file = os.path.join(html_build_dir, f"{module_name}.html")
        if os.path.exists(html_file):
            return convert_html_to_markdown(html_file)
        
        return None
        
    except subprocess.CalledProcessError as e:
        print(f"    Sphinx build failed: {e}")
        if e.stderr:
            # 只显示真正的错误，忽略警告
            error_lines = [line for line in e.stderr.split('\n') if 'ERROR:' in line]
            if error_lines:
                print(f"    Errors: {'; '.join(error_lines[:3])}")  # 只显示前3个错误
        return None
    except Exception as e:
        print(f"    Unexpected error: {e}")
        return None

def convert_html_to_markdown(html_file):
    """将 Sphinx 生成的 HTML 转换为 markdown"""
    try:
        # 首先尝试使用 pandoc 
        cmd = ['pandoc', '-f', 'html', '-t', 'markdown', '--wrap=none', html_file]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return clean_markdown_content(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"    Pandoc conversion failed: {e}")
        return None
    except FileNotFoundError:
        print("    Pandoc not found, trying BeautifulSoup conversion...")
        return simple_html_to_markdown(html_file)

def clean_markdown_content(markdown_content):
    """清理 markdown 内容"""
    if not markdown_content:
        return None
    
    lines = markdown_content.split('\n')
    cleaned_lines = []
    
    # 跳过无用的开头和结尾
    start_found = False
    
    for line in lines:
        line = line.strip()
        
        # 跳过空行直到找到实际内容
        if not start_found and not line:
            continue
            
        # 跳过 HTML 导航和其他无关内容
        if any(skip in line.lower() for skip in [
            'navigation', 'breadcrumb', 'sidebar', 'footer',
            'edit on github', 'view source', 'download'
        ]):
            continue
            
        # 找到实际内容的开始
        if line and not start_found:
            start_found = True
            
        if start_found:
            cleaned_lines.append(line if line else '')
    
    # 移除结尾的空行
    while cleaned_lines and not cleaned_lines[-1]:
        cleaned_lines.pop()
    
    return '\n'.join(cleaned_lines)

def simple_html_to_markdown(html_file):
    """简单的 HTML 到 markdown 转换（备用方案）"""
    try:
        from bs4 import BeautifulSoup
        import html2text
        
        with open(html_file, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f, 'html.parser')
        
        # 查找主要内容区域
        content = (soup.find('div', class_='body') or 
                  soup.find('div', class_='document') or
                  soup.find('div', class_='documentwrapper') or
                  soup.find('main') or
                  soup.find('body'))
        
        if not content:
            return None
        
        # 移除导航和其他无关元素
        for element in content.find_all(['nav', 'aside', 'footer', 'header']):
            element.decompose()
        
        # 使用 html2text 转换
        h = html2text.HTML2Text()
        h.ignore_links = False
        h.ignore_images = True
        h.body_width = 0  # 不换行
        
        return clean_markdown_content(h.handle(str(content)))
        
    except ImportError:
        print("    html2text not available. Install with: pip install html2text")
        # 最基本的文本提取
        with open(html_file, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f, 'html.parser')
        content = soup.find('div', class_='body') or soup.find('body')
        return content.get_text() if content else None
    except Exception as e:
        print(f"    Error in HTML conversion: {e}")
        return None

def markdown_to_mdx(markdown_content, module_name):
    """将 markdown 转换为 MDX 格式"""
    if not markdown_content:
        return None
    
    # 基本的 markdown 到 MDX 转换
    # 添加 MDX 头部
    mdx_content = f"---\ntitle: {module_name}\n---\n\n"
    
    # 处理标题层级，确保合适的结构
    lines = markdown_content.split('\n')
    processed_lines = []
    
    for line in lines:
        # 转换标题格式
        if line.startswith('#'):
            # 确保标题格式正确
            level = len(line) - len(line.lstrip('#'))
            title = line.lstrip('#').strip()
            if title:
                processed_lines.append('#' * level + ' ' + title)
        else:
            processed_lines.append(line)
    
    mdx_content += '\n'.join(processed_lines)
    
    return mdx_content

def get_module_display_name(module_name):
    """获取模块的美观显示名称"""
    if module_name in MODULE_NAME_DISPLAY:
        return MODULE_NAME_DISPLAY[module_name]
    # 如果没有映射，则将snake_case转换为title case
    return module_name.replace('_', ' ').title()

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

def get_changed_modules(package_name="camel", since_hours=24):
    """获取最近修改的模块（用于增量更新）"""
    changed_modules = []
    
    try:
        # 导入主包
        package = importlib.import_module(package_name)
        package_path = os.path.dirname(package.__file__)
        
        # 计算时间阈值
        time_threshold = time.time() - (since_hours * 3600)
        
        # 遍历包中的所有Python文件
        for root, dirs, files in os.walk(package_path):
            for file in files:
                if file.endswith(".py"):
                    file_path = os.path.join(root, file)
                    
                    # 检查文件修改时间
                    if os.path.getmtime(file_path) > time_threshold:
                        if file == "__init__.py":
                            # 处理包
                            rel_path = os.path.relpath(root, os.path.dirname(package_path))
                            module_name = rel_path.replace(os.sep, ".")
                            changed_modules.append(module_name)
                        else:
                            # 处理模块
                            rel_path = os.path.relpath(file_path, os.path.dirname(package_path))
                            module_name = os.path.splitext(rel_path)[0].replace(os.sep, ".")
                            changed_modules.append(module_name)
    
    except ImportError as e:
        print(f"Error importing {package_name}: {e}")
    
    return sorted(list(set(changed_modules)))

def is_content_substantial(content):
    """检查内容是否足够实质性，避免生成空文档"""
    if not content.strip():
        return False
    
    # 移除空行和常见的无用内容
    lines = [line.strip() for line in content.split('\n') if line.strip()]
    
    # 过滤掉只有标题的情况
    substantial_lines = []
    for line in lines:
        # 跳过标题行
        if line.startswith('#'):
            continue
        # 跳过只有模块ID的行
        if line.startswith('<a id='):
            continue
        # 跳过空的代码块
        if line in ['```', '```python']:
            continue
        substantial_lines.append(line)
    
    # 如果实质内容少于3行，认为不够实质性
    return len(substantial_lines) >= 3

def generate_mdx_docs(module_name, output_dir, sphinx_source_dir, sphinx_build_dir):
    """为指定模块生成MDX文档（使用 Sphinx）"""
    os.makedirs(output_dir, exist_ok=True)
    
    # 输出文件路径
    output_file = os.path.join(output_dir, f"{module_name}.mdx")
    
    try:
        # 使用 Sphinx 生成 markdown
        markdown_content = sphinx_build_to_markdown(sphinx_source_dir, sphinx_build_dir, module_name)
        
        if not markdown_content:
            print(f"    Skipped {module_name} (no content generated)")
            return None
        
        # 检查内容是否足够实质性
        if not is_content_substantial(markdown_content):
            print(f"    Skipped {module_name} (insufficient content)")
            return None
        
        # 转换为 MDX 格式
        mdx_content = markdown_to_mdx(markdown_content, module_name)
        
        if not mdx_content:
            print(f"    Skipped {module_name} (MDX conversion failed)")
            return None
        
        # 将输出写入文件
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(mdx_content)
        
        return output_file
    except Exception as e:
        print(f"Error generating docs for {module_name}: {e}")
        return None

def build_module_tree(mdx_files):
    """根据MDX文件名构建模块树"""
    # 创建新的子模块字典的工厂函数
    def new_module_dict():
        return {"pages": [], "submodules": defaultdict(new_module_dict)}
    
    # 使用嵌套的defaultdict构建树结构
    module_tree = new_module_dict()
    
    for file in mdx_files:
        # 从文件名获取模块路径
        module_path = file.stem  # 去掉.mdx后缀
        
        # 通常我们期望文件名是"camel.xxx.yyy"这样的格式
        if not module_path.startswith("camel."):
            # 如果不是camel模块，跳过
            continue
        
        # 分割模块路径
        parts = module_path.split('.')
        
        # 构建引用路径
        reference_path = f"reference/{module_path}"
        
        # 如果只是camel模块本身
        if len(parts) == 1:
            module_tree["pages"].append(reference_path)
            continue
        
        # 处理子模块
        current = module_tree
        for i, part in enumerate(parts[:-1]):  # 不包括最后一个部分，它是文件名
            if i == 0:  # camel根模块
                continue
                
            # 导航到子模块
            current = current["submodules"][part]
        
        # 确保pages列表存在
        if "pages" not in current:
            current["pages"] = []
        
        # 确保目录页（如camel.agents/camel.agents.mdx）出现在其子模块之前
        if parts[-1] == parts[-2]:
            current["pages"].insert(0, reference_path)
        else:
            current["pages"].append(reference_path)
    
    return module_tree

def convert_tree_to_navigation(module_tree):
    """将模块树转换为mint.json的navigation格式"""
    navigation = []
    
    # 首先添加顶级camel模块
    if "camel" in [Path(p).stem.split('.')[-1] for p in module_tree["pages"]]:
        navigation.append("reference/camel")
    
    # 按自定义顺序添加子模块
    for module_name in MODULE_ORDER:
        if module_name in module_tree["submodules"]:
            submodule = module_tree["submodules"][module_name]
            
            # 获取子模块的漂亮显示名称
            display_name = get_module_display_name(module_name)
            
            # 创建导航组
            nav_group = {
                "group": display_name,
                "pages": []
            }
            
            # 添加该模块的直接页面
            if "pages" in submodule:
                nav_group["pages"].extend(sorted(submodule["pages"]))
            
            # 递归处理子模块
            if "submodules" in submodule and submodule["submodules"]:
                for sub_name, sub_data in sorted(submodule["submodules"].items()):
                    if "pages" in sub_data and sub_data["pages"]:
                        # 直接扁平化子模块的页面
                        nav_group["pages"].extend(sorted(sub_data["pages"]))
            
            # 只有当有页面时才添加组
            if nav_group["pages"]:
                navigation.append(nav_group)
    
    return navigation

def update_mint_json(mint_json_path, navigation):
    """更新mint.json文件中的API Reference导航部分"""
    if not Path(mint_json_path).exists():
        print(f"Error: {mint_json_path} not found")
        return False
    
    with open(mint_json_path, "r", encoding="utf-8") as f:
        mint_data = json.load(f)
    
    # 找到API Reference tab并更新其groups
    tabs = mint_data.get("navigation", {}).get("tabs", [])
    for tab in tabs:
        if tab.get("tab") == "API Reference":
            tab["groups"] = navigation
            break
    
    # 保存更新后的mint.json
    with open(mint_json_path, "w", encoding="utf-8") as f:
        json.dump(mint_data, f, indent=2, ensure_ascii=False)
    
    return True

def main():
    parser = argparse.ArgumentParser(description="Generate API documentation using Sphinx and update mint.json configuration")
    parser.add_argument("--output_dir", type=str, default="docs/mintlify/reference",
                       help="Output directory for MDX files")
    parser.add_argument("--mint_json", type=str, default="docs/mintlify/mint.json",
                       help="Path to mint.json file")
    parser.add_argument("--package", type=str, default="camel",
                       help="Package name to generate documentation for")
    parser.add_argument("--clean", action="store_true",
                       help="Clean output directory before generating new files")
    parser.add_argument("--skip_generation", action="store_true",
                       help="Skip API documentation generation, only update mint.json")
    parser.add_argument("--incremental", action="store_true",
                       help="Only process modules that have been changed recently")
    parser.add_argument("--since_hours", type=int, default=24,
                       help="Hours to look back for changed files (used with --incremental)")
    args = parser.parse_args()
    
    if not args.skip_generation:
        # 检查 Sphinx 是否已安装
        try:
            subprocess.run(["sphinx-build", "--version"], 
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("ERROR: Sphinx is not installed. Please install it with:")
            print("  pip install sphinx sphinx-rtd-theme beautifulsoup4")
            sys.exit(1)
        
        # 检查可选依赖
        try:
            subprocess.run(["pandoc", "--version"], 
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            print("✅ Pandoc found (recommended for better HTML to Markdown conversion)")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("⚠️  Pandoc not found. Install for better conversion: https://pandoc.org/installing.html")
            print("   Fallback HTML parsing will be used.")
        
        # 创建临时目录用于 Sphinx
        with tempfile.TemporaryDirectory() as temp_dir:
            sphinx_source_dir = os.path.join(temp_dir, "source")
            sphinx_build_dir = os.path.join(temp_dir, "build")
            os.makedirs(sphinx_source_dir, exist_ok=True)
            os.makedirs(sphinx_build_dir, exist_ok=True)
            
            # 创建 Sphinx 配置
            create_sphinx_config(sphinx_source_dir, sphinx_build_dir, args.package)
            
            # 创建输出目录
            os.makedirs(args.output_dir, exist_ok=True)
            
            # 清理输出目录（如有需要）
            if args.clean:
                print(f"Cleaning output directory: {args.output_dir}")
                for file in glob.glob(os.path.join(args.output_dir, "*.mdx")):
                    os.remove(file)
            
            # 获取要处理的模块
            if args.incremental:
                print(f"Looking for modules changed in the last {args.since_hours} hours...")
                modules = get_changed_modules(args.package, args.since_hours)
                if not modules:
                    print("No modules have been changed recently.")
                    return
                print(f"Found {len(modules)} changed modules")
            else:
                print(f"Discovering all modules in {args.package}...")
                modules = get_all_modules(args.package)
            
            # 生成文档
            print(f"Generating documentation for {len(modules)} modules using Sphinx...")
            print("Note: Some warnings about docstring formatting are expected and will be handled gracefully.")
            generated_count = 0
            skipped_count = 0
            error_count = 0
            
            for i, module in enumerate(modules):
                print(f"  [{i+1}/{len(modules)}] Processing {module}...")
                try:
                    output_file = generate_mdx_docs(module, args.output_dir, sphinx_source_dir, sphinx_build_dir)
                    if output_file:
                        print(f"    ✅ Generated {os.path.basename(output_file)}")
                        generated_count += 1
                    else:
                        print(f"    ⚠️  Skipped {module} (insufficient content or errors)")
                        skipped_count += 1
                except Exception as e:
                    print(f"    ❌ Error processing {module}: {e}")
                    error_count += 1
            
            print(f"\n📊 Summary:")
            print(f"   Generated: {generated_count} files")
            print(f"   Skipped: {skipped_count} files") 
            print(f"   Errors: {error_count} files")
            
            if generated_count == 0:
                print("\n⚠️  No documentation was generated. This might be due to:")
                print("   - Module import issues")
                print("   - Missing or malformed docstrings")
                print("   - Sphinx configuration problems")
                print("\nTry running with a simple test first:")
                print("   python test_sphinx_docs.py")
    
    # 构建模块树和更新mint.json
    print("\nUpdating mint.json configuration...")
    
    # 获取生成的MDX文件
    mdx_files = list(Path(args.output_dir).glob("*.mdx"))
    if not mdx_files:
        print(f"No MDX files found in {args.output_dir}")
        return
    
    print(f"Found {len(mdx_files)} MDX files")
    
    # 构建模块树
    module_tree = build_module_tree(mdx_files)
    
    # 转换为navigation格式
    navigation = convert_tree_to_navigation(module_tree)
    
    # 更新mint.json
    if update_mint_json(args.mint_json, navigation):
        print(f"Updated {args.mint_json} with {len(navigation)} navigation groups")
    
    # 打印navigation结构摘要
    print("\nNavigation structure summary:")
    for item in navigation:
        if isinstance(item, str):
            print(f"- {item}")
        else:
            print(f"- Group: {item['group']} ({len(item['pages'])} pages)")
    
    print(f"\nAPI documentation build completed successfully!")
    print(f"Documentation files: {args.output_dir}")
    print(f"Configuration file: {args.mint_json}")
    
    if not args.skip_generation:
        print("\nTo preview your Mintlify documentation, run:")
        print("  cd docs/mintlify && npx mintlify dev")
        print("\n" + "="*60)
        print("DEPENDENCY INFORMATION")
        print("="*60)
        print("Required dependencies for this script:")
        print("  pip install sphinx sphinx-rtd-theme beautifulsoup4")
        print("\nOptional but recommended:")
        print("  pip install html2text  # Better HTML to Markdown conversion")
        print("  # Install pandoc: https://pandoc.org/installing.html")
        print("    # - macOS: brew install pandoc")
        print("    # - Ubuntu/Debian: apt-get install pandoc")
        print("    # - Windows: Download from https://pandoc.org/installing.html")
        print("\nWhat this script does:")
        print("  1. Uses Sphinx to extract docstrings from Python modules")
        print("  2. Converts RST format to Markdown (via HTML if needed)")
        print("  3. Transforms Markdown to MDX format for Mintlify")
        print("  4. Updates mint.json navigation structure")
        print("\nSphinx Extensions used:")
        print("  - sphinx.ext.autodoc: Extract docstrings automatically")
        print("  - sphinx.ext.napoleon: Support Google/NumPy style docstrings")
        print("  - sphinx.ext.viewcode: Add source code links")
        print("\nTroubleshooting:")
        print("  - If no docs are generated, check module imports")
        print("  - Docstring formatting warnings are usually harmless")
        print("  - Use --incremental to debug specific modules")

if __name__ == "__main__":
    main() 