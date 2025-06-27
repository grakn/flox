from typing import Optional, TypedDict

# State of the grox graph
class GroxState(TypedDict):
    foo: str
    bar: list[str]