# Daniel Kwei Ayitiah memorial book: review notes

**Files**
- `Ayitiah-Memorial-Book-A5-64pp.pdf`: reading/proof copy. A5 (148 × 210 mm), 64 pages, fonts embedded.
- `Ayitiah-Memorial-Book-A5-64pp-PRINT-3mm-bleed.pdf`: same book with 3 mm bleed (154 × 216 mm) for the printer. No crop marks.
- `source/`: scripts used to build the book from the Word file (see "Rebuilding").

**Text:** every paragraph of the Word file is in the book, unchanged (checked by script: ~19,500 words). The only differences are the labels listed under "Wording I changed" below.

## Please confirm before printing

1. **Photos of the three sons.** In the Word file the photos sit between the tributes and are not labelled. I matched them in document order: Edwin → man in white shirt with grey hair, Ken → man in navy suit and bow tie, Nii Armah → younger man in white. Shirley Ann, Dorothy, Korkor and Selma's photos sit directly under their headings in the Word file, so those are certain. **Please check the three sons' photos.** The grandchildren/family photo (page 28), the minister greeting Mr. Ayitiah (page 34) and the two photos on pages 61–62 are placed where they appear in the Word file.
2. **Image quality.** The cover photo is a 553 × 837 px scan, so it will print slightly soft at 72 mm wide (about 175 dpi). Please send the original photo if one exists. Everything else is 250 dpi or better at the printed size. The small church-building image in the Word file (146 px) is not used.
3. **Garbled text in the source.** The Johnson Family tribute (page 49) has the line "Nii Odeneho Kwei the Kl1`kl1`!". That is how it is in the Word file; it looks like a mis-typed Ga word. Please supply the correct spelling.
4. **Capitals.** The Osu Salem classmates' tribute (page 41) is entirely in capital letters in the Word file. I kept it. Sentence case would be easier to read, but only the author should approve that.
5. **Printer.** Please confirm with the printer: 64 pages at A5, stapled (saddle-stitch) or glued spine. Stapled 64pp needs thin paper. Colour is RGB; ask whether they want CMYK (the navy cover may shift slightly).

## Wording I changed (headings only)
- Dropped Word working notes: "Cover page.", "BOOKMARK INFO", "(bookmark too)".
- "Tribute by wife/widow" → "Tribute by his wife"; "Tribute by nephews/nieces" → "Tribute by Nephews and Nieces"; "Tribute by the Church, Calvary Presbyterian Church" → "Tribute by the Church".
- "PART I @ 9:00 AM" → "Part I at 9:00 AM". Upper-case headings were converted to normal capitalisation.
- Order of service rows are numbered 1, 2, 3… in each part. The Word file typed "7." twice in Part II (Vote of Thanks, Benediction); the book numbers it 1–9. "BYTHE" in the Johnson tribute → "By the".
- Other spelling and punctuation in the tributes is exactly as supplied.

## Things I added (no new facts)
- Cover, inside-cover page (with the "A charge to keep I have" hymn from the bookmark notes), title page, contents (page numbers automatic), closing page and back cover. All text on these comes from the Word file.
- Page 4 contents; pages 61–62 "Family Photographs"; page 63 closing.

## Rebuilding
`source/` holds the generator (`book.py`, `book.css`, `parse_docx.py`, `run.py`, `render.js`, `verify_text.py`). It needs the Word file unzipped next to it, Chromium (Playwright) and the Google Fonts Crimson Pro, Cormorant Garamond, Inter and Gentium Book Plus. File paths inside the scripts point to the session's scratch folder and need adjusting on another machine.
