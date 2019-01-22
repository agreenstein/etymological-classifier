# coding=utf-8
import numpy as np
import sklearn
from sklearn import svm
from nltk import word_tokenize, pos_tag
from nltk.stem.wordnet import WordNetLemmatizer
import random


# function that reads the contents of a file containing the etymologies of desired words and builds a dictionary
# in which the keys are the words and the etymologies are the values
def build_etym_dict(etym_file):
	etym_dict = {}
	etym_file_content = open(etym_file).readlines()
	# each line in the file is in the form "word	[etymology]"
	# go through the lines in the file (skip the header)
	for line in etym_file_content[1:]:
		curr_etym = []
		line = line.rstrip()
		# split into the word and the languages
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


# function that lemmatizes a given word
def get_lem(word):
	lemmatizer = WordNetLemmatizer()
	# structure of pos is (word, partOfSpeech)
	pos = pos_tag(word_tokenize(word))[0]
	# if the part of speech is an adjective, noun, or verb, then pass lemmatizer the part of speech for increased accuracy
	if pos[1][0].lower() in ['a','n','v']:
		return str(lemmatizer.lemmatize(pos[0],pos[1][0].lower())), pos[1][0].lower()
	# otherwise just pass lemmatizer the word
	else:
		return str(lemmatizer.lemmatize(pos[0])), pos[1][0].lower()


# function that creates a dictionary of all of the languages in a given dictionary of etymologies
# in the resulting dictionary, the languages present are the keys and the counts of those languages are the values
# sometimes non-languages or unwanted modifiers are present, so this needs to be cleaned
def get_list_of_languages(etym_dict):
	languages = {}
	# go through the words in the etymology dictionary
	for word, entry in etym_dict.items():
		# for each language in the entry, either add it to the dictionary or increment the dictionary count for that language
	    for lang in entry:
	            if lang not in languages:
	                    languages[lang] = 1
	            else:
	                    languages[lang] += 1
	return languages


# function to remove any words in the entry that aren't languages or acceptable modifiers
# it is used as part of the get_cleaned_languages function
# it takes in one phrase of an entry and returns a string of that phrase with any words that aren't languages or acceptable modifiers removed
def clean_entry(lang_entry, acceptable_modifiers, list_of_languages):
	cleaned = ""
	for word in word_tokenize(lang_entry):
		# special check for "proto" because sometimes languages are listed as, for example "Proto-Germanic", such that "proto" isn't an individual word
		if (word in acceptable_modifiers) or (word in list_of_languages) or ("Proto" in word):
			cleaned += word + " "
	# remove the extra space at the end
	cleaned = cleaned.strip()
	return cleaned


# function that takes in a language dictionary along with a list of acceptable modifiers
# and returns a dictionary containing only the languages in the original language dictionary that exist (with acceptable modifiers) in the list of languages
def get_cleaned_languages(languages_dict, acceptable_modifiers, list_of_languages):
	cleaned_languages = {}
	for lang, count in languages_dict.items():
		# clean the language entry
		curr = clean_entry(lang, acceptable_modifiers, list_of_languages)
		# add this cleaned language (and its count) to the dictionary
		# in the cases where a cleaned entry results in a language in the dictionary (e.g., when "West Germanic" is cleaned to "Germanic"), add to the count
		if curr != "":
			if curr not in cleaned_languages:
				cleaned_languages[curr] = count
			else:
				cleaned_languages[curr] += count
	return cleaned_languages


