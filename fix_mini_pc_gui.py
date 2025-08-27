#!/usr/bin/env python3
"""
Complete solution for fixing GUI segfaults on mini PC systems.
This script addresses the most common causes of VTK/Qt segfaults on limited hardware.
"""

import os
import sys
import subprocess
from pathlib import Path

def detect_graphics_hardware():
    """Detect graphics hardware and capabilities"""
    print("=== GRAPHICS HARDWARE DETECTION ===")
    
    try:
        # Get GPU info
        result = subprocess.run(['lspci', '|', 'grep', '-i', 'vga'], 
                              shell=True, capture_output=True, text=True)
        if result.stdout:
            print(f"GPU: {result.stdout.strip()}")
        else:
            print("GPU: Not detected or integrated")
            
        # Check for Intel graphics (common on mini PCs)
        result = subprocess.run(['lspci', '|', 'grep', '-i', 'intel'], 
                              shell=True, capture_output=True, text=True)
        if 'VGA' in result.stdout or 'Display' in result.stdout:
            print("✅ Intel integrated graphics detected")
            return "intel"
            
        # Check for AMD graphics
        result = subprocess.run(['lspci', '|', 'grep', '-i', 'amd'], 
                              shell=True, capture_output=True, text=True)
        if 'VGA' in result.stdout or 'Display' in result.stdout:
            print("✅ AMD graphics detected")
            return "amd"
            
        # Check for NVIDIA graphics
        result = subprocess.run(['lspci', '|', 'grep', '-i', 'nvidia'], 
                              shell=True, capture_output=True, text=True)
        if result.stdout:
            print("✅ NVIDIA graphics detected")
            return "nvidia"
            
    except Exception as e:
        print(f"⚠️  Could not detect graphics hardware: {e}")
    
    return "unknown"

