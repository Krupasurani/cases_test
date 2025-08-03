# # main.py
# """
# ITASSIST - Intelligent Test Case Generator
# Main application entry point

# Run with: streamlit run main.py
# """

# import os
# import sys
# import logging
# from pathlib import Path

# # Add src directory to Python path
# src_path = Path(__file__).parent / "src"
# sys.path.insert(0, str(src_path))

# # Configure logging (fix Unicode issue on Windows)
# logging.basicConfig(
#     level=logging.INFO,
#     format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
#     handlers=[
#         logging.FileHandler('itassist.log', encoding='utf-8'),
#         logging.StreamHandler()
#     ]
# )

# logger = logging.getLogger(__name__)

# def check_dependencies():
#     """Check if all required dependencies are installed"""
#     required_packages = [
#         ('streamlit', 'streamlit'),
#         ('openai', 'openai'), 
#         ('docx', 'python-docx'),
#         ('PyPDF2', 'PyPDF2'),
#         ('openpyxl', 'openpyxl'), 
#         ('pandas', 'pandas'),
#         ('pytesseract', 'pytesseract'),
#         ('cv2', 'opencv-python'),
#         ('PIL', 'Pillow')
#     ]
    
#     missing_packages = []
    
#     for import_name, package_name in required_packages:
#         try:
#             __import__(import_name)
#             logger.info(f"OK {package_name} loaded successfully")
#         except ImportError:
#             missing_packages.append(package_name)
#             logger.error(f"X {package_name} not found")
    
#     if missing_packages:
#         logger.error(f"Missing required packages: {', '.join(missing_packages)}")
#         logger.error("Please install missing packages using: pip install -r requirements.txt")
#         return False
    
#     logger.info("OK All dependencies checked and loaded successfully")
#     return True

# def setup_directories():
#     """Create necessary directories"""
#     directories = ['temp', 'outputs', 'logs']
    
#     for directory in directories:
#         dir_path = Path(directory)
#         dir_path.mkdir(exist_ok=True)
#         logger.info(f"Directory created/verified: {dir_path}")

# def check_environment():
#     """Check environment setup"""
#     logger.info("Checking environment setup...")
    
#     # Check Python version
#     python_version = sys.version_info
#     if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 8):
#         logger.error("Python 3.8+ is required")
#         return False
    
#     logger.info(f"Python version: {python_version.major}.{python_version.minor}.{python_version.micro}")
    
#     # Check OCR dependencies
#     try:
#         import pytesseract
#         import cv2
#         logger.info("OCR dependencies loaded successfully")
#     except ImportError as e:
#         logger.warning(f"OCR dependencies not fully available: {e}")
#         logger.warning("Some image processing features may not work")
    
#     return True

# def main():
#     """Main application entry point"""
    
#     print("🤖 ITASSIST - Intelligent Test Case Generator")
#     print("=" * 50)
    
#     # Check environment
#     if not check_environment():
#         sys.exit(1)
    
#     # Check dependencies (skip on error for now)
#     try:
#         check_dependencies()
#     except Exception as e:
#         logger.warning(f"Dependency check failed: {e}")
#         logger.warning("Continuing anyway...")
    
#     # Setup directories
#     setup_directories()
    
#     logger.info("Starting ITASSIST application...")
    
#     try:
#         # Import and run the Streamlit app
#         from ui.streamlit_app import main as streamlit_main
#         streamlit_main()
        
#     except ImportError as e:
#         logger.error(f"Failed to import Streamlit app: {e}")
#         logger.error("Make sure all dependencies are installed")
#         sys.exit(1)
    
#     except Exception as e:
#         logger.error(f"Application error: {e}")
#         sys.exit(1)

# if __name__ == "__main__":
#     main()


# main.py
"""
ITASSIST - Intelligent Test Case Generator (Enhanced)
Main application entry point with PACS.008 and Maker-Checker support

Features:
- Multi-format document processing
- PACS.008 smart detection and field extraction
- Maker-Checker workflow simulation
- Enhanced test case generation with banking domain intelligence
- Backward compatibility with existing functionality

Run with: streamlit run main.py
"""

import os
import sys
import logging
from pathlib import Path
import traceback

# Add src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

