import sys
import os
import re
import yaml

VALID_CATEGORIES = {
    'building_vulnerability',
    'earthquake_safety',
    'environmental_hazards',
    'local_context',
    'mitigation',
}

REQUIRED_FRONTMATTER_FIELDS = {'id', 'category', 'tags', 'source'}
REQUIRED_SOURCE_FIELDS = {'title', 'organization', 'url'}

def parse_frontmatter(text):
    match = re.match(r'^---\s*\n(.*?)\n---\s*\n?(.*)', text, re.DOTALL)
    if not match:
        raise ValueError("No valid YAML frontmatter found (must begin and end with '---')")
    raw_yaml = match.group(1)
    body = match.group(2).strip()
    metadata = yaml.safe_load(raw_yaml)
    if not isinstance(metadata, dict):
        raise ValueError("Frontmatter must evaluate to a YAML mapping (dictionary).")
    return metadata, body

def validate_frontmatter(metadata, file_path):
    errors = []
    basename = os.path.basename(file_path)
    for field in REQUIRED_FRONTMATTER_FIELDS:
        if field not in metadata or metadata[field] is None:
            errors.append(f"[{basename}] Missing required frontmatter field: '{field}'")
    doc_id = metadata.get('id')
    if doc_id is not None and not isinstance(doc_id, str):
        errors.append(f"[{basename}] Field 'id' must be a string, got {type(doc_id).__name__}")
    category = metadata.get('category')
    if category is not None:
        if isinstance(category, str):
            if category not in VALID_CATEGORIES:
                errors.append(f"[{basename}] Invalid category '{category}'. Must be one of: {sorted(VALID_CATEGORIES)}")
        else:
            errors.append(f"[{basename}] Field 'category' must be a string")
    tags = metadata.get('tags')
    if tags is not None and not isinstance(tags, list):
        errors.append(f"[{basename}] Field 'tags' must be a list, got {type(tags).__name__}")
    source = metadata.get('source')
    if source is not None:
        if isinstance(source, dict):
            for sf in REQUIRED_SOURCE_FIELDS:
                if sf not in source:
                    errors.append(f"[{basename}] Missing required source field: '{sf}'")
        else:
            errors.append(f"[{basename}] Field 'source' must be a mapping (dictionary)")
    applies = metadata.get('applies_when')
    if applies is not None and not isinstance(applies, dict):
        errors.append(f"[{basename}] Field 'applies_when' must be a mapping, got {type(applies).__name__}")
    return errors

# Test all markdown files
knowledge_dir = 'data/knowledge'
total_errors = 0
total_files = 0
total_chunks_estimate = 0

for root, dirs, files in os.walk(knowledge_dir):
    for fname in files:
        if fname.endswith('.md'):
            total_files += 1
            file_path = os.path.join(root, fname)
            with open(file_path, 'r', encoding='utf-8') as f:
                raw_text = f.read()
            try:
                metadata, body = parse_frontmatter(raw_text)
                errors = validate_frontmatter(metadata, file_path)
                if errors:
                    print(f'ERRORS in {fname}:')
                    for e in errors:
                        print(f'  {e}')
                    total_errors += len(errors)
                else:
                    # Estimate chunks (rough)
                    total_chunks_estimate += max(1, len(body) // 600)
                    print(f'OK: {fname} ({len(body)} chars)')
            except Exception as e:
                print(f'FAILED to parse {fname}: {e}')
                total_errors += 1

print(f'\n=== SUMMARY ===')
print(f'Files checked: {total_files}')
print(f'Validation errors: {total_errors}')
print(f'Estimated chunks: {total_chunks_estimate}')