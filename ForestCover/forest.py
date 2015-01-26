# -*- coding: utf-8 -*-
"""
@author: John Wittenauer

@notes: This script was tested on 64-bit Windows 7 using the Anaconda 2.0
distribution of 64-bit Python 2.7.
"""

import os
import time
import pickle
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sb
from sklearn import *
from sklearn.ensemble import *


def load(filename):
    """
    Load a previously training model from disk.
    """
    model_file = open(filename, 'rb')
    model = pickle.load(model_file)
    model_file.close()
    return model


def save(model, filename):
    """
    Persist a trained model to disk.
    """
    model_file = open(filename, 'wb')
    pickle.dump(model, model_file)
    model_file.close()


def process_training_data(filename, features, impute, standardize, whiten):
    """
    Reads in training data and prepares numpy arrays.
    """
    training_data = pd.read_csv(filename, sep=',')

    # impute missing values
    if impute == 'mean':
        training_data.fillna(training_data.mean())
    elif impute == 'zeros':
        training_data.fillna(0)

    X = training_data.iloc[:, 1:features].values
    y = training_data.iloc[:, features+1].values

    # create a standardization transform
    scaler = None
    if standardize:
        scaler = preprocessing.StandardScaler()
        scaler.fit(X)

    # create a PCA transform
    pca = None
    if whiten:
        pca = decomposition.PCA(whiten=True)
        pca.fit(X)

    return training_data, X, y, scaler, pca


def visualize(training_data, X, y, scaler, pca, features):
    """
    Computes statistics describing the data and creates some visualizations
    that attempt to highlight the underlying structure.

    Note: Use '%matplotlib inline' and '%matplotlib qt' at the IPython console
    to switch between display modes.
    """

    # feature histograms
    num_histograms = features / 16 if features % 16 == 0 else features / 16 + 1
    for i in range(num_histograms):
        fig, ax = plt.subplots(4, 4, figsize=(20, 10))
        for j in range(16):
            index = (i * 16) + j
            if index < (features - 1):
                ax[j / 4, j % 4].hist(X[:, index], bins=30)
                ax[j / 4, j % 4].set_title(training_data.columns[index + 1])
                ax[j / 4, j % 4].set_xlim((min(X[:, index]), max(X[:, index])))
            elif index < features:
                ax[j / 4, j % 4].hist(y, bins=30)
                ax[j / 4, j % 4].set_title(training_data.columns[index + 1])
                ax[j / 4, j % 4].set_xlim((min(y), max(y)))
        fig.tight_layout()

    # correlation matrix
    if scaler is not None:
        X = scaler.transform(X)

    fig2, ax2 = plt.subplots(figsize=(16, 10))
    colormap = sb.blend_palette(["#00008B", "#6A5ACD", "#F0F8FF", "#FFE6F8", "#C71585", "#8B0000"], as_cmap=True)
    sb.corrplot(training_data, annot=False, sig_stars=False, diag_names=False, cmap=colormap, ax=ax2)
    fig2.tight_layout()

    # pca plots
    if pca is not None:
        X = pca.transform(X)

        fig3, ax3 = plt.subplots(figsize=(16, 10))
        ax3.scatter(X[:, 0], X[:, 1], c=y, cmap=plt.get_cmap('Reds'))
        ax3.set_title('First & Second Principal Components')
        fig3.tight_layout()

        fig4, ax4 = plt.subplots(figsize=(16, 10))
        ax4.scatter(X[:, 1], X[:, 2], c=y, cmap=plt.get_cmap('Reds'))
        ax4.set_title('Second & Third Principal Components')
        fig4.tight_layout()

        fig5, ax5 = plt.subplots(figsize=(16, 10))
        ax5.scatter(X[:, 2], X[:, 3], c=y, cmap=plt.get_cmap('Reds'))
        ax5.set_title('Third & Fourth Principal Components')
        fig5.tight_layout()


def train(X, y, algorithm, scaler, pca, fit):
    """
    Trains a new model using the training data.
    """
    if scaler is not None:
        X = scaler.transform(X)

    if pca is not None:
        X = pca.transform(X)

    if algorithm == 'bayes':
        model = naive_bayes.GaussianNB()
    elif algorithm == 'logistic':
        model = linear_model.LogisticRegression(penalty='l2', C=1.0)
    elif algorithm == 'svm':
        model = svm.SVC(C=1.0, kernel='rbf', shrinking=True, probability=False, cache_size=200)
    elif algorithm == 'sgd':
        model = linear_model.SGDClassifier(loss='hinge', penalty='l2', alpha=0.0001,
                                           n_iter=1000, shuffle=False, n_jobs=-1)
    elif algorithm == 'forest':
        model = RandomForestClassifier(n_estimators=10, criterion='gini', max_features='auto', max_depth=None,
                                       min_samples_split=2, min_samples_leaf=1, max_leaf_nodes=None, n_jobs=-1)
    elif algorithm == 'boost':
        model = GradientBoostingClassifier(loss='deviance', learning_rate=0.1, n_estimators=100, subsample=1.0,
                                           min_samples_split=2, min_samples_leaf=1, max_depth=3, max_features=None,
                                           max_leaf_nodes=None)
    else:
        print 'No model defined for ' + algorithm
        exit()

    if fit:
        t0 = time.time()
        model.fit(X, y)
        t1 = time.time()
        print 'Model trained in {0:3f} s.'.format(t1 - t0)

        if algorithm == 'forest' or algorithm == 'boost':
            # generate a plot showing model performance and relative feature importance
            importances = model.feature_importances_

    return model


