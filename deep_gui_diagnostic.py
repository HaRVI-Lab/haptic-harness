#!/usr/bin/env python3
"""
Deep diagnostic for Intel graphics GUI segfault after generation.
This isolates the exact VTK/PyVista/Qt operation causing the crash.
"""

import os
import sys
import tempfile
import time
import gc
from pathlib import Path

def setup_intel_graphics_environment():
    """Setup optimal environment for Intel graphics"""
    print("=== SETTING UP INTEL GRAPHICS ENVIRONMENT ===")
    
    # Intel-specific optimizations
    intel_env = {
        # Intel graphics driver settings
        'INTEL_DEBUG': '',  # Clear any debug flags
        'MESA_LOADER_DRIVER_OVERRIDE': 'i965',  # Force Intel driver
        
        # VTK Intel optimizations
        'VTK_USE_OFFSCREEN': '0',  # We want onscreen for GUI
        'VTK_DEFAULT_RENDER_WINDOW_OFFSCREEN': '0',
        'VTK_SILENCE_GET_VOID_POINTER_WARNINGS': '1',
        
        # Qt Intel optimizations
        'QT_XCB_GL_INTEGRATION': 'xcb_egl',  # Use EGL instead of GLX
        'QT_OPENGL': 'desktop',  # Force desktop OpenGL
        'QT_X11_NO_MITSHM': '1',  # Disable shared memory
        
        # Mesa Intel optimizations
        'MESA_GL_VERSION_OVERRIDE': '4.5',  # Use higher GL version
        'MESA_GLSL_VERSION_OVERRIDE': '450',
        'INTEL_BLACKHOLE_DEFAULT': '0',  # Disable Intel blackhole
        
        # Memory management
        'MALLOC_CHECK_': '0',  # Disable malloc debugging
        'MALLOC_PERTURB_': '0',
    }
    
    for key, value in intel_env.items():
        os.environ[key] = value
        print(f"✅ Set {key}={value}")
    
    print("✅ Intel graphics environment configured")

