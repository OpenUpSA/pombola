#!/usr/bin/env python
"""Convert the Register of Members' Interests .docx into the *.json shape that
convert_to_import_json.py consumes.

This is the runnable version of docx_to_html_to_json.ipynb.

Usage:
    ./venv/bin/python docx_to_html_to_json.py register.docx 2026 2026-06-30 <source-url>

The first argument may also be an .html file from a previous run, in which case
the mammoth conversion is skipped and the html is re-parsed as-is.

Two things about the 2026 document that the notebook did not handle:

* Mammoth inlines the scanned page images as huge base64 <img> tags, and some
  of them land *inside* the heading elements, e.g.
  <ol><li><strong><img ...>PENSIONS</strong></li></ol>.  Every section regex
  keys off <strong>NAME</strong>, so those headings stopped matching and both
  the person split and the category extraction silently dropped data.  The
  images carry no information, so they are stripped up front.
* The MP name is emitted as <h2><a id="_bookmark7"></a>Surname, Title Given</h2>
  rather than the <ul><li><ol><li> nesting used in earlier years, so the name
  patterns fell through to a fallback that picked up the first section heading
  instead of the name.
"""

import json
import re
import sys

import mammoth
from bs4 import BeautifulSoup


CATEGORIES = [
    "SHARES AND OTHER FINANCIAL INTERESTS",
    "REMUNERATED EMPLOYMENT OR WORK OUTSIDE OF PARLIAMENT",
    "DIRECTORSHIPS AND PARTNERSHIPS",
    "CONSULTANCIES AND RETAINERSHIPS",
    "SPONSORSHIPS",
    "GIFTS AND HOSPITALITY",
    "BENEFITS AND INTERESTS FREE LOANS",
    "TRAVEL",
    "OWNERSHIP IN LAND AND PROPERTY",
    "PENSIONS",
    "RENTED PROPERTY",
    "INCOME GENERATING ASSETS",
    "TRUSTS",
]

# A few headings lose their bold run, so <strong> is optional
SECTION_PATTERN = (
    r"(<ol>\s*<li>\s*(?:<strong>)?\s*{}\s*(?:</strong>)?\s*</li>\s*</ol>.*?</table>)"
)

# The document is split into one chunk per person at the end of the TRUSTS table
PERSON_SPLIT_PATTERN = SECTION_PATTERN.format("TRUSTS")


def docx_to_html(file_path):
    with open(file_path, "rb") as docx_file:
        result = mammoth.convert_to_html(docx_file)
    return result.value


def clean_html(html):
    # Drop the scanned page images.  They are 40MB of base64 and, worse, some
    # of them sit inside the <strong> heading elements the parsing relies on.
    html = re.sub(r"<img[^>]*>", "", html)

    # Tables that span a page break come back as two tables; drop the repeated
    # header row so they read as one.
    html = re.sub(r"</table><table><tr>(.*?)</tr>", "", html)

    # Paragraphs inside <td>
    html = re.sub(r"</p><p>", " ", html)

    html = normalise_headings(html)

    return html


def normalise_headings(html):
    """Rewrite category headings that came through as plain paragraphs.

    Word's numbered lists mostly convert to <ol><li><strong>NAME</strong>,
    but a handful of them lose the list formatting and arrive as
    <p>7. GIFTS AND HOSPITALITY</p>, sometimes with the party name glued onto
    the front (<p>DA 1. SHARES AND OTHER FINANCIAL INTERESTS</p>).  Left alone
    those sections are invisible to the parsing below - and a stray TRUSTS
    heading also merges two people into one chunk.
    """
    for category in CATEGORIES:
        pattern = (
            r"<p>\s*(?P<prefix>[^<]*?)\s*(?:\d{1,2}\s*)?\.?\s*"
            + re.escape(category)
            + r"\s*</p>(?=<table)"
        )

        def replace(match):
            prefix = match.group("prefix").strip()
            paragraph = "<p>{0}</p>".format(prefix) if prefix else ""
            return paragraph + "<ol><li><strong>{0}</strong></li></ol>".format(
                category
            )

        html = re.sub(pattern, replace, html)

    return html


def strip_tags(html):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]*>", "", html)).strip()


