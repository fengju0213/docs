#!/usr/bin/env python3
"""
Simple test script to validate Sphinx-based documentation generation.
"""

import subprocess
import sys
import tempfile
import os
from pathlib import Path

def check_dependencies():
    """检查必要的依赖是否已安装"""
    dependencies = [
        ("sphinx-build", "Sphinx"),
        ("python", "Python")
    ]
    
    missing = []
    for cmd, name in dependencies:
        try:
            subprocess.run([cmd, "--version"], 
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            print(f"✅ {name} is available")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print(f"❌ {name} is not available")
            missing.append(name)
    
    # 检查 Python 包
    python_packages = [
        ("sphinx", "Sphinx"),
        ("bs4", "BeautifulSoup4")
    ]
    
    for package, name in python_packages:
        try:
            __import__(package)
            print(f"✅ {name} package is available")
        except ImportError:
            print(f"❌ {name} package is not available")
            missing.append(name)
    
    # 检查可选包
    optional_packages = [
        ("html2text", "html2text (for better HTML conversion)"),
    ]
    
    for package, name in optional_packages:
        try:
            __import__(package)
            print(f"✅ {name} is available (optional)")
        except ImportError:
            print(f"⚠️  {name} not available (optional)")
    
    return missing

def test_simple_module():
    """测试对一个简单模块的文档生成"""
    print("\n" + "="*50)
    print("Testing Sphinx documentation generation")
    print("="*50)
    
    # 导入我们的构建脚本
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from build_api_docs import (
        create_sphinx_config, 
        sphinx_build_to_markdown,
        markdown_to_mdx
    )
    
    with tempfile.TemporaryDirectory() as temp_dir:
        source_dir = os.path.join(temp_dir, "source")
        build_dir = os.path.join(temp_dir, "build")
        os.makedirs(source_dir)
        os.makedirs(build_dir)
        
        print(f"📁 Created temporary directories:")
        print(f"   Source: {source_dir}")
        print(f"   Build:  {build_dir}")
        
        # 创建配置
        print("🔧 Creating Sphinx configuration...")
        config_file = create_sphinx_config(source_dir, build_dir, "os")  # 使用 os 模块进行测试
        print(f"   Config created: {config_file}")
        
        # 测试文档生成
        print("📚 Testing documentation generation for 'os' module...")
        try:
            markdown_content = sphinx_build_to_markdown(source_dir, build_dir, "os")
            if markdown_content:
                print("✅ Markdown generation successful")
                print(f"   Content length: {len(markdown_content)} characters")
                print(f"   First 200 chars: {markdown_content[:200]}...")
                
                # 测试 MDX 转换
                print("🔄 Testing MDX conversion...")
                mdx_content = markdown_to_mdx(markdown_content, "os")
                if mdx_content:
                    print("✅ MDX conversion successful")
                    print(f"   MDX length: {len(mdx_content)} characters")
                    
                    # 保存示例文件
                    example_file = "example_os_docs.mdx"
                    with open(example_file, 'w', encoding='utf-8') as f:
                        f.write(mdx_content)
                    print(f"💾 Example saved to: {example_file}")
                else:
                    print("❌ MDX conversion failed")
            else:
                print("❌ Markdown generation failed")
        except Exception as e:
            print(f"❌ Error during documentation generation: {e}")

def main():
    print("🔍 Checking dependencies...")
    missing = check_dependencies()
    
    if missing:
        print(f"\n❌ Missing dependencies: {', '.join(missing)}")
        print("\nTo install missing dependencies:")
        print("  pip install sphinx sphinx-rtd-theme myst-parser beautifulsoup4")
        sys.exit(1)
    else:
        print("\n✅ All dependencies are available!")
    
    test_simple_module()
    
    print("\n" + "="*50)
    print("Test completed!")
    print("="*50)

if __name__ == "__main__":
    main() 