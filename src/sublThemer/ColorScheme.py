from __future__ import annotations

import os
import re
from typing import Iterable
from typing import NamedTuple
from typing import Optional
from typing import Sequence
from typing import TypeVar
from typing import Union

import json5 as json

DetailValue = Union[str, list[str]]
TaggedDetailValue = Union[DetailValue, dict[str, DetailValue]]


class ColorSchemeDetail(NamedTuple):
    """Container for tagged variations. Use "default" if implementing an optional, permutation type setting, 'light' and 'dark' are typical keys, or don't use a mapping and just give a universal string response."""

    value: TaggedDetailValue

    @classmethod
    def fromObj(cls, obj: TaggedDetailValue):
        return cls(value=obj)

    def tag(self, tag: str) -> Optional[str]:
        if isinstance(self.value, str):
            return self.value
        if isinstance(self.value, list):
            return self.value
        for testValue in tag, "default":
            if testValue in self.value:
                return self.value[testValue]
        return None

    def tags(self, tags: Iterable[str]) -> Optional[str]:
        for tag in tags:
            if ret := self.tag(tag):
                return ret
        return None

    def __repr__(self) -> str:
        return "ColorSchemeDetail(" + value + ")"


class ColorSchemeDetailDict(dict[str, ColorSchemeDetail]):
    @classmethod
    def fromDict(cls, inp: dict):
        return cls({k: ColorSchemeDetail.fromObj(v) for k, v in inp.items()})

    def tags(self, tags: Iterable[str]) -> dict:
        ret = {}
        for tag in tags:
            for k, v in self.items():
                try:
                    ret[k] = v.tags(tags)
                except Exception as e:
                    breakpoint()
        return ret


# @bob
class ColorSchemeRule(NamedTuple):
    scope: str
    name: str

    foreground: Optional[ColorSchemeDetail]
    background: Optional[ColorSchemeDetail]
    selection_foreground: Optional[ColorSchemeDetail]
    foreground_adjust: Optional[ColorSchemeDetail]
    font_style: Optional[ColorSchemeDetail]

    AttributeList = [
        "foreground",
        "background",
        "foreground_adjust",
        "selection_foreground",
        "font_style",
    ]

    @classmethod
    def fromObj(cls, obj: dict):
        initDict = {}

        for attribute in ColorSchemeRule.AttributeList:
            if value := obj.get(attribute):
                initDict[attribute] = ColorSchemeDetail(value)

        return cls(
            scope=obj["scope"],
            name=obj.get("name", ""),
            foreground=initDict.get("foreground"),
            background=initDict.get("background"),
            foreground_adjust=initDict.get("foreground_adjust"),
            selection_foreground=initDict.get("selection_foreground"),
            font_style=initDict.get("font_style"),
        )

    def asDict(self):
        return dict(filter(lambda r: r[1], self.__dict__.items()))

    def tags(self, tags: Iterable[str]) -> Optional[dict]:
        ret = {}
        for attribute in ColorSchemeRule.AttributeList:
            if value := getattr(self, attribute):
                ret[attribute] = value.tags(tags)
        if 0 < len(ret.keys()):
            ret["scope"] = self.scope
            if self.name:
                ret["name"] = self.name
            return ret
        return None


class ColorSchemeConfig(NamedTuple):
    name: str
    author: str
    desc: str

    replacements: ColorSchemeDetailDict

    variables: ColorSchemeDetailDict
    globals: ColorSchemeDetailDict
    rules: list[ColorSchemeRule]

    @classmethod
    def fromObj(cls, obj: dict):
        return cls(
            name=obj.get("name", "Unnamed ColorScheme"),
            author=obj.get("author", "Unkown Author"),
            desc=obj.get("desc", "This is a UI Color Scheme"),
            replacements=ColorSchemeDetailDict.fromDict(
                obj.get("replacements", {}),
            ),
            variables=ColorSchemeDetailDict.fromDict(obj.get("variables", {})),
            globals=ColorSchemeDetailDict.fromDict(obj.get("globals", {})),
            rules=[
                ColorSchemeRule.fromObj(rule) for rule in obj.get("rules", [])
            ],
        )

    @classmethod
    def fromFile(cls, filePath):
        assert os.path.isfile(filePath), f"Path '{filePath}' is not a file."
        with open(filePath, "r") as file:
            dataObj = json.loads(file.read())

        return cls.fromObj(dataObj)

    def tags(self, tags: Iterable[str]) -> dict:
        ret: dict = {
            "name": f"{self.name} - {', '.join(tags)}",
            "author": self.author,
            "desc": self.desc,
        }

        for k in "variables", "globals":
            ret[k] = getattr(self, k).tags(tags)

        ret["rules"] = []

        for rule in self.rules:
            if value := rule.tags(tags):
                ret["rules"].append(value)

        # Append automagical coloring
        for k in ret["variables"].keys():
            ret["rules"].append(
                {
                    "scope": f"etc.{k}",
                    "name": f"Automagical import {k}",
                    "foreground": f"var({k})",
                },
            )

        for rk, rv in self.replacements.tags(tags).items():
            searchStr = rk
            replaceStr = rv

            ret = replaceInKV(searchStr, replaceStr, ret)

        return ret


T = TypeVar("T")


def replaceInKV(searchString, replaceString, obj: T) -> T:
    recurse = lambda o: replaceInKV(searchString, replaceString, o)

    if isinstance(obj, str):
        ret = obj
        while True:
            newRet = re.sub(searchString, replaceString, ret)
            if ret == newRet:
                break
            ret = newRet

        return ret

    elif isinstance(obj, dict):
        ret = type(obj)()
        for k, v in obj.items():
            ret[recurse(k)] = recurse(v)
        return ret

    elif isinstance(obj, list):
        ret = type(obj)()
        for e in obj:
            ret.append(recurse(e))
        return ret

    else:
        return obj
