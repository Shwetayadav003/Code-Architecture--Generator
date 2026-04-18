import streamlit as st
import ast
import zipfile
import tempfile
from pathlib import Path

st.set_page_config(page_title="Code Architecture Generator", page_icon="🏗️", layout="wide")

# Professional CSS styling
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        padding: 2rem;
        border-radius: 1rem;
        margin-bottom: 2rem;
        text-align: center;
        color: white;
    }
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 0.5rem;
        text-align: center;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        border-top: 3px solid #2a5298;
    }
    .metric-number {
        font-size: 2rem;
        font-weight: bold;
        color: #2a5298;
    }
    .stButton > button {
        background: #2a5298;
        color: white;
        border: none;
        width: 100%;
    }
    .stButton > button:hover {
        background: #1e3c72;
    }
    .success-box {
        background: #d4edda;
        color: #155724;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #28a745;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="main-header">
    <h1>Code Architecture Generator</h1>
    <p>Upload Python code to generate architecture visualization</p>
</div>
""", unsafe_allow_html=True)

# Session state
if 'functions' not in st.session_state:
    st.session_state.functions = []
if 'classes' not in st.session_state:
    st.session_state.classes = []
if 'filename' not in st.session_state:
    st.session_state.filename = None
if 'analyzed' not in st.session_state:
    st.session_state.analyzed = False
if 'metrics' not in st.session_state:
    st.session_state.metrics = {}

# Sidebar
with st.sidebar:
    st.markdown("### Upload")
    upload_type = st.radio("Select type:", ["Single Python File", "Project Folder (ZIP)"])
    
    if upload_type == "Single Python File":
        uploaded_file = st.file_uploader("Choose a Python file", type=['py'])
    else:
        uploaded_file = st.file_uploader("Choose a ZIP file", type=['zip'])
    
    generate_btn = st.button("Generate Architecture", use_container_width=True)

def parse_code(code):
    try:
        tree = ast.parse(code)
        functions = []
        classes = []
        
        total_lines = len(code.split('\n'))
        total_functions = 0
        total_classes = 0
        total_methods = 0
        max_function_length = 0
        max_params = 0
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                functions.append(node.name)
                total_functions += 1
                
                func_lines = node.end_lineno - node.lineno if node.end_lineno else 1
                max_function_length = max(max_function_length, func_lines)
                
                num_params = len(node.args.args)
                max_params = max(max_params, num_params)
                
            elif isinstance(node, ast.ClassDef):
                methods = [m.name for m in node.body if isinstance(m, ast.FunctionDef)]
                classes.append({'name': node.name, 'methods': methods})
                total_classes += 1
                total_methods += len(methods)
        
        metrics = {
            'total_lines': total_lines,
            'total_functions': total_functions,
            'total_classes': total_classes,
            'total_methods': total_methods,
            'max_function_length': max_function_length,
            'max_params': max_params
        }
        
        return functions, classes, metrics
    except:
        return [], [], {}

def generate_diagram(functions, classes):
    lines = ["graph TD"]
    lines.append('    Main["Main Application"]')
    
    for i, cls in enumerate(classes):
        lines.append(f'    Class{i}["{cls["name"]}"]')
        lines.append(f'    Main --> Class{i}')
        
        for j, method in enumerate(cls['methods'][:5]):
            lines.append(f'    Method{i}{j}["{method}"]')
            lines.append(f'    Class{i} --> Method{i}{j}')
    
    for i, func in enumerate(functions[:10]):
        lines.append(f'    Function{i}["{func}"]')
        lines.append(f'    Main --> Function{i}')
    
    return "\n".join(lines)

def get_html_export(mermaid_code):
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
        <style>
            body {{ background: white; padding: 20px; font-family: Arial, sans-serif; }}
            .mermaid {{ text-align: center; }}
            h2 {{ color: #2a5298; }}
        </style>
    </head>
    <body>
        <h2>Code Architecture Diagram</h2>
        <div class="mermaid">
            {mermaid_code}
        </div>
        <script>mermaid.initialize({{ startOnLoad: true, theme: 'base' }});</script>
        <p style="margin-top: 20px; color: #666; font-size: 12px;">Generated by Code Architecture Generator</p>
    </body>
    </html>
    """

if generate_btn and uploaded_file:
    with st.spinner("Analyzing code..."):
        if upload_type == "Single Python File":
            content = uploaded_file.getvalue().decode('utf-8')
            functions, classes, metrics = parse_code(content)
            
            st.session_state.functions = functions
            st.session_state.classes = classes
            st.session_state.metrics = metrics
            st.session_state.filename = uploaded_file.name
            st.session_state.analyzed = True
            
        else:
            with tempfile.TemporaryDirectory() as tmpdir:
                zip_path = Path(tmpdir) / "upload.zip"
                with open(zip_path, "wb") as f:
                    f.write(uploaded_file.getvalue())
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(tmpdir)
                py_files = list(Path(tmpdir).rglob("*.py"))
                
                all_functions = []
                all_classes = []
                combined_metrics = {
                    'total_lines': 0,
                    'total_functions': 0,
                    'total_classes': 0,
                    'total_methods': 0,
                    'max_function_length': 0,
                    'max_params': 0
                }
                
                for py_file in py_files[:10]:
                    with open(py_file, 'r', encoding='utf-8') as f:
                        functions, classes, metrics = parse_code(f.read())
                        all_functions.extend(functions)
                        all_classes.extend(classes)
                        combined_metrics['total_lines'] += metrics.get('total_lines', 0)
                        combined_metrics['total_functions'] += metrics.get('total_functions', 0)
                        combined_metrics['total_classes'] += metrics.get('total_classes', 0)
                        combined_metrics['total_methods'] += metrics.get('total_methods', 0)
                        combined_metrics['max_function_length'] = max(combined_metrics['max_function_length'], metrics.get('max_function_length', 0))
                        combined_metrics['max_params'] = max(combined_metrics['max_params'], metrics.get('max_params', 0))
                
                st.session_state.functions = list(set(all_functions))
                unique_classes = []
                class_names = set()
                for c in all_classes:
                    if c['name'] not in class_names:
                        class_names.add(c['name'])
                        unique_classes.append(c)
                st.session_state.classes = unique_classes
                st.session_state.metrics = combined_metrics
                st.session_state.filename = f"ZIP with {len(py_files)} files"
                st.session_state.analyzed = True

elif generate_btn and not uploaded_file:
    st.warning("Please upload a file first")

if st.session_state.analyzed:
    functions = st.session_state.functions
    classes = st.session_state.classes
    metrics = st.session_state.metrics
    
    st.markdown(f"""
    <div class="success-box">
        Successfully analyzed: <strong>{st.session_state.filename}</strong>
    </div>
    """, unsafe_allow_html=True)
    
    # Metrics row
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f'<div class="metric-card"><div>Functions</div><div class="metric-number">{len(functions)}</div></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="metric-card"><div>Classes</div><div class="metric-number">{len(classes)}</div></div>', unsafe_allow_html=True)
    with col3:
        st.markdown(f'<div class="metric-card"><div>Total Nodes</div><div class="metric-number">{len(functions) + len(classes)}</div></div>', unsafe_allow_html=True)
    
    # Code Metrics Dashboard
    st.markdown("### Code Metrics")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Lines", metrics.get('total_lines', 0))
    with col2:
        st.metric("Functions", metrics.get('total_functions', 0))
    with col3:
        st.metric("Classes", metrics.get('total_classes', 0))
    with col4:
        st.metric("Methods", metrics.get('total_methods', 0))
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Max Function Length", f"{metrics.get('max_function_length', 0)} lines")
    with col2:
        st.metric("Max Parameters", metrics.get('max_params', 0))
    
    # Architecture Diagram
    st.markdown("### Architecture Diagram")
    
    mermaid_code = generate_diagram(functions, classes)
    
    # Display Mermaid diagram
    from streamlit.components.v1 import html
    
    mermaid_html = f"""
    <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
    <script>
        mermaid.initialize({{ startOnLoad: true, theme: 'base' }});
    </script>
    <div class="mermaid" style="background: white; padding: 20px; border-radius: 10px; overflow-x: auto;">
{mermaid_code}
    </div>
    """
    html(mermaid_html, height=450)
    
    # Export Options
    st.markdown("### Export Options")
    
    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            "Download Mermaid Code",
            mermaid_code,
            "architecture.mmd",
            mime="text/plain",
            use_container_width=True
        )
    with col2:
        html_export = get_html_export(mermaid_code)
        st.download_button(
            "Export as HTML",
            html_export,
            "architecture_diagram.html",
            mime="text/html",
            use_container_width=True
        )
    
    # Report download
    report = f"""CODE ARCHITECTURE REPORT

File: {st.session_state.filename}

METRICS:
  Total Lines: {metrics.get('total_lines', 0)}
  Functions: {len(functions)}
  Classes: {len(classes)}
  Methods: {metrics.get('total_methods', 0)}
  Max Function Length: {metrics.get('max_function_length', 0)} lines
  Max Parameters: {metrics.get('max_params', 0)}

FUNCTIONS ({len(functions)}):
{chr(10).join([f'  - {f}()' for f in functions[:50]])}

CLASSES ({len(classes)}):
{chr(10).join([f'  - {c["name"]}' for c in classes])}

Generated by Code Architecture Generator
"""
    
    st.download_button(
        "Download Full Report",
        report,
        "architecture_report.txt",
        use_container_width=True
    )
    
    # Expandable sections
    with st.expander("View All Functions"):
        cols = st.columns(4)
        for i, func in enumerate(functions):
            cols[i % 4].write(f"- {func}()")
    
    with st.expander("View All Classes"):
        for cls in classes:
            st.write(f"**{cls['name']}**")
            for method in cls['methods']:
                st.write(f"  - {method}()")

st.markdown("---")
st.caption("Upload a Python file to generate architecture diagram and code metrics")