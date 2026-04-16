import requests
import sys
import json
from datetime import datetime

class AIEducationAPITester:
    def __init__(self, base_url="https://learn-studio-3.preview.emergentagent.com"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0

    def run_test(self, name, method, endpoint, expected_status, data=None, files=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'} if not files else {}

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers)
            elif method == 'POST':
                if files:
                    response = requests.post(url, files=files)
                else:
                    response = requests.post(url, json=data, headers=headers)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    if 'id' in response_data:
                        print(f"   Generated ID: {response_data['id']}")
                    if 'status' in response_data:
                        print(f"   Status: {response_data['status']}")
                except:
                    pass
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data}")
                except:
                    print(f"   Response: {response.text[:200]}")

            return success, response.json() if response.headers.get('content-type', '').startswith('application/json') else {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_root_endpoint(self):
        """Test API root endpoint"""
        return self.run_test("API Root", "GET", "api/", 200)

    def test_module1_books(self):
        """Test Module 1: Digital Books endpoints"""
        print("\n📚 Testing Module 1: Digital Books")
        
        # Test book content creation
        book_data = {
            "latex_input": "\\section{Test}\nThis is a test book content.",
            "html_output": "<h2>Test</h2><p>This is a test book content.</p>"
        }
        success, response = self.run_test(
            "Create Book Content", "POST", "api/books/render", 200, book_data
        )
        
        # Test getting all books
        self.run_test("Get All Books", "GET", "api/books", 200)
        
        return success

    def test_module2_comics(self):
        """Test Module 2: Comic Scripts with GPT-5.2"""
        print("\n🎭 Testing Module 2: Comic Scripts")
        
        # Test comic script generation
        comic_data = {
            "concept": "Explain photosynthesis to elementary students using a fun story about a plant named Sunny"
        }
        success, response = self.run_test(
            "Generate Comic Script", "POST", "api/comics/generate", 200, comic_data
        )
        
        # Test getting all comics
        self.run_test("Get All Comics", "GET", "api/comics", 200)
        
        return success

    def test_module3_videos(self):
        """Test Module 3: Video Solutions"""
        print("\n🎥 Testing Module 3: Video Solutions")
        
        # Test video solution creation
        video_data = {
            "question_text": "What is the Pythagorean theorem and how do we use it?",
            "voiceover_style": "professional"
        }
        success, response = self.run_test(
            "Create Video Solution", "POST", "api/videos/create", 200, video_data
        )
        
        # Test image upload endpoint
        # Note: This is a placeholder test since we don't have actual file
        print("\n   📷 Testing Image Upload (placeholder)")
        print("   ⚠️  Image upload endpoint exists but requires actual file for full test")
        
        # Test getting all videos
        self.run_test("Get All Videos", "GET", "api/videos", 200)
        
        return success

    def test_module4_prompts(self):
        """Test Module 4: AI Video Prompts"""
        print("\n🎬 Testing Module 4: AI Video Prompts")
        
        # Test AI prompt creation
        prompt_data = {
            "subject": "A teacher explaining quantum physics",
            "action": "drawing diagrams on a whiteboard",
            "camera_angle": "Medium shot, slightly tilted",
            "lighting": "Soft natural light from window",
            "physics": "Realistic motion, gravity applies",
            "style": "Professional documentary style, 4K",
            "duration": "30 seconds"
        }
        success, response = self.run_test(
            "Create AI Prompt", "POST", "api/prompts/create", 200, prompt_data
        )
        
        # Test getting all prompts
        self.run_test("Get All Prompts", "GET", "api/prompts", 200)
        
        return success

def main():
    print("🚀 Starting AI Educational Content Creator API Tests")
    print("=" * 60)
    
    tester = AIEducationAPITester()
    
    # Test all modules
    results = []
    
    # Test API root
    root_success, _ = tester.test_root_endpoint()
    results.append(("API Root", root_success))
    
    # Test each module
    module1_success = tester.test_module1_books()
    results.append(("Module 1: Digital Books", module1_success))
    
    module2_success = tester.test_module2_comics()
    results.append(("Module 2: Comic Scripts", module2_success))
    
    module3_success = tester.test_module3_videos()
    results.append(("Module 3: Video Solutions", module3_success))
    
    module4_success = tester.test_module4_prompts()
    results.append(("Module 4: AI Video Prompts", module4_success))
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    for module_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {module_name}")
    
    print(f"\n📈 Overall: {tester.tests_passed}/{tester.tests_run} tests passed")
    
    # Determine exit code
    if tester.tests_passed == tester.tests_run:
        print("🎉 All tests passed!")
        return 0
    else:
        print("⚠️  Some tests failed. Check the details above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())