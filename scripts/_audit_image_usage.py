from pathlib import Path
import json
import re

root = Path(__file__).resolve().parents[1]
report_dir = root / "scripts" / "reports" / "audit"
report_dir.mkdir(parents=True, exist_ok=True)
image_root = root / 'image'
image_exts = {'.png', '.jpg', '.jpeg', '.webp', '.gif', '.svg'}

md_files = sorted(
    [p for p in root.glob('*.md') if re.match(r'^\d+\.', p.name)],
    key=lambda p: int(re.match(r'^(\d+)\.', p.name).group(1)),
)

def slug_from_doc(path: Path) -> str:
    return re.sub(r'^\d+\.', '', path.stem).removesuffix('-tutorial')

def markdown_image_refs(text: str):
    return re.findall(r'!\[[^\]]*\]\(([^)]+)\)', text)

rows = []
for md in md_files:
    text = md.read_text(encoding='utf-8', errors='replace')
    slug = slug_from_doc(md)
    img_dir = image_root / slug
    refs = markdown_image_refs(text)
    image_refs = [r for r in refs if r.replace('\\', '/').lstrip('./').startswith('image/')]
    any_image_refs = refs
    dir_exists = img_dir.exists() and img_dir.is_dir()
    generated = []
    if dir_exists:
        generated = [p for p in img_dir.rglob('*') if p.is_file() and p.suffix.lower() in image_exts]
    rows.append({
        'article': int(re.match(r'^(\d+)\.', md.name).group(1)),
        'file': md.name,
        'slug': slug,
        'expectedImageDir': str(img_dir).replace('\\', '/'),
        'referencesImageDir': bool(image_refs),
        'markdownImageRefCount': len(refs),
        'imageDirRefCount': len(image_refs),
        'imageDirExists': dir_exists,
        'generatedImageCount': len(generated),
        'sampleRefs': image_refs[:5],
        'sampleGenerated': [str(p).replace('\\', '/') for p in generated[:5]],
    })

no_image_dir_ref = [r for r in rows if not r['referencesImageDir']]
no_dir = [r for r in rows if not r['imageDirExists']]
empty_dir = [r for r in rows if r['imageDirExists'] and r['generatedImageCount'] == 0]
has_generated_but_not_referenced = [r for r in rows if r['generatedImageCount'] > 0 and not r['referencesImageDir']]
ref_but_no_generated = [r for r in rows if r['referencesImageDir'] and r['generatedImageCount'] == 0]

report = {
    'totalMarkdownDocs': len(rows),
    'noImageDirReferenceCount': len(no_image_dir_ref),
    'missingImageDirCount': len(no_dir),
    'emptyImageDirCount': len(empty_dir),
    'hasGeneratedImagesButNoMarkdownReferenceCount': len(has_generated_but_not_referenced),
    'referencesImageDirButNoGeneratedImagesCount': len(ref_but_no_generated),
    'noImageDirReference': no_image_dir_ref,
    'missingImageDir': no_dir,
    'emptyImageDir': empty_dir,
    'hasGeneratedImagesButNoMarkdownReference': has_generated_but_not_referenced,
    'referencesImageDirButNoGeneratedImages': ref_but_no_generated,
}
report_path = report_dir / 'audit-image-usage-report.json'
report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')

print(f"totalMarkdownDocs={len(rows)}")
print(f"noImageDirReferenceCount={len(no_image_dir_ref)}")
print(f"missingImageDirCount={len(no_dir)}")
print(f"emptyImageDirCount={len(empty_dir)}")
print(f"hasGeneratedImagesButNoMarkdownReferenceCount={len(has_generated_but_not_referenced)}")
print(f"referencesImageDirButNoGeneratedImagesCount={len(ref_but_no_generated)}")
print(f'report={report_path.relative_to(root)}')

print('\n## no image/ markdown reference')
for r in no_image_dir_ref:
    print(f"{r['file']} | dir_exists={r['imageDirExists']} | generated={r['generatedImageCount']} | dir={r['expectedImageDir']}")

print('\n## missing expected image dir')
for r in no_dir:
    print(f"{r['file']} | expected={r['expectedImageDir']}")

print('\n## empty expected image dir')
for r in empty_dir:
    print(f"{r['file']} | dir={r['expectedImageDir']}")
