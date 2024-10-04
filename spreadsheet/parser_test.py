import unittest

import parser
import spreadsheet


# Example usage
# expression = "3 + 4 * 2 / ( 1 - 5 ) ^ 2 ^ 3"
# tokens = tokenize(expression)
# parser = Parser(tokens)
# result = parser.parse()
# print(f"Result: {result}")

class TestTokenize(unittest.TestCase):
    def test_int(self):
        expected = [parser.Token("INT", "1234")]

        actual = parser.tokenize("1234")

        self.assertListEqual(expected, actual)

    def test_addr(self):
        expected = [parser.Token("ADDR", "AOEU1234")]

        actual = parser.tokenize("AOEU1234")

        self.assertEqual(expected, actual)

    def test_plus(self):
        expected = [parser.Token("+", "+")]

        actual = parser.tokenize("+")

        self.assertEqual(expected, actual)

    def test_minus(self):
        expected = [parser.Token("-", "-")]

        actual = parser.tokenize("-")

        self.assertEqual(expected, actual)

    def test_times(self):
        expected = [parser.Token("*", "*")]

        actual = parser.tokenize("*")

        self.assertEqual(expected, actual)

    def test_divided_by(self):
        expected = [parser.Token("/", "/")]

        actual = parser.tokenize("/")

        self.assertEqual(expected, actual)

    def test_full(self):
        expected = [
            parser.Token("INT", "1234"),
            parser.Token("*", "*"),
            parser.Token("ADDR", "AOEU1234")
        ]

        actual = parser.tokenize("1234*AOEU1234")

        self.assertEqual(expected, actual)

    def test_malformed_addr_at_end_of_expr(self):
        with self.assertRaises(ValueError) as ctx:
            parser.tokenize("AOEU")

        self.assertEqual(str(ctx.exception), "Malformed address")

    def test_malformed_addr_not_at_end_of_expr(self):
        with self.assertRaises(ValueError) as ctx:
            parser.tokenize("AOEU+")

        self.assertEqual(str(ctx.exception), "Malformed address")

    def test_space(self):
        expected = [
            parser.Token("INT", "1234")
        ]

        actual = parser.tokenize(" 1234")

        self.assertEqual(expected, actual)

    def test_unexpected_character(self):
        with self.assertRaises(ValueError) as ctx:
            parser.tokenize("…")

        self.assertEqual(str(ctx.exception), "Unexpected character: …")


class TestParserParseInt(unittest.TestCase):
    def test_single_call(self):
        expected = 1234

        p = parser.Parser([(parser.Token("INT", "1234"))])

        actual = p.parse_int()

        self.assertEqual(expected, actual(spreadsheet.Sheet([])))


class TestParserParseAddr(unittest.TestCase):
    def test(self):
        expected_output = 1234
        expected_dependencies = {"A1"}

        cell = spreadsheet.Cell()
        cell.set_expr(lambda _: 1234)

        sheet = spreadsheet.Sheet([[cell]])
        cell.update_val(sheet)

        p = parser.Parser([(parser.Token("ADDR", "A1"))])

        actual = p.parse_addr()

        self.assertEqual(expected_output, actual(sheet))
        self.assertEqual(expected_dependencies, p.addr_references)


