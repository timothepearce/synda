import random
import re
from enum import Enum
from itertools import product

from sqlmodel import Session

from synda.model.node import Node


class SpecialVariable(Enum):
    INSTRUCTIONS = "instructions"


class PromptBuilder:
    # @todo send multiple template at once: template: str | list[str
    # @todo send a single node at once: input_data: list[Node] | Node
    @staticmethod
    def build(
        session: Session,
        template: str,
        input_data: list[Node],
        instruction_sets: dict[str, list[str]] | None = None,
        instruction_mode: str = "random"
    ) -> list[str]:
        prompts_with_special_variables = (
            PromptBuilder._build_prompts_with_special_variables(
                template, input_data, instruction_sets, instruction_mode
            )
        )
        prompts_with_template_variables = (
            PromptBuilder._build_prompts_with_template_variables(
                session, prompts_with_special_variables, input_data
            )
        )
        return prompts_with_template_variables

    @staticmethod
    def _build_prompts_with_special_variables(
        template: str,
        input_data: list[Node],
        instruction_sets: dict[str, list[str]] | None,
        instruction_mode: str
    ) -> list[str]:
        special_variables = PromptBuilder._extract_special_variables(template)

        if len(special_variables) == 0:
            return [template for _ in input_data]

        prompts_with_special_variables = []

        for _ in input_data:
            instructions_list = PromptBuilder._build_instructions(instruction_sets, instruction_mode)
            
            for instructions in instructions_list:
                variable_value = {}
                for variable_name in special_variables:
                    if variable_name == SpecialVariable.INSTRUCTIONS.value:
                        variable_value[SpecialVariable.INSTRUCTIONS.value] = instructions

                formatted_prompt = template.format(**variable_value)
                prompts_with_special_variables.append(formatted_prompt)

        return prompts_with_special_variables

    @staticmethod
    def _build_prompts_with_template_variables(
        session: Session,
        prompts_with_special_variables: list[str],
        input_data: list[Node],
    ) -> list[str]:
        prompts_with_template_variables = []
        
        for prompt in prompts_with_special_variables:
            template_variables = PromptBuilder._extract_template_variables(prompt)
            
            if len(template_variables) == 0:
                prompts_with_template_variables.append(prompt)
                continue
                
            for node in input_data:
                variable_value = {}
                for variable_name in template_variables:
                    if variable_name not in node.ancestors:
                        continue
                    parent_node_id = node.ancestors[variable_name]
                    parent_node = Node.get(session, parent_node_id)
                    variable_value[variable_name] = parent_node.value

                formatted_prompt = prompt.format(**variable_value)
                prompts_with_template_variables.append(formatted_prompt)

        return prompts_with_template_variables

    @staticmethod
    def _extract_special_variables(template: str) -> list[str]:
        pattern = PromptBuilder._pattern_only_special_variables()
        matches = re.finditer(pattern, template)
        return [match.group(1) for match in matches]

    @staticmethod
    def _extract_template_variables(template: str) -> list[str]:
        pattern = PromptBuilder._pattern_without_special_variables()
        matches = re.finditer(pattern, template)
        return [match.group(1) for match in matches]

    @staticmethod
    def _pattern_only_special_variables() -> str:
        special_vars = "|".join(var.value for var in SpecialVariable)
        return rf"{{({special_vars})}}"

    @staticmethod
    def _pattern_without_special_variables() -> str:
        special_vars = "|".join(var.value for var in SpecialVariable)
        return rf"{{(?!{special_vars})([^}}]+)}}"

    @staticmethod
    def _build_instructions(instruction_sets: dict[str, list[str]] | None, mode: str = "random") -> list[str]:
        if instruction_sets is None:
            raise Exception("`instruction_sets` is missing from parameters.")
        if mode == "random":
            instructions_set = []
            for category, instructions in instruction_sets.items():
                selected_instruction = random.choice(instructions)
                instructions_set.append("- " + selected_instruction)
            return ["\n".join(instructions_set)]
        
        elif mode == "all_combinations":
            categories = instruction_sets.values()
            all_combinations = list(product(*categories))
            return ["\n".join("- " + instruction for instruction in combination) 
                    for combination in all_combinations]
        
        else:
            raise ValueError(f"Unknown instruction mode: {mode}")

    @staticmethod
    def _get_parent_nodes(
        session: Session, variables: set[str], input_data: list[Node]
    ) -> list[Node]:
        parent_node_ids = set()

        for node in input_data:
            for variable_name in variables:
                parent_node_ids.add(node.ancestors[variable_name])

        return Node.get(session, list(parent_node_ids))
