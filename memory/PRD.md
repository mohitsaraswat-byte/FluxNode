# AI Educational Content Creator Dashboard - PRD

## Problem Statement
Building a comprehensive AI-powered educational content creation dashboard with multiple modules for creating digital books, comic scripts, animated videos, and AI video prompts. Physics Wallah (PW) branded content creation platform.

## Architecture
- **Frontend**: Vanilla HTML5 + Tailwind CSS (CDN) + Vanilla JavaScript at `/dashboard.html`
- **Backend**: Python FastAPI + MongoDB
- **AI Integrations**: GPT-5.2 (Emergent LLM Key), Gemini Nano Banana (Emergent LLM Key), gTTS (free Indian TTS)
- **Video**: MoviePy for whiteboard-style video rendering

## User Personas
- Educational content creators (teachers, tutors)
- Physics Wallah content team
- Independent educators creating digital learning materials

## Core Requirements
1. 4-tab sidebar navigation with persistent layout
2. LaTeX to HTML dual-pane editor (Module 1)
3. AI-powered comic script generation with agent modes (Module 2)
4. AI image generation for comic panels (Module 2)
5. Whiteboard-style video generation with handwritten animation + Indian voice (Module 3)
6. 7-layer AI video prompt builder (Module 4)
7. Shared content library with publish/browse/copy (Module 5)

## What's Been Implemented (April 16, 2026)

### Phase 1 - MVP
- Full 5-module dashboard with sidebar navigation
- Module 1: Digital Books (LaTeX editor + HTML preview)
- Module 2: Comic Scripts (GPT-5.2 generation, 3 agent modes)
- Module 3: Video Solutions (MoviePy + gTTS, placeholder)
- Module 4: AI Video Prompts (7-layer form)
- Module 5: Shared Library (publish, browse, filter, copy)

### Phase 2 - Enhancements
- Gemini Nano Banana image generation for comic panels
- Agent mode switching: Default GPT-5.2, PW Comics Script Writer, Pixar Scene Designer
- MoviePy video rendering with PW background, Caveat handwriting font, Indian gTTS voice
- Simple collaboration: shared library with view/copy functionality
- All integrations tested and working (100% test pass rate)

## Prioritized Backlog

### P0 (Critical)
- [x] All 5 modules functional
- [x] GPT-5.2 comic generation working
- [x] Gemini Nano Banana image generation
- [x] MoviePy video rendering
- [x] Shared library collaboration

### P1 (Important)
- [ ] Integrate existing Cloudflare-hosted Digital Books builder into Module 1
- [ ] Improve video rendering quality (smoother character-by-character animation)
- [ ] Add solution step breakdown in video generation (numbered steps)
- [ ] Multiple panel image generation in batch
- [ ] User authentication for the library

### P2 (Nice to Have)
- [ ] History/saved items per module
- [ ] Export comic scripts to PDF
- [ ] Video templates (different backgrounds)
- [ ] Real-time collaboration editing
- [ ] Analytics dashboard for content usage
