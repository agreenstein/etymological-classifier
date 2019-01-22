# etymological-classifier
A support vector machine classifier that determines a text’s subjectivity (i.e., whether it is subjective or objective) using vectors created from the etymologies of words in the text.

# Overview
The data (in the rotten_imdb folder) consists of 5000 subjective and 5000 objective sentences taken from Rotten Tomatoes and IMDB movie reviews and synopses, respectively (originally used in Pang and Lee 2004). In scrape_etymologies.py, the website https://www.etymonline.com, a free online etymology dictionary that is the most common source of Wiktionary etymology entries, is scraped to determine the origin languages of each word.  Because this is a time intensive process, the etymologies of all the words were scraped at one time and stored for faster access later (scraped_etymologies.txt).

The file experiment.py uses functions from etym_classifier_utils.py to build an SVM classifier for various parameter settings and run n-fold cross validation to analyze the performance.  The data is vectorized in the following way: First, an ordered list of all of the different languages appearing in the various etymology entries is constructed, and is cleaned to only include languages appearing on the Wiktionary list of languages (along with several others and those augmented by acceptable modifiers).  Then, for each sentence in the corpus, the etymologies of the sentence’s words are retrieved, and an array of zeros corresponding to the ordered languages is incremented depending on the number of times a language appeared in that sentence.  Some permutations on the vectorization are possible as well. Either all languages of a word’s etymology entry can be used (its entire language history) or just the first language (the most recent one). Additionally, the language count in the resulting vector could be converted to a frequency measure by dividing by the number of words in the sentence that contributed to the vector. Lastly, stop words as defined in the NLTK corpus (e.g., “the”, “a”, “with”, “for”, etc.) could either be included or not.  For each setting, 10-fold cross validation was performed such that the subjective and objective examples were both split into 10 equal-sized bins, one bin from each was withheld as testing data, and the other nine were used for training

Running the experiment takes close to half an hour, so a sample output can be seen in experiment_results_F1scores_10fold.txt.  In this example, the classifier performed best when the vectorization was based on count and included all of the languages in a word's etymological entry, with F1 scores of approximately 0.66.


# Running the code
Environment: Python 2.7, with nltk, numpy, scikit-learn, and lxml packages installed.

The etymological data can be scraped by running python scrape_etymologies.py <output_filename>

The experiment can be run by python experiment.py <results_output_file>
