from typing import List, Set, Tuple

from expr import Expr


class Token:
    def __init__(self, type: str, value: str):
        self.type = type
        self.value = value

    def __eq__(self, other: 'Token') -> bool:
        return self.type == other.type and self.value == other.value


# «EXPR» ≔ «TERM» { "+" «TERM» | "-" «TERM» }
# «TERM» ≔ «FACTOR» { "*" «FACTOR» | "/" «FACTOR» }
# «FACTOR» ≔ «INT» | «ADDR» | "-" «FACTOR» | "(" «EXPR» ")"
# «ADDR» ≔ «COL» «ROW»
# «COL» ≔ [A-Z]+
# «ROW» ≔ «INT»
# «INT» ≔ [0-9]+
class Parser:
    operator = {
        '+': lambda lhs, rhs: lambda sheet: lhs(sheet) + rhs(sheet),
        '-': lambda lhs, rhs: lambda sheet: lhs(sheet) - rhs(sheet),
        '*': lambda lhs, rhs: lambda sheet: lhs(sheet) * rhs(sheet),
        '/': lambda lhs, rhs: lambda sheet: lhs(sheet) // rhs(sheet)
    }

    tokens: List[Token]
    current: int
    addr_references: Set[str]  # set of addresses the formula references

    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.current = 0
        self.addr_references = set()

    def parse(self) -> Tuple[Expr, Set[str]]:
        return self.parse_expr(), self.addr_references

    # «EXPR» ≔ «TERM» { "+" «TERM» | "-" «TERM» }
    def parse_expr(self) -> Expr:
        result = self.parse_term()

        while self.current < len(self.tokens) and self.tokens[self.current].type in ('+', '-'):
            op = self.tokens[self.current]
            self.current += 1

            right = self.parse_term()
            result = Parser.operator[op.type](result, right)

        return result

    # «TERM» ≔ «FACTOR» { "*" «FACTOR» | "/" «FACTOR» }
    def parse_term(self) -> Expr:
        result = self.parse_factor()

        while self.current < len(self.tokens) and self.tokens[self.current].type in ('*', '/'):
            op = self.tokens[self.current]
            self.current += 1

            right = self.parse_factor()
            result = Parser.operator[op.type](result, right)

        return result

    # «FACTOR» ≔ «INT» | «ADDR» | "-" «FACTOR» | "(" «EXPR» ")"
    def parse_factor(self) -> Expr:
        if self.current < len(self.tokens):
            token = self.tokens[self.current]
            if token.type == 'INT':
                return self.parse_int()
            elif token.type == 'ADDR':
                return self.parse_addr()
            elif token.type == '-':
                self.current += 1

                return lambda sheet: -self.parse_factor()(sheet)
            elif token.type == '(':
                self.current += 1
                result = self.parse_expr()
                if self.current < len(self.tokens) and self.tokens[self.current].type == ')':
                    self.current += 1

                    return result
                else:
                    raise ValueError("Mismatched parentheses")

        raise ValueError("Invalid syntax")

    # «ADDR» ≔ «COL» «ROW»
    # «COL» ≔ [A-Z]+
    # «ROW» ≔ «INT»
    def parse_addr(self) -> Expr:
        token = self.tokens[self.current]

        self.current += 1
        self.addr_references.add(token.value)

        return lambda sheet: sheet.get_val(token.value)

    # «INT» ≔ [0-9]+
    def parse_int(self) -> Expr:
        token = self.tokens[self.current]

        self.current += 1

        return lambda _: int(token.value)


def tokenize(expression: str) -> List[Token]:
    tokens = []
    current = 0
    while current < len(expression):
        char = expression[current]
        if char.isdigit():
            start = current
            while current < len(expression) and expression[current].isdigit():
                current += 1

            tokens.append(Token('INT', expression[start:current]))
        elif char.isupper():
            start = current
            while current < len(expression) and expression[current].isupper():
                current += 1

            if current == len(expression) or not expression[current].isdigit():
                raise ValueError("Malformed address")

            while current < len(expression) and expression[current].isdigit():
                current += 1

            tokens.append(Token('ADDR', expression[start:current]))
        elif char in '+-*/()':
            tokens.append(Token(char, char))
            current += 1
        elif char.isspace():
            current += 1
        else:
            raise ValueError(f"Unexpected character: {char}")

    return tokens