class TestParserParseFactor(unittest.TestCase):
    def test_int(self):
        expected = 1234

        p = parser.Parser([(parser.Token("INT", "1234"))])

        actual = p.parse_factor()

        self.assertEqual(expected, actual(spreadsheet.Sheet([])))

    def test_addr(self):
        expected = 1234

        cell = spreadsheet.Cell()
        cell.set_expr(lambda _: 1234)

        sheet = spreadsheet.Sheet([[cell]])
        cell.update_val(sheet)

        p = parser.Parser([(parser.Token("ADDR", "A1"))])

        actual = p.parse_factor()

        self.assertEqual(expected, actual(sheet))

    def test_negative_factor(self):
        expected = -1234

        p = parser.Parser([
            (parser.Token("-", "-")),
            (parser.Token("INT", "1234"))
        ])

        actual = p.parse_factor()(spreadsheet.Sheet([]))

        self.assertEqual(expected, actual)

    def test_nested_expr(self):
        expected = 2

        p = parser.Parser([
            (parser.Token("(", "(")),
            (parser.Token("INT", "2")),
            (parser.Token(")", ")"))
        ])

        actual = p.parse_factor()(spreadsheet.Sheet([]))

        self.assertEqual(expected, actual)

    def test_mismatched_parentheses(self):
        with self.assertRaises(ValueError) as ctx:
            p = parser.Parser([
                (parser.Token("(", "(")),
                (parser.Token("INT", "2"))
            ])

            _ = p.parse_factor()(spreadsheet.Sheet([]))

        self.assertEqual(str(ctx.exception), "Mismatched parentheses")

    def test_invalid_syntax(self):
        with self.assertRaises(ValueError) as ctx:
            p = parser.Parser([
                (parser.Token("…", "…"))
            ])

            _ = p.parse_factor()(spreadsheet.Sheet([]))

        self.assertEqual(str(ctx.exception), "Invalid syntax")


class TestParserParseTerm(unittest.TestCase):
    def test_single_factor(self):
        expected = 1234

        p = parser.Parser([
            (parser.Token("INT", "1234"))
        ])

        actual = p.parse_term()(spreadsheet.Sheet([]))

        self.assertEqual(expected, actual)

    def test_multiple_factors(self):
        expected = 15

        p = parser.Parser([
            (parser.Token("INT", "6")),
            (parser.Token("*", "*")),
            (parser.Token("INT", "5")),
            (parser.Token("/", "/")),
            (parser.Token("INT", "2"))
        ])

        actual = p.parse_term()(spreadsheet.Sheet([]))

        self.assertEqual(expected, actual)

    def test_invalid_syntax(self):
        with self.assertRaises(ValueError) as ctx:
            p = parser.Parser([
                (parser.Token("INT", "1234")),
                (parser.Token("*", "*"))
            ])

            _ = p.parse_term()(spreadsheet.Sheet([]))

        self.assertEqual(str(ctx.exception), "Invalid syntax")


class TestParserParseExpr(unittest.TestCase):
    def test_single_term(self):
        expected = 1234

        p = parser.Parser([
            (parser.Token("INT", "1234"))
        ])

        actual = p.parse_expr()(spreadsheet.Sheet([]))

        self.assertEqual(expected, actual)

    def test_multiple_factors(self):
        expected = 6

        p = parser.Parser([
            (parser.Token("INT", "5")),
            (parser.Token("+", "+")),
            (parser.Token("INT", "3")),
            (parser.Token("-", "-")),
            (parser.Token("INT", "2"))
        ])

        actual = p.parse_expr()(spreadsheet.Sheet([]))

        self.assertEqual(expected, actual)

    def test_invalid_syntax_incomplete(self):
        with self.assertRaises(ValueError) as ctx:
            p = parser.Parser([
                (parser.Token("INT", "1234")),
                (parser.Token("+", "+"))
            ])

            _ = p.parse_expr()(spreadsheet.Sheet([]))

        self.assertEqual(str(ctx.exception), "Invalid syntax")

    def test_invalid_syntax_extra_close_parenthesis(self):
        with self.assertRaises(ValueError) as ctx:
            p = parser.Parser([
                (parser.Token(")", ")"))
            ])

            _ = p.parse_expr()(spreadsheet.Sheet([]))

        self.assertEqual(str(ctx.exception), "Invalid syntax")

    def test_nested_expr(self):
        expected = 6

        p = parser.Parser([
            (parser.Token("(", "(")),
            (parser.Token("INT", "2")),
            (parser.Token(")", ")")),
            (parser.Token("*", "*")),
            (parser.Token("(", "(")),
            (parser.Token("INT", "3")),
            (parser.Token(")", ")"))
        ])

        actual = p.parse_expr()(spreadsheet.Sheet([]))

        self.assertEqual(expected, actual)


if __name__ == '__main__':
    unittest.main()
