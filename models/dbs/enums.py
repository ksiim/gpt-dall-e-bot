from enum import Enum, EnumMeta
from itertools import chain

class ChatModelEnum(Enum):
    GPT_4O = "GPT-4o"
    GPT_4O_MINI = "GPT-4o-mini"

class ImageModelEnum(Enum):
    DALL_E_3 = "Dall-E-3"
    
class TypeOfRequestEnum(Enum):
    CHAT = "chat"
    IMAGE = "image"
    
class ModelsEnumMeta(EnumMeta):
    def __new__(metacls, name, bases, classdict):
        combined_enums = {}
        for base in bases:
            combined_enums.update(base.__members__)
        for key, value in combined_enums.items():
            classdict[key] = value
        return super().__new__(metacls, name, bases, classdict)

class ModelsEnum(Enum):
    _ignore_ = 'member cls'
    cls = vars()
    for member in chain(list(ChatModelEnum), list(ImageModelEnum)):
        cls[member.name] = member.value

async def get_all_enum_values(enum: Enum):
    return [e.value for e in enum]

