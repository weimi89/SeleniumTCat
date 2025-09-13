@echo off
echo Installing Takkyubin Tool - Windows Compatible Version...

echo Step 1: Installing uv...
pip install uv

echo Step 2: Creating virtual environment...
uv venv

echo Step 3: Installing compatible versions for Windows...
uv pip install selenium==4.15.0
uv pip install webdriver-manager==4.0.1
uv pip install requests==2.31.0
uv pip install beautifulsoup4==4.12.2
uv pip install openpyxl==3.1.2
uv pip install python-dotenv==1.0.0

echo Step 4: Installing ddddocr with compatible ONNX version...
uv pip install ddddocr==1.4.7
uv pip install onnxruntime==1.15.1

echo Step 5: If above fails, trying CPU-only version...
uv pip uninstall -y onnxruntime
uv pip install onnxruntime-cpu==1.15.1

echo Setup complete! 
echo If you still get DLL errors, please install:
echo Microsoft Visual C++ Redistributable: https://aka.ms/vs/17/release/vc_redist.x64.exe
pause