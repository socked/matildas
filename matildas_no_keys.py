import urllib2
import json
import csv
import datetime
from nltk import tokenize
import re
import pandas as pd

bad_names = ['with', 'written', 'adapted', 'Various Illustrators', 'words', 'and', 'staff', 'the', 'by', 'edited', 'lyrics'] # to remove non-name author words
male_vocab = ['his', 'he', 'him', 'himself', 'man', 'boy']
female_vocab = ['her', 'she', 'hers', 'herself', 'woman', 'girl']
male_scores = dict(zip(male_vocab, [1] * len(male_vocab))) # make dict of words and scores of 1
female_scores = dict(zip(female_vocab, [1] * len(female_vocab)))


def get_books_on(date):
    """
    returns nyt bestsellers on a given week
    """
    books = []

    nyt_api_key = ''
    url = 'http://api.nytimes.com/svc/books/v2/lists/' + date + '/picture-books.json?&offset=&sortby=&sortorder=&api-key=' + nyt_api_key
    data = json.load(urllib2.urlopen(url))

    for item in data['results']:
        book_info = [date]
        for detail in item['book_details']:
            for k in ['primary_isbn13', 'title', 'author']:
                book_info.append(detail[k].encode('utf-8'))
        books.append(book_info)
    return books


def get_week_dates(start, end, step=datetime.timedelta(days=7)):
    """
    returns a list of dates
    """
    dates = []
    dt = start
    while dt <= end:
        date = dt.strftime("%Y-%m-%d")
        dates.append(date)
        dt += step

    return dates


def get_books(start=datetime.datetime(2008, 6, 3), end=datetime.datetime.today()):
    """
    returns list of bestselling books between given dates
    """
    dates = get_week_dates(start, end)
    books = map(get_books_on, dates)
    flattened = [val for sublist in books for val in sublist]
    
    return flattened


def get_descriptions(books):
    """
    submits a unique list of isbns to google books and returns a book description
    """
    google_api_key = ''
    uniques = unique(books)
    book_desc = []

    for b in uniques:
        url = 'https://www.googleapis.com/books/v1/volumes?q=isbn:' + b[1] + '&key=' + google_api_key
        data = json.load(urllib2.urlopen(url))
        items = data.get('items', [{'volumeInfo': {'description' : 'n/a'}}])
        description = items[0]['volumeInfo'].get('description', 'n/a').encode('utf-8')
        book_desc.append([b[2], b[3], description])

    return book_desc


def unique(books):
    """
    removes duplicates from a list of books
    """
    uniques = []
    isbns = []

    for book in books:
        if book[1] not in isbns:
            uniques.append(book)
            isbns.append(book[1])

    return uniques


def clean_author_names(name):
    """
    strips non-name words from an author field
    """
    author = name.split()
    author_clean = [word for word in author if word not in bad_names and len(word) > 1]

    return author_clean


def remove_author_from_one_desc(desc, author):
    """
    takes a book description and removes sentences that mention the author
    """
    clean_desc = []

    split_desc = tokenize.sent_tokenize(desc.decode('utf-8'))
    for sentence in split_desc:
        flag = False
        words = re.split('\W+', sentence)
        for word in words:
            if word in author or word == 'author' or word == 'illustrator':
                flag = True
            # elif word == 'author' or word == 'illustrator':
            #     flag = True
        if not flag:
            clean_desc.append(sentence)
    clean = ' '.join(clean_desc)
    return clean


def filter_descriptions(books):
    """
    takes a list of books and strips author mentions from book descriptions
    """
    clean_books = []

    for book in books:
        clean_author = clean_author_names(book[1])
        clean_desc = remove_author_from_one_desc(book[2], clean_author)
        clean_books.append([clean_author, clean_desc])

    return clean_books


def get_gender_scores(books):
    evaluated_books = []

    for book in books:
        description = book[1]
        desc_len = len(description.split())
        names = re.findall(r'[A-Z]\w+', description)
        name_scores = score_names(names)
        word_scores = score_words(description)
        evaluation = evaluate_gender_score(word_scores, name_scores)
        evaluated_books.append([name_scores, word_scores, evaluation, desc_len])

    return evaluated_books


def score_names(names):
    """
    sends list of names to genderize, returns gender counts
    """
    female_names = 0
    male_names = 0

    snip = ''.join(['name[%s]=%s&' % (index, name) for index, name in enumerate(names)])

    url = 'http://api.genderize.io/?' + snip
    if snip: 
        data = json.load(urllib2.urlopen(url))

        for entry in data:
            count = entry.get('count')
            if count > 60:
                gender = entry['gender']
                if gender == 'female':
                    female_names += 1
                elif gender == 'male':
                    male_names += 1

    return (female_names, male_names)


def score_words(description):
    
    male_words = 0
    female_words = 0
    words = re.split('\W+', description.lower())
    for word in words:
        male_words += male_scores.get(word, 0)
        female_words += female_scores.get(word, 0)
    return (female_words, male_words)


def evaluate_gender_score(word_scores, name_scores):

    female_score = name_scores[0] + word_scores[0]
    male_score = name_scores[1] + word_scores[1]

    if female_score == 0 and male_score == 0:
        evaluation = 'none'
    elif female_score > male_score:
        evaluation = 'female'
    elif male_score > female_score:
        evaluation = 'male'
    else:
        evaluation = 'tie'

    return evaluation


def get_one_author_gender(authors):
    """
    returns the gender of the (first) author
    """
    author_gender = 'n/a'
    if authors != []:
        url = 'http://api.genderize.io?name=' + authors[0]
        data = json.load(urllib2.urlopen(url))
        author_gender = data.get('gender', 'na')

    return author_gender


