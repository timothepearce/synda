import random
import re

from sqlmodel import Session

from synda.model.node import Node


class PromptBuilder:
    @staticmethod
    def build(
        session: Session,
        template: str,
        input_data: list[Node],
        instruction_sets: dict[str, list[str]] | None = None,
    ) -> list[str]:
        variables = PromptBuilder._extract_template_variables(template)
        prompts = []

        if len(variables) == 0:
            return [template for _ in input_data]

        parent_node_ids = set()
        for node in input_data:
            for variable_name in variables:
                if variable_name == "instructions":
                    continue
                parent_node_ids.add(node.ancestors[variable_name])

        parent_nodes = Node.get(session, list(parent_node_ids))

        for node in input_data:
            variable_value = {}
            for variable_name in variables:
                if variable_name == "instructions":
                    variable_value["instructions"] = (
                        PromptBuilder._build_instructions_set(instruction_sets)
                    )
                    continue

                parent_node_id = node.ancestors[variable_name]
                parent_node = next(
                    node for node in parent_nodes if node.id == parent_node_id
                )
                variable_value[variable_name] = parent_node.value

            formatted_prompt = template.format(**variable_value)
            print(formatted_prompt)
            prompts.append(formatted_prompt)

        return prompts

    @staticmethod
    def _extract_template_variables(template: str) -> list[str]:
        pattern = r"{([^}]+)}"
        matches = re.finditer(pattern, template)
        return [match.group(1) for match in matches]

    @staticmethod
    def _build_instructions_set(instructions_sets: dict[str, list[str]]) -> str:
        instructions_set = []

        for category, instructions in instructions_sets.items():
            selected_instruction = random.choice(instructions)
            instructions_set.append("- " + selected_instruction)

        return "\n".join(instructions_set)
