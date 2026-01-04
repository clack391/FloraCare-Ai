# FloraCare AI - Phase 4 Specification: UI Polish & Enhancements

## 1. Overview
**Goal**: Elevate the user experience with professional visuals (custom theme), visual intelligence (bounding boxes), and voice interaction.

## 2. Visual Style Guide
*   **Theme**: "Modern Nature"
*   **Colors**:
    *   Primary: `#4CAF50` (Leaf Green)
    *   Background: `#F9F9F9` (Soft White)
    *   Text: `#2E2E2E` (Dark Grey for readability)
*   **Typography**: Sans-serif (Source Sans Pro).

## 3. Services

### 3.1 Annotation Service (`src/services/annotator.py`)
Responsible for drawing bounding boxes on detected issues.

*   **Logic**:
    1.  Receive `image_bytes`.
    2.  Receive `PlantImageAnalysis`.
    3.  Iterate through detected symptoms.
    4.  If symptom has a `bounding_box` [ymin, xmin, ymax, xmax] (normalized 0-1000):
        *   Convert to pixel coordinates.
        *   Draw `Red` rectangle + Label.
    5.  Return annotated image bytes.

*   **Schema Update (`src/models/schemas.py`)**:
    We need to update `PlantImageAnalysis` or add a specific field for objects.
    *   *Approach*: Keep schema simple. Add `objects` list to `PlantImageAnalysis` specifically for detection.
    ```python
    class DetectedObject(BaseModel):
        name: str
        box_2d: List[int] # [ymin, xmin, ymax, xmax]

    class PlantImageAnalysis(BaseModel):
        # ... existing ...
        detected_objects: List[DetectedObject] = [] 
    ```

### 3.2 Voice Service (`src/frontend/components/voice.py`)
Responsible for transcribing user audio.

*   **Logic**:
    1.  User clicks "Record".
    2.  `st.audio_input` captures `.wav`.
    3.  Backend loads `whisper-base`.
    4.  Transcribe -> Return Text.
*   **Fallback**: If `ffmpeg` is missing, show "Voice Unavailable" warning but do not crash.

### 3.4 Interactive Elements
- **Voice Query:** Button to record question. (Existing)
- **Targeted Query (New):** Text input field `st.text_input` placed before "Analyze" button.
- **Direct Answer:** If user provides a query, the result card MUST display a "Direct Answer" section (e.g., `st.info` or `st.success`) addressing the specific question separately from the general diagnosis.

## 4. UI Flow Updates
1.  **Voice Query**: Added to Sidebar or Top Bar.
    *   *Action*: Records audio -> Updates `st.session_state.user_query`.
2.  **Results View**:
    *   **Image**: Now shows the *Annotated* version instead of the raw upload.
    *   **Toggle**: "Show Raw / Show Annotated".

## 5. Verification
*   **Annotation**: Upload `sick_leaf.jpg`. Verify red box appears around the spot.
*   **Voice**: Record "Help me". Verify text input fills with "Help me".
