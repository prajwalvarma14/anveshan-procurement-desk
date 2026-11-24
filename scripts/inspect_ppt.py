import pptx

prs = pptx.Presentation('DataSprint2.0_by_Anveshan_PPT_Template.pptx')
print(f"Slide count: {len(prs.slides)}")
print(f"Slide width: {prs.slide_width.inches} in ({prs.slide_width.pt} pt), height: {prs.slide_height.inches} in ({prs.slide_height.pt} pt)")

for idx, slide in enumerate(prs.slides):
    print(f"\n==================== SLIDE {idx+1} ====================")
    for shape in slide.shapes:
        if shape.has_text_frame:
            for p in shape.text_frame.paragraphs:
                p_text = p.text.strip()
                if p_text:
                    print(f"  [{shape.name}] (left={shape.left.inches:.2f}, top={shape.top.inches:.2f}, w={shape.width.inches:.2f}, h={shape.height.inches:.2f})")
                    print(f"    Text: {p_text}")
                    for r in p.runs:
                        c_str = str(r.font.color.rgb) if (r.font.color and r.font.color.type == 1) else 'inherit'
                        sz = f"{r.font.size.pt:.1f}pt" if r.font.size else 'inherit'
                        print(f"      Run: '{r.text}' | Font: {r.font.name} | Size: {sz} | Bold: {r.font.bold} | Color: {c_str}")
