"""
Simple test script to verify the application structure and basic functionality.
"""
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, '/home/runner/work/ai-coding-assistant/ai-coding-assistant')

def test_project_structure():
    """Test that all required files and directories exist."""
    required_files = [
        'app/__init__.py',
        'app/main.py',
        'app/worker.py',
        'app/api/__init__.py',
        'app/api/routes.py',
        'app/core/__init__.py',
        'app/core/config.py',
        'app/core/memory.py',
        'app/services/__init__.py',
        'app/services/agent.py',
        'tests/__init__.py',
        'tests/test_main.py',
        'requirements.txt',
        '.env',
        'Dockerfile',
        'docker-compose.yml'
    ]
    
    missing_files = []
    for file_path in required_files:
        full_path = os.path.join('/home/runner/work/ai-coding-assistant/ai-coding-assistant', file_path)
        if not os.path.exists(full_path):
            missing_files.append(file_path)
    
    if missing_files:
        print(f"❌ Missing files: {missing_files}")
        return False
    else:
        print("✅ All required files exist")
        return True


def test_memory_functionality():
    """Test the memory functionality without external dependencies."""
    try:
        # Test simple memory backend
        from app.core.memory import SimpleMemoryBackend
        
        backend = SimpleMemoryBackend()
        
        # Test adding documents
        docs = ["Hello world", "Python programming", "AI assistant"]
        metadata = [{"type": "test"}, {"type": "code"}, {"type": "ai"}]
        backend.add_documents(docs, metadata)
        
        # Test searching
        results = backend.search("hello")
        if len(results) > 0 and "hello" in results[0]['document'].lower():
            print("✅ Memory search functionality working")
            return True
        else:
            print("❌ Memory search not working correctly")
            return False
            
    except Exception as e:
        print(f"❌ Memory test failed: {e}")
        return False


def test_import_structure():
    """Test that Python modules can be imported."""
    try:
        # Test core imports (without external dependencies)
        import app
        from app.core.memory import RAGMemory, SimpleMemoryBackend
        
        print("✅ Core modules can be imported")
        return True
    except Exception as e:
        print(f"❌ Import test failed: {e}")
        return False


def test_readme_completeness():
    """Test that README.md contains required information."""
    try:
        with open('/home/runner/work/ai-coding-assistant/ai-coding-assistant/README.md', 'r') as f:
            readme_content = f.read()
        
        required_sections = [
            "AI Coding Assistant",
            "Features",
            "Project Structure",
            "Tech Stack"
        ]
        
        missing_sections = []
        for section in required_sections:
            if section not in readme_content:
                missing_sections.append(section)
        
        if missing_sections:
            print(f"❌ README missing sections: {missing_sections}")
            return False
        else:
            print("✅ README contains required sections")
            return True
            
    except Exception as e:
        print(f"❌ README test failed: {e}")
        return False


def run_all_tests():
    """Run all tests and report results."""
    print("🚀 Running AI Coding Assistant Tests")
    print("=" * 50)
    
    tests = [
        ("Project Structure", test_project_structure),
        ("Import Structure", test_import_structure),
        ("Memory Functionality", test_memory_functionality),
        ("README Completeness", test_readme_completeness),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 Testing {test_name}...")
        if test_func():
            passed += 1
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The AI Coding Assistant is ready to use.")
        return True
    else:
        print("⚠️  Some tests failed. Please check the issues above.")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)