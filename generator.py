from pydantic import ValidationError
import os
import json
from openai import OpenAI
import time
from models import CoreTruth, SuspectList, EvidenceBoard, MysteryCase, JudgeResponse
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1",
)

def generate_new_case(theme: str, difficulty: str = "medium", max_retries: int = 5):
    core_truth_schema_json = json.dumps(CoreTruth.model_json_schema(), indent=2)
    suspect_schema_json = json.dumps(SuspectList.model_json_schema(), indent=2)
    evidence_schema_json = json.dumps(EvidenceBoard.model_json_schema(), indent=2)

    core_truth_rules = ""
    suspects_rules = ""
    evidence_rules = ""

    if difficulty == "easy":
        core_truth_rules = "DIFFICULTY: EASY. The killer's alibi flaw must be a glaring, obvious physical contradiction (e.g., claiming to be in the rain but being dry)."
        suspects_rules = "DIFFICULTY: EASY. You MUST generate exactly 4 suspects. Innocent suspects should have basic motives."
        evidence_rules = "DIFFICULTY: EASY. You MUST generate 4 to 5 clues. Make the clues highly obvious. Use direct physical evidence like dropped nametags, matching torn fabric, or clear camera footage."
        
    elif difficulty == "medium":
        core_truth_rules = "DIFFICULTY: MEDIUM. The alibi flaw must rely on timeline overlaps or circumstantial events. It should require basic deduction to spot, not just a single dropped item."
        suspects_rules = "DIFFICULTY: MEDIUM. You MUST generate 5 to 6 suspects. Innocent suspects must have believable motives and solid alibis."
        evidence_rules = "DIFFICULTY: MEDIUM. You MUST generate 6 to 7 clues. Do not use direct, obvious physical evidence. Clues should rely on timelines, witness testimonies, and circumstantial motives."
        
    else:
        core_truth_rules = "DIFFICULTY: HARD. The killer's alibi flaw MUST be a complex temporal or spatial contradiction. It must require cross-referencing two completely separate, mundane facts to disprove. No single-point failures."
        suspects_rules = "DIFFICULTY: HARD. You MUST generate 6 to 8 suspects. Provide highly compelling red herring motives for multiple innocent suspects to dilute the suspect pool."
        evidence_rules = "DIFFICULTY: HARD. You MUST generate 8 to 10 clues. RULE: DO NOT put the guilty suspect's name in the physical clues that break their alibi. RULE: At least two innocent suspects must have physical clues pointing to them. RULE: Never create a single clue that completely destroys the killer's alibi; force the player to combine two separate clues."


    ## STEP 1 - Core truth
    core_truth_prompt = f"""
        You are an expert mystery writer and game designer.
        Generate the FOUNDATION of a true crime mystery in JSON format.

        Theme: {theme}
        Difficulty Rules: {core_truth_rules}

        CRITICAL JSON RULES:
        1. Output ONLY valid JSON matching the provided schema.
        2. Do NOT wrap the JSON in markdown blocks.

        GAME DESIGN RULES:
        1. REALISM: The cause_of_death must be realistic. No sci-fi weapons or magic.
        2. THE FLAW: The killer_alibi_flaw is the most important field. It must be a physical or temporal contradiction that can be proven by a detective. 
        3. DIFFICULTY CONTEXT: If the difficulty is Easy, the flaw should be obvious (e.g., claiming to be in the rain but being dry). If Hard, the flaw must be a highly specific timeline or circumstantial overlap.

        SCHEMA:
        {core_truth_schema_json}
    """
    print("generating core truth")
    core_truth_generated = api_call(core_truth_prompt, CoreTruth)
    if not core_truth_generated:
        return None
    print("done - core truth")


    ## STEP 2 - Suspects

    suspects_prompt = f"""
        You are an expert mystery writer and game designer.
        Generate the CAST OF SUSPECTS for a true crime mystery in JSON format.

        Theme: {theme}
        Difficulty Rules: {suspects_rules}

        THE ESTABLISHED TRUTH (DO NOT DEVIATE FROM THIS):
        {core_truth_generated.model_dump_json()}

        CRITICAL RULES FOR SUSPECTS:
        1. You MUST generate the number of suspects depicted in the difficulty.
        2. Exactly ONE suspect must be the killer. Their name, motive, and alibi MUST perfectly match the details provided in THE ESTABLISHED TRUTH.
        3. The killer's 'alibi_flaw' must explicitly state the flaw defined in the truth.
        4. All OTHER suspects are innocent. They must have strong motives (red herrings) but their 'alibi_flaw' MUST be "None". 
        5. Innocent suspects must have airtight alibis. Do not make them look guilty through sloppy timelines.
        6. You must stick to whatever the theme is when creating the suspects, clues, clothing and scene.


        SCHEMA:
        {suspect_schema_json}
    """

    print("generating suspects")
    suspects_generated = api_call(suspects_prompt, SuspectList)
    if not suspects_generated:
        return None
    print("done - suspects")


    ## STEP 3 - Evidence

    evidence_prompt = f"""
        You are an expert mystery writer and game designer.
        Generate the EVIDENCE BOARD (Clues and Solution) for a true crime mystery in JSON format.

        Theme: {theme}
        Difficulty Rules: {evidence_rules}

        THE ESTABLISHED TRUTH:
        {core_truth_generated.model_dump_json()}

        THE SUSPECTS:
        {suspects_generated.model_dump_json()}

        CRITICAL RULES FOR EVIDENCE:
        1. You MUST generate the number of clues depicted by the difficulty.
        2. You must include at least one clue that proves the killer's 'alibi_flaw' from the truth.
        3. You must include at least one clue about the murder weapon or cause of death.
        4. You must include clues that point logically to the innocent suspects' motives (red herrings) to misdirect the player.
        5. NO INSTANT WINS. Clues must be circumstantial physical evidence, timeline overlaps, or witness testimonies. Do not generate a video or a confession letter.
        6. The 'deduction_logic' must explain how the player connects the clue to a suspect without assuming they already know who the killer is.
        7. The 'solution_explanation' must explicitly explain how the player uses the specific clues to bust the killer's alibi.
        8. You must stick to whatever the theme is when creating the suspects, clues, clothing and scene.

        SCHEMA:
        {evidence_schema_json}
    """

    print("generating evidence")
    evidence_generated = api_call(evidence_prompt, EvidenceBoard)
    if not evidence_generated:
        return None
    print("done - evidence")

    final_case = MysteryCase(
        core_truth=core_truth_generated,
        suspects=suspects_generated.suspects,
        clues=evidence_generated.clues,
        solution_explanation=evidence_generated.solution_explanation
    )
    return final_case

