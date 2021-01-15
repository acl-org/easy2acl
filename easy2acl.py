#!/usr/bin/env python3

#
# easy2acl.py - Convert data from EasyChair for use with ACLPUB
#
# Original Author: Nils Blomqvist
# Forked/modified by: Asad Sayeed
# Further modifications and docs (for 2019 Anthology): Matt Post
# Index for LaTeX book proceedings: Mehdi Ghanimifard and Simon Dobnik
#
# Please see the documentation in the README file at http://github.com/acl-org/easy2acl.

import os
import re
import sys

from csv import DictReader
from glob import glob
from shutil import copy, rmtree
from unicode_tex import unicode_to_tex
from pybtex.database import BibliographyData, Entry
from PyPDF2 import PdfFileReader


def texify(string):
    """Return a modified version of the argument string where non-ASCII symbols have
    been converted into LaTeX escape codes.

    """
    return ' '.join(map(unicode_to_tex, string.split())).replace(r'\textquotesingle', "'")


#,----
#| Metadata
#`----
metadata = { 'chairs': [] }
with open('meta') as metadata_file:
    for line in metadata_file:
        key, value = line.rstrip().split(maxsplit=1)
        if key == 'chairs':
            metadata[key].append(value)
        else:
            metadata[key] = value

for key in 'abbrev volume title shortbooktitle booktitle month year location publisher chairs'.split():
    if key not in metadata:
        print('Fatal: missing key "{}" from "meta" file'.format(key))
        print("Please see the documentation at https://acl-org.github.io/ACLPUB/anthology.html.")
        sys.exit(1)

for key in "bib_url volume_name short_booktitle type".split():
    if key in metadata:
        print('Fatal: bad key "{}" in the "meta" file'.format(key))
        print("Please see the documentation at https://acl-org.github.io/ACLPUB/anthology.html.")
        sys.exit(1)

venue = metadata["abbrev"]
volume_name = metadata["volume"]
year = metadata["year"]

#
# Build a dictionary of submissions (which has author information).
#
submissions = {}

with open('submissions') as submissions_file:
    for line in submissions_file:
        entry = line.rstrip().split("\t")
        submission_id = entry[0]
        authors = entry[1].replace(' and', ',').split(', ')
        title = entry[2]

        submissions[submission_id] = (title, authors)
    print("Found ", len(submissions), " submitted files")

#
# Append each accepted submission, as a tuple, to the 'accepted' list.
# Order in this file is used to determine program order.
#
accepted = []

with open('accepted') as accepted_file:
    for line in accepted_file:
        entry = line.rstrip().split("\t")
        # modified here to filter out the rejected files rather than doing
        # that by hand
        if entry[-1] == 'ACCEPT':
            submission_id = entry[0]
            title = entry[1]
            authors = submissions[submission_id][1]

            accepted.append((submission_id, title, authors))
    print("Found ", len(accepted), " accepted files")

# Read abstracts
abstracts = {}
if os.path.exists('submission.csv'):
    with open('submission.csv') as csv_file:
        d = DictReader(csv_file)
        for row in d:
            abstracts[row['#']] = row['abstract']
    print('Found ', len(abstracts), 'abstracts')
else:
    print('No abstracts available.')

#
# Find all relevant PDFs
#

# The PDF of the full proceedings
full_pdf_file = 'pdf/{}_{}.pdf'.format(venue, year)
if not os.path.exists(full_pdf_file):
    print("Fatal: could not find full volume PDF '{}'".format(full_pdf_file))
    sys.exit(1)

# The PDF of the frontmatter
frontmatter_pdf_file = 'pdf/{}_{}_frontmatter.pdf'.format(venue, year)
if not os.path.exists(frontmatter_pdf_file):
    print("Fatal: could not find frontmatter PDF file '{}'".format(frontmatter_pdf_file))
    sys.exit(1)

# File locations of all PDFs (seeded with PDF for frontmatter)
pdfs = { '0': frontmatter_pdf_file }
for pdf_file in glob('pdf/{}_{}_paper_*.pdf'.format(venue, year)):
    submission_id = pdf_file.split('_')[-1].replace('.pdf', '')
    pdfs[submission_id] = pdf_file

