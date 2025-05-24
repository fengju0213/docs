# Sphinx-based API Documentation Generator

This tool generates API documentation using **Sphinx** instead of pydoc-markdown, providing better docstring extraction and more flexible output formatting.

## 🚀 Quick Start

### Prerequisites

1. **Install required dependencies:**
   ```bash
   pip install sphinx sphinx-rtd-theme beautifulsoup4
   ```

2. **Install optional but recommended tools:**
   ```bash
   # For better HTML to Markdown conversion
   pip install html2text
   
   # Install pandoc (best conversion quality)
   # macOS: brew install pandoc
   # Ubuntu/Debian: apt-get install pandoc
   # Windows: Download from https://pandoc.org/installing.html
   ```

### Basic Usage

```bash
# Generate documentation for all modules
python build_api_docs.py

# Generate for specific output directory
python build_api_docs.py --output_dir docs/api

# Clean and regenerate all docs
python build_api_docs.py --clean

# Only update changed modules (incremental)
python build_api_docs.py --incremental

# Skip generation, only update mint.json
python build_api_docs.py --skip_generation
```

### Test the Setup

```bash
# Run the test script to verify everything works
python test_sphinx_docs.py
```

## 🔧 How It Works

### 1. **Sphinx Integration**
- Uses `sphinx.ext.autodoc` to extract docstrings automatically
- Supports Google/NumPy style docstrings via `sphinx.ext.napoleon`
- Generates comprehensive API documentation with proper cross-references

### 2. **Multi-Format Pipeline**
```
Python Module → Sphinx → RST → HTML/Markdown → MDX
```

1. **RST Generation**: Creates RestructuredText files for each module
2. **Sphinx Build**: Uses Sphinx to process docstrings and generate output
3. **Format Conversion**: Converts to Markdown (preferably via MyST, fallback to HTML→MD)
4. **MDX Transformation**: Adds frontmatter and formats for Mintlify

### 3. **Intelligent Fallbacks**
- **Primary**: Direct Markdown generation via MyST parser
- **Secondary**: HTML generation + Pandoc conversion
- **Tertiary**: HTML generation + BeautifulSoup + html2text
- **Fallback**: Basic text extraction

## 📋 Features

### ✅ Improvements over pydoc-markdown

- **Better docstring parsing**: Handles complex docstrings more reliably
- **Rich formatting**: Supports rst, markdown, and mixed formats
- **Cross-references**: Automatic linking between modules
- **Flexible output**: Multiple output formats supported
- **Robust error handling**: Graceful fallbacks for problematic modules

### 🛠 Configuration Options

The Sphinx configuration includes:

- **autodoc**: Automatic API documentation
- **napoleon**: Google/NumPy docstring support  
- **viewcode**: Source code links
- **autosummary**: Module summaries
- **myst_parser**: Markdown input support

### 📁 File Structure

```
build_api_docs.py          # Main script (Sphinx-based)
test_sphinx_docs.py        # Test script
README_sphinx_docs.md      # This file

# Generated during build:
<temp>/source/             # Sphinx source files
<temp>/build/              # Sphinx build output
docs/reference/*.mdx       # Final MDX files
```

## 🔍 Troubleshooting

### Common Issues

1. **"Sphinx not found"**
   ```bash
   pip install sphinx sphinx-rtd-theme
   ```

2. **Poor HTML conversion quality**
   ```bash
   # Install pandoc for best results
   brew install pandoc  # macOS
   sudo apt-get install pandoc  # Ubuntu
   ```

3. **Missing docstrings in output**
   - Check that your modules have proper docstrings
   - Verify the module can be imported successfully
   - Use `--incremental` to debug specific modules

4. **Empty or minimal documentation**
   - The tool filters out modules with insufficient content
   - Check `is_content_substantial()` function for criteria
   - Modules need at least 3 lines of substantial content

### Debug Mode

```bash
# Add verbose output by checking intermediate files
python build_api_docs.py --clean
# Check the temporary Sphinx files in /tmp/
```

## 🆚 Comparison with pydoc-markdown

| Feature | pydoc-markdown | Sphinx |
|---------|---------------|--------|
| Setup complexity | Simple | Moderate |
| Docstring parsing | Basic | Excellent |
| Output quality | Good | Excellent |
| Cross-references | Limited | Full support |
| Customization | Limited | Extensive |
| Error handling | Basic | Robust |
| Performance | Fast | Moderate |

## 📚 Advanced Usage

### Custom Sphinx Extensions

Edit the `create_sphinx_config()` function to add more extensions:

```python
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
    'sphinx.ext.intersphinx',  # Cross-project references
    'sphinx.ext.mathjax',      # Math support
    'myst_parser',
]
```

### Module Filtering

Modify `get_all_modules()` to customize which modules are documented:

```python
# Skip test modules
if 'test' in module_name:
    continue
    
# Only document specific subpackages
if not module_name.startswith('camel.agents'):
    continue
```

## 🤝 Contributing

When modifying this tool:

1. Test with `test_sphinx_docs.py` first
2. Verify output quality with a sample module
3. Check that mint.json updates correctly
4. Update this README for any new features

---

**Note**: This tool replaces the previous pydoc-markdown implementation with a more robust Sphinx-based approach for better documentation quality and reliability. 