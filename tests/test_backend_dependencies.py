import pathlib
import unittest


class BackendDependencyTests(unittest.TestCase):
    def test_requirements_include_requests_used_by_llm_client(self):
        requirements = (pathlib.Path(__file__).parent.parent / "backend" / "requirements.txt").read_text()

        self.assertIn("requests==", requirements)


if __name__ == "__main__":
    unittest.main()
