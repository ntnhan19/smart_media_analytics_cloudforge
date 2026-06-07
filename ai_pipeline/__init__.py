"""
AI Pipeline — Smart Media Analytics
"""

import os

# Tự động thêm cuDNN vào PATH khi package được import.
# Cần thiết trên Windows vì nvidia-cudnn-cu12 cài DLL vào thư mục riêng
# không nằm trong System PATH mặc định.
try:
    import nvidia.cudnn
    _cudnn_bin = os.path.join(os.path.dirname(nvidia.cudnn.__file__), "bin")
    if os.path.isdir(_cudnn_bin):
        os.add_dll_directory(_cudnn_bin)
        if _cudnn_bin not in os.environ.get("PATH", ""):
            os.environ["PATH"] = _cudnn_bin + os.pathsep + os.environ.get("PATH", "")
except (ImportError, AttributeError, OSError):
    pass
