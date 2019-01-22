# coding=utf-8
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
import etym_classifier_utils as utils
import time


# this script should be called from the command line as follows:
# python experiment.py <results_output_file>
if __name__ == "__main__":
	start_time = time.time()
	outfile = sys.argv[1]
	output = open(outfile, 'w')
	output.write("-------Experiment Results-------\n")
	permutation_counter = 0

	lemmatizer = WordNetLemmatizer()
	stop_words = set(stopwords.words('english'))

	subjective_file = os.getcwd() + "/rotten_imdb/quote.tok.gt9.5000"
	subjective_content = open(subjective_file).readlines()
	objective_file = os.getcwd() + "/rotten_imdb/plot.tok.gt9.5000"
	objective_content = open(objective_file).readlines()

	etym_dict = utils.build_etym_dict("scraped_etymologies.txt")

	all_languages = utils.get_list_of_languages(etym_dict)
	# define the list of language modifiers that are acceptable
	acceptable_modifiers = ["Proto", "Old", "Middle", "High", "Low", "Late", "Medieval", "Modern", "Anglo-French", "American", "Canadian"]
	list_of_languages = []
	# read in a list of possible languages (from wiktionary)
	with open(os.getcwd() + "/list_of_languages.txt") as list_of_languages_file:
		content = list_of_languages_file.readlines()
		for line in content:
			list_of_languages.append(line.rstrip())
	other_languages = ["PIE", "Germanic", "Norse", "Etruscan", "Gaelic", "Italic", "Gaulish"]
	list_of_languages += other_languages
	cleaned_languages = utils.get_cleaned_languages(all_languages, acceptable_modifiers, list_of_languages)
	ordered_languages = collections.OrderedDict(sorted(cleaned_languages.items(), key=lambda t: t[0]))
	print "Languages cleaned"

	include_stopwords_options = [True, False]
	# outer loop of experiment: vary whether we include stopwords or not
	for include_stopwords in include_stopwords_options:
		print "-------Experiment variation: include_stopwords set to %s-------" % include_stopwords
		output.write("-------Experiment variation: include_stopwords set to %s-------\n" % include_stopwords)
		freq_or_count_options = ["count", "frequency"]
		# second loop: vary whether we generate vectors using language frequency or count
		for freq_or_count in freq_or_count_options:
			print "-------Experiment variation: vectors created using language %s-------" % freq_or_count
			output.write("-------Experiment variation: vectors created using language %s-------\n" % freq_or_count)
			subjective_vectors_first, subjective_vectors_all = utils.get_vectors(subjective_content, etym_dict, ordered_languages, acceptable_modifiers, list_of_languages, include_stopwords, stop_words, freq_or_count)
			objective_vectors_first, objective_vectors_all = utils.get_vectors(objective_content, etym_dict, ordered_languages, acceptable_modifiers, list_of_languages, include_stopwords, stop_words, freq_or_count)
			print "Vectors created"

			num_folds = 10
			subjective_testing_indices = utils.generate_folds(subjective_vectors_first, num_folds)
			objective_testing_indices = utils.generate_folds(objective_vectors_first, num_folds)
			first_or_all_languages_options = ["first language", "all languages"]
			# third loop: vary whether we use all the etymology information or just the most recent language
			# this is the third loop because it doesn't require that the vectors are remade, so for efficiency it should be within the other two loops
			for parameter in first_or_all_languages_options:
				print "-------Experiment variation: using %s-------" % parameter
				output.write("-------Experiment variation: using %s-------\n" % parameter)
				print "--Perumutation %d--" % permutation_counter
				permutation_counter += 1
				misclassified_indices_for_exp = []
				for i in range(num_folds):
					# split the data into testing and training given the indices for the current fold
					if parameter == "first language":
						sub_training_data, sub_training_labels, sub_testing_data, sub_testing_labels = utils.get_data_for_fold(subjective_testing_indices[i], subjective_vectors_first, "subjective")
						ob_training_data, ob_training_labels, ob_testing_data, ob_testing_labels = utils.get_data_for_fold(objective_testing_indices[i], objective_vectors_first, "objective")
					else:
						sub_training_data, sub_training_labels, sub_testing_data, sub_testing_labels = utils.get_data_for_fold(subjective_testing_indices[i], subjective_vectors_all, "subjective")
						ob_training_data, ob_training_labels, ob_testing_data, ob_testing_labels = utils.get_data_for_fold(objective_testing_indices[i], objective_vectors_all, "objective")
					training_data = sub_training_data + ob_training_data
					training_labels = sub_training_labels + ob_training_labels
					testing_data = sub_testing_data + ob_testing_data
					testing_labels  = sub_testing_labels + ob_testing_labels

					lb = sklearn.preprocessing.LabelBinarizer()
					y_train = np.array([number[0] for number in lb.fit_transform(training_labels)])
					y_test = np.array([number[0] for number in lb.fit_transform(testing_labels)])
					f1_pred = utils.classify_svm(training_data, y_train, testing_data)
					result = "f1_score: %.3f\n" % sklearn.metrics.f1_score(y_test, f1_pred)
					# predictions = utils.classify_svm(training_data, training_labels, testing_data)
					# misclassified_indices = utils.find_errors(predictions, testing_labels)
					# misclassified_indices_for_exp.append(misclassified_indices)
					# misclassified_pct = 100*(float(len(misclassified_indices)) / len(predictions))
					# result = "%.1f%% misclassified \n" % (misclassified_pct)
					print result
					output.write(result)

	total_time = time.time() - start_time
	print "time elapsed: %d minutes" % (total_time / 60)