def make_dfs(books, descriptions, gender_evaluation, author_gender):
    """
    structures information into dataframes
    """

    books_dates_df = make_books_df(books)
    uniques_desc_df = make_uniques_df(descriptions, gender_evaluation, author_gender)
    df_all = pd.merge(books_dates_df, uniques_desc_df, on = 'title', how = 'outer')

    return df_all


def make_uniques_df(descriptions, gender_evals, author_gender):

    titles = [book[0] for book in descriptions]
    descs = [book[2] for book in descriptions]
    female_names = [book[0][0] for book in gender_evals]
    male_names = [book[0][1] for book in gender_evals]
    female_words = [book[1][0] for book in gender_evals]
    male_words = [book[1][1] for book in gender_evals]
    evaluation = [book[2] for book in gender_evals]
    desc_len = [book[3] for book in gender_evals]

    desc_df = pd.DataFrame({'title' : titles,
                       'description' : descs,
                       'female names' : female_names,
                       'male names' : male_names,
                       'female words' : female_words,
                       'male words' : male_words,
                       'evals' : evaluation,
                       'author gender' : author_gender,
                       'desc len' : desc_len})

    normalized = normalize_data(desc_df)
    desc_df['normalized female'] = normalized[0]
    desc_df['normalized male'] = normalized[1]

    desc_df.to_csv('uniques.csv')
    return desc_df


def normalize_data(dataframe):
    female_sum = dataframe['female names'] + dataframe['female words']
    male_sum = dataframe['male names'] + dataframe['male words']
    normalized_female = female_sum * 100 / dataframe['desc len']
    normalized_male = male_sum * 100 / dataframe['desc len']
    normalized_df = pd.DataFrame({'title' : dataframe['title'],
                                  'normalized female score' : normalized_female,
                                 'normalized male score' : normalized_male})
    normalized_df.to_csv('normalized_scores.csv')
    return (normalized_female, normalized_male)


def make_books_df(books):
    """
    creates dataframe with books and dates
    """
    dates = [book[0] for book in books]
    isbns = [book[1] for book in books]
    titles = [book[2] for book in books]
    authors = [book[3] for book in books]

    books_dates_df = pd.DataFrame({'date' : dates,
                       'isbn' : isbns,
                       'title' : titles,
                       'author' : authors})

    #weighted_books_descriptives(books_dates_df)
    books_dates_df.to_csv('books_dates.csv')
    return books_dates_df


def unique_books_descriptives():
    """
    calculates and prints proportions of unique books
    """
    uniques_df = pd.read_csv('uniques.csv', header = 0)
    gender = uniques_df.evals.value_counts()
    female_prop = gender['female'].astype(float)/(gender['female'] + gender['male'])
    male_prop = gender['male'].astype(float)/(gender['female'] + gender['male'])

    female_authors = uniques_df[uniques_df['author gender'] == 'female'].evals.value_counts()
    male_authors = uniques_df[uniques_df['author gender'] == 'male'].evals.value_counts()
    female_authors_female_prop = female_authors['female'].astype(float)/(female_authors['female'] + female_authors['male'])
    female_authors_male_prop = female_authors['male'].astype(float)/(female_authors['female'] + female_authors['male'])
    male_authors_female_prop = male_authors['female'].astype(float)/(male_authors['female'] + male_authors['male'])
    male_authors_male_prop = male_authors['male'].astype(float)/(male_authors['female'] + male_authors['male'])

    print 'unique books, females:', female_prop * 100
    print 'unique books, males:',  male_prop * 100
    print 'unique books, female authors, females:', female_authors_female_prop * 100
    print 'unique books, female authors, males:', female_authors_male_prop * 100
    print 'unique books, male authors, females:', male_authors_female_prop * 100
    print 'unique books, male authors, males:', male_authors_male_prop * 100
    print
    return

def weighted_books_descriptives():
    """
    calculates and prints proportions of weighted books
    """
    matildas_df = pd.read_csv('matildas.csv', header = 0)
    gender_all = matildas_df.evals.value_counts()
    female_prop_all = gender_all['female'].astype(float)/(gender_all['female'] + gender_all['male'])
    male_prop_all = gender_all['male'].astype(float)/(gender_all['female'] + gender_all['male'])

    all_female_authors = matildas_df[matildas_df['author gender'] == 'female'].evals.value_counts()
    all_male_authors = matildas_df[matildas_df['author gender'] == 'male'].evals.value_counts()
    all_female_authors_female_prop = all_female_authors['female'].astype(float)/(all_female_authors['female'] + all_female_authors['male'])
    all_female_authors_male_prop = all_female_authors['male'].astype(float)/(all_female_authors['female'] + all_female_authors['male'])
    all_male_authors_female_prop = all_male_authors['female'].astype(float)/(all_male_authors['female'] + all_male_authors['male'])
    all_male_authors_male_prop = all_male_authors['male'].astype(float)/(all_male_authors['female'] + all_male_authors['male'])

    print 'weighted books, females:', female_prop_all * 100
    print 'weighted books, males:',  male_prop_all * 100
    print 'weighted books, female authors, females:', all_female_authors_female_prop * 100
    print 'weighted books, female authors, males:', all_female_authors_male_prop * 100
    print 'weighted books, male authors, females:', all_male_authors_female_prop * 100
    print 'weighted books, male authors, males:', all_male_authors_male_prop * 100


def main():

    books = get_books()
    descriptions = get_descriptions(books)
    clean_desc = filter_descriptions(descriptions)
    gender_evaluation = get_gender_scores(clean_desc)
    author_gender = [get_one_author_gender(book[0]) for book in clean_desc]
    data = make_dfs(books, descriptions, gender_evaluation, author_gender)
    data.to_csv('matildas.csv')
    unique_books_descriptives()
    weighted_books_descriptives()

if __name__ == '__main__':
    main()