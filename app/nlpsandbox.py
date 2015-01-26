import nltk

class Text():
    def __init__(self, text=""):
        self.text = text

    def tokens(self):
        return nltk.word_tokenize(self.text)

    def tagged(self):
        return nltk.pos_tag(self.tokens())

    def types(self):
        types = {}
        for token in self.tagged():
            if token[1] not in types.keys():
                types[token[1]] = [token[0]]
            else:
                types[token[1]].append(token[0])

        return types

    def nounTags(self):
        nounTags = []
        for tag in self.tagged():
            if tag[1][0:2] == 'NN' or tag[1] in ['PRP', 'JJ', 'DT', 'PRP$']:
                nounTags.append(tag[1])
        return nounTags

    def verbTags(self):
        verbTags = []
        for tag in self.tagged():
            if tag[1][0:2] == 'VB' or tag[1] in []:
                verbTags.append(tag[1])
        return verbTags

    def nouns(self):
        return ', '.join([token for token, tag in self.tagged if tag in self.nounTags])

    def verbs(self):
        return ', '.join([token for token, tag in self.tagged if tag in self.verbTags])

    def sentences(self):
        sentenceLists = []
        sentence = []
        for token in self.tagged():
            sentence.append(token[0])

            if token[1] == '.':
                sentenceLists.append(sentence)
                sentence = []

        sentences = []
        for sentence in sentenceLists:
            sentences.append(Sentence(' '.join(sentence)))

        return sentences

# Special Text class with functions for finding "parts" of the sentence
class Sentence(Text):

    # Breaks up sentences into "parts" based upon noun, verb, and preposition alteration
    def simpleParts(self):
        parts = []
        parts.append([])
        switch = 'verb'

        for token in self.tagged():
            addNew = False
            if token[1] in [':',';',',']:
                addNew=True
                switch = 'verb'
            elif token[1] == 'IN':
                parts.append([])
                switch = 'verb'
            else:
                checkList = self.nounTags() if switch == 'noun' else self.verbTags()

                if token[1] in checkList:
                    parts.append([])
                    switch = 'noun' if switch == 'verb' else 'verb'

            parts[-1].append(token)
            if addNew:
                parts.append([])

        strippedParts = []
        for part in parts:
            if len(part) > 0:
                strippedParts.append(part)

        return strippedParts

    # Nests the "simple parts" of a sentence based on basic punctuation
    def nestedParts(self):
        nestedParts = [[]]

        for part in self.simpleParts():
            if part[-1][0] in [':',';',',']:
                nestedParts[-1].append(part)
                nestedParts.append([])
            else:
                nestedParts[-1].append(part)

        return nestedParts