def test_vtk_render_window_lifecycle():
    """Test VTK render window creation and destruction"""
    print("\n=== TESTING VTK RENDER WINDOW LIFECYCLE ===")
    
    try:
        import vtk
        
        # Test basic render window
        print("Creating VTK render window...")
        render_window = vtk.vtkRenderWindow()
        render_window.SetSize(400, 300)
        render_window.SetWindowName("Test Window")
        
        renderer = vtk.vtkRenderer()
        render_window.AddRenderer(renderer)
        
        # Test with a simple object
        sphere_source = vtk.vtkSphereSource()
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(sphere_source.GetOutputPort())
        
        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        renderer.AddActor(actor)
        
        print("✅ VTK objects created successfully")
        
        # Test render
        print("Testing render...")
        render_window.Render()
        print("✅ VTK render successful")
        
        # Test cleanup - this is where segfaults often occur
        print("Testing cleanup...")
        renderer.RemoveActor(actor)
        render_window.RemoveRenderer(renderer)
        
        # Force cleanup
        del actor
        del mapper
        del sphere_source
        del renderer
        del render_window
        
        # Force garbage collection
        gc.collect()
        
        print("✅ VTK cleanup successful")
        return True
        
    except Exception as e:
        print(f"❌ VTK render window test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_pyvista_plotter_lifecycle():
    """Test PyVista plotter creation and destruction"""
    print("\n=== TESTING PYVISTA PLOTTER LIFECYCLE ===")
    
    try:
        import pyvista as pv
        
        # Configure PyVista for Intel graphics
        pv.set_plot_theme('document')
        pv.global_theme.background = 'white'
        pv.global_theme.window_size = [400, 300]
        pv.global_theme.anti_aliasing = False  # Disable anti-aliasing for Intel
        pv.global_theme.line_smoothing = False
        pv.global_theme.point_smoothing = False
        pv.global_theme.polygon_smoothing = False
        
        print("Creating PyVista plotter...")
        plotter = pv.Plotter(off_screen=False, window_size=[400, 300])
        
        # Add a simple mesh
        sphere = pv.Sphere()
        print("Adding mesh to plotter...")
        plotter.add_mesh(sphere, color='red', show_edges=True)
        
        print("✅ PyVista plotter created and mesh added")
        
        # Test show/close cycle - this often causes segfaults
        print("Testing show/close cycle...")
        plotter.show(auto_close=False, interactive=False)
        
        print("Closing plotter...")
        plotter.close()
        
        # Force cleanup
        del plotter
        del sphere
        gc.collect()
        
        print("✅ PyVista plotter lifecycle successful")
        return True
        
    except Exception as e:
        print(f"❌ PyVista plotter test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_pyvistaqt_interactor_lifecycle():
    """Test PyVistaQt interactor creation and destruction"""
    print("\n=== TESTING PYVISTAQT INTERACTOR LIFECYCLE ===")
    
    try:
        from PyQt5 import QtWidgets, QtCore
        import pyvista as pv
        from pyvistaqt import QtInteractor
        
        # Configure PyVista
        pv.set_plot_theme('document')
        pv.global_theme.anti_aliasing = False
        
        print("Creating Qt application...")
        app = QtWidgets.QApplication([])
        
        print("Creating QtInteractor...")
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout()
        
        # This is the critical part - QtInteractor creation
        interactor = QtInteractor(widget)
        layout.addWidget(interactor.interactor)
        widget.setLayout(layout)
        
        print("✅ QtInteractor created successfully")
        
        # Add mesh
        sphere = pv.Sphere()
        print("Adding mesh to QtInteractor...")
        interactor.add_mesh(sphere, color='blue', show_edges=True)
        
        print("✅ Mesh added to QtInteractor")
        
        # Show widget briefly
        widget.show()
        app.processEvents()
        time.sleep(0.5)  # Brief display
        
        print("Testing QtInteractor cleanup...")
        
        # Clear the interactor
        interactor.clear()
        
        # Close widget
        widget.close()
        
        # Cleanup
        del interactor
        del widget
        del sphere
        
        app.quit()
        del app
        
        gc.collect()
        
        print("✅ QtInteractor lifecycle successful")
        return True
        
    except Exception as e:
        print(f"❌ QtInteractor test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_mesh_update_cycle():
    """Test the specific mesh update cycle that happens after generation"""
    print("\n=== TESTING MESH UPDATE CYCLE ===")
    
    try:
        from PyQt5 import QtWidgets, QtCore
        import pyvista as pv
        from pyvistaqt import QtInteractor
        from haptic_harness_generator.core.generator import Generator
        
        # Configure for Intel graphics
        pv.set_plot_theme('document')
        pv.global_theme.anti_aliasing = False
        pv.global_theme.line_smoothing = False
        
        app = QtWidgets.QApplication([])
        
        with tempfile.TemporaryDirectory() as temp_dir:
            print(f"Creating generator with temp dir: {temp_dir}")
            generator = Generator(temp_dir)
            
            # Generate meshes
            print("Generating meshes...")
            generator.regen()
            
            print("✅ Meshes generated successfully")
            
            # Create interactor
            widget = QtWidgets.QWidget()
            layout = QtWidgets.QVBoxLayout()
            interactor = QtInteractor(widget)
            layout.addWidget(interactor.interactor)
            widget.setLayout(layout)
            
            print("Testing initial mesh display...")
            interactor.add_mesh(generator.tyvek_tile, color='green', show_edges=True)
            
            widget.show()
            app.processEvents()
            
            print("✅ Initial mesh display successful")
            
            # This is the critical part - updating meshes after generation
            print("Testing mesh update (this often causes segfaults)...")
            
            # Clear existing mesh
            interactor.clear()
            
            # Add updated mesh - this simulates post-generation update
            interactor.add_mesh(generator.foam, color='red', show_edges=True)
            
            app.processEvents()
            
            print("✅ Mesh update successful")
            
            # Test camera reset
            print("Testing camera reset...")
            interactor.reset_camera()
            app.processEvents()
            
            print("✅ Camera reset successful")
            
            # Cleanup
            widget.close()
            app.quit()
            
            print("✅ Mesh update cycle completed successfully")
            return True
            
    except Exception as e:
        print(f"❌ Mesh update cycle failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_multiple_interactors():
    """Test multiple QtInteractors like in the real application"""
    print("\n=== TESTING MULTIPLE QTINTERACTORS ===")
    
    try:
        from PyQt5 import QtWidgets, QtCore
        import pyvista as pv
        from pyvistaqt import QtInteractor
        from haptic_harness_generator.core.generator import Generator
        
        pv.set_plot_theme('document')
        pv.global_theme.anti_aliasing = False
        
        app = QtWidgets.QApplication([])
        
        with tempfile.TemporaryDirectory() as temp_dir:
            generator = Generator(temp_dir)
            generator.regen()
            
            print("Creating multiple QtInteractors...")
            
            main_widget = QtWidgets.QWidget()
            main_layout = QtWidgets.QHBoxLayout()
            
            interactors = []
            meshes = [
                generator.tyvek_tile,
                generator.foam,
                generator.magnet_ring,
            ]
            
            # Create 3 interactors like in the real app
            for i, mesh in enumerate(meshes):
                print(f"Creating interactor {i+1}...")
                
                interactor = QtInteractor(main_widget)
                interactor.add_mesh(mesh, color=['red', 'green', 'blue'][i], show_edges=True)
                
                interactors.append(interactor)
                main_layout.addWidget(interactor.interactor)
                
                print(f"✅ Interactor {i+1} created successfully")
            
            main_widget.setLayout(main_layout)
            main_widget.show()
            
            app.processEvents()
            time.sleep(1)  # Let it render
            
            print("Testing simultaneous updates...")
            
            # Update all interactors simultaneously - this often causes issues
            for i, interactor in enumerate(interactors):
                interactor.clear()
                interactor.add_mesh(meshes[i], color='yellow', show_edges=True)
            
            app.processEvents()
            
            print("✅ Simultaneous updates successful")
            
            # Cleanup
            main_widget.close()
            app.quit()
            
            print("✅ Multiple interactors test successful")
            return True
            
    except Exception as e:
        print(f"❌ Multiple interactors test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run deep diagnostic for Intel graphics GUI issues"""
    print("DEEP GUI DIAGNOSTIC FOR INTEL GRAPHICS")
    print("=" * 50)
    
    # Setup Intel-optimized environment
    setup_intel_graphics_environment()
    
    tests = [
        ("VTK Render Window Lifecycle", test_vtk_render_window_lifecycle),
        ("PyVista Plotter Lifecycle", test_pyvista_plotter_lifecycle),
        ("PyVistaQt Interactor Lifecycle", test_pyvistaqt_interactor_lifecycle),
        ("Mesh Update Cycle", test_mesh_update_cycle),
        ("Multiple Interactors", test_multiple_interactors),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n🧪 Running: {test_name}")
        try:
            results[test_name] = test_func()
            if results[test_name]:
                print(f"✅ {test_name} PASSED")
            else:
                print(f"❌ {test_name} FAILED")
                break  # Stop at first failure to isolate the issue
        except Exception as e:
            print(f"💥 {test_name} CRASHED: {e}")
            results[test_name] = False
            break
    
    print("\n" + "=" * 50)
    print("DIAGNOSTIC RESULTS:")
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {test_name}: {status}")
    
    # Identify the exact failure point
    failed_tests = [name for name, passed in results.items() if not passed]
    
    if not failed_tests:
        print("\n🎉 All tests passed! The issue may be in the specific interaction pattern.")
        print("Try running the actual application - it should work now.")
    else:
        first_failure = failed_tests[0]
        print(f"\n🎯 SEGFAULT OCCURS IN: {first_failure}")
        print("This is the exact component causing the crash.")
        
        # Provide specific fixes based on failure point
        if "VTK Render Window" in first_failure:
            print("\n🔧 SOLUTION: VTK render window issue")
            print("- Try: export VTK_USE_OFFSCREEN=1")
            print("- Or: Use software rendering")
            
        elif "PyVista Plotter" in first_failure:
            print("\n🔧 SOLUTION: PyVista plotter issue")
            print("- Disable anti-aliasing and smoothing")
            print("- Use smaller window sizes")
            
        elif "QtInteractor" in first_failure:
            print("\n🔧 SOLUTION: PyVistaQt interactor issue")
            print("- This is the most common Intel graphics issue")
            print("- Try different Qt OpenGL backend")
            
        elif "Mesh Update" in first_failure:
            print("\n🔧 SOLUTION: Post-generation mesh update issue")
            print("- The segfault happens during GUI refresh after generation")
            print("- Need safer mesh clearing/updating")
            
        elif "Multiple Interactors" in first_failure:
            print("\n🔧 SOLUTION: Multiple interactor conflict")
            print("- Intel graphics may not handle multiple OpenGL contexts well")
            print("- Need to serialize interactor operations")

if __name__ == "__main__":
    main()
