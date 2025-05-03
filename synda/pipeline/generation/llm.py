import asyncio
import requests
from sqlmodel import Session

from synda.model.provider import Provider
from synda.model.run import Run
from synda.model.step import Step
from synda.pipeline.executor import Executor
from synda.model.node import Node
from synda.utils.llm_provider import LLMProvider
from synda.utils.vllm_provider import VLLMProvider
from synda.utils.prompt_builder import PromptBuilder
from synda.progress_manager import ProgressManager


class LLM(Executor):
    def __init__(self, session: Session, run: Run, step_model: Step):
        super().__init__(session, run, step_model, save_on_completion=False)
        self.progress = ProgressManager("GENERATION")
        self.provider = Provider.get(self.config.parameters.provider)
        self.model = self.config.parameters.model
        self.batch = self.config.parameters.batch
        self.batch_size = self.config.parameters.batch_size

    def execute(self, pending_nodes: list[Node], processed_nodes: list[Node]):
        template = self.config.parameters.template
        occurrences = self.config.parameters.occurrences
        instruction_sets = self.config.parameters.instruction_sets
        instruction_mode = self.config.parameters.instruction_mode
        pending_nodes = self._build_node_occurrences(pending_nodes, occurrences)

        if not self.batch or self.batch_size is None:
            result = self._execute_sequential(
                pending_nodes, processed_nodes, template, instruction_sets, instruction_mode
            )
        else:
            result = self._execute_batch(
                pending_nodes=pending_nodes,
                processed_nodes=processed_nodes,
                template=template,
                instruction_sets=instruction_sets,
                instruction_mode=instruction_mode,
                use_vllm="vllm" in self.provider.name
            )

        return result

    def _execute_sequential(
        self,
        pending_nodes: list[Node],
        processed_nodes: list[Node],
        template: str,
        instruction_sets: list,
        instruction_mode: str
    ) -> list[Node]:
        result = processed_nodes or []
        
        with self.progress.task(
            "Generating...",
            len(pending_nodes) + len(processed_nodes),
            completed=len(processed_nodes),
        ) as advance:
            for node in pending_nodes:
                prompts = self._build_prompts(node, template, instruction_sets, instruction_mode)
                for prompt in prompts:
                    llm_answer = self._call_llm(prompt)
                    result_node = self._create_result_node(node, llm_answer, prompt)
                    result.append(result_node)
                advance()
                
        return result

    def _execute_batch(
        self,
        pending_nodes: list[Node],
        processed_nodes: list[Node],
        template: str,
        instruction_sets: list,
        instruction_mode: str,
        use_vllm: bool
    ) -> list[Node]:
        result = processed_nodes or []
        
        all_prompts = []
        node_map = {}
        for node in pending_nodes:
            prompts = self._build_prompts(node, template, instruction_sets, instruction_mode)
            for prompt in prompts:
                all_prompts.append(prompt)
                node_map[prompt] = node
        with self.progress.task(
            "Generating...",
            len(pending_nodes) + len(processed_nodes),
            completed=len(processed_nodes),
            batch_size=self.batch_size
        ) as advance:
            for i in range(0, len(all_prompts), self.batch_size):
                batch_prompts = all_prompts[i:i + self.batch_size]
                if use_vllm:
                    responses = self._call_vllm(prompts=batch_prompts)
                else:
                    loop = asyncio.get_event_loop()
                    tasks = [
                        loop.run_in_executor(
                            None,
                            self._call_llm,
                            prompt
                        )
                        for prompt in batch_prompts
                    ]
                    responses = loop.run_until_complete(asyncio.gather(*tasks))
                for prompt, response in zip(batch_prompts, responses):
                    node = node_map[prompt]
                    result_node = self._create_result_node(node, response, prompt)
                    result.append(result_node)
                advance()
                
        return result

    def _call_vllm(self, prompts: list[str]):
        return VLLMProvider.call(
            provider=self.provider.name,
            model=self.model,
            api_url=self.provider.api_url,
            prompts=prompts,
            temperature=self.config.parameters.temperature,
        )

    def _hosted_vllm_batch_inference(self, prompts):
        llm_answers = requests.post(
            self.provider.api_url,
            json={
                "model": self.model,
                "prompt": prompts,
                "temperature": self.config.parameters.temperature,
            }
        ).json()
        return [answer["text"] for answer in llm_answers["choices"]]
        
    def _build_prompts(self, node: Node, template: str, instruction_sets: list, instruction_mode: str) -> list[str]:
        return PromptBuilder.build(
            self.session,
            template,
            [node],
            instruction_sets=instruction_sets,
            instruction_mode=instruction_mode
        )
        
    def _call_llm(self, prompt: str) -> str:
        return LLMProvider.call(
            self.provider.name,
            self.model,
            self.provider.api_key,
            prompt,
            url=self.provider.api_url,
            temperature=self.config.parameters.temperature,
        )
        
    def _create_result_node(self, node: Node, value: str, metadata: str) -> Node:
        result_node = Node(
            parent_node_id=node.id,
            value=value,
            node_metadata=metadata,
            ancestors={'source': node.id}
        )
        self.step_model.save_during_execution(self.session, [node], [result_node])

        return result_node

    @staticmethod
    def _build_node_occurrences(
        pending_nodes: list[Node], occurrences: int
    ) -> list[Node]:
        nodes = []
        for node in pending_nodes:
            [nodes.append(node) for _ in range(occurrences)]
            
        return nodes
