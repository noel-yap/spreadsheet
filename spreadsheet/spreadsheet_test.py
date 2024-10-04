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

        a1.dependents = {a2}

        self.assertEqual(0, a1.val)
        self.assertEqual(0, a2.val)

        a1.update_val(Sheet())

        self.assertEqual(2, a1.val)
        self.assertEqual(3, a2.val)


class TestSheet(unittest.TestCase):
    def test_topologically_sorted_dependents(self):
        sheet = Sheet()
        sheet.set_contents("D1", "=B1+C1")
        sheet.set_contents("C1", "=A1+B1+B2")
        sheet.set_contents("C2", "=B1+B2")
        sheet.set_contents("B1", "=A1+A2")
        sheet.set_contents("B2", "=A1+A2")

        a1 = sheet.get_cell(Addr("A1"))
        b1 = sheet.get_cell(Addr("B1"))
        b2 = sheet.get_cell(Addr("B2"))
        c1 = sheet.get_cell(Addr("C1"))
        c2 = sheet.get_cell(Addr("C2"))
        d1 = sheet.get_cell(Addr("D1"))

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
        with self.assertRaises(ValueError) as ctx:
            sheet = Sheet()
            sheet.set_contents("A1", "=A2")
            sheet.set_contents("A2", "=A1")

        self.assertEqual(str(ctx.exception), "Cyclic reference detected")


if __name__ == '__main__':
    unittest.main()
