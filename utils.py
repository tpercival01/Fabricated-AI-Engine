import copy

def sanitize_case_for_frontend(case_data: dict) -> dict:
    case_data_copy = copy.deepcopy(case_data)
    case_data_copy.pop('solution_explanation', None)

    if "core_truth" in case_data_copy:
        case_data_copy["core_truth"].pop("killer_name", None)
        case_data_copy["core_truth"].pop("killer_motive", None)
        case_data_copy["core_truth"].pop("killer_alibi", None)
        case_data_copy["core_truth"].pop("killer_alibi_flaw", None)
    
    if "suspects" in case_data_copy:
        for suspect in case_data_copy["suspects"]:
            suspect.pop("is_guilty", None)
            suspect.pop("alibi_flaw", None)
            
    if "clues" in case_data_copy:
        for clue in case_data_copy["clues"]:
            clue.pop("points_to_suspect_id", None)
            clue.pop("deduction_logic", None)
            
    return case_data_copy
    
