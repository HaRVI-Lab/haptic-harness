#!/usr/bin/env python3
"""
Headless version of the haptic harness generator for systems without proper graphics support.
This version generates files without the GUI interface.
"""

import os
import sys
import argparse
import tempfile
from pathlib import Path

def setup_headless_environment():
    """Configure environment for headless operation"""
    # Set Qt to use offscreen platform
    os.environ['QT_QPA_PLATFORM'] = 'offscreen'
    
    # Set dummy display if not set
    if 'DISPLAY' not in os.environ:
        os.environ['DISPLAY'] = ':99'
    
    # Disable VTK warnings
    os.environ['VTK_SILENCE_GET_VOID_POINTER_WARNINGS'] = '1'
    
    # Set PyVista to use offscreen rendering
    try:
        import pyvista as pv
        pv.set_plot_theme('document')
        pv.OFF_SCREEN = True
    except ImportError:
        pass

def check_environment():
    """Check that the environment is correctly set up for headless operation"""
    errors = []
    
    # Check VTK version
    try:
        import vtk
        vtk_version = vtk.vtkVersion.GetVTKVersion()
        if vtk_version != "9.3.0":
            errors.append(f"Wrong VTK version: expected 9.3.0, got {vtk_version}")
    except ImportError:
        errors.append("VTK not installed")
    
    # Check vtkbool import
    try:
        from vtkbool.vtkBool import vtkPolyDataBooleanFilter
    except ImportError:
        errors.append("vtkbool import failed - check that vtkbool is installed correctly")
    
    # Check conda environment
    conda_env = os.environ.get('CONDA_DEFAULT_ENV', 'NOT_IN_CONDA')
    if conda_env != 'hhgen':
        errors.append(f"Not in expected conda environment 'hhgen', currently in: {conda_env}")
    
    if errors:
        print("❌ ENVIRONMENT CHECK FAILED")
        print("The following issues were detected:")
        for error in errors:
            print(f"  - {error}")
        return False
    
    print("✅ Environment check passed")
    return True

def generate_preset(preset_name, output_dir, run_number=1):
    """Generate files for a specific preset"""
    print(f"Generating {preset_name} (run {run_number})...")
    
    try:
        from haptic_harness_generator.core.generator import Generator
        from haptic_harness_generator.core.config_manager import ConfigurationManager
        
        # Create generator
        generator = Generator(output_dir)
        
        # Load preset configuration
        if preset_name not in ConfigurationManager.PRESETS:
            raise ValueError(f"Unknown preset: {preset_name}")
        
        config = ConfigurationManager.PRESETS[preset_name]
        
        # Apply configuration to generator
        for param_name, value in config.items():
            if hasattr(generator, param_name):
                # Handle angle conversions
                if param_name in ["mountBottomAngleOpening", "mountTopAngleOpening"]:
                    value = value * 3.14159 / 180  # Convert to radians
                setattr(generator, param_name, value)
        
        # Generate files
        generator.regen()
        
        # List generated files
        generated_files = []
        for file_path in Path(output_dir).glob("*"):
            if file_path.is_file():
                generated_files.append(file_path.name)
        
        print(f"✅ Generated {len(generated_files)} files for {preset_name}")
        return generated_files
        
    except Exception as e:
        print(f"❌ Failed to generate {preset_name}: {e}")
        import traceback
        traceback.print_exc()
        return []

def run_baseline_generation():
    """Run baseline generation for all presets"""
    print("HAPTIC HARNESS GENERATOR - HEADLESS BASELINE GENERATION")
    print("=" * 60)
    
    # Setup headless environment
    setup_headless_environment()
    
    # Check environment
    if not check_environment():
        sys.exit(1)
    
    # Create baseline directory structure
    baseline_dir = Path("baseline")
    baseline_dir.mkdir(exist_ok=True)
    
    presets = ["Standard 4-sided", "Compact 4-sided", "Standard 6-sided"]
    
    for preset in presets:
        print(f"\n=== PROCESSING {preset.upper()} ===")
        
        # Create preset directory
        preset_dir = baseline_dir / preset.replace(" ", "_")
        preset_dir.mkdir(exist_ok=True)
        
        # Generate multiple runs
        for run in range(1, 11):  # 10 runs as specified in guide
            run_dir = preset_dir / f"run_{run:02d}"
            run_dir.mkdir(exist_ok=True)
            
            generated_files = generate_preset(preset, str(run_dir), run)
            
            if not generated_files:
                print(f"❌ Failed to generate files for {preset} run {run}")
                break
        else:
            print(f"✅ Completed all 10 runs for {preset}")
    
    print("\n" + "=" * 60)
    print("BASELINE GENERATION COMPLETE")
    
    # Summary
    total_files = 0
    for preset_dir in baseline_dir.iterdir():
        if preset_dir.is_dir():
            preset_files = sum(1 for run_dir in preset_dir.iterdir() 
                             if run_dir.is_dir() 
                             for file in run_dir.iterdir() 
                             if file.is_file())
            total_files += preset_files
            print(f"{preset_dir.name}: {preset_files} files")
    
    print(f"Total files generated: {total_files}")

def run_single_generation():
    """Run single generation for testing"""
    parser = argparse.ArgumentParser(description="Haptic Harness Generator - Headless Mode")
    parser.add_argument(
        "--export-dir",
        help="Absolute path to export files to",
        default=None,
        required=True,
    )
    parser.add_argument(
        "--preset",
        help="Preset to use",
        choices=["Standard 4-sided", "Compact 4-sided", "Standard 6-sided"],
        default="Standard 4-sided"
    )
    
    args = parser.parse_args()
    export_dir = os.path.abspath(args.export_dir)
    
    if not os.path.isabs(export_dir):
        print(f"Error: Please provide an absolute path. Converted path: {export_dir}")
        sys.exit(1)
    
    try:
        os.makedirs(export_dir, exist_ok=True)
        print(f"Files will be exported to: {export_dir}")
    except OSError as e:
        print(f"Error creating directory {export_dir}: {e}")
        sys.exit(1)
    
    # Setup headless environment
    setup_headless_environment()
    
    # Check environment
    if not check_environment():
        sys.exit(1)
    
    # Generate files
    generated_files = generate_preset(args.preset, export_dir)
    
    if generated_files:
        print(f"\n✅ SUCCESS: Generated {len(generated_files)} files")
        for file in sorted(generated_files):
            print(f"  - {file}")
    else:
        print("\n❌ FAILED: No files generated")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) == 1 or (len(sys.argv) == 2 and sys.argv[1] == "--baseline"):
        # Run baseline generation
        run_baseline_generation()
    else:
        # Run single generation
        run_single_generation()
