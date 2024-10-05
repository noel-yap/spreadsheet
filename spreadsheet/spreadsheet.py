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

    @staticmethod
    def topologically_sorted(cells: List['Cell']):
        result = []

        in_degree = {c: len(c.dependencies) for c in cells}

        queue = [c for c in in_degree if in_degree[c] == 0]
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
        # TODO(nyap): consider caching the subgraph to improve compute efficiency (at the expense of memory efficiency)
        #             this would require updating the cache each time the subgraph is updated
        subgraph = []
        queue = [self]
        while queue:
            cell = queue.pop(0)
            if cell not in subgraph:
                subgraph.append(cell)
                queue.extend(cell.dependents)

        for c in sheet.topologically_sorted_cells:
            if c in subgraph:
                c.val = c.expr(sheet)


class Sheet:
    cells: defaultdict[str, defaultdict[int, Cell]]
    topologically_sorted_cells: List[Cell]

    def __init__(self):
        self.cells = defaultdict(lambda: defaultdict(Cell))
        self.topologically_sorted_cells = []

    def set_contents(self, addr: str, contents: str):
        expr, addr_refs = self.convert_contents_to_callable(contents)

        cell = self.get_cell(Addr(addr))
        cell.set_expr(expr)
        cell.set_dependencies(set(self.get_cell(addr) for addr in addr_refs))

        try:
            cells_to_be_topologically_sorted = set(self.topologically_sorted_cells)
            cells_to_be_topologically_sorted.add(cell)
            cells_to_be_topologically_sorted.update(cell.dependencies)
            self.topologically_sorted_cells = Cell.topologically_sorted(list(cells_to_be_topologically_sorted))
        except ValueError:
            # FIXME(nyap): figure out what to do when there's a cyclic reference
            pass

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
