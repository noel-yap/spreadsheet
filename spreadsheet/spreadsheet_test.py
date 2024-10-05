import unittest

from addr import Addr
from spreadsheet import Cell, Sheet


class TestConvertContentsToCallable(unittest.TestCase):
    def test_int(self):
        expected = 2

        actual = Sheet.convert_contents_to_callable("2")[0](Sheet())

        self.assertEqual(expected, actual)

    def test_formula(self):
        expected = 5

        actual = Sheet.convert_contents_to_callable("=2+3")[0](Sheet())

        self.assertEqual(expected, actual)


class TestCell(unittest.TestCase):
    def test_topologically_sorted_dependents(self):
        a1 = Cell()
        a2 = Cell()
        b1 = Cell()
        b1.set_dependencies({a1, a2})
        b2 = Cell()
        b2.set_dependencies({a1, a2})
        c1 = Cell()
        c1.set_dependencies({a1, b1, b2})
        c2 = Cell()
        c2.set_dependencies({b1, b2})
        d1 = Cell()
        d1.set_dependencies({b1, c1})

        actual = Cell.topologically_sorted([d1, c2, c1, b2, b1, a2, a1])

        self.assertLess(actual.index(a1), actual.index(b1))
        self.assertLess(actual.index(a1), actual.index(b2))
        self.assertLess(actual.index(a1), actual.index(c1))
        self.assertLess(actual.index(b1), actual.index(c1))
        self.assertLess(actual.index(b1), actual.index(c2))
        self.assertLess(actual.index(b1), actual.index(d1))
        self.assertLess(actual.index(b2), actual.index(c1))
        self.assertLess(actual.index(b2), actual.index(c2))
        self.assertLess(actual.index(c1), actual.index(d1))

    def test_cyclic_reference_detection(self):
        a1 = Cell()
        a2 = Cell()
        a3 = Cell()
        a1.set_dependencies({a2})
        a2.set_dependencies({a3})
        a3.set_dependencies({a1})

        with self.assertRaises(ValueError) as ctx:
            Cell.topologically_sorted([a1, a2, a3])

        self.assertEqual(str(ctx.exception), "Cyclic reference detected")

    def test_set_dependencies(self):
        a1 = Cell()
        a2 = Cell()
        a3 = Cell()
        b1 = Cell()
        b2 = Cell()
        c1 = Cell()

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
        a1 = Cell()
        a1.expr = lambda _: 2
        a2 = Cell()
        a2.expr = lambda _: 3
        a3 = Cell()
        a3.expr = lambda _: 5

        a1.dependents = {a2}
        a2.dependents = {a3}

        self.assertEqual(0, a1.val)
        self.assertEqual(0, a2.val)
        self.assertEqual(0, a3.val)

        sheet = Sheet()
        sheet.topologically_sorted_cells = [a1, a2, a3]

        a1.update_val(sheet)

        self.assertEqual(2, a1.val)
        self.assertEqual(3, a2.val)
        self.assertEqual(5, a3.val)

    def test_update_subgraph(self):
        a1 = Cell()
        a1.expr = lambda _: 2
        a2 = Cell()
        a2.expr = lambda _: 3
        a3 = Cell()
        a3.expr = lambda _: 5

        a1.dependents = {a2}
        a2.dependents = {a3}

        self.assertEqual(0, a1.val)
        self.assertEqual(0, a2.val)
        self.assertEqual(0, a3.val)

        sheet = Sheet()
        sheet.topologically_sorted_cells = [a1, a2, a3]

        a2.update_val(sheet)

        self.assertEqual(0, a1.val)
        self.assertEqual(3, a2.val)
        self.assertEqual(5, a3.val)


class TestSheet(unittest.TestCase):
    def test_set_contents(self):
        sheet = Sheet()
        sheet.set_contents("A1", "2")
        sheet.set_contents("A2", "=A1")

        self.assertEqual(2, sheet.get_val("A1"))
        self.assertEqual(2, sheet.get_val("A2"))
        self.assertEqual(
            [
                sheet.get_cell(Addr("A1")),
                sheet.get_cell(Addr("A2"))
            ],
            sheet.topologically_sorted_cells)

    def test_set_contents_reverse(self):
        sheet = Sheet()
        sheet.set_contents("A2", "=A1")
        sheet.set_contents("A1", "2")

        self.assertEqual(2, sheet.get_val("A1"))
        self.assertEqual(2, sheet.get_val("A2"))
        self.assertEqual(
            [
                sheet.get_cell(Addr("A1")),
                sheet.get_cell(Addr("A2"))
            ],
            sheet.topologically_sorted_cells)


if __name__ == '__main__':
    unittest.main()
