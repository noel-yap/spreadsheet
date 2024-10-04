import unittest

import spreadsheet


class TestConvertAddrColToCol(unittest.TestCase):
    def test_a(self):
        expected = 0

        actual = spreadsheet.Sheet.convert_addr_col_to_col("A")

        self.assertEqual(expected, actual)

    def test_z(self):
        expected = 25

        actual = spreadsheet.Sheet.convert_addr_col_to_col("Z")

        self.assertEqual(expected, actual)

    def test_aa(self):
        expected = 26

        actual = spreadsheet.Sheet.convert_addr_col_to_col("AA")

        self.assertEqual(expected, actual)

    def test_az(self):
        expected = 26 + 25

        actual = spreadsheet.Sheet.convert_addr_col_to_col("AZ")

        self.assertEqual(expected, actual)

    def test_zz(self):
        expected = 26 * 26 + 25

        actual = spreadsheet.Sheet.convert_addr_col_to_col("ZZ")

        self.assertEqual(expected, actual)


class TestConvertAddrRowToRow(unittest.TestCase):
    def test_1(self):
        expected = 0

        actual = spreadsheet.Sheet.convert_addr_row_to_row("1")

        self.assertEqual(expected, actual)

    def test_10(self):
        expected = 9

        actual = spreadsheet.Sheet.convert_addr_row_to_row("10")

        self.assertEqual(expected, actual)


class TestConvertAddrToColRow(unittest.TestCase):
    def test_a1(self):
        expected_col = 0
        expected_row = 0

        actual_col, actual_row = spreadsheet.Sheet.convert_addr_to_col_row("A1")

        self.assertEqual(expected_col, actual_col)
        self.assertEqual(expected_row, actual_row)

    def test_zz11(self):
        expected = (26 * 26 + 25, 10)

        actual = spreadsheet.Sheet.convert_addr_to_col_row("ZZ11")

        self.assertEqual(expected, actual)


class TestConvertContentsToCallable(unittest.TestCase):
    def test_int(self):
        expected = 2

        actual = spreadsheet.Sheet.convert_contents_to_callable("2")[0](spreadsheet.Sheet([]))

        self.assertEqual(expected, actual)

    def test_formula(self):
        expected = 5

        actual = spreadsheet.Sheet.convert_contents_to_callable("=2+3")[0](spreadsheet.Sheet([]))

        self.assertEqual(expected, actual)


class TestCell(unittest.TestCase):
    def test_set_dependencies(self):
        a1 = spreadsheet.Cell()
        a2 = spreadsheet.Cell()
        a3 = spreadsheet.Cell()
        b1 = spreadsheet.Cell()
        b2 = spreadsheet.Cell()
        c1 = spreadsheet.Cell()

        a1.dependents = {b1, b2}
        a2.dependents = {b1, b2}
        b1.dependents = {c1}
        b1.dependencies = {a1, a2}

        b1.set_dependencies({a1, a3})

        self.assertEqual({b1, b2}, a1.dependents)
        self.assertEqual({b2}, a2.dependents)
        self.assertEqual({b1}, a3.dependents)
        self.assertEqual({c1}, b1.dependents)

    def test_update_val(self):
        a1 = spreadsheet.Cell()
        a1.expr = lambda _: 2
        a2 = spreadsheet.Cell()
        a2.expr = lambda _: 3

        a1.dependents = {a2}

        self.assertEqual(0, a1.val)
        self.assertEqual(0, a2.val)

        a1.update_val(spreadsheet.Sheet([[a1, a2]]))

        self.assertEqual(2, a1.val)
        self.assertEqual(3, a2.val)


class TestSheet(unittest.TestCase):
    def test_topologically_sorted_dependents(self):
        a1 = spreadsheet.Cell()
        a2 = spreadsheet.Cell()
        b1 = spreadsheet.Cell()
        b2 = spreadsheet.Cell()
        c1 = spreadsheet.Cell()
        c2 = spreadsheet.Cell()
        d1 = spreadsheet.Cell()

        sheet = spreadsheet.Sheet([
            [a1, a2],
            [b1, b2],
            [c1, c2],
            [d1]
        ])
        sheet.set_contents("D1", "=B1+C1")
        sheet.set_contents("C1", "=A1+B1+B2")
        sheet.set_contents("C2", "=B1+B2")
        sheet.set_contents("B1", "=A1+A2")
        sheet.set_contents("B2", "=A1+A2")

        actual = a1.topologically_sorted_dependents()

        self.assertLess(actual.index(a1), actual.index(b1))
        self.assertLess(actual.index(a1), actual.index(b2))
        self.assertLess(actual.index(a1), actual.index(c1))
        self.assertLess(actual.index(b1), actual.index(c1))
        self.assertLess(actual.index(b1), actual.index(c2))
        self.assertLess(actual.index(b1), actual.index(d1))
        self.assertLess(actual.index(b2), actual.index(c1))
        self.assertLess(actual.index(b2), actual.index(c2))
        self.assertLess(actual.index(c1), actual.index(d1))

    def test_cyclic_reference(self):
        a1 = spreadsheet.Cell()
        a2 = spreadsheet.Cell()

        with self.assertRaises(ValueError) as ctx:
            sheet = spreadsheet.Sheet([[a1, a2]])
            sheet.set_contents("A1", "=A2")
            sheet.set_contents("A2", "=A1")

        self.assertEqual(str(ctx.exception), "Cyclic reference detected")


if __name__ == '__main__':
    unittest.main()
