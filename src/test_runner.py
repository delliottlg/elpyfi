#!/usr/bin/env python3
"""
Test Runner for PM Claude
Runs tests for all managed services and reports results
"""

import subprocess
import sys
from pathlib import Path
from typing import List, Dict, Tuple
import time
from datetime import datetime

class ServiceTestRunner:
    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.results = {}
        # Use shared venv
        self.python_cmd = str(base_path / "venv/bin/python")
        
    def run_command(self, cmd: List[str], cwd: Path) -> Tuple[bool, str, str]:
        """Run a command and return success status, stdout, and stderr"""
        try:
            result = subprocess.run(
                cmd,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            return result.returncode == 0, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return False, "", "Test timed out after 5 minutes"
        except Exception as e:
            return False, "", str(e)
    
    def test_elpyfi_core(self) -> Dict:
        """Run tests for elpyfi-core"""
        print("\n🔧 Testing elpyfi-core...")
        engine_path = self.base_path / "services/elpyfi-core/elpyfi-engine"
        
        # Use shared venv to run tests
        success, stdout, stderr = self.run_command(
            [self.python_cmd, "test_engine.py"], 
            engine_path
        )
        
        return {
            "service": "elpyfi-core",
            "success": success,
            "output": stdout,
            "error": stderr,
            "test_files": ["test_engine.py"]
        }
    
    def test_elpyfi_ai(self) -> Dict:
        """Run tests for elpyfi-ai"""
        print("\n🤖 Testing elpyfi-ai...")
        ai_path = self.base_path / "services/elpyfi-ai"
        
        # Run pytest on tests directory using shared venv
        success, stdout, stderr = self.run_command(
            [self.python_cmd, "-m", "pytest", "tests/", "-v", "--tb=short"],
            ai_path
        )
        
        return {
            "service": "elpyfi-ai",
            "success": success,
            "output": stdout,
            "error": stderr,
            "test_files": [
                "tests/test_analyzer.py",
                "tests/test_api.py",
                "test_ai_mode.py",
                "test_performance.py",
                "test_scenarios.py"
            ]
        }
    
    def test_elpyfi_api(self) -> Dict:
        """Run tests for elpyfi-api"""
        print("\n🌐 Testing elpyfi-api...")
        api_path = self.base_path / "services/elpyfi-api"
        
        # Check if any test files exist
        test_dir = api_path / "tests"
        test_files = list(test_dir.glob("test_*.py"))
        
        if test_files:
            success, stdout, stderr = self.run_command(
                [self.python_cmd, "-m", "pytest", "tests/", "-v"],
                api_path
            )
        else:
            return {
                "service": "elpyfi-api",
                "success": True,
                "output": "No tests found in tests/ directory",
                "error": "",
                "test_files": []
            }
        
        return {
            "service": "elpyfi-api",
            "success": success,
            "output": stdout,
            "error": stderr,
            "test_files": [str(f.name) for f in test_files]
        }
    
    def test_elpyfi_dashboard(self) -> Dict:
        """Run tests for elpyfi-dashboard"""
        print("\n📊 Testing elpyfi-dashboard...")
        dashboard_path = self.base_path / "services/elpyfi-dashboard"
        
        # Check if test script exists in package.json
        package_json = dashboard_path / "package.json"
        if package_json.exists():
            # For now, just run lint as there are no tests
            success, stdout, stderr = self.run_command(
                ["npm", "run", "lint"],
                dashboard_path
            )
            
            return {
                "service": "elpyfi-dashboard",
                "success": success,
                "output": stdout or "No tests configured, ran lint instead",
                "error": stderr,
                "test_files": []
            }
        
        return {
            "service": "elpyfi-dashboard",
            "success": True,
            "output": "No test configuration found",
            "error": "",
            "test_files": []
        }
    
    def run_all_tests(self) -> None:
        """Run tests for all services"""
        print(f"🚀 PM Claude Test Runner")
        print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 50)
        
        services = [
            self.test_elpyfi_core,
            self.test_elpyfi_ai,
            self.test_elpyfi_api,
            self.test_elpyfi_dashboard
        ]
        
        all_success = True
        
        for test_func in services:
            result = test_func()
            self.results[result["service"]] = result
            if not result["success"]:
                all_success = False
        
        # Print summary
        print("\n" + "=" * 50)
        print("📋 TEST SUMMARY")
        print("=" * 50)
        
        for service, result in self.results.items():
            status = "✅ PASSED" if result["success"] else "❌ FAILED"
            test_count = len(result["test_files"])
            print(f"{service:20} {status} ({test_count} test files)")
            
            if not result["success"] and result["error"]:
                print(f"  Error: {result['error'][:100]}...")
        
        print("\n" + "=" * 50)
        overall = "✅ ALL TESTS PASSED" if all_success else "❌ SOME TESTS FAILED"
        print(f"Overall: {overall}")
        
        return all_success

def main():
    """Main entry point"""
    base_path = Path(__file__).parent.parent
    runner = ServiceTestRunner(base_path)
    
    success = runner.run_all_tests()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()