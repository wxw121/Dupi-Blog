from pathlib import Path
import json
import re

root = Path(__file__).resolve().parents[1]
report_dir = root / "scripts" / "reports" / "audit"
report_dir.mkdir(parents=True, exist_ok=True)
image_root = root / 'image'
image_exts = {'.png', '.jpg', '.jpeg', '.webp', '.gif', '.svg'}

numbered_md = sorted(
    [p for p in root.glob('*.md') if re.match(r'^\d+\.', p.name)],
    key=lambda p: int(re.match(r'^(\d+)\.', p.name).group(1)),
)

def slug_from_doc(path: Path) -> str:
    stem = re.sub(r'^\d+\.', '', path.stem)
    if stem.endswith('-tutorial'):
        stem = stem[:-len('-tutorial')]
    return stem

def markdown_image_refs(text: str):
    return re.findall(r'!\[[^\]]*\]\(([^)]+)\)', text)

rows = []
for md in numbered_md:
    text = md.read_text(encoding='utf-8', errors='replace')
    number = int(re.match(r'^(\d+)\.', md.name).group(1))
    slug = slug_from_doc(md)
    expected_dir = image_root / slug
    refs = markdown_image_refs(text)
    image_refs = [r for r in refs if r.replace('\\', '/').lstrip('./').startswith('image/')]
    dir_exists = expected_dir.exists() and expected_dir.is_dir()
    generated = []
    if dir_exists:
        generated = sorted(
            [p for p in expected_dir.rglob('*') if p.is_file() and p.suffix.lower() in image_exts],
            key=lambda p: str(p).lower(),
        )
    rows.append({
        'article': number,
        'file': md.name,
        'slug': slug,
        'expectedImageDir': str(expected_dir).replace('\\', '/'),
        'hasMarkdownImageReference': bool(refs),
        'referencesImageDir': bool(image_refs),
        'markdownImageRefCount': len(refs),
        'imageDirRefCount': len(image_refs),
        'imageDirExists': dir_exists,
        'generatedImageCount': len(generated),
        'sampleRefs': image_refs[:5],
        'sampleGenerated': [str(p).replace('\\', '/') for p in generated[:5]],
    })

no_image_dir_reference = [r for r in rows if not r['referencesImageDir']]
missing_image_dir = [r for r in rows if not r['imageDirExists']]
empty_image_dir = [r for r in rows if r['imageDirExists'] and r['generatedImageCount'] == 0]
no_generated_images = [r for r in rows if not r['imageDirExists'] or r['generatedImageCount'] == 0]
has_generated_but_not_referenced = [r for r in rows if r['generatedImageCount'] > 0 and not r['referencesImageDir']]
references_image_dir_but_no_generated = [r for r in rows if r['referencesImageDir'] and r['generatedImageCount'] == 0]

report = {
    'totalMarkdownDocs': len(rows),
    'noImageDirReferenceCount': len(no_image_dir_reference),
    'noGeneratedImagesCount': len(no_generated_images),
    'missingImageDirCount': len(missing_image_dir),
    'emptyImageDirCount': len(empty_image_dir),
    'hasGeneratedImagesButNoMarkdownReferenceCount': len(has_generated_but_not_referenced),
    'referencesImageDirButNoGeneratedImagesCount': len(references_image_dir_but_no_generated),
    'noImageDirReference': no_image_dir_reference,
    'noGeneratedImages': no_generated_images,
    'missingImageDir': missing_image_dir,
    'emptyImageDir': empty_image_dir,
    'hasGeneratedImagesButNoMarkdownReference': has_generated_but_not_referenced,
    'referencesImageDirButNoGeneratedImages': references_image_dir_but_no_generated,
}
report_path = report_dir / 'audit-image-usage-report-rerun.json'
report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')

print(f'totalMarkdownDocs={len(rows)}')
print(f'noImageDirReferenceCount={len(no_image_dir_reference)}')
print(f'noGeneratedImagesCount={len(no_generated_images)}')
print(f'missingImageDirCount={len(missing_image_dir)}')
print(f'emptyImageDirCount={len(empty_image_dir)}')
print(f'hasGeneratedImagesButNoMarkdownReferenceCount={len(has_generated_but_not_referenced)}')
print(f'referencesImageDirButNoGeneratedImagesCount={len(references_image_dir_but_no_generated)}')
print(f'report={report_path.relative_to(root)}')

print('\n## generated images exist but markdown does not reference image/')
for r in has_generated_but_not_referenced:
    print(f"{r['file']} | generated={r['generatedImageCount']} | dir={r['expectedImageDir']}")

print('\n## no image/ reference in markdown')
for r in no_image_dir_reference:
    print(f"{r['file']} | generated={r['generatedImageCount']} | dir_exists={r['imageDirExists']} | dir={r['expectedImageDir']}")

print('\n## no generated images')
for r in no_generated_images:
    reason = 'missing_dir' if not r['imageDirExists'] else 'empty_dir'
    print(f"{r['file']} | {reason} | dir={r['expectedImageDir']}")
