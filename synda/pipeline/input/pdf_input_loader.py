import PyPDF2

from sqlmodel import Session

from synda.pipeline.input import InputLoader
from synda.config.input import Input
from synda.model.node import Node


class PDFInputLoader(InputLoader):
    def __init__(self, input_config: Input):
        self.properties = input_config.properties
        super().__init__()

    def load(self, session: Session) -> list[Node]:
        result = []
        
        with open(self.properties.path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            total_pages = len(reader.pages)
            page_indices = self.properties.get_page_indices(total_pages)
            
            for page_num in page_indices:
                page = reader.pages[page_num]
                text = page.extract_text()
                
                # Create one node per page with the extracted text
                result.append(Node(value=text, node_metadata=[{
                    "source_type": "pdf",
                    "source_path": self.properties.path,
                    "page_number": page_num + 1,
                    "total_pages": total_pages
                }]))

        self.persist_nodes(session, result)

        return result