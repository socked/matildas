matildas
========

This Python program aims to document gender of characters in currently popular children's books.

1. The New York Times bestselling picture books list is pulled (available dating back to June 2008).
2. More elaborate descriptions of each book are accessed through Google Books.
3. Sentences containing author names are removed from the book descriptions, to keep the focus on character genders.
4. The descriptions are scored for gender-relevant words, such as gendered pronouns and proper names (sent to a gendered database of names).
5. Author names are categorized using the genderized database of names.
6. Data is analyzed, including normalization for number of gendered terms (words + names) for length of description.

The html uses d3.js to display some of the findings.

1. Books are charted depending on the male and female term frequency (normalized for description length). Hover over a datapoint to see the name of the book.
2. A summary of the number of books that are male character dominant versus female character dominant is printed on the chart.
3. The default/initial display shows all books analyzed. Click on the top buttons to view only the books authored by a male or only books authored by a female.
