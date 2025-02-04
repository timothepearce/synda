import re

from sqlmodel import Session

from synda.model.node import Node


class PromptBuilder:
    @staticmethod
    def extract_template_variables(template: str) -> list[str]:
        pattern = r"{([^}]+)}"
        matches = re.finditer(pattern, template)
        return [match.group(1) for match in matches]

    @staticmethod
    def build(session: Session, template: str, input_data: list[Node]) -> list[str]:
        variables = PromptBuilder.extract_template_variables(template)
        prompts = []

        if len(variables) == 0:
            return [template for _ in input_data]

        parent_node_ids = set()
        for node in input_data:
            for variable_name in variables:
                parent_node_ids.add(node.ancestors[variable_name])

        parent_nodes = Node.get(session, list(parent_node_ids))

        for node in input_data:
            variable_value = {}
            for variable_name in variables:
                parent_node_id = node.ancestors[variable_name]
                parent_node = next(
                    node for node in parent_nodes if node.id == parent_node_id
                )
                variable_value[variable_name] = parent_node.value

            prompts.append(template.format(**variable_value))

        return prompts
