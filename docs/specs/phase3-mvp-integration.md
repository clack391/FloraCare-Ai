# FloraCare AI - Phase 3 Specification: MVP Integration

## 1. Overview
**Goal**: Create a user-friendly interface (Streamlit) communicating with a robust backend (FastAPI) to expose the core Plant Diagnosis logic.
**Scope**: 
-   **Backend**: `src/api/main.py` (FastAPI)
-   **Frontend**: `src/frontend/app.py` (Streamlit)

## 2. Infrastructure Updates

### 2.1 Backend API (`src/api/main.py`)
The backend serves as the bridge between the UI and the `RAGPipeline`.

**Endpoints**:

*   **`POST /diagnose`**
    *   **Input**: `multipart/form-data`
        *   `file`: Uploaded Image File
        *   `location`: String (e.g., "London,UK")
        *   `plant_name`: String (e.g., "Tomato 1")
    *   **Action**:
        1.  Save image to temp directory.
        2.  Invoke `RAGPipeline(location, plant_name)`.
        3.  Return `DiagnosisReport` JSON.
    *   **Response**: `200 OK` + JSON Body (Schema matched to `src.models.schemas.DiagnosisReport`)

*   **`GET /history/{plant_id}`**
    *   **Input**: `plant_id` (UUID)
    *   **Action**: Query `Database.get_recent_history`.
    *   **Response**: `200 OK` + List[String]

*   **`GET /health`**
    *   **Response**: `{"status": "ok"}`

### 2.2 Frontend UI (`src/frontend/app.py`)
Streamlit provides the interactive layer.

**UI Layout**:
1.  **Sidebar**:
    *   Title/Logo
    *   Settings: `Location` (Text Input), `Plant Name` (Text Input)
    *   History View (Future expansion)
2.  **Main Area**:
    *   **Upload Widget**: `st.file_uploader` (Types: jpg, png)
    *   **Analyze Button**: Triggers API call.
    *   **Results Container**:
        *   **Header**: `Diagnosis: {diagnosis_title}`
        *   **Weather Card**: Metric Component (Temp, Humidity).
        *   **Analysis**: Bullet points of symptoms.
        *   **Treatment**: Ordered list.
        *   **Sources**: `st.expander` with retrieved knowledge chunks.

**State Management**:
*   `st.session_state['uploaded_file']`: Persistence across re-runs.
*   `st.session_state['diagnosis_result']`: Store API response to prevent re-fetching on interaction.

## 3. Data Flow
1.  User enters "Mumbai,IN" and uploads "sick_leaf.jpg".
2.  FE sends `POST /diagnose` to BE.
3.  BE saves file -> Pipeline Fetches Weather (Mumbai) -> Pipeline Check History -> Pipeline Generates Diagnosis -> Writes to DB.
4.  BE returns JSON.
5.  FE parses JSON -> Displays "Fungal Infection" + "Mumbai Weather: 30C, Humid".

## 4. Verification
*   **Dry Run**: Manual pass confirming the full loop saves data to `floracare.db`.
