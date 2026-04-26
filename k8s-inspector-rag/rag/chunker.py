import re


def chunk_by_headers(content, source):

    title_match = re.match(r'^# (.+)',content)
    doc_title = title_match.group(1) if title_match else source

    sections = re.split(r'\n(?=##)', content)

    chunks = []
    for section in sections:
        section = section.strip()
        if not section or section.startswith('#') and not section.startswith('##'):
            continue

        chunk_text = f"[{doc_title}]\n{section}"

        heading_match = re.match(r'## (.+)', section)
        heading = heading_match.group(1) if heading_match else "intro"

        chunks.append({
            "text": chunk_text,
            "source": source,
            "section": heading
        })
    
    return chunks
