from fastapi import FastAPI, HTTPException
from generator import generate_new_case
from models import GenerateCaseRequest, GuessRequest
from database import supabase
from utils import sanitize_case_for_frontend

app = FastAPI()

@app.get("/")
async def root():
  return {"status": "online", "game": "Infinite Detective"}

@app.post("/api/cases/generate")
def generate_case_endpoint(request: GenerateCaseRequest):
  print("Successfully accessing generate endpoint")
  try:
    json_case = generate_new_case(request.theme, request.difficulty)
    json_case_dict = json_case.model_dump()

    payload = {
      "theme": request.theme,
      "difficulty": request.difficulty,
      "case_data": json_case_dict,
      "is_solved": False
    }
    response = supabase.table("cases").insert(payload).execute()
    print(json_case_dict)
    sanitized = sanitize_case_for_frontend(json_case_dict)

    return {"case_id": response.data[0]["id"], "case_data": sanitized}
  except Exception as e:
    print(e)
  
@app.post("/api/cases/{case_id}/guess")
def guess_endpoint(case_id: str, request: GuessRequest):
  print(f"checking case: {case_id}")
  print(f"player guessed: {request.suspect_id}")

  response = supabase.table("cases").select("case_data").eq("id", case_id).execute()

  if not response.data:
    raise HTTPException(status_code=404, detail="Case not found")
  
  case_data = response.data[0]["case_data"]

  for suspect in case_data["suspects"]:
    if suspect["id"] == request.suspect_id:
      if suspect["is_guilty"]:
        return {"correct": True, "message": "You caught the killer!"}
      else:
        return {"correct": False, "message": "You accused the wrong person!"}
      

@app.post("/api/cases/{case_id}/interrogate")
def interrogate_endpoint():
  pass