import sys
import os
import numpy as np
import sklearn
from sklearn import svm
from nltk import word_tokenize
import collections
from nltk.corpus import stopwords
from nltk.stem.wordnet import WordNetLemmatizer
from get_etym import get_lem

def build_etym_dict(etym_file):
	etym_dict = {}
	etym_file_content = open(etym_file).readlines()
	# each line in the file is in the form "word	[etymology]"
	# go through the lines in the file (skip the header)
	for line in etym_file_content[1:]:
		curr_etym = []
		line = line.rstrip()
		word, etym = line.split('\t')
		# remove the quotes and brackets
		etym = etym.replace("'", "")
		etym = etym[1:-1]
		for lang in etym.split(','):
			# strip any leading or trailing spaces and add it to curr_etym
			curr_etym.append(lang.strip())
		# none of the words in our etym_file are in there twice so we can just add them to the dictionary
		etym_dict[word] = curr_etym
	return etym_dict

def get_list_of_languages(etym_dict):
	languages = {}
	for word, entry in etym_dict.items():
	    for lang in entry:
	            if lang not in languages:
	                    languages[lang] = 1
	            else:
	                    languages[lang] += 1
	return languages

def get_cleaned_languages(languages_dict, acceptable_modifiers, list_of_languages, other_languages):
	cleaned_languages = {}
	for lang, count in languages.items():
		curr = clean_entry(lang, acceptable_modifiers, list_of_languages, other_languages)
		# add this cleaned entry to the dictionary
		if curr != "":
			if curr not in cleaned_languages:
				cleaned_languages[curr] = count
			else:
				cleaned_languages[curr] += count
	return cleaned_languages

def vectorize(line, ordered_languages):
	line_vector = np.zeros(len(ordered_languages))
	for word in word_tokenize(line):
		lem = get_lem(word)[0]
		curr_entry = ""
		if lem in etym_dict:
			curr_entry = etym_dict[lem]
			for lang in curr_entry:
				cleaned_lang = clean_entry(lang, acceptable_modifiers, list_of_languages, other_languages)
				idx = ordered_languages.keys().index(cleaned_lang)
				line_vector[idx] += 1
	return line_vector

# function to remove any words in the entry that aren't languages or acceptable modifiers
def clean_entry(lang_entry, acceptable_modifiers, list_of_languages, other_languages):
	cleaned = ""
	for word in word_tokenize(lang_entry):
		if (word in acceptable_modifiers) or (word in list_of_languages) or (word in other_languages) or ("Proto" in word):
			cleaned += word + " "
	cleaned = cleaned.strip()
	return cleaned


if __name__ == "__main__":
	lemmatizer = WordNetLemmatizer()
	stop_words = set(stopwords.words('english'))

	subjective_file = os.getcwd() + "/rotten_imdb/quote.tok.gt9.5000"
	subjective_content = open(subjective_file).readlines()
	objective_file = os.getcwd() + "/rotten_imdb/plot.tok.gt9.5000"
	objective_content = open(objective_file).readlines()

	etym_dict = build_etym_dict("scraped_etymologies.txt")

	languages = get_list_of_languages(etym_dict)
	acceptable_modifiers = ["Proto", "Old", "Middle", "High", "Low", "Late", "Medieval", "Modern", "Anglo-French", "American", "Canadian"]
	list_of_languages = []
	with open(os.getcwd() + "/list_of_languages.txt") as lol:
		content = lol.readlines()
		for line in content:
			list_of_languages.append(line.rstrip())
	other_languages = ["PIE", "Germanic", "Norse", "Etruscan", "Gaelic", "Italic", "Gaulish"]
	cleaned_languages = get_cleaned_languages(languages, acceptable_modifiers, list_of_languages, other_languages)
	ordered_languages = collections.OrderedDict(sorted(cleaned_languages.items(), key=lambda t: t[0]))


line = subjective_content[100]

	# print curr_entry

