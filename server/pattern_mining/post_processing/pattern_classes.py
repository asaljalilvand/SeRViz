import numpy as np

class Rule:
    def __init__(self, LHS: np.ndarray, RHS: int, support: int, confidence: float):
        self.LHS = LHS
        self.RHS = RHS
        self.support = support
        self.confidence = confidence
        self.seq_ids = []
        self.support_percentage = -1
        self.id = self._generate_id()

    def __iter__(self):
        '''
        Allow an object of the class to be casted to a dict
        Required for serializing Rules with json
        '''
        for key in self.__dict__:
            yield key, getattr(self, key)

    def __str__(self):
        return str(self.LHS) + " ==> " + str(self.RHS)

    def _generate_id(self):
        # initially the id was generated with uuid, but changed it to the following to reduce data size passed to
        # front-end
        return ''.join([str(item) for item in self.LHS]) + str(self.RHS) + str(self.support) + str(
            int(self.confidence * 100))


class FrequentItemSet:
    def __init__(self, items: np.ndarray, support: float):
        self.items = items
        self.support = support
        self.seq_ids = []
        self.support_percentage = -1
        self.id = self._generate_id()

    def __iter__(self):
        '''
        Allow an object of the class to be casted to a dict
        Required for serializing Rules with json
        '''
        for key in self.__dict__:
            yield key, getattr(self, key)

    def _generate_id(self):
        # initially the id was generated with uuid, but changed it to the following to reduce data size passed to
        # front-end
        return ''.join([str(item) for item in self.items]) + str(self.support)
