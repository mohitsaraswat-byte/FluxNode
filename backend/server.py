from fastapi import FastAPI, APIRouter, UploadFile, File, Form
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
import uuid
from datetime import datetime, timezone
import base64
from emergentintegrations.llm.chat import LlmChat, UserMessage

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============= Models =============

class BookContent(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    latex_input: str
    html_output: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class BookContentCreate(BaseModel):
    latex_input: str
    html_output: str

class ComicScript(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    concept: str
    script: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ComicScriptRequest(BaseModel):
    concept: str

class VideoSolution(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    question_text: str
    question_image: Optional[str] = None
    voiceover_style: str
    video_url: Optional[str] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class VideoSolutionCreate(BaseModel):
    question_text: str
    voiceover_style: str

class AIPrompt(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    subject: str
    action: str
    camera_angle: str
    lighting: str
    physics: str
    style: str
    duration: str
    final_prompt: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class AIPromptCreate(BaseModel):
    subject: str
    action: str
    camera_angle: str
    lighting: str
    physics: str
    style: str
    duration: str

# ============= Routes =============

@api_router.get("/")
async def root():
    return {"message": "AI Educational Content Creator API"}

# Module 1: Digital Books
@api_router.post("/books/render", response_model=BookContent)
async def render_book_content(input: BookContentCreate):
    """Save and return book content with LaTeX to HTML conversion"""
    book_dict = input.model_dump()
    book_obj = BookContent(**book_dict)
    
    doc = book_obj.model_dump()
    doc['timestamp'] = doc['timestamp'].isoformat()
    
    await db.book_contents.insert_one(doc)
    return book_obj

@api_router.get("/books", response_model=List[BookContent])
async def get_book_contents():
    """Get all saved book contents"""
    books = await db.book_contents.find({}, {"_id": 0}).to_list(100)
    for book in books:
        if isinstance(book['timestamp'], str):
            book['timestamp'] = datetime.fromisoformat(book['timestamp'])
    return books

# Module 2: Comic Scripts with GPT-5.2
@api_router.post("/comics/generate")
async def generate_comic_script(request: ComicScriptRequest):
    """Generate comic script from educational concept using GPT-5.2"""
    try:
        api_key = os.environ.get('EMERGENT_LLM_KEY')
        if not api_key:
            return JSONResponse(
                status_code=500,
                content={"error": "EMERGENT_LLM_KEY not configured"}
            )
        
        # Initialize LLM Chat
        chat = LlmChat(
            api_key=api_key,
            session_id=f"comic-{uuid.uuid4()}",
            system_message="You are an expert educational comic script writer. Create engaging, visual comic scripts that explain complex educational concepts through sequential panels. Each panel should have clear visual descriptions and dialogue."
        ).with_model("openai", "gpt-5.2")
        
        # Create user message
        user_message = UserMessage(
            text=f"Create a detailed comic script to explain this educational concept: {request.concept}\n\nFormat the script with panel numbers, visual descriptions, and dialogue. Make it educational yet entertaining."
        )
        
        # Generate script
        response = await chat.send_message(user_message)
        
        # Save to database
        comic_obj = ComicScript(
            concept=request.concept,
            script=response
        )
        
        doc = comic_obj.model_dump()
        doc['timestamp'] = doc['timestamp'].isoformat()
        await db.comic_scripts.insert_one(doc)
        
        return JSONResponse(content={
            "id": comic_obj.id,
            "concept": comic_obj.concept,
            "script": comic_obj.script,
            "status": "success"
        })
        
    except Exception as e:
        logger.error(f"Error generating comic script: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e), "status": "failed"}
        )

@api_router.get("/comics", response_model=List[ComicScript])
async def get_comic_scripts():
    """Get all saved comic scripts"""
    comics = await db.comic_scripts.find({}, {"_id": 0}).to_list(100)
    for comic in comics:
        if isinstance(comic['timestamp'], str):
            comic['timestamp'] = datetime.fromisoformat(comic['timestamp'])
    return comics

# Module 3: Video Solutions
@api_router.post("/videos/create", response_model=VideoSolution)
async def create_video_solution(input: VideoSolutionCreate):
    """Create video solution (placeholder - actual video generation would be implemented here)"""
    video_obj = VideoSolution(
        question_text=input.question_text,
        voiceover_style=input.voiceover_style,
        video_url="https://example.com/placeholder-video.mp4"
    )
    
    doc = video_obj.model_dump()
    doc['timestamp'] = doc['timestamp'].isoformat()
    
    await db.video_solutions.insert_one(doc)
    return video_obj

@api_router.post("/videos/upload-question-image")
async def upload_question_image(file: UploadFile = File(...)):
    """Upload question image for video solution"""
    try:
        contents = await file.read()
        base64_image = base64.b64encode(contents).decode('utf-8')
        return JSONResponse(content={
            "status": "success",
            "image_data": base64_image,
            "filename": file.filename
        })
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

@api_router.get("/videos", response_model=List[VideoSolution])
async def get_video_solutions():
    """Get all video solutions"""
    videos = await db.video_solutions.find({}, {"_id": 0}).to_list(100)
    for video in videos:
        if isinstance(video['timestamp'], str):
            video['timestamp'] = datetime.fromisoformat(video['timestamp'])
    return videos

# Module 4: AI Video Prompts
@api_router.post("/prompts/create", response_model=AIPrompt)
async def create_ai_prompt(input: AIPromptCreate):
    """Create AI video generation prompt from 7-layer form"""
    # Compile the final prompt
    final_prompt = f"Subject: {input.subject}. Action: {input.action}. Camera: {input.camera_angle}. Lighting: {input.lighting}. Physics: {input.physics}. Style: {input.style}. Duration: {input.duration}."
    
    prompt_obj = AIPrompt(
        subject=input.subject,
        action=input.action,
        camera_angle=input.camera_angle,
        lighting=input.lighting,
        physics=input.physics,
        style=input.style,
        duration=input.duration,
        final_prompt=final_prompt
    )
    
    doc = prompt_obj.model_dump()
    doc['timestamp'] = doc['timestamp'].isoformat()
    
    await db.ai_prompts.insert_one(doc)
    return prompt_obj

@api_router.get("/prompts", response_model=List[AIPrompt])
async def get_ai_prompts():
    """Get all AI prompts"""
    prompts = await db.ai_prompts.find({}, {"_id": 0}).to_list(100)
    for prompt in prompts:
        if isinstance(prompt['timestamp'], str):
            prompt['timestamp'] = datetime.fromisoformat(prompt['timestamp'])
    return prompts

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()