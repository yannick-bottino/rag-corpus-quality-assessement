from pathlib import Path
from .models import ParsedDoc, Block


def _docling_available() -> bool:
    try:
        import docling  # noqa: F401
        return True
    except Exception:
        return False


def _parse_docling(path: str) -> tuple[str, list[Block]]:
    from docling.document_converter import DocumentConverter, PdfFormatOption
    from docling.datamodel.base_models import InputFormat
    from docling.datamodel.pipeline_options import PdfPipelineOptions
    # Corpus ne-numerique : pas d'OCR (cadrage). Desactiver l'OCR evite aussi la saturation
    # memoire observee sur les PDF riches en images. La detection de structure de tableaux reste active.
    opts = PdfPipelineOptions(do_ocr=False)
    converter = DocumentConverter(
        format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=opts)})
    result = converter.convert(path)
    md = result.document.export_to_markdown()
    blocks: list[Block] = []
    for item, _level in result.document.iterate_items():
        kind = getattr(item, "label", item.__class__.__name__)
        text = getattr(item, "text", "") or ""
        blocks.append(Block(kind=str(kind), text=text))
    return md, blocks


def _parse_pypdf(path: str) -> tuple[str, list[Block]]:
    from pypdf import PdfReader
    reader = PdfReader(path)
    parts, blocks = [], []
    for i, page in enumerate(reader.pages):
        text = (page.extract_text() or "").strip()
        if text:
            parts.append(text)
            blocks.append(Block(kind="text", text=text, page=i + 1))
    return "\n\n".join(parts), blocks


def _confidence(markdown: str, blocks: list[Block], pages: int | None = None) -> float:
    if not blocks:
        return 0.0
    non_empty = sum(1 for b in blocks if b.text.strip())
    ratio = non_empty / len(blocks)
    length_ok = min(1.0, len(markdown) / 500.0)
    conf = 0.5 * ratio + 0.5 * length_ok
    # Detection de perte de contenu : une extraction anormalement faible par page
    # (ex. parser qui echoue silencieusement sur des pages) plafonne la confiance.
    if pages and pages > 0 and (len(markdown) / pages) < 200:
        conf = min(conf, 0.4)
    return round(conf, 3)


def parse_document(path: str, category: str, use_docling: bool = False,
                   pages: int | None = None) -> ParsedDoc:
    # pypdf par defaut (ne-numerique : complet et rapide). Docling est opt-in.
    if use_docling and _docling_available():
        try:
            md, blocks = _parse_docling(path)
            md_pypdf, blocks_pypdf = _parse_pypdf(path)
            # Garde anti-degradation : Docling peut rendre une extraction partielle SANS lever
            # (ex. saturation memoire sur certaines pages). Si le volume de texte s'effondre
            # face a pypdf, on retombe sur pypdf pour ne pas perdre du contenu en silence.
            if len(md) < 0.6 * len(md_pypdf):
                md, blocks = md_pypdf, blocks_pypdf
        except Exception:
            md, blocks = _parse_pypdf(path)
    else:
        md, blocks = _parse_pypdf(path)
    return ParsedDoc(doc_id=Path(path).stem, markdown=md, blocks=blocks,
                     parse_confidence=_confidence(md, blocks, pages))
