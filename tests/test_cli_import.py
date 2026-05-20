import unittest


class CliImportTest(unittest.TestCase):
    def test_importing_cli_does_not_initialize_runtime_context(self):
        try:
            import InquirerPy  # noqa: F401
            import rich  # noqa: F401
            import typer  # noqa: F401
        except ModuleNotFoundError as exc:
            self.skipTest(f'CLI dependency is not installed: {exc.name}')

        import heirloom.cli as cli

        self.assertIsNone(cli.config)
        self.assertIsNone(cli.heirloom)


if __name__ == '__main__':
    unittest.main()
