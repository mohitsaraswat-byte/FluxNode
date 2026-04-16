from fastapi import FastAPI, APIRouter, UploadFile, File, Form
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
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
import asyncio
from emergentintegrations.llm.chat import LlmChat, UserMessage, ImageContent

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app
app = FastAPI()
api_router = APIRouter(prefix="/api")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Ensure output directories exist
VIDEOS_DIR = ROOT_DIR / "generated_videos"
IMAGES_DIR = ROOT_DIR / "generated_images"
VIDEOS_DIR.mkdir(exist_ok=True)
IMAGES_DIR.mkdir(exist_ok=True)

# ============= Agent System Prompts =============
AGENT_PROMPTS = {
    "default": "You are an expert educational comic script writer. Create engaging, visual comic scripts that explain complex educational concepts through sequential panels. Each panel should have clear visual descriptions and dialogue. Make it educational yet entertaining.",
    "pw_script_writer": """You are PW Comics Script Writer, a specialized agent for Physics Wallah educational content. You create detailed comic scripts that:
- Break down complex physics/chemistry/biology/math concepts into fun, relatable stories
- Use Indian student characters (like Ravi, Priya, Aman) who are curious and ask good questions
- Include a wise teacher character who explains with real-world analogies
- Format each panel with: PANEL NUMBER, SETTING, CHARACTER ACTIONS, DIALOGUE, and EDUCATIONAL NOTE
- Always conclude with a summary panel that reinforces the key concept
- Use humor and relatable school/college scenarios from Indian education context
- Include exam-relevant tips where applicable""",
    "pixar_scene_designer": """You are Pixar Comics Scene Designer, a specialized visual storytelling agent. You design comic scenes with:
- Rich, cinematic visual descriptions inspired by Pixar animation quality
- Detailed color palette suggestions for each panel (warm tones for positive moments, cool for tension)
- Character expressions described with micro-emotions (slight eyebrow raise, half-smile, wide eyes)
- Dynamic camera angles: bird's eye, dutch angle, extreme close-up, over-the-shoulder
- Lighting direction notes: golden hour glow, dramatic backlighting, soft ambient
- Background environment details that reinforce the educational theme
- Panel composition rules: rule of thirds, leading lines, visual hierarchy
- Suggested visual metaphors to make abstract concepts tangible
- Each panel description should be detailed enough for an illustrator or AI image generator to recreate"""
}

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
    agent_mode: str = "default"
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ComicScriptRequest(BaseModel):
    concept: str
    agent_mode: str = "default"

class ComicImageRequest(BaseModel):
    panel_description: str
    style: str = "educational comic illustration"

class VideoSolutionCreate(BaseModel):
    question_text: str
    solution_text: str
    voiceover_style: str = "professional"

class AIPromptCreate(BaseModel):
    subject: str
    action: str
    camera_angle: str
    lighting: str
    physics: str
    style: str
    duration: str

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

