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
import random

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

def vectorize(line, ordered_languages, only_first):
	line_vector = np.zeros(len(ordered_languages))
	try:
		for word in word_tokenize(line):
			try:
				lem = get_lem(word)[0]
				curr_entry = ""
				if lem in etym_dict:
					curr_entry = etym_dict[lem]
					if only_first:
						cleaned_lang = clean_entry(curr_entry[0], acceptable_modifiers, list_of_languages, other_languages)
						idx = ordered_languages.keys().index(cleaned_lang)
						line_vector[idx] += 1
					else:
						for lang in curr_entry:
								cleaned_lang = clean_entry(lang, acceptable_modifiers, list_of_languages, other_languages)
								idx = ordered_languages.keys().index(cleaned_lang)
								line_vector[idx] += 1
			except:
				pass
	except:
		return False
	return line_vector

# function to remove any words in the entry that aren't languages or acceptable modifiers
def clean_entry(lang_entry, acceptable_modifiers, list_of_languages, other_languages):
	cleaned = ""
	for word in word_tokenize(lang_entry):
		if (word in acceptable_modifiers) or (word in list_of_languages) or (word in other_languages) or ("Proto" in word):
			cleaned += word + " "
	cleaned = cleaned.strip()
	return cleaned

def experiment(num_test, subjective_vectors, objective_vectors):
	training_data = []
	training_labels = []
	testing_data = []
	testing_labels = []
	testing_indices = random.sample(range(0, len(subjective_vectors)), num_test)
	for i in range(len(subjective_vectors)):
		if i in testing_indices:
			testing_data.append(subjective_vectors[i])
			testing_labels.append("subjective")
		else:
			training_data.append(subjective_vectors[i])
			training_labels.append("subjective")

	for i in range(len(objective_vectors)):
		if i in testing_indices:
			testing_data.append(objective_vectors[i])
			testing_labels.append("objective")
		else:
			training_data.append(objective_vectors[i])
			training_labels.append("objective")

	classifier = svm.SVC()
	classifier.fit(training_data, training_labels)
	predictions = classifier.predict(testing_data)

	misclassified = 0
	for i in range(len(predictions)):
		if predictions[i] != testing_labels[i]:
			misclassified += 1
	return misclassified




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

	subjective_vectors_onlyFirst = []
	subjective_vectors_all = []
	for i in range(len(subjective_content)):
		line = subjective_content[i]
		vec_onlyFirst = vectorize(line, ordered_languages, True)
		if type(vec_onlyFirst) != bool:
			subjective_vectors_onlyFirst.append(vec_onlyFirst)
		vec_all = vectorize(line, ordered_languages, False)
		if type(vec_all) != bool:
			subjective_vectors_all.append(vec_all)

	objective_vectors_onlyFirst = []
	objective_vectors_all = []
	for i in range(len(objective_content)):
		line = objective_content[i]
		vec_onlyFirst = vectorize(line, ordered_languages, True)
		if type(vec_onlyFirst) != bool:
			objective_vectors_onlyFirst.append(vec_onlyFirst)
		vec_all = vectorize(line, ordered_languages, False)
		if type(vec_all) != bool:
			objective_vectors_all.append(vec_all)

	misclassified_onlyFirst = []
	misclassified_all = []
	num_test = 100
	for i in range(5):
		print "-----Trial %d-----" % i
		curr_misclassified_onlyFirst = experiment(num_test, subjective_vectors_onlyFirst, objective_vectors_onlyFirst)
		misclassified_pct_onlyFirst = 100*(float(curr_misclassified_onlyFirst) / (num_test*2))
		print "%.1f%% correctly classified when only using first origin" % (100 - misclassified_pct_onlyFirst)
		misclassified_onlyFirst.append(misclassified_pct_onlyFirst)
		curr_misclassified_all = experiment(num_test, subjective_vectors_all, objective_vectors_all)
		misclassified_pct_all = 100*(float(curr_misclassified_all) / (num_test*2))
		print "%.1f%% correctly classified when using all origins" % (100 - misclassified_pct_all)
		misclassified_all.append(misclassified_pct_all)

