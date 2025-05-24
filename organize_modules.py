#!/usr/bin/env python3
import json
import os
import re
from pathlib import Path
import sys
from collections import defaultdict

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
    "camel",
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

def get_module_display_name(module_name):
    """获取模块的美观显示名称"""
    if module_name in MODULE_NAME_DISPLAY:
        return MODULE_NAME_DISPLAY[module_name]
    # 如果没有映射，则将snake_case转换为title case
    return module_name.replace('_', ' ').title()

def get_module_files(reference_dir):
    """获取reference目录下的所有MDX文件"""
    reference_path = Path(reference_dir)
    if not reference_path.exists():
        print(f"Error: {reference_dir} directory not found")
        return []
    
    return list(reference_path.glob("*.mdx"))

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
        if module_name == "camel":
            continue  # 已处理过
            
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
                        # 如果子模块有多个页面，创建一个子组
                        if len(sub_data["pages"]) > 1:
                            sub_display_name = get_module_display_name(sub_name)
                            sub_group = {
                                "group": f"{display_name} {sub_display_name}",
                                "pages": sorted(sub_data["pages"])
                            }
                            # nav_group["pages"].append(sub_group)
                            # 直接扁平化
                            nav_group["pages"].extend(sorted(sub_data["pages"]))
                        else:
                            # 单个页面直接添加
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
    
    # 更新API Reference部分
    for i, group in enumerate(mint_data.get("navigation", [])):
        if group.get("group") == "API Reference":
            mint_data["navigation"][i]["pages"] = navigation
            break
    
    # 保存更新后的mint.json
    with open(mint_json_path, "w", encoding="utf-8") as f:
        json.dump(mint_data, f, indent=2)
    
    return True

def main():
    """主函数"""
    reference_dir = "mintlify/reference"
    mint_json_path = "mintlify/mint.json"
    
    # 获取模块文件
    mdx_files = get_module_files(reference_dir)
    if not mdx_files:
        print("No MDX files found")
        return
    
    print(f"Found {len(mdx_files)} MDX files")
    
    # 构建模块树
    module_tree = build_module_tree(mdx_files)
    
    # 转换为navigation格式
    navigation = convert_tree_to_navigation(module_tree)
    
    # 更新mint.json
    if update_mint_json(mint_json_path, navigation):
        print(f"Updated {mint_json_path} with {len(navigation)} navigation items")
    
    # 打印navigation结构
    print("\nNavigation structure:")
    for item in navigation:
        if isinstance(item, str):
            print(f"- {item}")
        else:
            print(f"- Group: {item['group']}")
            for page in item['pages']:
                if isinstance(page, str):
                    print(f"  - {page}")
                else:
                    print(f"  - Subgroup: {page['group']}")
                    for subpage in page['pages']:
                        print(f"    - {subpage}")

if __name__ == "__main__":
    main() 