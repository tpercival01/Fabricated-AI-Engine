from pydantic import BaseModel, Field, model_validator, ConfigDict
from typing import List, Optional, Literal, Dict

class CrimeScene(BaseModel):
    model_config = ConfigDict(extra="forbid")
    location: str = Field(..., description="Where the crime happened")
    details: str = Field(..., description="Visual description of the scene")
    image_prompt: str = Field(
        ..., description="Prompt for an AI image generator to draw the scene"
    )

class CoreTruth(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str = Field(..., description="Catchy title for the mystery")
    victim_name: str = Field(..., description="Name of the victim")
    time_of_death: str = Field(..., description="Exact time of the murder")
    cause_of_death: str = Field(..., description="Exactly how they were killed")
    crime_scene: CrimeScene
    killer_name: str = Field(..., description="The name of the true killer")
    killer_motive: str = Field(..., description="Why the killer did it")
    killer_alibi: str = Field(..., description="The killer's fake alibi")
    killer_alibi_flaw: str = Field(
        ..., description="The specific, provable lie in the killer's alibi"
    )

class Suspect(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str = Field(..., description="Unique ID, e.g., suspect_1")
    name: str = Field(..., description="Full name of the suspect")
    appearance: str = Field(..., description="Physical traits (hair, height, etc)")
    clothing: str = Field(..., description="EXACTLY what they are wearing")
    motive: str = Field(..., description="Why they might have done it")
    alibi: str = Field(..., description="Excuse for the time of murder")
    relationship_to_victim: str = Field(..., description="How does the suspect know the victim")
    alibi_flaw: Optional[str] = Field(None, description="If guilty, what is the provable lie in their alibi? If innocent, output 'None'.")
    is_guilty: bool = Field(..., description="True if they are the killer")
    image_prompt: str = Field(
        ..., description="Prompt for an AI to draw this suspect in their clothing"
    )

    @model_validator(mode='after')
    def check_guilty_has_flaw(self) -> 'Suspect':
        if self.is_guilty and (self.alibi_flaw is None or self.alibi_flaw.lower() == 'none'):
            raise ValueError("The guilty suspect MUST have a valid alibi_flaw.")

        if not self.is_guilty and self.alibi_flaw is not None and self.alibi_flaw.lower() != 'none':
             raise ValueError("Innocent suspects must have 'None' for their alibi_flaw.")

        return self

class SuspectList(BaseModel):
    model_config = ConfigDict(extra="forbid")
    suspects: List[Suspect] = Field(..., min_length=4, max_length=8)


class Clue(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str = Field(..., description="Unique ID for the clue, e.g., clue_1")
    name: str = Field(..., description="Short name of the clue")
    description: str = Field(..., description="Detailed description")
    points_to_suspect_id: Optional[str] = Field(
        None, description="ID of the suspect this implicates, if any"
    )
    deduction_logic: str = Field(..., description="A sentence explaining exactly how the player is supposed to connect this physical clue to the suspect's profile, motive, or alibi.")
    image_prompt: str = Field(
        ..., description="Prompt for an AI image generator to draw this clue"
    )

class EvidenceBoard(BaseModel):
    model_config = ConfigDict(extra="forbid")
    clues: List[Clue] = Field(..., min_length=4, max_length=10)
    solution_explanation: str = Field(..., description="How the player is supposed to piece this together")

class MysteryCase(BaseModel):
    core_truth: CoreTruth
    suspects: List[Suspect]
    clues: List[Clue]
    solution_explanation: str

class GenerateCaseRequest(BaseModel):
    theme: str = Field(..., description="The main theme of the mystery case")
    difficulty: Literal["easy", "medium", "hard"] = Field(default="medium", description="Difficulty level of the case")

class GuessRequest(BaseModel):
    suspect_id: str

class InterrogationRequest(BaseModel):
    suspect_id: str
    message: str
    chat_history: List[Dict[str,str]]