def split_document_by_person(html):
    sections = re.split(PERSON_SPLIT_PATTERN, html, flags=re.DOTALL)

    combined = [
        sections[i] + sections[i + 1] for i in range(0, len(sections) - 1, 2)
    ]
    if len(sections) % 2 != 0:
        combined.append(sections[-1])

    return combined


def find_name_element(person_html):
    """Return the match for the element holding the MP's name, or None."""
    for pattern in (
        r"<h2>(.*?)</h2>",
        r"<ul><li><ol><li>(.*?)</li></ol></li></ul>",
    ):
        match = re.search(pattern, person_html, flags=re.DOTALL)
        if match:
            return match
    return None


def extract_person(person_html):
    name_match = find_name_element(person_html)
    if not name_match:
        return None

    name = strip_tags(name_match.group(1))
    if not name or name.upper() in CATEGORIES:
        return None

    title = ""
    # "Surname, Title Given Names" -> "Given Names Surname"
    parts = name.split(", ")
    surname = parts[0].strip()
    if len(parts) > 1:
        words = parts[1].split()
        title = words[0].strip()
        given_names = " ".join(words[1:]).strip()
        if not given_names:
            # No title, just a single given name ("Nkosi, Sithembile")
            title, given_names = "", title
        name = "{0} {1}".format(given_names, surname).strip()

    # The party is the paragraph between the name and the first section, if
    # the document bothered to repeat it there.
    after_name = person_html[name_match.end():]
    party_match = re.search(
        r"^(?:\s*)<p>(.*?)</p>", after_name, flags=re.DOTALL
    )
    if party_match:
        party = strip_tags(party_match.group(1))
    else:
        # Fall back to the party heading this person sits under
        heading = re.findall(r"<h1>(.*?)</h1>", person_html, flags=re.DOTALL)
        party = strip_tags(heading[-1]) if heading else None

    person = {"mp": name, "title": title, "party": party}
    for category in CATEGORIES:
        person[category] = extract_category(person_html, category)

    return person


def extract_category(person_html, category):
    matches = re.findall(
        SECTION_PATTERN.format(re.escape(category)), person_html, flags=re.DOTALL
    )
    if not matches:
        return None

    tables = re.findall(r"<table.*?>(.*?)</table>", matches[0], flags=re.DOTALL)
    if not tables:
        return None

    return parse_table("<table>" + tables[0] + "</table>")


def parse_table(html_table):
    soup = BeautifulSoup(html_table, "html.parser")
    rows = soup.find_all("tr")
    if not rows:
        return None

    headers = [header.get_text(strip=True) for header in rows[0].find_all("p")]

    data = []
    for row in rows[1:]:
        values = [value.get_text(strip=True) for value in row.find_all("p")]
        data.append(
            {
                headers[i]: values[i] if i < len(values) else ""
                for i in range(len(headers))
            }
        )

    return data


def main():
    docx_path = sys.argv[1] if len(sys.argv) > 1 else "register.docx"
    year = sys.argv[2] if len(sys.argv) > 2 else "2026"
    date = sys.argv[3] if len(sys.argv) > 3 else "2026-06-30"
    source = sys.argv[4] if len(sys.argv) > 4 else (
        "https://www.parliament.gov.za/storage/app/media/"
        "Register%20of%20Members%20Interests/"
        "Register_of_members_interests_june_{0}.pdf".format(year)
    )

    if docx_path.endswith(".html"):
        # Re-parse an html file produced by an earlier run
        with open(docx_path) as html_file:
            html = clean_html(html_file.read())
    else:
        html = clean_html(docx_to_html(docx_path))
        with open("output.html", "w") as html_file:
            html_file.write(html)

    people = []
    skipped = 0
    for person_html in split_document_by_person(html):
        person = extract_person(person_html)
        if person is None:
            skipped += 1
            continue
        people.append(person)

    output = {
        "date": date,
        "source": source,
        "year": year,
        "register": people,
    }

    out_name = "{0}.json".format(year)
    with open(out_name, "w") as outfile:
        json.dump(output, outfile, indent=2)

    missing = sum(
        1 for p in people for c in CATEGORIES if p[c] is None
    )
    sys.stderr.write(
        "{0}: {1} people, {2} chunks skipped, {3} missing category tables\n".format(
            out_name, len(people), skipped, missing
        )
    )


if __name__ == "__main__":
    main()