def judge_generator(prompt_dict):

    core_truth = prompt_dict["core_truth"]
    case_data = prompt_dict["case_data"]
    case_theme = prompt_dict["case_theme"]
    solution_explanation = prompt_dict["solution_explanation"]
    clues = prompt_dict["game_clues"]
    players_clues = prompt_dict["players_clues"]
    player_theory = prompt_dict["player_theory"]
    player_suspect_id = prompt_dict["player_suspect_id"]
    accused_suspect_name = prompt_dict["accused_suspect_name"]
    
    judge_prompt = f"""
        You are an authority figure, judge, or law enforcement officer appropriate for this era and setting: {case_theme}. 
        A detective has submitted their final accusation for a murder case. You must grade their accusation based STRICTLY on the absolute truth of the case.

        ABSOLUTE TRUTH:
        The true killer is {core_truth['killer_name']}.
        The real solution logic: {solution_explanation}

        THE DETECTIVE'S ACCUSATION:
        Accused Suspect Name: {accused_suspect_name}
        Evidence Provided: {players_clues}
        Detective's Theory: {player_theory}

        RULES FOR GRADING:
        1. If 'Accused Suspect Name' ({accused_suspect_name}) does NOT exactly match the true killer ({core_truth['killer_name']}), the player fails automatically. 'is_correct' MUST be false. 
        2. If they accused the right person, BUT the 'Evidence Provided' does not prove the solution, or their theory is nonsense, they fail due to lack of evidence. 'is_correct' MUST be false.
        3. If they accused the right person AND provided the correct evidence/theory, 'is_correct' MUST be true.
        4. Write your 'feedback' directly to the detective IN CHARACTER based on the setting ({case_theme}). If they accused the wrong person, reprimand them harshly for almost ruining an innocent person's life.
        5. Output ONLY valid JSON matching this schema: {json.dumps(JudgeResponse.model_json_schema())}
        """
    
    print("Asking the AI Judge...")
    try:
      response = client.chat.completions.create(
          model="llama-3.3-70b-versatile",
          messages=[
              {"role": "system", "content": judge_prompt},
              {"role": "user", "content": "Grade the accusation now."}
          ],
          temperature=0.7,
          response_format={"type": "json_object"}
      )
      
      raw_json_string = response.choices[0].message.content
      
      raw_json_string = raw_json_string.strip("`").removeprefix("json").strip()
      
      judge_decision = JudgeResponse.model_validate_json(raw_json_string)
          
      return judge_decision

    except Exception as e:
        print(f"Judge Error: {e}")

def api_call(prompt: str, model_class, max_retries: int = 5):
    for attempt in range(max_retries):
        print(f"Attempt {attempt + 1} of {max_retries}: Asking Groq...")

        try:
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": "Generate the mystery JSON now."}
                ],
                response_format={"type": "json_object"}
            )

            raw_json_string = response.choices[0].message.content

            raw_json_string = raw_json_string.strip("`").removeprefix("json").strip()

            validated_case = model_class.model_validate_json(raw_json_string)
            print("Success! Valid JSON generated.")
            return validated_case

        except ValidationError as e:
            print(f"Validation failed on attempt {attempt + 1}.")
            print("The AI missed these constraints:")
            for err in e.errors():
                print(f"- Location: {err.get('loc')}, Error: {err.get('msg')}")

            if attempt == max_retries - 1:
                print("Max retries reached. The AI is failing to format correctly.")
                return None

            time.sleep(1)

        except Exception as e:
            print(f"A general error occurred: {e}")
            return None
