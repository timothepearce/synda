from datasets import load_dataset

from synda.config.input.input_properties import InputProperties


class HuggingFaceInputProperties(InputProperties):
    dataset_name: str
    split: str = "train"
    column_name: str

    def validate_properties(self) -> "HuggingFaceInputProperties":
        try:
            dataset = load_dataset(self.dataset_name, split=self.split)
            
            if self.column_name not in dataset.column_names:
                raise ValueError(
                    f"Column '{self.column_name}' not found in dataset. Available columns: {', '.join(dataset.column_names)}"
                )
                
            return self
            
        except Exception as e:
            raise ValueError(f"Failed to validate HuggingFace dataset: {str(e)}")
