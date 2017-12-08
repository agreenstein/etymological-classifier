# coding=utf-8
import sys
import os
import lxml.html
import urllib2
import re
import nltk
from nltk import word_tokenize, pos_tag
from nltk.stem.wordnet import WordNetLemmatizer
from nltk.corpus import stopwords


# function that takes an input word, gets the lemmatization of it, submits a url request to the appropriate etymology page,
# and finds the languages contained within the response entries
# returns either an array of the langauge origin, or false if there is an error
def get_etym(word, tested_link_words):	
	try:
		etym = []
		lem, pos = get_lem(word)
		url = "https://www.etymonline.com/word/%s" % lem
		doc = lxml.html.parse(urllib2.urlopen(url))
		# When the same word is used as multiple parts of speech, only one of the entries actually has the etymology information
		# Derivative parts of speech refer to the main entry
		# For example: call (n.) early 14c., "a loud cry, an outcry," also "a summons, an invitation," from call (v.).
		# Because of this, we can just get the etymologies for all of the entries, and follow the links
		entries = doc.xpath("//section[@class = 'word__defination--2q7ZH']/object/p[2]")
		for entry in entries:
			entry_text = lxml.etree.tostring(entry)
			links = re.findall('<a href="\/word\/?\'?([^"\'>]*)', entry_text)
			# Find the other words linked in the entries
			# If any of them are roots (not prefixes or suffixes that include a "-" or single letters), get the etymology of them by recursively calling get_etym
			for link_word in links:
				if "-" not in link_word and len(link_word) > 1 and link_word not in tested_link_words:
					tested_link_words.append(link_word)
					etym = get_etym(link_word, tested_link_words)
			curr_resp = parse_etym_paragraph(entry_text)
			# just add the first entry
			if len(etym) == 0:
				etym += curr_resp
			# for other entries check if we already have it
			else:
				curr_diff = []
				for resp in curr_resp:
					if resp not in etym:
						curr_diff.append(resp)
				etym += curr_diff
		return etym
	except:
		# print "No etymology information for word %s (lem %s) \n" % (word, lem)
		return False


# function that parses the etymology entry on a given page to find the origin languages contained within
# it returns an array of the origin languages contained within an entry
# because the entries list origin languages from most to least recent, the relative order is maintained such that
# the first language returned is the most recent
def parse_etym_paragraph(paragraph):
	# remove the text within parentheses: these are either irrelevant details of time (e.g. centuries) or part of speech, 
	# or a description of other words that it is the source of
	paragraph = remove_in_paren(paragraph)
	# remove the html syntax from the paragraph
	cleaned_paragraph = re.sub(re.compile('<.*?>'), "", paragraph)
	etymologies = []
	# split the entry up into branches delineated by "from" statements
	for branch in cleaned_paragraph.split("from "):
		curr_branch = word_tokenize(branch)
		# the language will be the first phrase (after "from " or the first phrase overall)
		curr_etym = curr_branch[0]
		# only look at the words in the entry (if there is a date included, which happens sometimes for the first word of the entry, skip it)
		# and utilize the fact that languages referenced in the entries have capital letters (inluding any modifiers, e.g. "Old Norse") by using str.istitle
		if any(char.isdigit() for char in curr_etym) or curr_etym[0].isupper() == False:
			continue
		# go through the next words in the branch and add them to curr_etym until we don't have a language name anymore
		# things can get wonky when other characters like "ænlic" are included so also check that the first character is a letter
		for i in range(1,len(curr_branch)):
			if (curr_etym + " " + curr_branch[i]).istitle() and curr_branch[i].isalpha():
				curr_etym += " " + curr_branch[i]
			else:
				break
		# by appended the languages, the relative order is retained
		etymologies.append(curr_etym)
	return etymologies


# function that lemmatizes a given word
def get_lem(word):
	# structure of pos is (word, partOfSpeech)
	pos = pos_tag(word_tokenize(word))[0]
	# if the part of speech is an adjective, noun, or verb, then pass lemmatizer the part of speech for increased accuracy
	if pos[1][0].lower() in ['a','n','v']:
		return str(lemmatizer.lemmatize(pos[0],pos[1][0].lower())), pos[1][0].lower()
	# otherwise just pass lemmatizer the word
	else:
		return str(lemmatizer.lemmatize(pos[0])), pos[1][0].lower()


# function to remove text within parentheses
# this is necessary because entries often contain sentences in parentheses saying "source also of..." that list related words in other languges
# when looking for a word's languages of origin though, we don't want this data
def remove_in_paren(paragraph):
	# assume that each open parenthesis has a matching closed one
	num_to_remove = paragraph.count('(')
	removed_all = False
	removed = 0
	while removed < num_to_remove:
		# find the last open parenthesis
		open_paren = paragraph.rfind('(')
		# find the first closed parenthesis from that index on
		closed_paren_diff = paragraph[open_paren:].find(')')
		if open_paren == -1 or closed_paren_diff == -1:
			break
		else:
			# update the paragraph to remove the text between the matching open and closed parens
			# the index of the closed parenthesis can be found by adding the closed_paren_diff to the open_paren index
			paragraph = paragraph[0:open_paren] + paragraph[(open_paren + closed_paren_diff + 1):]
			removed += 1
	return paragraph



# the main function
# this file should be called from the command line as follows:
# python scrape_etymologies.py <output_filename>
# the file assumes that the data to get the etymologies for is in a folder called "rotten_imdb" in the current directory
# when run, the program goes through all of the words in the subjective and objective data files and finds the origin languages for them
# the results are stored in an output file for quicker access later
if __name__ == "__main__":
	lemmatizer = WordNetLemmatizer()
	# the following line may need to be run the first time
	# nltk.download('wordnet')
	# pass this function the full path to the data (which should be a text file)
	subjective_file = os.getcwd() + "/rotten_imdb/quote.tok.gt9.5000"
	subjective_content = open(subjective_file).readlines()
	objective_file = os.getcwd() + "/rotten_imdb/plot.tok.gt9.5000"
	objective_content = open(objective_file).readlines()
	# run all of the data and save the etymologies in a file so that looking up the etymologies later is faster
	outfile = sys.argv[1]
	output = open(outfile, 'w')
	header = 'word\t[etymology]\n'
	output.write(header)
	# all_content = objective_content + subjective_content
	all_content = subjective_content
	# create a dictionary of words that we already scraped
	# this was necessary because approximately half of the total lines were saved before a crash
	prev_words = {}
	prev_scrap = open("scraped_etymologies_0.txt").readlines()
	prev_scrap = prev_scrap[1:]
	for line in prev_scrap:
		line = line.rstrip()
		prev_word = line.split('\t')[0]
		prev_words[prev_word] = 1
	words = {}
	counter = 0
	for line in all_content:
		try:
			print "\n" + line
			for word in word_tokenize(line):
				if word not in words and word not in prev_words:
					words[word] = 1
					pos = pos_tag(word_tokenize(word))[0][1]
					word_etym = get_etym(word, [])
					if word_etym:
						print word + " - " + str(word_etym)
						outline = '{0}\t{1}\n'.format(word, str(word_etym))
						output.write(outline)
		except:
			print "skipping a line because of an error"
		counter += 1
		if counter % 100 == 0:
			print "\n \n \n--------------Checking line number %d-------------- \n \n \n" % counter


