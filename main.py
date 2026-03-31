from fastapi import FastAPI, HTTPException, Request
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from generator import generate_new_case, judge_generator
from models import GenerateCaseRequest, AccuseRequest, ActionRequest
from database import supabase
from utils import sanitize_case_for_frontend
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
  return {"status": "online", "game": "Infinite Detective"}

@app.get("/api/cases/{case_id}")
def get_case_endpoint(case_id: str):
    response = supabase.table("cases").select("*").eq("id", case_id).execute()
    
    if not response.data:
        raise HTTPException(status_code=404, detail="Case not found")
        
    raw_case_data = response.data[0]["case_data"]
    theme = response.data[0]["theme"]
    
    safe_case = sanitize_case_for_frontend(raw_case_data)
    
    return {
        "case_id": case_id,
        "theme": theme,
        "case_data": safe_case
    }

@app.post("/api/cases/generate")
@limiter.limit("5/hour")
def generate_case_endpoint(request: Request, payload: GenerateCaseRequest):
  print("Successfully accessing generate endpoint")
  try:
    json_case = generate_new_case(payload.theme, payload.difficulty)
    json_case_dict = json_case.model_dump()

    payload_obj = {
      "theme": payload.theme,
      "difficulty": payload.difficulty,
      "case_data": json_case_dict,
      "is_solved": False
    }
    response = supabase.table("cases").insert(payload_obj).execute()
    sanitized = sanitize_case_for_frontend(json_case_dict)
    return {"case_id": response.data[0]["id"], "case_data": sanitized}
  except Exception as e:
    print(e)
  
@app.post("/api/cases/{case_id}/accuse")
@limiter.limit("10/hour")
def accuse_endpoint(case_id: str, request: Request, payload: AccuseRequest):

  response = supabase.table("cases").select("case_data, theme").eq("id", case_id).execute()

  if not response.data:
    raise HTTPException(status_code=404, detail="Case not found")
  
  case_data = response.data[0]["case_data"]
  case_theme = response.data[0]["theme"]
  core_truth = case_data["core_truth"]
  solution_explanation = case_data["solution_explanation"]
  clues = case_data["clues"]

  players_clues = []

  clue_lookup = {c["id"]: c["description"] for c in clues}
  
  for clue_id in payload.clue_ids:
    players_clues.append(clue_lookup[clue_id])

  players_clues_string = " ".join(players_clues)

  accused_suspect_name = "Unknown"
  for suspect in case_data["suspects"]:
      if suspect["id"] == payload.suspect_id:
          accused_suspect_name = suspect["name"]
          break

  prompt_dict = {
    "case_data": case_data,
    "case_theme": case_theme,
    "core_truth": core_truth,
    "solution_explanation": solution_explanation,
    "game_clues": clues,
    "players_clues": players_clues_string,
    "player_theory": payload.player_theory,
    "player_suspect_id": payload.suspect_id,
    "accused_suspect_name": accused_suspect_name
  }
  judge_response = judge_generator(prompt_dict)
  return {
     "is_correct": judge_response.is_correct,
     "feedback": judge_response.feedback,
     "actual_killer": case_data["core_truth"]["killer_name"],
     "killer_motive": case_data["core_truth"]["killer_motive"],
     "alibi_flaw": case_data["core_truth"]["killer_alibi_flaw"],
     "solution_explanation": case_data["solution_explanation"]
  }

@app.post("/api/cases/{case_id}/interrogate")
def interrogate_endpoint():
  pass

@app.post("/api/v2/session/start")
def start_session():
  response = supabase.table("daily_cases").select("target_date, victim_data, full_graph, solution").eq("id", "30404973-9634-4935-bc08-7e248d60eb94").execute()
  session_obj = {
     "case_id": "30404973-9634-4935-bc08-7e248d60eb94",
     "player_id": "1",
     "current_ap": 20
  }

  session_insert = supabase.table("sessions").insert(session_obj).execute()
  new_session_id = session_insert.data[0]["id"]

  unlocked_obj = {
     "session_id": new_session_id,
     "node_id": "n2"
  }

  unlocked_insert = supabase.table("unlocked_nodes").insert(unlocked_obj).execute()
  
  final_response = {
    "session_id": new_session_id,
    "current_ap": 20,
    "victim": {
      "name": response.data[0]["victim_data"]["name"],
      "description": response.data[0]["victim_data"]["description"]
    },
    "unlocked_nodes": [unlocked_insert.data[0]["node_id"]]
  }

  return final_response

@app.post("/api/v2/session/action")
def use_action(actionRequest: ActionRequest):

  temp_session_id = actionRequest.session_id

  response = supabase.table("sessions").select("*").eq("id", temp_session_id).execute()

  if not response.data:
    raise HTTPException(status_code=404, detail="Session not found")
     
  session_obj = response.data[0]
  print(session_obj)

  if session_obj["current_ap"] < 1:
    raise HTTPException(status_code=403, detail="Insufficient Action Points")

  new_ap = session_obj["current_ap"] - 1

  supabase.table("sessions").update({"current_ap": new_ap}).eq("id", temp_session_id).execute()

  supabase.table("unlocked_nodes").insert({"session_id": temp_session_id, "node_id": "n3"}).execute()

  return {"current_ap": new_ap, "unlocked_node": "n3"}