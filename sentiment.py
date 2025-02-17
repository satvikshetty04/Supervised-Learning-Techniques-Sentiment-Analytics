import sys
import collections
import sklearn.naive_bayes
import sklearn.linear_model
import nltk
import random
random.seed(0)
from gensim.models.doc2vec import LabeledSentence, Doc2Vec, TaggedDocument
#nltk.download("stopwords")          # Download the stop words from nltk


# User input path to the train-pos.txt, train-neg.txt, test-pos.txt, and test-neg.txt datasets
if len(sys.argv) != 3:
    print "python sentiment.py <path_to_data> <0|1>"
    print "0 = NLP, 1 = Doc2Vec"
    exit(1)
path_to_data = sys.argv[1]
method = int(sys.argv[2])



def main():
    train_pos, train_neg, test_pos, test_neg = load_data(path_to_data)
    
    if method == 0:
        train_pos_vec, train_neg_vec, test_pos_vec, test_neg_vec = feature_vecs_NLP(train_pos, train_neg, test_pos, test_neg)
        nb_model, lr_model = build_models_NLP(train_pos_vec, train_neg_vec)
    if method == 1:
        train_pos_vec, train_neg_vec, test_pos_vec, test_neg_vec = feature_vecs_DOC(train_pos, train_neg, test_pos, test_neg)
        nb_model, lr_model = build_models_DOC(train_pos_vec, train_neg_vec)
    print "Naive Bayes"
    print "-----------"
    evaluate_model(nb_model, test_pos_vec, test_neg_vec, True)
    print ""
    print "Logistic Regression"
    print "-------------------"
    evaluate_model(lr_model, test_pos_vec, test_neg_vec, True)



def load_data(path_to_dir):
    """
    Loads the train and test set into four different lists.
    """
    train_pos = []
    train_neg = []
    test_pos = []
    test_neg = []
    with open(path_to_dir+"train-pos.txt", "r") as f:
        for i,line in enumerate(f):
            words = [w.lower() for w in line.strip().split() if len(w)>=3]
            train_pos.append(words)
    with open(path_to_dir+"train-neg.txt", "r") as f:
        for line in f:
            words = [w.lower() for w in line.strip().split() if len(w)>=3]
            train_neg.append(words)
    with open(path_to_dir+"test-pos.txt", "r") as f:
        for line in f:
            words = [w.lower() for w in line.strip().split() if len(w)>=3]
            test_pos.append(words)
    with open(path_to_dir+"test-neg.txt", "r") as f:
        for line in f:
            words = [w.lower() for w in line.strip().split() if len(w)>=3]
            test_neg.append(words)

    return train_pos, train_neg, test_pos, test_neg



def feature_vecs_NLP(train_pos, train_neg, test_pos, test_neg):
    """
    Returns the feature vectors for all text in the train and test datasets.
    """
    # English stopwords from nltk
    stopwords = set(nltk.corpus.stopwords.words('english'))
    # Determine a list of words that will be used as features. 
    # This list should have the following properties:
    #   (1) Contains no stop words
    #   (2) Is in at least 1% of the positive texts or 1% of the negative texts
    #   (3) Is in at least twice as many postive texts as negative texts, or vice-versa.
    # YOUR CODE HERE
    pos_train_words_dict = {}
    for line in train_pos:
        words_in_line = set(line)
        for word in words_in_line:
            if word in stopwords:
                continue
            if word in pos_train_words_dict:
                pos_train_words_dict[word] += 1
            else:
                pos_train_words_dict[word] = 1

    neg_train_words_dict = {}
    for line in train_neg:
        words_in_line = set(line)
        for word in words_in_line:
            if word in stopwords:
                continue
            if word in neg_train_words_dict:
                neg_train_words_dict[word] += 1
            else:
                neg_train_words_dict[word] = 1

    neg_len = len(train_neg) * 0.01
    pos_len = len(train_pos) * 0.01

    features = []
    for word in pos_train_words_dict:
        if pos_train_words_dict[word] >= pos_len and pos_train_words_dict[word]/2 >= neg_train_words_dict.get(word):
            features.append(word)

    for word in neg_train_words_dict:
        if neg_train_words_dict[word] >= pos_len and neg_train_words_dict[word] / 2 >= pos_train_words_dict.get(word):
            features.append(word)

    # Using the above words as features, construct binary vectors for each text in the training and test set.
    # These should be python lists containing 0 and 1 integers.
    # YOUR CODE HERE
    print "Generating feature vectors.."
    def generate_feature_vector(data, features):
        vec = []
        for line in data:
            vec.append([1 if x in line else 0 for x in features])
        return vec

    train_pos_vec = generate_feature_vector(train_pos, features)
    train_neg_vec = generate_feature_vector(train_neg, features)
    test_pos_vec = generate_feature_vector(test_pos, features)
    test_neg_vec = generate_feature_vector(test_neg, features)

    # Return the four feature vectors
    return train_pos_vec, train_neg_vec, test_pos_vec, test_neg_vec



