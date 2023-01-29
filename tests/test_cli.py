import unittest

from click.testing import CliRunner

from pynostr.cli import main


class TestEvent(unittest.TestCase):
    def test_keygen(self):
        runner = CliRunner()
        result = runner.invoke(main, ['keygen'])
        self.assertEqual(result.exit_code, 0)

    def test_convert(self):
        runner = CliRunner()
        result = runner.invoke(
            main,
            [
                'convert',
                'npub1mg2nzunrsk9df94zr3uudhzltnu6lzq2muax09xmhu5gxxrvnkqsvpjg3p',
            ],
        )
        self.assertEqual(result.exit_code, 0)
