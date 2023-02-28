import unittest

from pynostr.exception import NIPValidationException
from pynostr.key import PrivateKey
from pynostr.report import Report, ReportType


class TestReport(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reported_pubkey = PrivateKey().public_key.hex()

    def test_report_type(self):
        report1 = Report(
            report_type="invalidtype", reported_pubkey=self.reported_pubkey
        )
        with self.assertRaisesRegex(NIPValidationException, "valid report type"):
            report1.to_event()
        report2 = Report(report_type=ReportType.NUDITY)
        with self.assertRaisesRegex(
            NIPValidationException, "pubkey of the user being reported"
        ):
            report2.to_event()

    def test_report_tags(self):
        report = Report(
            reported_pubkey=self.reported_pubkey,
            note_id="fakenoteid",
            report_type=ReportType.ILLEGAL,
            victim_pubkey="thevictim",
        )
        report_event = report.to_event()
        self.assertEqual(len(report_event.tags), 2)
        tag_types = [tag[0] for tag in report_event.tags]
        self.assertEqual(tag_types, ["e", "p"])
