from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
import json
import httpx
import base64

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="../frontend"), name="static")

@app.get("/")
def root():
    return FileResponse("../frontend/index.html")

def pdf_to_base64_images(contents: bytes) -> list:
    import fitz
    doc = fitz.open(stream=contents, filetype="pdf")
    images = []
    for i, page in enumerate(doc):
        if i >= 2:
            break
        mat = fitz.Matrix(2.0, 2.0)
        pix = page.get_pixmap(matrix=mat)
        png_bytes = pix.tobytes("png")
        images.append(base64.standard_b64encode(png_bytes).decode("utf-8"))
    doc.close()
    return images

MEDICAL_PROMPT = """You are MedRisk AI, an expert clinical report analyser trained on medical literature, 
laboratory reference standards, and diagnostic guidelines (including WHO, AHA, ACC, and ICMR standards).

Your task is to analyse the uploaded medical/lab report image and return a structured JSON risk assessment.

CLINICAL ANALYSIS GUIDELINES:
- Use established medical reference ranges (e.g. AHA for cardiac, WHO for blood counts, ADA for glucose)
- For echo reports: assess EF, wall motion, valve function, chamber dimensions, Doppler findings
- For blood tests: assess CBC, lipid panel, liver/kidney function, thyroid, HbA1c, glucose etc.
- For any report: identify critical values that need urgent attention
- Consider patient age/sex if mentioned in the report when assessing risk
- Flag borderline values that may become clinically significant
- Use ICD-10 aligned terminology where appropriate
- Distinguish between acute risk (needs urgent care) vs chronic risk (needs monitoring)

RISK LEVELS:
- Low: All values within normal limits, no significant abnormalities
- Medium: 1-2 borderline/mildly abnormal values, or mild findings needing monitoring
- High: Critical values, significantly abnormal results, or findings requiring urgent medical attention

Return ONLY this JSON structure, no markdown, no backticks, no extra text:
{
  "risk_level": "Low",
  "risk_summary": "One clinically precise sentence summarising the overall risk and key finding",
  "patient_info": {
    "name": "patient name if visible or Unknown",
    "age": "age if visible or Unknown",
    "sex": "Male/Female if visible or Unknown",
    "report_type": "type of report e.g. Echo Cardiogram, CBC, Lipid Panel"
  },
  "findings": [
    {
      "test": "Exact test/parameter name",
      "value": "measured value with unit",
      "normal_range": "reference range with unit",
      "status": "Normal",
      "clinical_significance": "brief clinical meaning of this value",
      "note": "1 sentence patient-friendly explanation"
    }
  ],
  "critical_flags": ["any values needing urgent attention, empty array if none"],
  "explanation": "3-4 sentence clinical summary: what the report shows overall, what the key findings mean together, and the clinical picture for this patient",
  "next_steps": [
    "Specific, actionable step 1",
    "Specific, actionable step 2",
    "Specific, actionable step 3"
  ],
  "follow_up_timeline": "When should the patient follow up e.g. Within 1 week, In 3 months, Annual checkup"
}

status must be exactly one of: Normal, High, Low, Borderline, Critical
risk_level must be exactly one of: Low, Medium, High
Return ONLY valid JSON."""

@app.post("/analyse")
async def analyse_report(file: UploadFile = File(...)):
    allowed_types = ["application/pdf", "image/jpeg", "image/png", "image/jpg"]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Only PDF, JPG, and PNG files are supported.")

    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="GROQ_API_KEY not set.")

    contents = await file.read()
    is_pdf = file.content_type == "application/pdf"

    image_b64_list = []
    if is_pdf:
        try:
            image_b64_list = pdf_to_base64_images(contents)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Could not process PDF: {str(e)}")
        if not image_b64_list:
            raise HTTPException(status_code=400, detail="PDF appears to be empty.")
    else:
        image_b64_list = [base64.standard_b64encode(contents).decode("utf-8")]

    content_parts = []
    mime = "image/png" if is_pdf else file.content_type
    for img_b64 in image_b64_list:
        content_parts.append({
            "type": "image_url",
            "image_url": {"url": f"data:{mime};base64,{img_b64}"}
        })
    content_parts.append({"type": "text", "text": MEDICAL_PROMPT})

    payload = {
        "model": "meta-llama/llama-4-scout-17b-16e-instruct",
        "messages": [{"role": "user", "content": content_parts}],
        "temperature": 0.1,
        "max_tokens": 2000
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json=payload
        )

    if response.status_code != 200:
        raise HTTPException(status_code=500, detail=f"Groq API error: {response.text}")

    data = response.json()
    try:
        raw = data["choices"][0]["message"]["content"]
        clean = raw.replace("```json", "").replace("```", "").strip()
        result = json.loads(clean)
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to parse response. Please try again.")

    return result
