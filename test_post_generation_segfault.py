#!/usr/bin/env python3
"""
Test script to reproduce and verify the post-generation segfault issue.
This helps confirm the fix works correctly.
"""

import os
import sys
import tempfile
import time
from pathlib import Path

def test_generation_only():
    """Test just the generation part without GUI"""
    print("=== TESTING GENERATION ONLY (NO GUI) ===")
    
    try:
        from haptic_harness_generator.core.generator import Generator
        
        with tempfile.TemporaryDirectory() as temp_dir:
            print(f"Generating files in: {temp_dir}")
            
            generator = Generator(temp_dir)
            start_time = time.time()
            generator.regen()
            end_time = time.time()
            
            print(f"✅ Generation completed in {end_time - start_time:.2f} seconds")
            
            # Check files
            files = list(Path(temp_dir).glob("*"))
            stl_files = [f for f in files if f.suffix == '.stl']
            dxf_files = [f for f in files if f.suffix == '.dxf']
            
            print(f"✅ Generated {len(stl_files)} STL files, {len(dxf_files)} DXF files")
            
            return True
            
    except Exception as e:
        print(f"❌ Generation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_gui_initialization():
    """Test GUI initialization without generation"""
    print("\n=== TESTING GUI INITIALIZATION ===")
    
    try:
        # Set safe environment
        os.environ['QT_X11_NO_MITSHM'] = '1'
        os.environ['VTK_SILENCE_GET_VOID_POINTER_WARNINGS'] = '1'
        
        from PyQt5 import QtWidgets, QtCore
        from haptic_harness_generator.ui.main_window import MyMainWindow
        
        # Create application
        app = QtWidgets.QApplication([])
        
        with tempfile.TemporaryDirectory() as temp_dir:
            print(f"Creating GUI with temp dir: {temp_dir}")
            
            # Create main window but don't show it
            window = MyMainWindow(userDir=temp_dir, show=False)
            
            print("✅ GUI initialization successful")
            
            # Clean up
            window.close()
            app.quit()
            
            return True
            
    except Exception as e:
        print(f"❌ GUI initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_signal_handling():
    """Test the signal handling that might cause post-generation segfaults"""
    print("\n=== TESTING SIGNAL HANDLING ===")
    
    try:
        from PyQt5 import QtWidgets, QtCore
        from haptic_harness_generator.core.generator import Generator, Signals
        
        app = QtWidgets.QApplication([])
        
        # Create a test signal handler
        class TestSignalHandler(QtCore.QObject):
            def __init__(self):
                super().__init__()
                self.progress_received = False
                self.finished_received = False
            
            def on_progress(self, value):
                self.progress_received = True
                print(f"📊 Progress: {value}")
            
            def on_finished(self):
                self.finished_received = True
                print("🏁 Finished signal received")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            generator = Generator(temp_dir)
            handler = TestSignalHandler()
            
            # Connect signals
            generator.signals.progress.connect(handler.on_progress)
            generator.signals.finished.connect(handler.on_finished)
            
            print("🔗 Signals connected, testing emission...")
            
            # Test signal emission
            generator.signals.progress.emit(5)
            generator.signals.finished.emit()
            
            # Process events
            app.processEvents()
            
            if handler.progress_received and handler.finished_received:
                print("✅ Signal handling test passed")
                app.quit()
                return True
            else:
                print("❌ Signals not received properly")
                app.quit()
                return False
                
    except Exception as e:
        print(f"❌ Signal handling test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_full_generation_cycle():
    """Test the full generation cycle that causes the segfault"""
    print("\n=== TESTING FULL GENERATION CYCLE ===")
    
    try:
        from PyQt5 import QtWidgets, QtCore
        from haptic_harness_generator.core.generator import Generator, WorkerWrapper
        
        # Set safe environment
        os.environ['QT_X11_NO_MITSHM'] = '1'
        os.environ['VTK_SILENCE_GET_VOID_POINTER_WARNINGS'] = '1'
        
        app = QtWidgets.QApplication([])
        
        class TestMainWindow(QtWidgets.QMainWindow):
            def __init__(self, temp_dir):
                super().__init__()
                self.temp_dir = temp_dir
                self.generator = Generator(temp_dir)
                self.threadpool = QtCore.QThreadPool()
                
                # Connect signals with safe handling
                self.generator.signals.progress.connect(self.safe_progress_update)
                self.generator.signals.finished.connect(self.safe_task_finished)
                
                self.generation_completed = False
                
            def safe_progress_update(self, value):
                try:
                    print(f"📊 Safe progress update: {value}")
                except Exception as e:
                    print(f"⚠️  Progress update warning: {e}")
            
            def safe_task_finished(self):
                try:
                    print("🏁 Safe task finished handler")
                    self.generation_completed = True
                    
                    # Check files were created
                    files = list(Path(self.temp_dir).glob("*"))
                    print(f"✅ Files created: {len(files)}")
                    
                    # Close application after a delay
                    QtCore.QTimer.singleShot(1000, self.close_safely)
                    
                except Exception as e:
                    print(f"⚠️  Task finished warning: {e}")
                    QtCore.QTimer.singleShot(1000, self.close_safely)
            
            def close_safely(self):
                try:
                    print("🚪 Closing application safely...")
                    self.close()
                    QtWidgets.QApplication.instance().quit()
                except Exception as e:
                    print(f"⚠️  Close warning: {e}")
                    sys.exit(0)
            
            def start_generation(self):
                print("🚀 Starting generation in thread...")
                self.threadpool.start(WorkerWrapper(self.generator))
        
        with tempfile.TemporaryDirectory() as temp_dir:
            print(f"Testing full cycle with temp dir: {temp_dir}")
            
            window = TestMainWindow(temp_dir)
            window.show()
            
            # Start generation
            window.start_generation()
            
            # Run event loop with timeout
            timer = QtCore.QTimer()
            timer.timeout.connect(lambda: app.quit() if window.generation_completed else None)
            timer.start(30000)  # 30 second timeout
            
            app.exec_()
            
            if window.generation_completed:
                print("✅ Full generation cycle completed successfully")
                return True
            else:
                print("❌ Generation cycle did not complete")
                return False
                
    except Exception as e:
        print(f"❌ Full generation cycle test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests to identify the segfault cause"""
    print("POST-GENERATION SEGFAULT DIAGNOSTIC")
    print("=" * 45)
    
    tests = [
        ("Generation Only", test_generation_only),
        ("GUI Initialization", test_gui_initialization), 
        ("Signal Handling", test_signal_handling),
        ("Full Generation Cycle", test_full_generation_cycle),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n🧪 Running: {test_name}")
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ Test {test_name} crashed: {e}")
            results[test_name] = False
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 45)
    print("TEST RESULTS SUMMARY:")
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {test_name}: {status}")
    
    if all(results.values()):
        print("\n🎉 All tests passed! The fix should work.")
    else:
        failed_tests = [name for name, passed in results.items() if not passed]
        print(f"\n⚠️  Failed tests: {', '.join(failed_tests)}")
        print("The segfault likely occurs in one of the failed components.")
    
    print("\nIf segfault still occurs after generation:")
    print("1. Files are still created successfully")
    print("2. The issue is in GUI cleanup/update after generation")
    print("3. Use the safe launcher to handle this gracefully")

if __name__ == "__main__":
    main()
