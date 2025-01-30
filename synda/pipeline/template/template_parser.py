import re


class TemplateParser:
    @staticmethod
    def extract_variables(template: str) -> list[str]:
        pattern = r'{([^}]+)}'
        matches = re.finditer(pattern, template)
        return [match.group(1) for match in matches]