def predict(X, model, scaler, pca):
    """
    Predicts the class label.
    """
    if scaler is not None:
        X = scaler.transform(X)

    if pca is not None:
        X = pca.transform(X)

    y_est = model.predict(X)

    return y_est


def predict_probability(X, model, scaler, pca):
    """
    Predicts the class probabilities.
    """
    if scaler is not None:
        X = scaler.transform(X)

    if pca is not None:
        X = pca.transform(X)

    y_prob = model.predict_proba(X)[:, 1]

    return y_prob


def score(X, y, model, scaler, pca):
    """
    Create weighted signal and background sets and calculate the AMS.
    """
    if scaler is not None:
        X = scaler.transform(X)

    if pca is not None:
        X = pca.transform(X)

    return model.score(X, y)


def cross_validate(X, y, algorithm, scaler, pca, metric):
    """
    Performs cross-validation to estimate the true performance of the model.
    """
    model = train(X, y, algorithm, scaler, pca, False)

    if metric != 'none':
        scores = cross_validation.cross_val_score(model, X, y, cv=5, scoring=metric)
    else:
        scores = cross_validation.cross_val_score(model, X, y, cv=5)

    return np.mean(scores)


def process_test_data(filename, features, impute):
    """
    Reads in the test data set and prepares it for prediction by the model.
    """
    test_data = pd.read_csv(filename, sep=',')

    # impute missing values
    if impute == 'mean':
        test_data.fillna(test_data.mean())
    elif impute == 'zeros':
        test_data.fillna(0)

    X_test = test_data.iloc[:, 1:features].values

    return test_data, X_test


def create_submission(test_data, y_est, submit_file):
    """
    Create a new submission file with test data and predictions generated by the model.
    """
    submit = pd.DataFrame(columns=['Id', 'Cover_Type'])
    submit['Id'] = test_data['Id']
    submit['Cover_Type'] = y_est
    submit.to_csv(submit_file, sep=',', index=False, index_label=False)


def generate_features():
    """
    Generates new derived features to add to the data set for model training.
    """
    return None


def select_features():
    """
    Selects a subset of the total number of features available.
    """
    return None


def grid_search():
    """
    Performs an exhaustive search over the specified model parameters.
    """
    return None


def ensemble():
    """
    Creates an ensemble of many models together.
    """
    return None


def main():
    # perform some initialization
    load_training_data = True
    load_model = False
    train_model = True
    save_model = False
    create_visualizations = False
    create_submission_file = False
    code_dir = 'C:\\Users\\John\\PycharmProjects\\Kaggle\\ForestCover\\'
    data_dir = 'C:\\Users\\John\\Documents\\Kaggle\\ForestCover\\'
    training_file = 'train.csv'
    test_file = 'test.csv'
    submit_file = 'submission.csv'
    model_file = 'model.pkl'
    features = 54
    algorithm = 'bayes'  # logistic, bayes, svm, sgd, forest, boost
    metric = 'none'  # accuracy, f1, rcc_auc, mean_absolute_error, mean_squared_error, r2_score, none
    impute = 'none'  # zeros, mean, none
    standardize = False
    whiten = False

    os.chdir(code_dir)

    print 'Starting process...'
    print 'algorithm={0}, standardize={1}, whiten={2}'.format(algorithm, standardize, whiten)

    if load_training_data:
        print 'Reading in training data...'
        training_data, X, y, scaler, pca = process_training_data(
            data_dir + training_file, features, impute, standardize, whiten)

    if create_visualizations:
        print 'Creating visualizations...'
        visualize(training_data, X, y, scaler, pca, features)

    if load_model:
        print 'Loading model from disk...'
        model = load(data_dir + model_file)

    if train_model:
        print 'Training model on full data set...'
        model = train(X, y, algorithm, scaler, pca, True)

        print 'Calculating training score...'
        model_score = score(X, y, model, scaler, pca)
        print 'Training score =', model_score

        print 'Performing cross-validation...'
        cross_val_score = cross_validate(X, y, algorithm, scaler, pca, metric)
        print 'Cross-validation score =', cross_val_score

    if save_model:
        print 'Saving model to disk...'
        save(model, data_dir + model_file)

    if create_submission_file:
        print 'Reading in test data...'
        test_data, X_test = process_test_data(data_dir + test_file, features, impute)

        print 'Predicting test data...'
        y_est = predict(X_test, model, scaler, pca)

        print 'Creating submission file...'
        create_submission(test_data, y_est, data_dir + submit_file)

    print 'Process complete.'


if __name__ == "__main__":
    main()