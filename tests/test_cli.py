import unittest

from typer.testing import CliRunner

from pynostr.cli import app


class TestEvent(unittest.TestCase):
    def test_keygen(self):
        runner = CliRunner()
        result = runner.invoke(app, ['keygen'])
        self.assertEqual(result.exit_code, 0)

    def test_convert(self):
        runner = CliRunner()
        result = runner.invoke(
            app,
            [
                'convert',
                'npub1mg2nzunrsk9df94zr3uudhzltnu6lzq2muax09xmhu5gxxrvnkqsvpjg3p',
            ],
        )
        self.assertEqual(result.exit_code, 0)