# Configure logging with enhanced format
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('itassist.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def check_dependencies():
    """Check if all required dependencies are installed"""
    logger.info("Checking dependencies...")
    
    required_packages = [
        ('streamlit', 'streamlit'),
        ('openai', 'openai'), 
        ('docx', 'python-docx'),
        ('PyPDF2', 'PyPDF2'),
        ('openpyxl', 'openpyxl'), 
        ('pandas', 'pandas'),
        ('pytesseract', 'pytesseract'),
        ('cv2', 'opencv-python'),
        ('PIL', 'Pillow'),
        ('dotenv', 'python-dotenv')
    ]
    
    missing_packages = []
    loaded_packages = []
    
    for import_name, package_name in required_packages:
        try:
            __import__(import_name)
            logger.info(f"✓ {package_name} loaded successfully")
            loaded_packages.append(package_name)
        except ImportError:
            missing_packages.append(package_name)
            logger.error(f"✗ {package_name} not found")
    
    if missing_packages:
        logger.error(f"Missing required packages: {', '.join(missing_packages)}")
        logger.error("Please install missing packages using: pip install -r requirements.txt")
        return False
    
    logger.info(f"✓ All {len(loaded_packages)} dependencies loaded successfully")
    return True

def check_enhanced_dependencies():
    """Check if enhanced features dependencies are available"""
    logger.info("Checking enhanced features dependencies...")
    
    enhanced_features = {
        'pacs008_config': False,
        'enhanced_test_generator': False
    }
    
    try:
        from config.pacs008_config import PACS008_FIELD_DEFINITIONS
        enhanced_features['pacs008_config'] = True
        logger.info("✓ PACS.008 configuration loaded")
    except ImportError as e:
        logger.warning(f"PACS.008 config not available: {e}")
    
    try:
        from ai_engine.enhanced_test_generator import EnhancedTestCaseGenerator
        enhanced_features['enhanced_test_generator'] = True
        logger.info("✓ Enhanced test generator loaded")
    except ImportError as e:
        logger.warning(f"Enhanced test generator not available: {e}")
    
    return enhanced_features

def setup_directories():
    """Create necessary directories"""
    directories = ['temp', 'outputs', 'logs', 'input']
    
    for directory in directories:
        dir_path = Path(directory)
        dir_path.mkdir(exist_ok=True)
        logger.info(f"✓ Directory verified: {dir_path}")

def check_environment():
    """Check environment setup and configuration"""
    logger.info("Checking environment setup...")
    
    # Check Python version
    python_version = sys.version_info
    if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 8):
        logger.error("Python 3.8+ is required")
        return False
    
    logger.info(f"✓ Python version: {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    # Check OCR dependencies
    try:
        import pytesseract
        import cv2
        logger.info("✓ OCR dependencies loaded successfully")
    except ImportError as e:
        logger.warning(f"OCR dependencies not fully available: {e}")
        logger.warning("Some image processing features may not work")
    
    # Check OpenAI API key
    openai_key = os.getenv("OPENAI_API_KEY", "")
    if openai_key:
        # Mask the key for logging
        masked_key = openai_key[:8] + "..." + openai_key[-4:] if len(openai_key) > 12 else "****"
        logger.info(f"✓ OpenAI API key detected: {masked_key}")
    else:
        logger.warning("OpenAI API key not found in environment - will need to be provided in UI")
    
    return True

def load_configuration():
    """Load application configuration"""
    logger.info("Loading application configuration...")
    
    try:
        # Load environment variables
        from dotenv import load_dotenv
        load_dotenv()
        logger.info("✓ Environment variables loaded")
    except Exception as e:
        logger.warning(f"Could not load .env file: {e}")
    
    try:
        # Load basic configuration
        from config.settings import Settings
        settings = Settings()
        logger.info("✓ Basic configuration loaded")
        return settings
    except Exception as e:
        logger.warning(f"Could not load settings: {e}")
        return None

def check_file_permissions():
    """Check file system permissions"""
    logger.info("Checking file system permissions...")
    
    test_dirs = ['temp', 'outputs', 'logs']
    
    for test_dir in test_dirs:
        try:
            test_file = Path(test_dir) / "test_write.tmp"
            test_file.write_text("test")
            test_file.unlink()
            logger.info(f"✓ Write permissions OK for {test_dir}")
        except Exception as e:
            logger.error(f"✗ Write permission issue in {test_dir}: {e}")
            return False
    
    return True

def display_startup_banner():
    """Display application startup banner"""
    banner = """
    ╔══════════════════════════════════════════════════════════════╗
    ║                    🤖 ITASSIST ENHANCED                      ║
    ║              Intelligent Test Case Generator                 ║
    ║                                                              ║
    ║  ✨ Features:                                                ║
    ║    📄 Multi-format document processing                      ║
    ║    🏦 PACS.008 smart detection & field extraction          ║
    ║    👥 Maker-Checker workflow simulation                    ║
    ║    🧪 Enhanced test case generation                        ║
    ║    🎯 Banking domain intelligence                          ║
    ║                                                              ║
    ║  🚀 Ready for BFSI test automation!                        ║
    ╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)

def validate_system_requirements():
    """Validate all system requirements"""
    logger.info("Validating system requirements...")
    
    checks = {
        'environment': check_environment(),
        'dependencies': check_dependencies(),
        'directories': True,  # setup_directories() always succeeds
        'permissions': check_file_permissions()
    }
    
    # Setup directories
    setup_directories()
    
    # Check enhanced features
    enhanced_features = check_enhanced_dependencies()
    
    # Summary
    failed_checks = [name for name, status in checks.items() if not status]
    
    if failed_checks:
        logger.error(f"System validation failed: {', '.join(failed_checks)}")
        return False, enhanced_features
    else:
        logger.info("✓ All system requirements validated successfully")
        return True, enhanced_features

def main():
    """Enhanced main application entry point"""
    
    # Display startup banner
    display_startup_banner()
    
    logger.info("=" * 60)
    logger.info("Starting ITASSIST Enhanced Application")
    logger.info("=" * 60)
    
    try:
        # Validate system requirements
        system_ok, enhanced_features = validate_system_requirements()
        
        if not system_ok:
            logger.error("System validation failed - some features may not work properly")
            print("\n⚠️  System validation failed - check logs for details")
        
        # Load configuration
        config = load_configuration()
        
        # Log enhanced features status
        if enhanced_features['pacs008_config'] and enhanced_features['enhanced_test_generator']:
            logger.info("🏦 Enhanced PACS.008 features: ENABLED")
            print("🏦 PACS.008 Smart Mode: ENABLED")
        else:
            logger.info("📄 Standard mode: Enhanced features not available")
            print("📄 Running in Standard Mode")
        
        # Display feature summary
        print(f"""
📊 System Status:
   • Dependencies: {'✓' if check_dependencies() else '✗'}
   • PACS.008 Config: {'✓' if enhanced_features['pacs008_config'] else '✗'}
   • Enhanced Generator: {'✓' if enhanced_features['enhanced_test_generator'] else '✗'}
   • File Permissions: {'✓' if check_file_permissions() else '✗'}

🚀 Starting Streamlit application...
        """)
        
        logger.info("Initializing Streamlit application...")
        
        # Import and run the Streamlit app
        try:
            from ui.streamlit_app import main as streamlit_main
            
            # Pass enhanced features status to Streamlit app
            os.environ['ITASSIST_ENHANCED_FEATURES'] = str(enhanced_features)
            
            logger.info("✓ Streamlit app imported successfully")
            logger.info("🌐 Starting web interface...")
            
            # Run the Streamlit application
            streamlit_main()
            
        except ImportError as e:
            logger.error(f"Failed to import Streamlit app: {e}")
            logger.error("Make sure all dependencies are installed")
            print(f"\n❌ Import Error: {e}")
            print("💡 Try running: pip install -r requirements.txt")
            sys.exit(1)
        
        except Exception as e:
            logger.error(f"Streamlit application error: {e}")
            logger.error(f"Stack trace: {traceback.format_exc()}")
            print(f"\n❌ Application Error: {e}")
            sys.exit(1)
    
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
        print("\n👋 Application stopped by user")
        sys.exit(0)
    
    except Exception as e:
        logger.error(f"Critical application error: {e}")
        logger.error(f"Stack trace: {traceback.format_exc()}")
        print(f"\n💥 Critical Error: {e}")
        print("📝 Check itassist.log for detailed error information")
        sys.exit(1)

def check_installation():
    """Check if this is a fresh installation"""
    required_files = [
        "src/ui/streamlit_app.py",
        "src/processors/document_processor.py",
        "src/exporters/excel_exporter.py",
        "requirements.txt"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        logger.error(f"Missing required files: {missing_files}")
        print(f"""
❌ Installation appears to be incomplete.

Missing files:
{chr(10).join(f'  • {f}' for f in missing_files)}

Please ensure all ITASSIST files are properly installed.
        """)
        return False
    
    return True

def display_help():
    """Display help information"""
    help_text = """
🤖 ITASSIST - Intelligent Test Case Generator

USAGE:
    streamlit run main.py

FEATURES:
    📄 Document Processing:
       • DOCX, PDF, XLSX, Images
       • OCR for scanned documents
       • Table and embedded content extraction

    🏦 PACS.008 Smart Mode:
       • Automatic field detection
       • ISO 20022 validation
       • Maker-Checker workflow simulation

    🧪 Test Case Generation:
       • Context-aware test scenarios
       • Banking domain intelligence
       • Multiple export formats

REQUIREMENTS:
    • Python 3.8+
    • OpenAI API key
    • All dependencies from requirements.txt

CONFIGURATION:
    • Set OPENAI_API_KEY in .env file
    • Or provide API key in the web interface

SUPPORT:
    • Check itassist.log for detailed logs
    • Ensure all requirements.txt packages are installed
    """
    print(help_text)

if __name__ == "__main__":
    # Handle command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] in ['-h', '--help', 'help']:
            display_help()
            sys.exit(0)
        elif sys.argv[1] in ['-v', '--version', 'version']:
            print("ITASSIST Enhanced v2.0")
            sys.exit(0)
        elif sys.argv[1] in ['check', '--check']:
            # Run system check only
            display_startup_banner()
            system_ok, enhanced_features = validate_system_requirements()
            if system_ok:
                print("✅ System check passed - ready to run!")
            else:
                print("❌ System check failed - see logs for details")
            sys.exit(0 if system_ok else 1)
    
    # Check installation
    if not check_installation():
        sys.exit(1)
    
    # Run main application
    main()