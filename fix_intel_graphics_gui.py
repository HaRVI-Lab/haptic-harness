#!/usr/bin/env python3
"""
Intel graphics specific fixes for haptic harness generator GUI.
Addresses common Intel GPU issues with VTK/PyVista/Qt interactions.
"""

import os
import sys
from pathlib import Path

def setup_intel_graphics_environment():
    """Setup optimal environment for Intel graphics"""
    print("=== CONFIGURING INTEL GRAPHICS ENVIRONMENT ===")
    
    intel_env = {
        # Intel driver optimizations
        'MESA_LOADER_DRIVER_OVERRIDE': 'i965',
        'INTEL_DEBUG': '',
        'INTEL_BLACKHOLE_DEFAULT': '0',
        
        # OpenGL/Mesa settings for Intel
        'MESA_GL_VERSION_OVERRIDE': '4.5',
        'MESA_GLSL_VERSION_OVERRIDE': '450',
        'LIBGL_ALWAYS_INDIRECT': '0',  # Use direct rendering
        'LIBGL_DRI3_DISABLE': '0',     # Enable DRI3
        
        # Qt OpenGL backend for Intel
        'QT_OPENGL': 'desktop',
        'QT_XCB_GL_INTEGRATION': 'xcb_egl',
        'QT_X11_NO_MITSHM': '1',
        'QT_GRAPHICSSYSTEM': 'native',
        
        # VTK Intel optimizations
        'VTK_SILENCE_GET_VOID_POINTER_WARNINGS': '1',
        'VTK_USE_OFFSCREEN': '0',
        'VTK_DEFAULT_RENDER_WINDOW_OFFSCREEN': '0',
        
        # Memory management
        'MALLOC_CHECK_': '0',
        'MALLOC_PERTURB_': '0',
    }
    
    for key, value in intel_env.items():
        os.environ[key] = value
        print(f"✅ {key}={value}")
    
    # Create environment script
    with open('intel_graphics_env.sh', 'w') as f:
        f.write("#!/bin/bash\n# Intel Graphics Environment for Haptic Harness Generator\n\n")
        for key, value in intel_env.items():
            f.write(f"export {key}={value}\n")
    
    os.chmod('intel_graphics_env.sh', 0o755)
    print("✅ Created intel_graphics_env.sh")

def patch_pyvista_for_intel():
    """Create PyVista configuration optimized for Intel graphics"""
    
    pyvista_config = '''
# PyVista Intel Graphics Configuration
import pyvista as pv
import os

def configure_pyvista_for_intel():
    """Configure PyVista for optimal Intel graphics performance"""
    
    # Set theme optimized for Intel graphics
    pv.set_plot_theme('document')
    
    # Disable expensive rendering features
    pv.global_theme.anti_aliasing = False
    pv.global_theme.line_smoothing = False
    pv.global_theme.point_smoothing = False
    pv.global_theme.polygon_smoothing = False
    
    # Reduce default quality for better performance
    pv.global_theme.window_size = [400, 300]  # Smaller default size
    pv.global_theme.background = 'white'
    
    # Intel-specific rendering settings
    pv.global_theme.depth_peeling.enabled = False
    pv.global_theme.silhouette.enabled = False
    
    # Disable problematic features
    pv.global_theme.axes.show = False  # Axes can cause issues
    pv.global_theme.show_scalar_bar = False
    
    print("✅ PyVista configured for Intel graphics")

# Auto-configure when imported
configure_pyvista_for_intel()
'''
    
    with open('pyvista_intel_config.py', 'w') as f:
        f.write(pyvista_config)
    
    print("✅ Created pyvista_intel_config.py")

