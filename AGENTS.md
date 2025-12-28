# GenAI Gallery Viewer

## Overview
This application is a web-based gallery viewer for user-generated generative AI images created via ComfyUI. It serves as an interface to browse, view, and manage these images.

## Architecture

### Frontend
- **Framework**: Vue.js
- **Styling**: Tailwind CSS
- **Responsibility**: 
  - Communicates with the backend service.
  - Displays a gallery of images.
  - Provides detailed views for individual images.
  - Handles user interactions (filtering, sorting, etc.).

### Backend
- **Language**: Python
- **Framework**: FastAPI
- **Database**: SQLite
- **Responsibility**:
  - API endpoints for listing and retrieving images.
  - Metadata management stored in SQLite.
  - Serving image files (or proxying/referencing them).
  - Integration with ComfyUI outputs (watching directories or receiving webhooks - TBD based on ComfyUI setup).

## Purpose
To provide a seamless and aesthetically pleasing experience for viewing generative AI artwork, abstracting the raw file management often associated with tools like ComfyUI.