def feature_vecs_DOC(train_pos, train_neg, test_pos, test_neg):
    """
    Returns the feature vectors for all text in the train and test datasets.
    """
    # Doc2Vec requires LabeledSentence objects as input.
    # Turn the datasets from lists of words to lists of LabeledSentence objects.
    # YOUR CODE HERE
    def generate_labels(data, label):
        labels = []
        for i, j in enumerate(data):
            labels.append(TaggedDocument(words=j, tags=[label + str(i)]))
        return labels

    labeled_train_pos = generate_labels(train_pos, "TRAIN_POS_")
    labeled_train_neg = generate_labels(train_neg, "TRAIN_NEG_")
    labeled_test_pos = generate_labels(test_pos, "TEST_POS_")
    labeled_test_neg = generate_labels(test_neg, "TEST_NEG_")
    # Initialize model
    model = Doc2Vec(min_count=1, window=10, size=100, sample=1e-4, negative=5, workers=4)
    sentences = labeled_train_pos + labeled_train_neg + labeled_test_pos + labeled_test_neg
    model.build_vocab(sentences)

    # Train the model
    # This may take a bit to run 
    for i in range(5):
        print "Training iteration %d" % (i)
        random.shuffle(sentences)
        model.train(sentences)

    # Use the docvecs function to extract the feature vectors for the training and test data
    # YOUR CODE HERE
    print "Generating feature vectors.."
    def generate_feature_vectors(data, label):
        feature_vector = []
        for i in range(len(data)):
            feature_vector.append(model.docvecs[label + str(i)])
        return feature_vector
    train_pos_vec = generate_feature_vectors(train_pos, "TRAIN_POS_")
    train_neg_vec = generate_feature_vectors(train_neg, "TRAIN_NEG_")
    test_pos_vec = generate_feature_vectors(test_pos, "TEST_POS_")
    test_neg_vec = generate_feature_vectors(test_neg, "TEST_NEG_")

    # Return the four feature vectors
    return train_pos_vec, train_neg_vec, test_pos_vec, test_neg_vec



def build_models_NLP(train_pos_vec, train_neg_vec):
    """
    Returns a BernoulliNB and LosticRegression Model that are fit to the training data.
    """
    Y = ["pos"]*len(train_pos_vec) + ["neg"]*len(train_neg_vec)

    # Use sklearn's BernoulliNB and LogisticRegression functions to fit two models to the training data.
    # For BernoulliNB, use alpha=1.0 and binarize=None
    # For LogisticRegression, pass no parameters
    # YOUR CODE HERE
    print "Building model..."
    X = train_pos_vec + train_neg_vec
    nb_model = sklearn.naive_bayes.BernoulliNB(alpha=1.0, binarize=None)
    nb_model.fit(X,Y)
    lr_model = sklearn.linear_model.LogisticRegression()
    lr_model.fit(X,Y)
    print nb_model
    return nb_model, lr_model



def build_models_DOC(train_pos_vec, train_neg_vec):
    """
    Returns a GaussianNB and LosticRegression Model that are fit to the training data.
    """
    Y = ["pos"]*len(train_pos_vec) + ["neg"]*len(train_neg_vec)

    # Use sklearn's GaussianNB and LogisticRegression functions to fit two models to the training data.
    # For LogisticRegression, pass no parameters
    # YOUR CODE HERE
    print "Building model..."
    X = train_pos_vec + train_neg_vec
    nb_model = sklearn.naive_bayes.GaussianNB()
    nb_model.fit(X, Y)
    lr_model = sklearn.linear_model.LogisticRegression()
    lr_model.fit(X, Y)
    return nb_model, lr_model



def evaluate_model(model, test_pos_vec, test_neg_vec, print_confusion=False):
    """
    Prints the confusion matrix and accuracy of the model.
    """
    # Use the predict function and calculate the true/false positives and true/false negative.
    # YOUR CODE HERE
    tp, tn, fp, fn = 0, 0, 0, 0
    pos_prediction = model.predict(test_pos_vec)
    neg_prediction = model.predict(test_neg_vec)
    for i in pos_prediction:
        if i == "pos":
            tp += 1
        else:
            fn += 1
    for i in neg_prediction:
        if i == "neg":
            tn += 1
        else:
            fp += 1
    accuracy = (tp + tn)/(float) (tp +tn + fp + fn)

    if print_confusion:
        print "predicted:\tpos\tneg"
        print "actual:"
        print "pos\t\t%d\t%d" % (tp, fn)
        print "neg\t\t%d\t%d" % (fp, tn)
    print "accuracy: %f" % (accuracy)



if __name__ == "__main__":
    main()