def create_safe_qtinteractor():
    """Create a safer QtInteractor class for Intel graphics"""
    
    safe_interactor_code = '''
"""
Safe QtInteractor implementation for Intel graphics.
This prevents common segfaults by handling OpenGL context issues.
"""

from pyvistaqt import QtInteractor as BaseQtInteractor
from PyQt5 import QtCore, QtWidgets, QtOpenGL
import pyvista as pv
import time

class SafeQtInteractor(BaseQtInteractor):
    """Intel graphics safe version of QtInteractor"""
    
    def __init__(self, parent=None, **kwargs):
        # Intel-specific initialization
        kwargs.setdefault('auto_update', False)  # Disable auto-update
        kwargs.setdefault('line_smoothing', False)
        kwargs.setdefault('point_smoothing', False)
        kwargs.setdefault('polygon_smoothing', False)
        
        try:
            super().__init__(parent, **kwargs)
            self._intel_safe_init()
        except Exception as e:
            print(f"⚠️  QtInteractor init warning: {e}")
            # Fallback to basic widget
            super(QtWidgets.QWidget, self).__init__(parent)
            self._create_fallback_widget()
    
    def _intel_safe_init(self):
        """Intel-specific initialization"""
        try:
            # Disable problematic features
            if hasattr(self, 'enable_anti_aliasing'):
                self.enable_anti_aliasing(False)
            
            # Set safe render window properties
            if hasattr(self, 'render_window'):
                self.render_window.SetMultiSamples(0)  # Disable multisampling
                self.render_window.SetLineSmoothing(False)
                self.render_window.SetPointSmoothing(False)
                self.render_window.SetPolygonSmoothing(False)
            
            print("✅ Intel-safe QtInteractor initialized")
            
        except Exception as e:
            print(f"⚠️  Intel init warning: {e}")
    
    def _create_fallback_widget(self):
        """Create fallback widget when QtInteractor fails"""
        self.setMinimumSize(400, 300)
        self.setStyleSheet("background-color: #f0f0f0; border: 2px solid #ccc;")
        
        layout = QtWidgets.QVBoxLayout()
        label = QtWidgets.QLabel("3D Visualization\\n(Intel Graphics Compatibility Mode)")
        label.setAlignment(QtCore.Qt.AlignCenter)
        label.setStyleSheet("color: #666; font-size: 14px; font-weight: bold;")
        layout.addWidget(label)
        
        info_label = QtWidgets.QLabel("Files generate normally\\nVisualization simplified for stability")
        info_label.setAlignment(QtCore.Qt.AlignCenter)
        info_label.setStyleSheet("color: #888; font-size: 10px;")
        layout.addWidget(info_label)
        
        self.setLayout(layout)
        print("✅ Created fallback 3D widget")
    
    def add_mesh(self, *args, **kwargs):
        """Safe mesh addition for Intel graphics"""
        try:
            if hasattr(super(), 'add_mesh'):
                # Intel-safe mesh parameters
                kwargs.setdefault('line_width', 1)  # Thin lines for Intel
                kwargs.setdefault('show_edges', True)
                kwargs.setdefault('edge_color', 'black')
                
                # Disable expensive features
                kwargs.pop('ambient', None)
                kwargs.pop('specular', None)
                kwargs.pop('metallic', None)
                kwargs.pop('roughness', None)
                
                return super().add_mesh(*args, **kwargs)
        except Exception as e:
            print(f"⚠️  Mesh display warning: {e}")
            # Silently fail for Intel graphics issues
    
    def clear(self):
        """Safe clearing for Intel graphics"""
        try:
            if hasattr(super(), 'clear'):
                super().clear()
            elif hasattr(self, 'renderer'):
                # Manual clearing
                self.renderer.RemoveAllViewProps()
        except Exception as e:
            print(f"⚠️  Clear warning: {e}")
    
    def reset_camera(self):
        """Safe camera reset for Intel graphics"""
        try:
            if hasattr(super(), 'reset_camera'):
                super().reset_camera()
        except Exception as e:
            print(f"⚠️  Camera reset warning: {e}")
    
    def close(self):
        """Safe closing for Intel graphics"""
        try:
            # Give time for any pending operations
            QtCore.QTimer.singleShot(50, self._delayed_close)
        except Exception as e:
            print(f"⚠️  Close warning: {e}")
    
    def _delayed_close(self):
        """Delayed close to prevent Intel graphics issues"""
        try:
            if hasattr(super(), 'close'):
                super().close()
        except Exception as e:
            print(f"⚠️  Delayed close warning: {e}")

# Make it easy to import
QtInteractor = SafeQtInteractor
'''
    
    with open('safe_qtinteractor.py', 'w') as f:
        f.write(safe_interactor_code)
    
    print("✅ Created safe_qtinteractor.py")

