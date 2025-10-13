import asyncio
from services.extraction_keyword.facade import ExtractionKeywordService
from services.extraction_keyword.translator import LocalTranslator


def print_tree(nodes, level=0):
    

    for node in nodes:
        indent = "  " * level
        print(f"{indent}- {node.name}")
        if node.children:
            print_tree(node.children, level + 1)


async def main():
    translator = LocalTranslator()
    pipeline = ExtractionKeywordService(translator)

    text_ru = """
    Антоновские яблоки

    Бунин Иван Алексеевич

    I

    …Вспоминается мне ранняя погожая осень.

    1900
    """

    a = await pipeline.generate(text_ru)
    roots_ru = a.ru
    roots_en = a.en
    print(type(roots_ru))
    print("=== ДЕРЕВО НА РУССКОМ ===")
    print_tree(roots_ru)
    print("\n=== ДЕРЕВО ПЕРЕВЕДЁННОЕ НА АНГЛИЙСКИЙ ===")
    print_tree(roots_en)


if __name__ == "__main__":
    asyncio.run(main())
