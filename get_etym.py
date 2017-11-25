# coding=utf-8
import os
import lxml.html
import urllib2
import re
import nltk
from nltk import word_tokenize, pos_tag
from nltk.stem.wordnet import WordNetLemmatizer
from nltk.corpus import stopwords

lemmatizer = WordNetLemmatizer()
stop_words = set(stopwords.words('english'))
# nltk.download('wordnet')

# pass this function the full path to the data (which should be a text file)
subjective_file = os.getcwd() + "/rotten_imdb/quote.tok.gt9.5000"
subjective_content = open(subjective_file).readlines()
objective_file = os.getcwd() + "/rotten_imdb/plot.tok.gt9.5000"
objective_content = open(objective_file).readlines()


def get_etym(word, tested_link_words):	
	try:
		etym = []
		lem, pos = get_lem(word)
		url = "https://www.etymonline.com/word/%s" % lem
		doc = lxml.html.parse(urllib2.urlopen(url))
		# When the same word is used as multiple parts of speech, only one of the entries actually has the etymology information
		# Derivative parts of speech refer to the main entry
		# For example: call (n.) early 14c., "a loud cry, an outcry," also "a summons, an invitation," from call (v.).
		# I think when there are multiple entries, adjectives are always the first entry, nouns the second, and verbs the third
		# Because of this, we can just get the etymologies for all of the entries, and then filter out later for languages
		entries = doc.xpath("//section[@class = 'word__defination--2q7ZH']/object/p[2]")
		for entry in entries:
			entry_text = lxml.etree.tostring(entry)
			links = re.findall('<a href="\/word\/?\'?([^"\'>]*)', entry_text)
			# Find the other words linked in the entries
			# If any of them are roots (not prefixes or suffixes that include a "-"), get the etymology of them
			for link_word in links:
				if "-" not in link_word and link_word not in tested_link_words:
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

def parse_etym_paragraph(paragraph):
	# remove the html syntax from the paragraph
	cleaned_paragraph = re.sub(re.compile('<.*?>'), "", paragraph)
	# only take the first sentence that describes the word origins (often entries say "source also for xyz..." and we don't want this)
	# TODO this is a problem, maybe shouldn't use a regex --> try instead to just find "(source" and corresponding ")"
	etym_def = re.sub('\(source[^>]+\)', '', cleaned_paragraph)
	etymologies = []
	# split the entry up into branches delineated by "from" statements
	for branch in etym_def.split("from "):
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


def get_lem(word):
	# structure of pos is (word, partOfSpeech)
	pos = pos_tag(word_tokenize(word))[0]
	# if the part of speech is an adjective, noun, or verb, then pass lematize the part of speech
	if pos[1][0].lower() in ['a','n','v']:
		return str(lemmatizer.lemmatize(pos[0],pos[1][0].lower())), pos[1][0].lower()
	# otherwise just pass lematize the word
	else:
		return str(lemmatizer.lemmatize(pos[0])), pos[1][0].lower()


## Use the functions
languages = []
with open(os.getcwd() + "/list_of_languages.txt") as lol:
	content = lol.readlines()
	for line in content:
		languages.append(line.rstrip())


# line = subjective_content[0]
# use a dictionary to keep track of what word origins we've seen
origins = {}
for line in objective_content[0:2]:
	curr_origins = {}
	for word in word_tokenize(line):
		if word not in stop_words:
			print "word is %s " % word
			pos = pos_tag(word_tokenize(word))[0][1]
			word_etym = get_etym(word, [])
			if word_etym:
				print word_etym
				for origin in word_etym:
					if origin not in origins:
						origins[origin] = 0
					origins[origin] += 1
					if origin not in curr_origins:
						curr_origins[origin] = 0
					curr_origins[origin] += 1
	print "\n" + "line is: %s" % line 
	for origin in curr_origins:
		# if origin in languages:
		print "%s - %d" % (origin, curr_origins[origin]) 

print "Total for all objective content:"
for origin in origins:
	# if origin in languages:
	# 	print "%s - %d" % (origin, origins[origin])
	print "%s - %d" % (origin, origins[origin])
