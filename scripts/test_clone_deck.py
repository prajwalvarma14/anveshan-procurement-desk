import zipfile
import re
import os
import pptx

src_pptx = 'DataSprint2.0_by_Anveshan_PPT_Template.pptx'
cloned_pptx = 'cloned_presentation.pptx'

# We want 9 slides total:
# Slide 1: Cover
# Slide 2: Team
# Slides 3 to 9: Content slides (7 content slides)

with zipfile.ZipFile(src_pptx, 'r') as zin:
    file_map = {item.filename: zin.read(item.filename) for item in zin.infolist()}

slide4_xml = file_map['ppt/slides/slide4.xml']
slide4_rels = file_map['ppt/slides/_rels/slide4.xml.rels']

# We need slides 3 to 9 to be clones of slide4
# Slide 3 in original had text structure instructions, slide 4 had EMPTY SLIDE.
# We will make slides 3, 4, 5, 6, 7, 8, 9 all clones of slide4!
for i in range(3, 10):
    file_map[f'ppt/slides/slide{i}.xml'] = slide4_xml
    file_map[f'ppt/slides/_rels/slide{i}.xml.rels'] = slide4_rels

# Update [Content_Types].xml
ct = file_map['[Content_Types].xml'].decode('utf-8')
for i in range(5, 10):
    entry = f'<Override PartName="/ppt/slides/slide{i}.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>'
    if entry not in ct:
        ct = ct.replace('</Types>', f'{entry}</Types>')
file_map['[Content_Types].xml'] = ct.encode('utf-8')

# Update ppt/_rels/presentation.xml.rels
pres_rels = file_map['ppt/_rels/presentation.xml.rels'].decode('utf-8')
# slide 3 and 4 already exist (rId4 and rId5)
# Add rId19 to rId23 for slides 5 to 9
for i, s_num in enumerate(range(5, 10), start=19):
    rel_entry = f'<Relationship Id="rId{i}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="slides/slide{s_num}.xml"/>'
    pres_rels = pres_rels.replace('</Relationships>', f'{rel_entry}</Relationships>')
file_map['ppt/_rels/presentation.xml.rels'] = pres_rels.encode('utf-8')

# Update ppt/presentation.xml
pres_xml = file_map['ppt/presentation.xml'].decode('utf-8')
# slide 3 and 4 were id 258 (rId4) and 259 (rId5)
# Add slides 5 to 9
sld_entries = ""
for i, s_num in enumerate(range(5, 10), start=19):
    sld_id = 260 + (s_num - 5)
    sld_entries += f'<p:sldId id="{sld_id}" r:id="rId{i}"/>'
pres_xml = pres_xml.replace('</p:sldIdLst>', f'{sld_entries}</p:sldIdLst>')
file_map['ppt/presentation.xml'] = pres_xml.encode('utf-8')

# Write out cloned_pptx
with zipfile.ZipFile(cloned_pptx, 'w', compression=zipfile.ZIP_DEFLATED) as zout:
    for fname, data in file_map.items():
        zout.writestr(fname, data)

print(f"Generated {cloned_pptx}!")
prs = pptx.Presentation(cloned_pptx)
print(f"Verified with python-pptx! Total slides: {len(prs.slides)}")
for idx, s in enumerate(prs.slides):
    print(f"  Slide {idx+1}: {len(s.shapes)} shapes")
