# #1 Calculate similarity of sentences

from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

s1 ="String sentence 1 This is team eight"
s2 ="String sentence 2 Team eight is working on a steam engine"
def cosine_sentences(s1, s2):  
  # tokenization
  X_list = word_tokenize(X) 
  Y_list = word_tokenize(Y)
  # remove stop words from the string
  sw = stopwords.words('english') 
  l1 =[];l2 =[]
  X_set = {w for w in X_list if not w in sw} 
  Y_set = {w for w in Y_list if not w in sw}
  
  # form a set containing keywords of both strings 
  rvector = X_set.union(Y_set) 
  for w in rvector:
    if w in X_set: l1.append(1) # create a vector
    else: l1.append(0)
    if w in Y_set: l2.append(1)
    else: l2.append(0)

  c = 0
  # calculating cosine
  for i in range(len(rvector)):
    += l1[i]*l2[i]
    
  cosine = c / float((sum(l1)*sum(l2))**0.5)
  print("similarity: ", cosine)