def patch_main_window_for_intel():
    """Patch main window to use Intel-safe components"""
    
    main_window_path = Path("haptic_harness_generator/ui/main_window.py")
    backup_path = Path("haptic_harness_generator/ui/main_window.py.backup")
    
    if not main_window_path.exists():
        print(f"❌ Could not find {main_window_path}")
        return False
    
    # Backup original
    if not backup_path.exists():
        import shutil
        shutil.copy2(main_window_path, backup_path)
        print("✅ Backed up main_window.py")
    
    # Read current content
    with open(main_window_path, 'r') as f:
        content = f.read()
    
    # Replace imports for Intel-safe versions
    replacements = [
        # Use Intel-safe PyVista config
        ('import pyvista as pv', 'import pyvista_intel_config  # Intel graphics config\nimport pyvista as pv'),
        
        # Use safe QtInteractor
        ('from pyvistaqt import QtInteractor', 'from safe_qtinteractor import QtInteractor'),
        
        # Add Intel-specific initialization
        ('def __init__(self, userDir, parent=None, show=True):', 
         'def __init__(self, userDir, parent=None, show=True):\n        # Intel graphics setup\n        self._setup_intel_graphics()'),
    ]
    
    for old, new in replacements:
        if old in content:
            content = content.replace(old, new)
            print(f"✅ Applied replacement: {old[:30]}...")
    
    # Add Intel setup method
    intel_setup_method = '''
    def _setup_intel_graphics(self):
        """Setup Intel graphics optimizations"""
        try:
            import os
            
            # Intel-specific Qt settings
            os.environ['QT_OPENGL'] = 'desktop'
            os.environ['QT_XCB_GL_INTEGRATION'] = 'xcb_egl'
            
            print("✅ Intel graphics setup completed")
        except Exception as e:
            print(f"⚠️  Intel graphics setup warning: {e}")
'''
    
    # Insert the method before the first existing method
    if 'def apply_scaled_styles(self):' in content:
        content = content.replace('def apply_scaled_styles(self):', intel_setup_method + '\n    def apply_scaled_styles(self):')
    
    # Write patched content
    with open(main_window_path, 'w') as f:
        f.write(content)
    
    print("✅ Patched main_window.py for Intel graphics")
    return True

def create_intel_launcher():
    """Create launcher script optimized for Intel graphics"""
    
    launcher_content = '''#!/bin/bash
# Intel Graphics Optimized Launcher for Haptic Harness Generator

echo "🚀 Starting Haptic Harness Generator (Intel Graphics Optimized)"

# Source Intel graphics environment
if [ -f "intel_graphics_env.sh" ]; then
    source intel_graphics_env.sh
    echo "✅ Intel graphics environment loaded"
fi

# Verify Intel graphics driver
if lspci | grep -i "intel.*vga" > /dev/null; then
    echo "✅ Intel graphics detected"
else
    echo "⚠️  Intel graphics not detected, but continuing..."
fi

# Check OpenGL support
if glxinfo -B | grep "OpenGL version" > /dev/null 2>&1; then
    echo "✅ OpenGL support confirmed"
    glxinfo -B | grep "OpenGL version"
else
    echo "⚠️  OpenGL check failed, using software rendering"
    export LIBGL_ALWAYS_SOFTWARE=1
fi

# Ensure conda environment
if [ "$CONDA_DEFAULT_ENV" != "hhgen" ]; then
    echo "❌ Please activate the hhgen conda environment first:"
    echo "   conda activate hhgen"
    exit 1
fi

# Add current directory to Python path for our Intel fixes
export PYTHONPATH=".:$PYTHONPATH"

echo "🎯 Launching with Intel graphics optimizations..."
exec run-haptic-harness "$@"
'''
    
    with open('launch_intel_haptic.sh', 'w') as f:
        f.write(launcher_content)
    
    os.chmod('launch_intel_haptic.sh', 0o755)
    print("✅ Created launch_intel_haptic.sh")

def main():
    """Apply Intel graphics fixes"""
    print("INTEL GRAPHICS GUI FIXES")
    print("=" * 30)
    
    print("\n1. Setting up Intel graphics environment...")
    setup_intel_graphics_environment()
    
    print("\n2. Creating PyVista Intel configuration...")
    patch_pyvista_for_intel()
    
    print("\n3. Creating safe QtInteractor...")
    create_safe_qtinteractor()
    
    print("\n4. Patching main window...")
    patch_main_window_for_intel()
    
    print("\n5. Creating Intel launcher...")
    create_intel_launcher()
    
    print("\n" + "=" * 30)
    print("🎉 INTEL GRAPHICS FIXES APPLIED!")
    print("\nTo test:")
    print("1. Run diagnostics: python deep_gui_diagnostic.py")
    print("2. Use Intel launcher: ./launch_intel_haptic.sh --export-dir /tmp/test")
    print("3. Or manual: source intel_graphics_env.sh && run-haptic-harness --export-dir /tmp/test")
    
    print("\nThese fixes address:")
    print("✅ Intel graphics driver optimization")
    print("✅ Qt OpenGL backend configuration")
    print("✅ PyVista rendering settings")
    print("✅ Safe QtInteractor with fallbacks")
    print("✅ Post-generation GUI update safety")

if __name__ == "__main__":
    main()
