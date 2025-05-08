from typing import TypedDict, Optional, Literal

class TimeData(TypedDict):
    time_text: str
    type_time: Optional[Literal["t", "T", "d", "D", "F", "R"]]