class LibraryItem(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    creator_name: str
    module_type: str
    title: str
    content: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class PublishRequest(BaseModel):
    creator_name: str
    module_type: str
    title: str
    content: str

# ============= Routes =============

@api_router.get("/")
async def root():
    return {"message": "AI Educational Content Creator API"}

# Module 1: Digital Books
@api_router.post("/books/render")
async def render_book_content(input: BookContentCreate):
    book_obj = BookContent(**input.model_dump())
    doc = book_obj.model_dump()
    doc['timestamp'] = doc['timestamp'].isoformat()
    await db.book_contents.insert_one(doc)
    doc.pop('_id', None)
    return JSONResponse(content={"id": book_obj.id, "status": "success"})

@api_router.get("/books")
async def get_book_contents():
    books = await db.book_contents.find({}, {"_id": 0}).to_list(100)
    return JSONResponse(content=books)

# Module 2: Comic Scripts with GPT-5.2 + Agent Modes
@api_router.post("/comics/generate")
async def generate_comic_script(request: ComicScriptRequest):
    try:
        api_key = os.environ.get('EMERGENT_LLM_KEY')
        if not api_key:
            return JSONResponse(status_code=500, content={"error": "EMERGENT_LLM_KEY not configured"})

        agent_mode = request.agent_mode if request.agent_mode in AGENT_PROMPTS else "default"
        system_prompt = AGENT_PROMPTS[agent_mode]

        chat = LlmChat(
            api_key=api_key,
            session_id=f"comic-{uuid.uuid4()}",
            system_message=system_prompt
        ).with_model("openai", "gpt-5.2")

        user_message = UserMessage(
            text=f"Create a detailed comic script to explain this educational concept: {request.concept}\n\nFormat the script with panel numbers, visual descriptions, and dialogue."
        )

        response = await chat.send_message(user_message)

        comic_obj = ComicScript(concept=request.concept, script=response, agent_mode=agent_mode)
        doc = comic_obj.model_dump()
        doc['timestamp'] = doc['timestamp'].isoformat()
        await db.comic_scripts.insert_one(doc)

        return JSONResponse(content={
            "id": comic_obj.id,
            "concept": comic_obj.concept,
            "script": comic_obj.script,
            "agent_mode": agent_mode,
            "status": "success"
        })

    except Exception as e:
        logger.error(f"Error generating comic script: {str(e)}")
        return JSONResponse(status_code=500, content={"error": str(e), "status": "failed"})

# Module 2: Gemini Nano Banana Image Generation for Comic Panels
@api_router.post("/comics/generate-image")
async def generate_comic_image(request: ComicImageRequest):
    try:
        api_key = os.environ.get('EMERGENT_LLM_KEY')
        if not api_key:
            return JSONResponse(status_code=500, content={"error": "EMERGENT_LLM_KEY not configured"})

        chat = LlmChat(
            api_key=api_key,
            session_id=f"img-{uuid.uuid4()}",
            system_message="You are a comic panel illustrator."
        ).with_model("gemini", "gemini-3.1-flash-image-preview").with_params(modalities=["image", "text"])

        msg = UserMessage(
            text=f"Create a colorful educational comic panel illustration: {request.panel_description}. Style: {request.style}. Make it vibrant, kid-friendly, and visually appealing."
        )

        text, images = await chat.send_message_multimodal_response(msg)

        if images and len(images) > 0:
            image_id = str(uuid.uuid4())
            image_data = images[0]['data']
            image_bytes = base64.b64decode(image_data)
            image_path = IMAGES_DIR / f"{image_id}.png"
            with open(image_path, "wb") as f:
                f.write(image_bytes)

            return JSONResponse(content={
                "status": "success",
                "image_id": image_id,
                "image_data": image_data[:50] + "...",
                "image_base64": image_data,
                "text_response": text
            })
        else:
            return JSONResponse(content={
                "status": "partial",
                "text_response": text,
                "message": "Text generated but no image returned"
            })

    except Exception as e:
        logger.error(f"Error generating image: {str(e)}")
        return JSONResponse(status_code=500, content={"error": str(e), "status": "failed"})

@api_router.get("/comics")
async def get_comic_scripts():
    comics = await db.comic_scripts.find({}, {"_id": 0}).to_list(100)
    return JSONResponse(content=comics)

# Module 3: Video Solutions with MoviePy + gTTS
# Background task tracker
video_tasks = {}

async def _run_video_generation(video_id, question, solution, voice_style):
    """Background task for video generation"""
    try:
        video_tasks[video_id] = {"status": "processing", "progress": "Generating audio..."}
        video_path = await generate_whiteboard_video(video_id, question, solution, voice_style)
        if video_path:
            doc = {
                "id": video_id,
                "question_text": question,
                "solution_text": solution,
                "voiceover_style": voice_style,
                "video_filename": f"{video_id}.mp4",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            await db.video_solutions.insert_one(doc)
            video_tasks[video_id] = {"status": "completed", "video_url": f"/api/videos/download/{video_id}"}
        else:
            video_tasks[video_id] = {"status": "failed", "error": "Video generation failed"}
    except Exception as e:
        logger.error(f"Background video error: {str(e)}")
        video_tasks[video_id] = {"status": "failed", "error": str(e)}

@api_router.post("/videos/create")
async def create_video_solution(input: VideoSolutionCreate):
    try:
        video_id = str(uuid.uuid4())
        # Start background task
        asyncio.create_task(_run_video_generation(video_id, input.question_text, input.solution_text, input.voiceover_style))
        video_tasks[video_id] = {"status": "processing", "progress": "Starting video generation..."}
        # Return immediately so the request doesn't timeout
        return JSONResponse(content={"id": video_id, "status": "processing"})
    except Exception as e:
        logger.error(f"Error creating video: {str(e)}")
        return JSONResponse(status_code=500, content={"error": str(e), "status": "failed"})

@api_router.get("/videos/status/{video_id}")
async def get_video_status(video_id: str):
    """Poll this endpoint to check video generation progress"""
    if video_id in video_tasks:
        return JSONResponse(content={"id": video_id, **video_tasks[video_id]})
    # Check if video already exists on disk
    video_path = VIDEOS_DIR / f"{video_id}.mp4"
    if video_path.exists():
        return JSONResponse(content={"id": video_id, "status": "completed", "video_url": f"/api/videos/download/{video_id}"})
    return JSONResponse(status_code=404, content={"id": video_id, "status": "not_found"})

@api_router.get("/videos/download/{video_id}")
async def download_video(video_id: str):
    video_path = VIDEOS_DIR / f"{video_id}.mp4"
    if video_path.exists():
        return FileResponse(str(video_path), media_type="video/mp4", filename=f"solution_{video_id}.mp4")
    return JSONResponse(status_code=404, content={"error": "Video not found"})

@api_router.get("/videos")
async def get_video_solutions():
    videos = await db.video_solutions.find({}, {"_id": 0}).to_list(100)
    return JSONResponse(content=videos)

# Module 4: AI Video Prompts
@api_router.post("/prompts/create")
async def create_ai_prompt(input: AIPromptCreate):
    final_prompt = f"Subject: {input.subject}. Action: {input.action}. Camera: {input.camera_angle}. Lighting: {input.lighting}. Physics: {input.physics}. Style: {input.style}. Duration: {input.duration}."

    prompt_obj = AIPrompt(
        subject=input.subject, action=input.action, camera_angle=input.camera_angle,
        lighting=input.lighting, physics=input.physics, style=input.style,
        duration=input.duration, final_prompt=final_prompt
    )
    doc = prompt_obj.model_dump()
    doc['timestamp'] = doc['timestamp'].isoformat()
    await db.ai_prompts.insert_one(doc)

    return JSONResponse(content={
        "id": prompt_obj.id,
        "final_prompt": final_prompt,
        "status": "success"
    })

@api_router.get("/prompts")
async def get_ai_prompts():
    prompts = await db.ai_prompts.find({}, {"_id": 0}).to_list(100)
    return JSONResponse(content=prompts)

# Module 5: Shared Library (Collaboration)
@api_router.post("/library/publish")
async def publish_to_library(input: PublishRequest):
    item = LibraryItem(
        creator_name=input.creator_name,
        module_type=input.module_type,
        title=input.title,
        content=input.content
    )
    doc = item.model_dump()
    doc['timestamp'] = doc['timestamp'].isoformat()
    await db.shared_library.insert_one(doc)
    return JSONResponse(content={"id": item.id, "status": "published"})

@api_router.get("/library")
async def get_library_items(module_type: Optional[str] = None):
    query = {}
    if module_type:
        query["module_type"] = module_type
    items = await db.shared_library.find(query, {"_id": 0}).sort("timestamp", -1).to_list(100)
    return JSONResponse(content=items)

@api_router.get("/library/{item_id}")
async def get_library_item(item_id: str):
    item = await db.shared_library.find_one({"id": item_id}, {"_id": 0})
    if item:
        return JSONResponse(content=item)
    return JSONResponse(status_code=404, content={"error": "Item not found"})

# ============= Video Generation Helper =============

async def generate_whiteboard_video(video_id, question, solution, voice_style):
    """Generate whiteboard-style video with handwritten text animation and Indian TTS voice"""
    try:
        from PIL import Image, ImageDraw, ImageFont
        from gtts import gTTS
        from moviepy import ImageSequenceClip, AudioFileClip, concatenate_videoclips, CompositeVideoClip, ImageClip

        # Paths
        bg_path = ROOT_DIR / "assets" / "pw_background.png"
        font_path = ROOT_DIR / "assets" / "fonts" / "Caveat-Medium.ttf"
        audio_path = VIDEOS_DIR / f"{video_id}_audio.mp3"
        video_path = VIDEOS_DIR / f"{video_id}.mp4"

        # Load background
        bg = Image.open(bg_path).convert("RGB")
        bg = bg.resize((1080, 1080))

        # Load fonts
        try:
            font_question = ImageFont.truetype(str(font_path), 32)
            font_solution = ImageFont.truetype(str(font_path), 36)
            font_label = ImageFont.truetype(str(font_path), 28)
        except Exception:
            font_question = ImageFont.load_default()
            font_solution = font_question
            font_label = font_question

        # Writing area
        x_start, y_start = 60, 80
        max_width = 900
        line_height_q = 42
        line_height_s = 48

        # Word-wrap text
        def wrap_text(text, font, max_w):
            lines = []
            for paragraph in text.split('\n'):
                words = paragraph.split(' ')
                current_line = ""
                for word in words:
                    test_line = current_line + (" " if current_line else "") + word
                    bbox = font.getbbox(test_line)
                    if bbox[2] - bbox[0] <= max_w:
                        current_line = test_line
                    else:
                        if current_line:
                            lines.append(current_line)
                        current_line = word
                if current_line:
                    lines.append(current_line)
            return lines

        q_lines = wrap_text(question, font_question, max_width)
        s_lines = wrap_text(solution, font_solution, max_width)

        # Generate TTS audio (Indian English)
        full_text = f"Question: {question}. Solution: {solution}"
        tts = gTTS(text=full_text, lang='en', tld='co.in', slow=False)
        tts.save(str(audio_path))

        audio = AudioFileClip(str(audio_path))
        audio_duration = audio.duration

        # Calculate timing
        total_chars = len(question) + len(solution)
        char_time = audio_duration / max(total_chars, 1)

        # Generate frames
        frames = []
        fps = 12

        # Phase 1: Question label appears
        label_frames = int(fps * 0.5)
        for _ in range(label_frames):
            frame = bg.copy()
            draw = ImageDraw.Draw(frame)
            draw.rectangle([x_start - 10, y_start - 10, x_start + max_width + 10, y_start + 30], fill=(255, 248, 240, 230))
            draw.text((x_start, y_start - 5), "Question", fill=(204, 0, 0), font=font_label)
            frames.append(frame)

        # Phase 2: Write question character by character
        y_pos = y_start + 40
        chars_written = 0
        for line_idx, line in enumerate(q_lines):
            for char_idx in range(1, len(line) + 1):
                frame = bg.copy()
                draw = ImageDraw.Draw(frame)
                # Question box background
                q_box_height = y_start + 35 + len(q_lines) * line_height_q + 20
                draw.rectangle([x_start - 10, y_start - 10, x_start + max_width + 10, q_box_height],
                             fill=(255, 248, 240))
                draw.line([x_start - 10, y_start - 10, x_start - 10, q_box_height], fill=(204, 0, 0), width=5)
                draw.text((x_start, y_start - 5), "Question", fill=(204, 0, 0), font=font_label)
                # Draw completed lines
                for prev_idx in range(line_idx):
                    draw.text((x_start, y_start + 35 + prev_idx * line_height_q),
                            q_lines[prev_idx], fill=(17, 17, 17), font=font_question)
                # Draw current partial line
                partial = line[:char_idx]
                draw.text((x_start, y_start + 35 + line_idx * line_height_q),
                        partial, fill=(17, 17, 17), font=font_question)
                chars_written += 1
                # Add frame at writing speed
                if chars_written % max(1, int(fps * char_time * 3)) == 0 or char_idx == len(line):
                    frames.append(frame)

        # Pause after question
        pause_frames = int(fps * 0.8)
        for _ in range(pause_frames):
            frames.append(frames[-1] if frames else bg.copy())

        # Phase 3: Solution label
        sol_y_start = y_start + 35 + len(q_lines) * line_height_q + 40
        for _ in range(int(fps * 0.3)):
            frame = frames[-1].copy() if frames else bg.copy()
            draw = ImageDraw.Draw(frame)
            draw.text((x_start, sol_y_start), "Solution", fill=(68, 68, 68), font=font_label)
            frames.append(frame)

        # Phase 4: Write solution character by character
        for line_idx, line in enumerate(s_lines):
            for char_idx in range(1, len(line) + 1):
                frame = frames[-1].copy() if frames else bg.copy()
                draw = ImageDraw.Draw(frame)
                # Draw completed solution lines
                for prev_idx in range(line_idx):
                    draw.text((x_start, sol_y_start + 35 + prev_idx * line_height_s),
                            s_lines[prev_idx], fill=(204, 0, 0), font=font_solution)
                # Current partial line
                partial = line[:char_idx]
                draw.text((x_start, sol_y_start + 35 + line_idx * line_height_s),
                        partial, fill=(204, 0, 0), font=font_solution)
                chars_written += 1
                if chars_written % max(1, int(fps * char_time * 3)) == 0 or char_idx == len(line):
                    frames.append(frame)

        # Final pause
        for _ in range(int(fps * 1.5)):
            frames.append(frames[-1] if frames else bg.copy())

        if not frames:
            return None

        # Convert PIL frames to numpy arrays
        import numpy as np
        frame_arrays = [np.array(f) for f in frames]

        # Calculate fps to match audio
        actual_fps = max(1, len(frame_arrays) / audio_duration)

        # Create video
        video_clip = ImageSequenceClip(frame_arrays, fps=actual_fps)
        video_clip = video_clip.with_audio(audio)
        video_clip.write_videofile(str(video_path), codec='libx264', audio_codec='aac',
                                   logger=None, threads=2)

        # Cleanup
        if audio_path.exists():
            os.remove(str(audio_path))

        return str(video_path)

    except Exception as e:
        logger.error(f"Video generation error: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


# Include the router
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
