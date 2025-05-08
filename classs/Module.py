import asyncio
import functools
import inspect
import textwrap

from .Context import Context
from .FClient import FClient
from concurrent.futures import ThreadPoolExecutor
from typing import Literal, get_args, Any, Tuple, get_origin, Dict, Optional, Union

__all__ = ["Module", "tool", "FunctionMeta"]

pool = ThreadPoolExecutor()


def is_typeddict(cls):
    return isinstance(cls, type) and issubclass(cls, dict) and hasattr(cls, '__annotations__') and hasattr(cls,
                                                                                                           '__total__')
def is_optional_type(type_hint):
    return get_origin(type_hint) is Union and type(None) in get_args(type_hint) and len(get_args(type_hint)) == 2

class FunctionMeta:
    master_class = None

    def __init__(self, func: callable, decs: str | None, descriptions: Dict[str, str]):
        self.func = func
        self.name = func.__name__
        if func.__doc__ is None and decs is None:
            raise ValueError("Function docstring and decs pram is not defined")
        self.description = textwrap.dedent(func.__doc__) if func.__doc__ is not None else textwrap.dedent(decs)
        sig = inspect.signature(func)
        clean_prams = dict(sig.parameters)
        self.parameters = {
            i.name: self._transform_type_to_json_type(i.annotation) for i in list(clean_prams.values())[2:]
        }
        self.required = self._gen_required(list(clean_prams.items())[2:])
        for key, value in self.parameters.items():
            if key in descriptions:
                value["description"] = descriptions[key]

    def _gen_required(self, kv):
        required = []
        for k, v in kv:
            if type(v) is inspect.Parameter:
                if v.default is inspect.Parameter.empty and not is_optional_type(v.annotation):
                    required.append(k)
            else:
                if not is_optional_type(v):
                    required.append(k)
        return required

    def to_dict(self):
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": self.parameters,
                    "required": self.required,
                    "additionalProperties": False
                }
            }
        }

    def _get_literal_type(self, args: Tuple[Any, ...]):
        main_type = type(args[0])
        for arg in args:
            if type(arg) != main_type:
                raise TypeError(
                    f"Literal type must be the same type, but got {type(arg)} and {main_type}"
                )
        return self._transform_type_to_json_type(main_type)["type"]

    def _transform_type_to_json_type(self, type_class: Any):
        type_schema = {}
        if type_class is str:
            type_schema["type"] = "string"
        elif type_class is int or type_class is float:
            type_schema["type"] = "integer"
        elif type_class is bool:
            type_schema["type"] = "boolean"
        elif get_origin(type_class) is Literal:
            type_schema["enum"] = list(get_args(type_class))
            type_schema["type"] = self._get_literal_type(type_schema["enum"])
        elif get_origin(type_class) is list:
            if not get_args(type_class):
                raise TypeError("Use typing.List[type] instead of typing.List without type")
            type_schema["type"] = "array"
            type_schema["items"] = self._transform_type_to_json_type(type_class.__args__[0])
        elif is_optional_type(type_class):
            type_real = get_args(type_class)[0]
            type_schema = self._transform_type_to_json_type(type_real)
        elif is_typeddict(type_class):
            type_schema["type"] = "object"
            type_schema["properties"] = {}
            for key, value in type_class.__annotations__.items():
                type_schema["properties"][key] = self._transform_type_to_json_type(value)
            type_schema["required"] = self._gen_required(type_class.__annotations__.items())
        elif type_class is None or type_class is type(None):
            type_schema["type"] = "null"
        else:
            raise TypeError(
                f"Unsupported type: {type_class} support (str, int, float, bool, typing.List[type], typing.TypedDict, typing.Optional[type], None)")
        return type_schema

    def set_master_class(self, master_class):
        self.master_class = master_class

    async def call(self, ctx: Context, *args, **kwargs):
        if self.master_class is not None:
            args = (self.master_class, ctx) + args
        else:
            args = (ctx,) + args
        fn = self.func
        if not inspect.iscoroutinefunction(fn):
            fn = self._call_sync
        return await fn(*args, **kwargs)

    async def _call_sync(self, *args, **kwargs):
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(pool, functools.partial(self.func, *args, **kwargs))


def tool(decs: str=None, **arg_descriptions):
    def decorator(func):
        func_meta = FunctionMeta(func, decs, arg_descriptions)
        return func_meta

    return decorator

class Module:
    functions: Dict[str, FunctionMeta] = {}
    client: FClient

    def __init__(self, client: FClient):
        self.client = client
        for name in dir(self):
            pram: FunctionMeta = getattr(self, name)
            if not isinstance(pram, FunctionMeta):
                continue
            if pram.name in self.functions:
                raise ValueError(f"Function name \"{pram.name}\" is already defined")
            self.functions[pram.name] = pram
            pram.set_master_class(self)