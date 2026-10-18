"""Regression checks for editorial changes lost during report regeneration."""
import unittest
from pathlib import Path
from wingcheck.report_editorial import apply_report_wording


class ReportWordingTests(unittest.TestCase):
    def test_final_excel_explanation(self):
        text = '# Report\n\n- Excel-Flugn\u00e4herung M0*L\u00b2/(2EI) ist doppelt so gro\u00df wie die korrekte Gleichlast-Kragtr\u00e4gerformel q*L\u2074/(8EI).\n'
        result = apply_report_wording(text)
        self.assertIn('bei gleichbleibender Biegesteifigkeit', result)
        self.assertIn('als N\u00e4herung f\u00fcr Fall A', result)
        self.assertEqual(result, apply_report_wording(result))

    def test_generated_report_preserves_accepted_changes(self):
        text = Path('results/report.md').read_text(encoding='utf-8')
        for phrase in ('Fall B wurde gebaut', 'Absch\u00e4tzung der Schwingungsfrequenz nach Rayleigh',
                       'Zus\u00e4tzliche Verformung durch Schub', 'Materialmengen je Halbfl\u00fcgel'):
            self.assertIn(phrase, text)
        for phrase in ('results_before_', 'results_uniform_load', 'Test-Reaktionsrest', 'np.float64'):
            self.assertNotIn(phrase, text)
        self.assertLess(text.index('## Schwingungsmessung'), text.index('## FEM-Anh\u00e4nge'))
        self.assertLess(text.index('## Messwerte und aktuelle FEM-Ergebnisse'), text.index('## FEM-Anh\u00e4nge'))
        self.assertEqual(text, apply_report_wording(text))


if __name__ == '__main__':
    unittest.main()
