"""
Defines a goal.
"""

from typing import Literal
from io import StringIO


class Goal:
    """A goal, which may be simple or composite."""

    class _ChildList(list):
        """A list which will notify the parent on addition or removal."""

        def __init__(self, parent: 'Goal', iterable=None):
            self.parent = parent
            if iterable is None:
                super().__init__()
            else:
                super().__init__(iterable)

        def __delitem__(self, key):
            super().__delitem__(key)
            self.parent._resolve_auto_done()

        def __delattr__(self, item):
            super().__delattr__(item)
            self.parent._resolve_auto_done()

        def __add__(self, other):
            super().__add__(other)
            self.parent._resolve_auto_done()

        def __iadd__(self, other):
            super().__add__(other)
            self.parent._resolve_auto_done()

        def append(self, __object):
            super().append(__object)
            self.parent._resolve_auto_done()

        def extend(self, __iterable):
            super().extend(__iterable)
            self.parent._resolve_auto_done()

        def insert(self, i, x):
            super().insert(i, x)
            self.parent._resolve_auto_done()

        def remove(self, __value):
            super().remove(__value)
            self.parent._resolve_auto_done()

        def pop(self, __index=-1):
            super().pop(__index)
            self.parent._resolve_auto_done()

        def clear(self):
            super().clear()
            self.parent._resolve_auto_done()

    def __init__(
            self,
            title: str,
            done: bool | Literal['auto'] = False,
            parent: 'Goal' = None,
            children: list['Goal'] = None
    ):
        self.title = title
        self._done = done
        self.parent = parent
        self.children = Goal._ChildList(self, children)

        self._auto_done_result = False
        self._resolve_auto_done()

    def __dict__(self):
        return {
            'title': self.title,
            'done': self._done,
            'children': [x.__dict__() for x in self.children]
        }

    @property
    def done(self) -> bool:
        if self._done == 'auto':
            return self._auto_done_result
        else:
            return bool(self._done)  # bool call is here to keep PyCharm from freaking out. Should never be non-bool.

    @done.setter
    def done(self, val: bool | Literal['auto']):
        self._done = val
        self._resolve_auto_done()

    @property
    def auto(self) -> bool:
        """True if this task is set to autocomplete when its children finish."""
        return self._done == 'auto'

    def pretty_str(self, spaces: int = 0, space_inc: int = 4) -> str:
        """Prints a pretty representation of the goal and its children."""
        result = StringIO()

        result.write(' ' * spaces + self.title)
        if self.done:
            result.write(' (X)')
        if self._done == 'auto':
            result.write(' (auto)')
        result.write('\n')
        for child in self.children:
            result.write(child.pretty_str(spaces + space_inc, space_inc))

        return result.getvalue()

    @staticmethod
    def from_dict(dictionary: dict, parent: 'Goal' = None) -> 'Goal':
        result = Goal(
            dictionary['title'],
            dictionary['done'],
            parent
        )
        parsed_children = [Goal.from_dict(child, result) for child in dictionary['children']]
        result.children.extend(parsed_children)
        return result

    def _resolve_auto_done(self):
        """Resolves the 'auto-done' result. This should be called under two circumstances: (1) when a child goal's
        'done' value is modified; (2) when a child goal is added or removed."""
        if self._done == 'auto':
            children_done = [x.done for x in self.children]
            self._auto_done_result = all(children_done)
        if self.parent is not None:
            self.parent._resolve_auto_done()
