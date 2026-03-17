import copy

def sanitize_case_for_frontend(case_data: dict) -> dict:
    case_data_copy = copy.deepcopy(case_data)
    case_data_copy.pop('core_truth', None)
    case_data_copy.pop('solution_explanation', None)

    for suspect in case_data_copy["suspects"]:
        suspect.pop('is_guilty', None)
        suspect.pop('alibi_flaw', None)
    
    return case_data_copy
    
