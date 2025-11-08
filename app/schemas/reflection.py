from typing import List, Literal

from pydantic import BaseModel, Field


class ReflectionSummaryRequest(BaseModel):
    what_happened: str = Field(..., alias="whatHappened")
    emotions: List[str]
    what_you_did: str = Field(..., alias="whatYouDid")
    desired_outcome: str = Field(..., alias="howYouWishItHadGone")

    def to_chain_payload(self) -> dict:
        return {
            "what_happened": self.what_happened,
            "emotions": self.emotions,
            "what_you_did": self.what_you_did,
            "desired_outcome": self.desired_outcome,
        }


class ReflectionSummaryResponse(BaseModel):
    summary: str
    keyInsights: List[str] = Field(default_factory=list)
    suggestedPhrases: List[str] = Field(default_factory=list)


class ReflectionChatMessage(BaseModel):
    sender: Literal["user", "ai"]
    text: str


class ReflectionChatRequest(ReflectionSummaryRequest):
    persona_name: str = Field(..., alias="personaName")
    persona_tone: str = Field(..., alias="personaTone")
    persona_personality: str = Field(..., alias="personaPersonality")
    conversation: List[ReflectionChatMessage] = Field(default_factory=list)
    message: str

    def to_chat_payload(self) -> dict:
        payload = self.to_chain_payload()
        payload.update(
            {
                "persona_name": self.persona_name,
                "persona_tone": self.persona_tone,
                "persona_personality": self.persona_personality,
                "conversation": [msg.model_dump() for msg in self.conversation],
                "message": self.message,
            }
        )
        return payload


class ReflectionChatResponse(BaseModel):
    reply: str
