from typing import TYPE_CHECKING

from nebula.pipeline.pipeline_context import PipelineContext
from nebula.utils import is_debug_enabled

if TYPE_CHECKING:
    from nebula.config import Config


class Pipeline:
    def __init__(self, config: "Config"):
        self.config = config
        self.pipeline = config.pipeline
        self.data: PipelineContext = None

    def execute(self):
        input_data = self._load_input_data()
        self.data = PipelineContext(
            current_data=input_data,
            history=[]
        )

        for parser in self.pipeline:
            if is_debug_enabled():
                print(parser)
            executor = parser.get_executor()
            executor.execute(self.data)

        self._save_output_data()

    # @todo move into a source class loader
    def _load_input_data(self) -> list[str]:
        input = self.config.input
        if input.type != "csv":
            raise ValueError(f"Input type '{input.type}' not supported")

        import pandas as pd
        df = pd.read_csv(
            input.properties.path,
            sep=input.properties.separator
        )
        return df[input.properties.target_column]

    # @todo move into an output class saver
    def _save_output_data(self) -> None:
        output = self.config.output
        if output.type != "csv":
            raise ValueError(f"Destination type '{output.type}' not supported")

        import pandas as pd

        output_dict = {
            'final_output': self.data.current_data,
        }

        for i, step in enumerate(self.data.history):
            step_prefix = f"step_{i + 1}"

            output_dict.update({
                f"{step_prefix}_type": step.step_type,
                f"{step_prefix}_method": step.metadata['method'],
                f"{step_prefix}_input": step.input_data,
                f"{step_prefix}_output": step.output_data,
            })

            params = step.metadata.get('parameters')
            if params:
                output_dict[f"{step_prefix}_parameters"] = str(params)

            # prompts = step.metadata.get('prompts')
            # if prompts:
            #     output_dict[f"{step_prefix}_prompts"] = prompts

        df = pd.DataFrame(output_dict)

        # Sauvegarder en CSV
        df.to_csv(
            output.properties.path,
            sep=output.properties.separator,
            index=False
        )
