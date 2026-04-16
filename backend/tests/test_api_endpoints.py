"""
Comprehensive API Tests for AI Educational Content Creator
Tests all 5 modules: Digital Books, Comic Scripts, Video Solutions, AI Prompts, Shared Library
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://learn-studio-3.preview.emergentagent.com').rstrip('/')


class TestAPIRoot:
    """Test API root endpoint"""
    
    def test_api_root(self):
        """Test API root returns correct message"""
        response = requests.get(f"{BASE_URL}/api/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "AI Educational Content Creator API" in data["message"]


class TestModule1DigitalBooks:
    """Module 1: Digital Books - LaTeX to HTML rendering"""
    
    def test_render_book_content(self):
        """Test creating book content with LaTeX input"""
        payload = {
            "latex_input": "\\section{TEST_Section}\nThis is a **test** book content.",
            "html_output": "<h2>TEST_Section</h2><p>This is a <strong>test</strong> book content.</p>"
        }
        response = requests.post(f"{BASE_URL}/api/books/render", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["status"] == "success"
        assert len(data["id"]) > 0
    
    def test_get_all_books(self):
        """Test retrieving all book contents"""
        response = requests.get(f"{BASE_URL}/api/books")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestModule2ComicScripts:
    """Module 2: Comic Scripts with GPT-5.2 and Agent Modes"""
    
    def test_generate_comic_default_mode(self):
        """Test comic generation with default GPT-5.2 agent"""
        payload = {
            "concept": "TEST_Explain gravity to kids",
            "agent_mode": "default"
        }
        response = requests.post(f"{BASE_URL}/api/comics/generate", json=payload, timeout=60)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "script" in data
        assert data["agent_mode"] == "default"
        assert len(data["script"]) > 0
    
    def test_generate_comic_pw_script_writer_mode(self):
        """Test comic generation with PW Script Writer agent"""
        payload = {
            "concept": "TEST_Explain Newton's laws",
            "agent_mode": "pw_script_writer"
        }
        response = requests.post(f"{BASE_URL}/api/comics/generate", json=payload, timeout=60)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["agent_mode"] == "pw_script_writer"
        assert "script" in data
    
    def test_generate_comic_pixar_mode(self):
        """Test comic generation with Pixar Scene Designer agent"""
        payload = {
            "concept": "TEST_Explain water cycle",
            "agent_mode": "pixar_scene_designer"
        }
        response = requests.post(f"{BASE_URL}/api/comics/generate", json=payload, timeout=60)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["agent_mode"] == "pixar_scene_designer"
    
    def test_generate_comic_invalid_mode_fallback(self):
        """Test that invalid agent mode falls back to default"""
        payload = {
            "concept": "TEST_Explain atoms",
            "agent_mode": "invalid_mode"
        }
        response = requests.post(f"{BASE_URL}/api/comics/generate", json=payload, timeout=60)
        assert response.status_code == 200
        data = response.json()
        assert data["agent_mode"] == "default"  # Should fallback to default
    
    def test_generate_panel_image(self):
        """Test Gemini Nano Banana image generation for comic panels"""
        payload = {
            "panel_description": "TEST_A friendly cartoon sun teaching a plant about photosynthesis",
            "style": "educational comic illustration"
        }
        response = requests.post(f"{BASE_URL}/api/comics/generate-image", json=payload, timeout=60)
        assert response.status_code == 200
        data = response.json()
        # Image generation may return partial (text only) or full (with image)
        assert data["status"] in ["success", "partial"]
        if data["status"] == "success":
            assert "image_base64" in data
            assert len(data["image_base64"]) > 0
    
    def test_get_all_comics(self):
        """Test retrieving all comic scripts"""
        response = requests.get(f"{BASE_URL}/api/comics")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestModule3VideoSolutions:
    """Module 3: Video Solutions with MoviePy + gTTS"""
    
    def test_create_video_solution(self):
        """Test video creation with MoviePy and Indian gTTS voice"""
        payload = {
            "question_text": "TEST_What is 2+2?",
            "solution_text": "TEST_The answer is 4. Two plus two equals four.",
            "voiceover_style": "professional"
        }
        response = requests.post(f"{BASE_URL}/api/videos/create", json=payload, timeout=120)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "id" in data
        assert "video_url" in data
        assert "/api/videos/download/" in data["video_url"]
        return data["id"]
    
    def test_download_video(self):
        """Test video download endpoint"""
        # First create a video
        payload = {
            "question_text": "TEST_What is 3+3?",
            "solution_text": "TEST_The answer is 6.",
            "voiceover_style": "friendly"
        }
        create_response = requests.post(f"{BASE_URL}/api/videos/create", json=payload, timeout=120)
        assert create_response.status_code == 200
        video_id = create_response.json()["id"]
        
        # Then download it
        download_response = requests.get(f"{BASE_URL}/api/videos/download/{video_id}")
        assert download_response.status_code == 200
        assert download_response.headers.get("content-type") == "video/mp4"
    
    def test_download_nonexistent_video(self):
        """Test downloading a video that doesn't exist"""
        response = requests.get(f"{BASE_URL}/api/videos/download/nonexistent-id-12345")
        assert response.status_code == 404
        data = response.json()
        assert "error" in data
    
    def test_get_all_videos(self):
        """Test retrieving all video solutions"""
        response = requests.get(f"{BASE_URL}/api/videos")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestModule4AIPrompts:
    """Module 4: AI Video Prompts - 7-layer methodology"""
    
    def test_create_ai_prompt(self):
        """Test creating AI video prompt with all 7 layers"""
        payload = {
            "subject": "TEST_A teacher explaining quantum physics",
            "action": "drawing diagrams on a whiteboard",
            "camera_angle": "Medium shot, slightly tilted",
            "lighting": "Soft natural light from window",
            "physics": "Realistic motion, gravity applies",
            "style": "Professional documentary style, 4K",
            "duration": "30 seconds"
        }
        response = requests.post(f"{BASE_URL}/api/prompts/create", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "id" in data
        assert "final_prompt" in data
        # Verify final prompt contains all components
        assert "TEST_A teacher" in data["final_prompt"]
        assert "drawing diagrams" in data["final_prompt"]
    
    def test_get_all_prompts(self):
        """Test retrieving all AI prompts"""
        response = requests.get(f"{BASE_URL}/api/prompts")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestModule5SharedLibrary:
    """Module 5: Shared Library - Collaboration features"""
    
    def test_publish_to_library(self):
        """Test publishing content to shared library"""
        payload = {
            "creator_name": "TEST_Educator",
            "module_type": "comic_script",
            "title": "TEST_Photosynthesis Comic",
            "content": "TEST_Panel 1: A plant named Sunny wakes up..."
        }
        response = requests.post(f"{BASE_URL}/api/library/publish", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "published"
        assert "id" in data
        return data["id"]
    
    def test_get_library_items_all(self):
        """Test retrieving all library items"""
        response = requests.get(f"{BASE_URL}/api/library")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_library_items_filtered_by_type(self):
        """Test filtering library items by module type"""
        # First publish a comic_script item
        payload = {
            "creator_name": "TEST_FilterTest",
            "module_type": "comic_script",
            "title": "TEST_Filter Comic",
            "content": "TEST_Content for filter test"
        }
        requests.post(f"{BASE_URL}/api/library/publish", json=payload)
        
        # Filter by comic_script
        response = requests.get(f"{BASE_URL}/api/library?module_type=comic_script")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # All items should be comic_script type
        for item in data:
            assert item["module_type"] == "comic_script"
    
    def test_get_library_item_by_id(self):
        """Test retrieving a specific library item by ID"""
        # First publish an item
        payload = {
            "creator_name": "TEST_GetById",
            "module_type": "book_content",
            "title": "TEST_Book for ID test",
            "content": "TEST_Book content here"
        }
        publish_response = requests.post(f"{BASE_URL}/api/library/publish", json=payload)
        item_id = publish_response.json()["id"]
        
        # Get by ID
        response = requests.get(f"{BASE_URL}/api/library/{item_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == item_id
        assert data["creator_name"] == "TEST_GetById"
        assert data["title"] == "TEST_Book for ID test"
    
    def test_get_nonexistent_library_item(self):
        """Test retrieving a library item that doesn't exist"""
        response = requests.get(f"{BASE_URL}/api/library/nonexistent-id-12345")
        assert response.status_code == 404
        data = response.json()
        assert "error" in data
    
    def test_publish_video_prompt_type(self):
        """Test publishing video_prompt type to library"""
        payload = {
            "creator_name": "TEST_PromptCreator",
            "module_type": "video_prompt",
            "title": "TEST_Cinematic Prompt",
            "content": "Subject: A scientist. Action: Mixing chemicals..."
        }
        response = requests.post(f"{BASE_URL}/api/library/publish", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "published"


class TestDataPersistence:
    """Test MongoDB data persistence across operations"""
    
    def test_comic_persistence(self):
        """Test that created comics persist in database"""
        # Create a comic
        unique_concept = f"TEST_Persistence_{int(time.time())}"
        payload = {
            "concept": unique_concept,
            "agent_mode": "default"
        }
        create_response = requests.post(f"{BASE_URL}/api/comics/generate", json=payload, timeout=60)
        assert create_response.status_code == 200
        created_id = create_response.json()["id"]
        
        # Verify it appears in the list
        list_response = requests.get(f"{BASE_URL}/api/comics")
        assert list_response.status_code == 200
        comics = list_response.json()
        found = any(c["id"] == created_id for c in comics)
        assert found, "Created comic not found in database"
    
    def test_library_persistence(self):
        """Test that published library items persist"""
        unique_title = f"TEST_LibPersist_{int(time.time())}"
        payload = {
            "creator_name": "TEST_Persist",
            "module_type": "comic_script",
            "title": unique_title,
            "content": "TEST_Persistence content"
        }
        create_response = requests.post(f"{BASE_URL}/api/library/publish", json=payload)
        assert create_response.status_code == 200
        created_id = create_response.json()["id"]
        
        # Verify it appears in the list
        list_response = requests.get(f"{BASE_URL}/api/library")
        assert list_response.status_code == 200
        items = list_response.json()
        found = any(i["id"] == created_id for i in items)
        assert found, "Published library item not found in database"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