# function that takes in a given example from the data and an ordered list of the languages in the corpus, and finds the langauges present in that example
# the function also takes in a boolean, include_stopwords, that determines whether words in the stopwords list (also a parameter) should be included in the vectorization
# the function returns two vectors of length (number of languages) where an index in the vector corresponds to the index of a langauge in the ordered languages list
# and the value at that index represents the number of times that language is in the example
# the first vector uses only the first language in a given word's language list (so it represents the most recent language of origin)
# the other vector uses all of the langauges
# lastly, the function takes a variable indicating whether the vector values should be determined by the count of languages present or frequency (relative to number of words)
def vectorize(line, etym_dict, ordered_languages, acceptable_modifiers, list_of_languages, include_stopwords, stop_words, freq_or_count):
	# initialize the vectors
	vector_first = np.zeros(len(ordered_languages))
	vector_all = np.zeros(len(ordered_languages))
	words_added = 0
	try:
		for word in word_tokenize(line):
			if (include_stopwords == False) and (word in stop_words):
				continue
			else:
				try:
					lem = get_lem(word)[0]
					curr_entry = ""
					# the lem should be in the dictionary, but check just in case
					if lem in etym_dict:
						curr_entry = etym_dict[lem]
						first = True
						for lang in curr_entry:
							cleaned_lang = clean_entry(lang, acceptable_modifiers, list_of_languages)
							idx = ordered_languages.keys().index(cleaned_lang)
							if first == True:
								vector_first[idx] += 1
							vector_all[idx] += 1
							first = False
						words_added += 1
				# if there's a problem with getting the languages for a given word, skip it
				except Exception as e:
					# print e
					pass
	# if there are any problems with word tokenizing the line, return false
	except Exception as e:
		# print e
		return False
	if freq_or_count == "frequency":
		if words_added != 0:
			for i in range(len(vector_first)):
				vector_first[i] /= float(words_added)
				vector_all[i] /= float(words_added)
	return vector_first, vector_all


def get_vectors(content, etym_dict, ordered_languages, acceptable_modifiers, list_of_languages, include_stopwords, stop_words, freq_or_count):
	vectors_first = []
	vectors_all = []
	for line in content:
		# vectorize the line, if there's an error (because it returned False, which isn't iterable) then skip
		try:
			vector_first, vector_all = vectorize(line, etym_dict, ordered_languages, acceptable_modifiers, list_of_languages, include_stopwords, stop_words, freq_or_count)
			vectors_first.append(vector_first)
			vectors_all.append(vector_all)
		except:
			pass
	return vectors_first, vectors_all

# function to generate a testing indices of a list of vectors for a given number of folds
# this function will create an array of length (num_folds) in which each element contains the indices of (number of vectors / num_folds) vectors that
# represent the testing data for a given fold
def generate_folds(vectors, num_folds):
	testing_data_indices = []
	num_vectors = len(vectors)
	# figure out how many examples are in each fold given the desired number of folds and the total number of examples
	fold_size = num_vectors / num_folds
	# Randomly generate a list of the indices between 0 and the number of vectors (sample without replacement so each index is in there only once)
	rand_indices = random.sample(xrange(num_vectors), num_vectors)
	# for each fold, take the next fold_size number of indices and put them in testing_data_indices
	for fold_count in range(num_folds):
		# the testing indices of the first fold are 0:fold_size-1, the second are fold_size:2*fold_size-1, and so on
		start = fold_size * fold_count
		end = fold_size * (fold_count + 1)
		if fold_count != num_folds - 1:
			curr_indices = rand_indices[start:end]
		else:
			# if we're at the end, just take all of the remaining vectors
			curr_indices = rand_indices[start:(len(rand_indices))]
		testing_data_indices.append(curr_indices)
	return testing_data_indices


# function to get the testing and training vectors for a the testing/training indices in a given fold
# it is passed the testing indices for the fold and vectors, and the label
# it separates the vectors into testing/training data depending on whether a given vector's index is in the testing indices or not
# the function returns arrays of the testing and training data and labels for the fold
def get_data_for_fold(testing_data_indices, vectors, label):
	training_data = []
	training_labels = []
	testing_data = []
	testing_labels = []
	# go through the indices in range of the number of vectors and put the data into testing/training depending on if the the index is in testing indices
	for i in range(len(vectors)):
		if i in testing_data_indices:
			testing_data.append(vectors[i])
			testing_labels.append(label)
		else:
			training_data.append(vectors[i])
			training_labels.append(label)
	return training_data, training_labels, testing_data, testing_labels 



# function that builds an svm classifier, fits training data using training labels, and makes predictions on testing data
# the function returns the predictions array
def classify_svm(training_data, training_labels, testing_data):
	classifier = svm.SVC()
	classifier.fit(training_data, training_labels)
	predictions = classifier.predict(testing_data)
	return predictions


# function that finds predictions that were misclassified
# the function keeps track of the indices in the testing/prediction data where the misclassifications were made 
# and returns that array so that the misclassified examples can be accessed later (the total number of miclassifications can be found by determining the length of the array)
def find_errors(predictions, testing_labels):
	misclassified_indices = []
	for i in range(len(predictions)):
		if predictions[i] != testing_labels[i]:
			misclassified_indices.append(i)
	return misclassified_indices


