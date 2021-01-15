# easy2acl.py

This short script is useful in the scenario where peer-reviewing is done using EasyChair but proceedings are to be produced with aclpub.
The user must retrieve information from EasyChair before running the script.

Please report bugs and suggest improvements.

## Prerequisites

The Python 3 `unicode_tex` package is needed and can be installed using pip (`pip3 install -r requirements.txt`).
The tar command is also needed (and should be available at PATH).

## How to run

Create the files `meta`, `accepted`, `submissions`, and the folder `pdf` as shown.
More details can be found below in [Getting data from EasyChair](#getting-data-from-easychair).
Before running `easy2acl.py`, your file structure should look like this:

    |-- meta                # conference metadata
    |-- submissions         # copied list of submissions
    |-- submission.csv      # (optional) to include abstracts
    |-- accepted            # copied list of accepted papers
    `-- pdf
        |-- ${abbrev}_${year}.pdf              # full volume of consolidated PDFs
        |-- ${abbrev}_${year}_frontmatter.pdf  # front matter of proceedings
        |-- ${abbrev}_${year}_paper_1.pdf
        |-- ${abbrev}_${year}_paper_2.pdf
        `-- ...

(where ${abbrev} and ${year} are defined in the `meta` file, see below)

When you run the script for the first time, create a dummy pdf file for the full volume consolidated PDF file and the front matter proceedings file using the above file naming convention.
We will replace the dummy files later and repeat the procedure.

Run the script:

    $ python3 easy2acl.py

When the script has finished, you will see the following additional files in the `proceedings` folder.

    |-- proceedings/
        `-- cdrom/
            |-- ${abbrev}-${year}.bib     # all bib entries
            |-- ${abbrev}-${year}.pdf     # entire volume
            |-- bib/
            |   |-- {year}.{abbrev}-{volume}.0.bib  # frontmatter
            |   |-- {year}.{abbrev}-{volume}.1.bib  # first paper
            |   |-- {year}.{abbrev}-{volume}.2.bib  # second paper
            |   `-- ...
            `-- pdf/
                |-- {year}.{abbrev}-{volume}.0.pdf  # frontmatter
                |-- {year}.{abbrev}-{volume}.1.pdf  # first paper
                |-- {year}.{abbrev}-{volume}.2.pdf  # second paper
                `-- ...

This is the input format that [the ingestion scripts for the ACL Anthology](https://github.com/acl-org/ACLPUB) expect.

The `easyacl.py` script also creates a file `book-proceedings/all_papers.tex` which contains an index of files that is read in automatically by `book-proceedings.tex`.
This document can be used to generate a full volume consolidated PDF file.
This file contains front matter (which you should edit), and automatically creates a table of contents and includes all papers from `all_papers.tex`.
To create the book proceedings simply edit the front matter and recompile `book_proceedings.tex`.
Copy `book-proceedings.pdf` to `${abbrev}_${year}_frontmatter.pdf` in your `pdf` folder.
To create `${abbrev}_${year}_frontmatter.pdf` extract the front matter pages with roman page numbers from `book-proceedings.pdf`.
Finally, re-run `python3 easy2acl.py` to replace the dummy full book proceedings and front matter files in the `proceedings` folder that you will use in the next step.

Once this data is generated, you can proceed with ACLPUB to generate the XML ingestion file and layout that the Anthology requires.


## Additional information

It is your responsibility to make sure that the input files above are created correct.
Easychair may change, and the author(s) of this script make no claims that this script works as intended.
Below are some things to look out for regarding the data you get from EasyChair, and the assumptions made by the script.

* **Title of submission in EasyChair does not match title in the submitted PDF.** In case of a substantial change to the title, and depending on the policy of your conference, you might want to contact the Program Chair.  You might want to do so anyways in case the title is used anywhere else, for example in the conference program.

* **Order of authors of submission in EasyChair does not match the order in the submitted PDF.**

* **Author has multiple names before the last name, e.g. `<first> <middle> <last>`.** This can cause problems with the order of the papers since they are written in alphabetical order according to the first author's last name. The script assumes the format `<first> [<first> <first> ...] <last>`.

* **Some diacritics and special characters in names are not converted by the script.** Certain characters that you expected to be translated into LaTeX escape codes, but were not, might be because they are not handled in the unicode_tex package.
  Make sure that the name was properly written in EasyChair; it might be that the person who entered the name forgot to add diacritics.
  If you want to be nice, you can check the names in your resulting `bib/` files against the names of the actual submissions and make the appropriate changes.

## Getting data from EasyChair

Start by downloading the actual submissions: In EasyChair, go to the page _Submissions_ and click the link _Download submissions_ found in the upper right hand side. Extract the PDF files to a folder `pdf`. See [How to run](#how-to-run) for the file structure.

### The metadata file

The `meta` file defines a number of conference-level values that are needed to generate the BibTeX and to interpret the file names.
Information on the layout and format of this file can be found on [this page in the ACLPUB documentation](https://acl-org.github.io/ACLPUB/anthology.html#the-meta-file).

An example file can be found [here](example-files/meta).

### Information about all submissions

On the same page _Submissions_: In the table, starting with the first submission entry (excluding the first row/header starting with `#`), select and copy the entire table. Copy and paste this into a proper text editor of your choice and save the file as `submissions`. Remember to not force any linebreaks. Each row in the table should correspond to one line in the resulting file. A sample `submissions` file is available [here](example-files/submissions).

We now have information about all the submissions but not whether they are accepted or not. Of course we do not want to include the rejected submissions. We need to get one more piece of information.

### A list of the accepted submissions

Go to _Status -> All submissions_.
Here we find the information on what submissions are accepted.
Copy the content of this table as you did with the previous one. Save the content as `accepted`, and make sure that each row in the table corresponds to one line in the resulting file.
A sample `accepted` file is available [here](example-files/accepted).
**Please note**: the generated proceedings will order the papers in the order they are found in this file.
Please reorder the entires in `accepted' according to the order you would like them displayed (typically, the order they are presented in the program).

### Abstracts

If you wish to have abstracts included on the Anthology paper pages ([example](https://www.aclweb.org/anthology/P18-1020/)), you will need to provide that information to the script.
This information can be found in the file `submission.csv` (it is possible this is only available with the paid version of Easychair).
Place this file in the directory as described above.
If present, the abstracts will be generated into the BibTeX files for ingestion by the Anthology scripts.

### A short explanation of the steps above

Neither of the two pages we saved data from alone contain all the information we need to create the necessary files.
The _Submissions_ page does not say which papers are accepted, and the _Status page_ does not tell us the author names of the papers.
By taking the intersection of the submission IDs of the two lists that we saved, we get the information we need about the accepted submissions.

Copying the table contents directly from the web browser results in a nice tab separated list when pasting into a text editor.
This makes it easy to work with, and if the table format should change in EasyChair it is simple to adapt the script.