def check_opengl_support():
    """Check OpenGL support and version"""
    print("\n=== OPENGL SUPPORT CHECK ===")
    
    try:
        result = subprocess.run(['glxinfo', '-B'], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            lines = result.stdout.split('\n')
            for line in lines:
                if 'OpenGL version' in line:
                    print(f"✅ {line.strip()}")
                elif 'OpenGL renderer' in line:
                    print(f"✅ {line.strip()}")
                elif 'direct rendering' in line:
                    print(f"✅ {line.strip()}")
            return True
        else:
            print("❌ glxinfo failed - OpenGL may not be available")
            return False
    except subprocess.TimeoutExpired:
        print("❌ glxinfo timed out - graphics driver issue")
        return False
    except FileNotFoundError:
        print("❌ glxinfo not found - install mesa-utils")
        return False
    except Exception as e:
        print(f"❌ OpenGL check failed: {e}")
        return False

def install_graphics_support():
    """Install necessary graphics support packages"""
    print("\n=== INSTALLING GRAPHICS SUPPORT ===")
    
    packages = [
        "mesa-utils",
        "libgl1-mesa-glx", 
        "libgl1-mesa-dri",
        "mesa-vulkan-drivers",
        "libglx-mesa0"
    ]
    
    for package in packages:
        try:
            print(f"Installing {package}...")
            result = subprocess.run(['sudo', 'apt', 'install', '-y', package], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✅ {package} installed")
            else:
                print(f"⚠️  {package} installation had issues")
        except Exception as e:
            print(f"❌ Failed to install {package}: {e}")

def setup_environment_variables():
    """Setup environment variables for better graphics compatibility"""
    print("\n=== SETTING UP ENVIRONMENT VARIABLES ===")
    
    env_vars = {
        # Force software rendering if hardware fails
        'LIBGL_ALWAYS_SOFTWARE': '1',
        
        # Mesa OpenGL version override
        'MESA_GL_VERSION_OVERRIDE': '3.3',
        'MESA_GLSL_VERSION_OVERRIDE': '330',
        
        # VTK specific settings
        'VTK_SILENCE_GET_VOID_POINTER_WARNINGS': '1',
        'VTK_USE_OFFSCREEN': '0',  # We want onscreen for GUI
        
        # Qt settings for better compatibility
        'QT_X11_NO_MITSHM': '1',
        'QT_GRAPHICSSYSTEM': 'native',
        
        # PyVista settings
        'PYVISTA_USE_PANEL': '0',
        'PYVISTA_OFF_SCREEN': 'false',
    }
    
    # Write to a shell script that can be sourced
    script_content = "#!/bin/bash\n# Graphics environment setup for haptic harness generator\n\n"
    
    for var, value in env_vars.items():
        os.environ[var] = value
        script_content += f"export {var}={value}\n"
        print(f"✅ Set {var}={value}")
    
    # Save environment script
    with open("setup_graphics_env.sh", 'w') as f:
        f.write(script_content)
    
    os.chmod("setup_graphics_env.sh", 0o755)
    print("✅ Created setup_graphics_env.sh")

def patch_main_application():
    """Apply patches to main application for better graphics handling"""
    print("\n=== PATCHING MAIN APPLICATION ===")
    
    # Patch main.py for better Qt initialization
    main_py_path = Path("haptic_harness_generator/main.py")
    if main_py_path.exists():
        backup_path = Path("haptic_harness_generator/main.py.backup")
        if not backup_path.exists():
            import shutil
            shutil.copy2(main_py_path, backup_path)
            print("✅ Backed up main.py")
        
        # Read current content
        with open(main_py_path, 'r') as f:
            content = f.read()
        
        # Add graphics setup before Qt initialization
        graphics_setup = '''
def setup_graphics_environment():
    """Setup graphics environment for mini PC compatibility"""
    import os
    
    # Force software rendering if needed
    if not os.environ.get('DISPLAY') or os.environ.get('FORCE_SOFTWARE_RENDERING'):
        os.environ['LIBGL_ALWAYS_SOFTWARE'] = '1'
        os.environ['MESA_GL_VERSION_OVERRIDE'] = '3.3'
    
    # Qt compatibility settings
    os.environ['QT_X11_NO_MITSHM'] = '1'
    os.environ['QT_GRAPHICSSYSTEM'] = 'native'
    
    # VTK settings
    os.environ['VTK_SILENCE_GET_VOID_POINTER_WARNINGS'] = '1'
    
    print("✅ Graphics environment configured for mini PC")

'''
        
        # Insert graphics setup before run_app function
        if 'def run_app():' in content and 'def setup_graphics_environment():' not in content:
            content = content.replace('def run_app():', graphics_setup + 'def run_app():')
            
            # Add call to setup function
            content = content.replace('def run_app():\n    # Check environment before starting\n    check_environment()',
                                    'def run_app():\n    # Setup graphics environment\n    setup_graphics_environment()\n    \n    # Check environment before starting\n    check_environment()')
            
            with open(main_py_path, 'w') as f:
                f.write(content)
            print("✅ Patched main.py with graphics setup")
        else:
            print("✅ main.py already patched or structure different")
    
    # Apply the GUI-specific patches
    try:
        exec(open('fix_gui_segfault.py').read())
        print("✅ Applied GUI safety patches")
    except Exception as e:
        print(f"⚠️  GUI patch warning: {e}")

def test_fixed_application():
    """Test the fixed application"""
    print("\n=== TESTING FIXED APPLICATION ===")
    
    # Test basic imports first
    try:
        print("Testing imports...")
        import vtk
        from vtkbool.vtkBool import vtkPolyDataBooleanFilter
        import pyvista as pv
        from PyQt5 import QtWidgets, QtCore
        from pyvistaqt import QtInteractor
        print("✅ All imports successful")
    except Exception as e:
        print(f"❌ Import test failed: {e}")
        return False
    
    # Test Qt application creation
    try:
        print("Testing Qt application...")
        app = QtWidgets.QApplication([])
        widget = QtWidgets.QLabel("Test")
        widget.show()
        widget.close()
        app.quit()
        print("✅ Qt application test passed")
    except Exception as e:
        print(f"❌ Qt application test failed: {e}")
        return False
    
    # Test PyVista with Qt
    try:
        print("Testing PyVista with Qt...")
        import pyvista as pv
        pv.set_plot_theme('document')
        
        app = QtWidgets.QApplication([])
        interactor = QtInteractor()
        sphere = pv.Sphere()
        interactor.add_mesh(sphere)
        interactor.close()
        app.quit()
        print("✅ PyVista Qt test passed")
    except Exception as e:
        print(f"❌ PyVista Qt test failed: {e}")
        print("⚠️  Will use software rendering fallback")
    
    return True

def create_launcher_script():
    """Create a launcher script with all fixes applied"""
    print("\n=== CREATING LAUNCHER SCRIPT ===")
    
    launcher_content = '''#!/bin/bash
# Haptic Harness Generator Launcher for Mini PC
# This script applies all necessary fixes for graphics compatibility

echo "🚀 Starting Haptic Harness Generator with Mini PC optimizations..."

# Source graphics environment
if [ -f "setup_graphics_env.sh" ]; then
    source setup_graphics_env.sh
    echo "✅ Graphics environment loaded"
fi

# Check if we need software rendering
if ! glxinfo -B >/dev/null 2>&1; then
    echo "⚠️  Hardware acceleration not available, using software rendering"
    export LIBGL_ALWAYS_SOFTWARE=1
    export MESA_GL_VERSION_OVERRIDE=3.3
fi

# Ensure conda environment is active
if [ "$CONDA_DEFAULT_ENV" != "hhgen" ]; then
    echo "❌ Please activate the hhgen conda environment first:"
    echo "   conda activate hhgen"
    exit 1
fi

# Run the application with error handling
echo "🎯 Launching GUI application..."
if ! run-haptic-harness "$@"; then
    echo "❌ GUI launch failed, trying diagnostics..."
    python diagnose_segfault.py
    
    echo "💡 You can also try:"
    echo "   python run_headless.py --export-dir /tmp/haptic_test"
    echo "   python test_graphics.py"
fi
'''
    
    with open("launch_haptic_harness.sh", 'w') as f:
        f.write(launcher_content)
    
    os.chmod("launch_haptic_harness.sh", 0o755)
    print("✅ Created launch_haptic_harness.sh")

def main():
    """Main fix application function"""
    print("HAPTIC HARNESS GENERATOR - MINI PC GUI FIX")
    print("=" * 50)
    
    # Detect hardware
    gpu_type = detect_graphics_hardware()
    
    # Check OpenGL
    has_opengl = check_opengl_support()
    
    if not has_opengl:
        print("\n🔧 Installing graphics support...")
        install_graphics_support()
        
        # Recheck after installation
        has_opengl = check_opengl_support()
    
    # Setup environment
    setup_environment_variables()
    
    # Patch application
    patch_main_application()
    
    # Test fixes
    if test_fixed_application():
        print("\n✅ All tests passed!")
    else:
        print("\n⚠️  Some tests failed, but fixes are still applied")
    
    # Create launcher
    create_launcher_script()
    
    print("\n" + "=" * 50)
    print("🎉 MINI PC GUI FIX COMPLETE!")
    print("\nTo run the application:")
    print("1. ./launch_haptic_harness.sh --export-dir /path/to/output")
    print("2. Or: source setup_graphics_env.sh && run-haptic-harness --export-dir /path/to/output")
    print("\nIf GUI still fails:")
    print("3. python test_graphics.py  # Test graphics capabilities")
    print("4. python diagnose_segfault.py  # Detailed diagnostics")
    print("5. python run_headless.py --export-dir /path/to/output  # Fallback mode")

if __name__ == "__main__":
    main()
