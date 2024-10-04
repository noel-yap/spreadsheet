from collections import defaultdict
from typing import Dict, List, Optional, Set, Tuple

import parser
from addr import Addr
from expr import Expr


class Cell:
    dependents: Set['Cell']  # cells that depend on this one
    dependencies: Set['Cell']  # cells that this cell depends on
    expr: Expr
    val: int

    def __init__(self):
        self.dependents = set()
        self.dependencies = set()
        self.expr = lambda _: 0
        self.val = 0

    def set_expr(self, expr: Expr):
        self.expr = expr

    def set_dependencies(self, dependencies: Set['Cell']):
        for d in self.dependencies.difference(dependencies):
            d.remove_dependent(self)
        for d in dependencies.difference(self.dependencies):
            d.add_dependent(self)
        self.dependencies = dependencies

    def add_dependent(self, dependent: 'Cell'):
        self.dependents.add(dependent)

    def remove_dependent(self, dependent: 'Cell'):
        self.dependents.remove(dependent)

    def get_val(self) -> int:
        return self.val

    def update_val(self, sheet: 'Sheet'):
        for c in self.topologically_sorted_dependents():
            c.val = c.expr(sheet)

    def topologically_sorted_dependents(self) -> Optional[List['Cell']]:
        result = []

        processed = set()
        dependencies: Dict[Cell, Set[Cell]] = defaultdict(Set[Cell])
        dependencies[self] = set()
        queue = [self]
        while queue:
            cell = queue.pop()
            if cell not in processed:
                processed.add(cell)
                queue.extend(cell.dependents)
                for d in cell.dependents:
                    dependencies[d] = dependencies.get(d, set())
                    dependencies[d].add(cell)

        in_degree = {c: len(d) for c, d in dependencies.items()}

        queue = [self]
        while queue:
            cell = queue.pop(0)
            result.append(cell)

            for d in cell.dependents:
                in_degree[d] -= 1
                if in_degree[d] == 0:
                    queue.append(d)

        if len(result) != len(in_degree):
            raise ValueError("Cyclic reference detected")

        return result


class Sheet:
    cells: defaultdict[str, defaultdict[int, Cell]]

    def __init__(self):
        self.cells = defaultdict(lambda: defaultdict(Cell))

    def set_contents(self, addr: str, contents: str):
        expr, addr_refs = self.convert_contents_to_callable(contents)

        cell = self.get_cell(Addr(addr))
        cell.set_expr(expr)
        cell.set_dependencies(set(self.get_cell(addr) for addr in addr_refs))
        cell.update_val(self)

    def get_cell(self, addr: Addr) -> Cell:
        return self.cells[addr.col][addr.row]

    def get_val(self, addr: str) -> int:
        return self.get_cell(Addr(addr)).get_val()

    @staticmethod
    def convert_contents_to_callable(expr: str) -> Tuple[Expr, Set[Addr]]:
        if expr[0] == '=':
            tokens = parser.tokenize(expr[1:])
        else:  # int
            tokens = parser.tokenize(expr)

        p = parser.Parser(tokens)
        expr, addr_refs = p.parse()

        return expr, {Addr(a) for a in addr_refs}