# List of accepted papers (seeded with frontmatter)
accepted.insert(0, ('0', metadata['booktitle'], metadata['chairs']))

#
# Create Anthology tarball
#

# Create destination directories
for dir in ['bib', 'pdf']:
    dest_dir = os.path.join('proceedings/cdrom', dir)
    if not os.path.exists(dest_dir):
        os.makedirs(dest_dir)

# Copy over "meta" file
print('COPYING meta -> proceedings/meta', file=sys.stderr)
copy('meta', 'proceedings/meta')

final_bibs = []
start_page = 1
for paper_id, entry in enumerate(accepted):
    submission_id, paper_title, authors = entry
    authors = ' and '.join(authors)
    if not submission_id in pdfs:
        print('Fatal: no PDF found for paper', paper_id, file=sys.stderr)
        sys.exit(1)

    pdf_path = pdfs[submission_id]
    dest_path = 'proceedings/cdrom/pdf/{}.{}-{}.{}.pdf'.format(year, venue, volume_name, paper_id)

    copy(pdf_path, dest_path)
    print('COPYING', pdf_path, '->', dest_path, file=sys.stderr)

    bib_path = dest_path.replace('pdf', 'bib')
    if not os.path.exists(os.path.dirname(bib_path)):
        os.makedirs(os.path.dirname(bib_path))

    anthology_id = os.path.basename(dest_path).replace('.pdf', '')

    bib_type = 'inproceedings' if submission_id != '0' else 'proceedings'
    bib_entry = Entry(bib_type, [
        ('author', authors),
        ('title', paper_title),
        ('year', metadata['year']),
        ('month', metadata['month']),
        ('address', metadata['location']),
        ('publisher', metadata['publisher']),
    ])

    # Add page range if not frontmatter
    if paper_id > 0:
        with open(pdf_path, 'rb') as in_:
            file = PdfFileReader(in_)
            last_page = start_page + file.getNumPages() - 1
            bib_entry.fields['pages'] = '{}--{}'.format(start_page, last_page)
            start_page = last_page + 1

    # Add the abstract if present
    if submission_id in abstracts:
        bib_entry.fields['abstract'] = abstracts.get(submission_id)

    # Add booktitle for non-proceedings entries
    if bib_type == 'inproceedings':
        bib_entry.fields['booktitle'] = metadata['booktitle']

    try:
        bib_string = BibliographyData({ anthology_id: bib_entry }).to_string('bibtex')
    except TypeError as e:
        print('Fatal: Error in BibTeX-encoding paper', submission_id, file=sys.stderr)
        sys.exit(1)
    final_bibs.append(bib_string)
    with open(bib_path, 'w') as out_bib:
        print(bib_string, file=out_bib)
        print('CREATED', bib_path)

# Create an index for LaTeX book proceedings
if not os.path.exists('book-proceedings'):
    os.makedirs('book-proceedings')

with open('book-proceedings/all_papers.tex', 'w') as book_file:
    for entry in accepted:
        submission_id, paper_title, authors = entry
        if submission_id == '0':
            continue
        if len(authors) > 1:
            authors = ', '.join(authors[:-1]) + ' and ' + authors[-1]
        else:
            authors = authors[0]

        print("""\goodpaper{{../{pdf_file}}}{{{title}}}%
{{{authors}}}\n""".format(authors=texify(authors), pdf_file=pdfs[submission_id], title=texify(paper_title)), file=book_file)


# Write the volume-level bib with all the entries
dest_bib = 'proceedings/cdrom/{}-{}.bib'.format(venue, year)
with open(dest_bib, 'w') as whole_bib:
    print('\n'.join(final_bibs), file=whole_bib)
    print('CREATED', dest_bib)

# Copy over the volume-level PDF
dest_pdf = dest_bib.replace('bib', 'pdf')
print('COPYING', full_pdf_file, '->', dest_pdf, file=sys.stderr)
copy(full_pdf_file, dest_pdf)
