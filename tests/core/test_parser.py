from unittest import TestCase

from backdrop.core import parser


class TestParser(TestCase):
    def test_json_to_csv_empty(self):
        assert "" == parser.json_to_csv({})
        assert "" == parser.json_to_csv([{}, {}])

    def test_json_to_csv(self):
        data = [
            dict(a=1, b=2, c=3),
            dict(a=1, b=2, cc=33),
            dict(a=1, bb=22, c=3, cc=33),
        ]
        csv = "a,b,bb,c,cc\r\n1,2,,3,\r\n1,2,,,33\r\n1,,22,3,33\r\n"
        assert csv == parser.json_to_csv(data=data)

        data = [
            dict(a="1", b=2, c=3),
            dict(a="1", b=2, cc=33),
            dict(a="1", bb=22, c=3, cc=33),
        ]
        csv = "a,b,bb,c,cc\r\n1,2,,3,\r\n1,2,,,33\r\n1,,22,3,33\r\n"
        assert csv == parser.json_to_csv(data=data)
