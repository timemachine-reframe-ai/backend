from pydantic import BaseModel


class TokenPayload(BaseModel):
    sub: str
    exp: int

    @property
    def user_id(self) -> int:
        try:
            return int(self.sub)
        except ValueError:
            raise ValueError("Token subject is not a valid integer user id") from None
