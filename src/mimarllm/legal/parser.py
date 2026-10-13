"""Conservative Turkish legal text tree parser, with source line continuity.

This grammar only supports common unambiguous headings. It does not invent
missing clauses or merge amending articles into consolidated legislation.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from mimarllm.legal.models import (
    LegalDocumentMetadata, LegalLine, LegalNode, LegalNodeKind, LegalReviewIssue,
    LegalTable,
)

_SECTION = re.compile(
    r"^\s*(?:[\wÇĞİÖŞÜçğıöşü]+\s+)?BÖLÜM\b", re.IGNORECASE,
)
_TEMP = re.compile(
    r"^\s*GE[ÇC][İI]C[İI]\s+MADDE\s+([0-9]+(?:/[0-9]+)?)\s*(?:[—–-]|\b|:)\s*(.*)$",
    re.IGNORECASE,
)
_ARTICLE = re.compile(
    r"^\s*MADDE\s+([0-9]+(?:/[0-9]+)?)(?:\s*[-—–.:]\s*|\s+)(.*)$",
    re.IGNORECASE,
)
_PARAGRAPH = re.compile(r"^\s*\(\s*([0-9]+)\s*\)\s+(.+)$")
_ITEM = re.compile(r"^\s*([a-zçğıöşü])\s*[)\-]\s+(.+)$", re.IGNORECASE)


@dataclass
class ParsedTree:
    nodes: list[LegalNode]
    line_to_node_id: dict[str, str]
    issues: list[LegalReviewIssue]


def parse_legal_tree(lines: list[LegalLine], metadata: LegalDocumentMetadata,
                     *, max_nodes: int = 50_000) -> ParsedTree:
    """Parse single-document source line candidates in visual page order."""
    if max_nodes < 1:
        raise ValueError("Invalid LegalAST node budget")
    nodes: list[LegalNode] = []
    issues: list[LegalReviewIssue] = []
    assignments: dict[str, str] = {}
    section: str | None = None
    article: str | None = None
    paragraph: str | None = None
    item: str | None = None
    previous_page: int | None = None

    def add(kind: LegalNodeKind, text: str, line: LegalLine, parent: str | None,
            *, article_no: str | None = None, paragraph_no: str | None = None,
            item_key: str | None = None) -> str:
        if len(nodes) >= max_nodes:
            raise ValueError("LegalAST node budget exceeded")
        key = f"{line.source.document_sha256[:16]}:node:{len(nodes)}"
        nodes.append(LegalNode(
            node_id=key, parent_node_id=parent, kind=kind,
            order_index=len(nodes), text=text, spans=(line.source,),
            article_number=article_no, paragraph_number=paragraph_no,
            item_key=item_key,
        ))
        assignments[line.line_id] = key
        return key

    for line in lines:
        text = line.text.strip()
        if not text:
            continue
        if previous_page is not None and previous_page != line.source.page_index:
            issues.append(LegalReviewIssue(
                code="PAGE_BREAK_READING_ORDER_REVIEW_REQUIRED",
                page_index=line.source.page_index,
                source_line_id=line.line_id,
                detail="Continued article and page header/footer positions need review",
            ))
        previous_page = line.source.page_index

        m_section = _SECTION.match(text)
        m_temp = _TEMP.match(text)
        m_article = _ARTICLE.match(text) if not m_temp else None
        m_para = _PARAGRAPH.match(text)
        m_item = _ITEM.match(text)

        if m_section:
            section = add(LegalNodeKind.SECTION, text, line, None)
            article = paragraph = item = None
        elif m_temp or m_article:
            header = m_temp or m_article
            number = header.group(1)
            inline = _PARAGRAPH.match(header.group(2).strip())
            # The parent and inline paragraph share one original PDF line;
            # both retain the SAME full-line source polygon. No invented
            # sub-line coordinate is passed off as original glyph geometry.
            article_text = text
            if inline:
                article_text = text[:text.find(header.group(2))].strip()
            article = add(
                LegalNodeKind.TEMPORARY_ARTICLE if m_temp else LegalNodeKind.ARTICLE,
                article_text, line, section, article_no=number,
            )
            paragraph = item = None
            if inline:
                paragraph = add(
                    LegalNodeKind.PARAGRAPH, header.group(2).strip(), line,
                    article, article_no=number, paragraph_no=inline.group(1),
                )
                issues.append(LegalReviewIssue(
                    code="INLINE_PARAGRAPH_FULL_LINE_BBOX",
                    page_index=line.source.page_index,
                    source_line_id=line.line_id,
                    detail="Inline article/paragraph source span covers complete PDF line",
                ))
        elif m_para and article:
            paragraph = add(
                LegalNodeKind.PARAGRAPH, text, line, article,
                article_no=nodes[next(i for i, n in enumerate(nodes)
                                      if n.node_id == article)].article_number,
                paragraph_no=m_para.group(1),
            )
            item = None
        elif m_item and article:
            # Some regulations permit direct lettered items under an article.
            # The legal interpretation of the inferred parent needs review.
            parent = paragraph or article
            if paragraph is None:
                issues.append(LegalReviewIssue(
                    code="ITEM_WITHOUT_EXPLICIT_PARAGRAPH_REVIEW_REQUIRED",
                    page_index=line.source.page_index,
                    source_line_id=line.line_id,
                    detail="Lettered item has no preceding explicit paragraph",
                ))
            item = add(LegalNodeKind.ITEM, text, line, parent,
                       item_key=m_item.group(1).lower())
        else:
            active = item or paragraph or article
            if active is not None:
                i = next(i for i, node in enumerate(nodes) if node.node_id == active)
                prev = nodes[i]
                nodes[i] = prev.model_copy(update={
                    "text": prev.text + "\n" + text,
                    "spans": (*prev.spans, line.source),
                })
                assignments[line.line_id] = active
            else:
                add(LegalNodeKind.TEXT, text, line, section)
                issues.append(LegalReviewIssue(
                    code="UNSCOPED_LEGAL_TEXT_REVIEW_REQUIRED",
                    page_index=line.source.page_index, source_line_id=line.line_id,
                    detail="Text is outside a recognized article/paragraph hierarchy",
                ))

        if metadata.document_kind == "AMENDMENT" and (m_temp or m_article):
            issues.append(LegalReviewIssue(
                code="AMENDMENT_ARTICLE_NOT_CONSOLIDATED",
                page_index=line.source.page_index, source_line_id=line.line_id,
                detail="Amendment's own article number is not the target regulation article",
            ))

    return ParsedTree(nodes, assignments, issues)


def suggest_table_parents(
    tables: list[LegalTable], lines: list[LegalLine],
    tree: ParsedTree,
) -> tuple[list[LegalTable], list[LegalReviewIssue]]:
    """Suggest (NEVER certify) the most recent same-page legal text parent."""
    result = []
    issues = []
    for table in tables:
        start_y = min(p[1] for p in table.source.polygon)
        predecessors = [
            (max(p[1] for p in line.source.polygon), line.line_id)
            for line in lines
            if line.source.page_index == table.page_index
            and max(p[1] for p in line.source.polygon) <= start_y
            and line.line_id in tree.line_to_node_id
        ]
        parent = tree.line_to_node_id[
            max(predecessors, key=lambda row: row[0])[1]
        ] if predecessors else None
        result.append(table.model_copy(update={
            "suggested_parent_node_id": parent,
        }))
        issues.append(LegalReviewIssue(
            code="TABLE_PARENT_AND_GRID_REVIEW_REQUIRED",
            page_index=table.page_index,
            detail="Table-to-article relation and missing/spanned cells need human review",
        ))
    return result, issues
