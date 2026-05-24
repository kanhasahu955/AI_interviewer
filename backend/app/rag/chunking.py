from langchain_text_splitters import RecursiveCharacterTextSplitter

splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200
)

def split_text(text):
    return splitter.split_text(text)


def chunk_text(text: str) -> list[str]:
    return split_text(text)