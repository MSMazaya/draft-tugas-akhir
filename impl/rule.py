from configuration import COMPONENTS, RULE_FILE_PATH
import csv
import time
import numpy
import re
from utils import printd

def assign(name, value):
    Rule.context[name] = value
    return True

def declare(name, defaultValue=None):
    assign(name, defaultValue)
    return True

class Rule:
    context = {}

    def __init__(self, id, ruletype, amount, checkperiod, rule):
        assert type(id) is str or type(id) is int or type(id) is float
        assert type(ruletype) is str and ruletype.lower() in ["cpu", "mem", "init"]
        if type(amount) is str:
            try:
                amount = int(amount)
            except ValueError:
                pass
        assert type(amount) is int
        if type(checkperiod) is str:
            try:
                checkperiod = int(checkperiod)
            except ValueError:
                pass
        assert type(checkperiod) is int and checkperiod > 0
        assert type(rule) is str and len(rule) > 0
        self.id = id
        self.ruletype = ruletype
        self.amount = amount
        self.checkperiod = checkperiod
        self.nextcheck = 0
        self.rawrule = rule
        self.requiredPredictionTime = []

        ruleSplitted = rule.split(" ")
        if self.ruletype != "init":
            for keyword in COMPONENTS:
                for declared in ruleSplitted:
                    if keyword in declared and '[+' in declared and ']' in declared:
                        predictTime = declared.replace(keyword, "", 1)
                        assert predictTime.startswith("[+") and predictTime.endswith("]")
                        predictTime = predictTime.replace("[+", "", 1)
                        predictTime = predictTime[::-1].replace("]", "", 1)[::-1]
                        try:
                            predictTime = int(predictTime)
                        except ValueError:
                            print(f"Invalid rule: {self.rawrule}")
                            exit(0)
                        rule = rule.replace(declared, f"x[{predictTime}]['{keyword}']")
                        self.requiredPredictionTime.append(predictTime)
        
        fnPrefixVar = r'assign\([^,)\s]+|declare\([^,)\s]+'
        varName = r'assign\(\K[^,)\s]+|declare\(\K[^,)\s]+'

        fnPrefixAll = re.findall(fnPrefixVar, rule)
        varNameAll = re.findall(varName, rule)
        assert len(fnPrefixAll) == len(varNameAll)
        for fnPrefix in set(fnPrefixAll):
            for vn in set(varNameAll):
                fnPrefixReplaced = fnPrefix.replace(vn, f"'{vn}'")
                rule = rule.replace(fnPrefix, fnPrefixReplaced)

        self.rule = eval("lambda x: " + rule)

    def test(self, data):
        result = self.rule(data)
        assert type(result) is bool or type(result) is numpy.bool_
        if self.ruletype == "init":
            if self.nextcheck == -1:
                return True
            
            if not result:
                print(f"Rule {str(self)} failed to initialize")
                exit(0)
            self.nextcheck = -1
        elif self.ruletype != "init":
            if result:
                if self.nextcheck < time.time():
                    self.nextcheck = time.time() + self.checkperiod
                else:
                    result = False
        return result
    
    def __str__(self):
        return f"Rule({self.id}, {self.ruletype}, {self.amount}, {self.rawrule}, {self.requiredPredictionTime}, {self.checkperiod}, {self.nextcheck})"

class RuleManager:
    def __init__(self):
        self.rules = []
        with open(RULE_FILE_PATH, "r") as file:
            csvdata = csv.DictReader(file)
            for each in csvdata:
                self.rules.append(Rule(*each.values()))
        self.testRules = self.rules.filter(lambda x: x.ruletype != "init")
        self.initRules = self.rules.filter(lambda x: x.ruletype == "init" and len(x.requiredPredictionTime) == 0)
        printd(f"Loaded rule: {[str(x) for x in self.rules]}")
        initiatedRules = self.__run({}, self.initRules)
        printd(f"Initiated rule: {[str(x) for x in initiatedRules]}")

    def get_required_prediction_time(self):
        result = set()
        for each in self.rules:
            for x in each.requiredPredictionTime:
                result.add(x)
        result = list(result)
        result.sort()
        return result
    
    def __run(self, data, rules):
        result = []
        for each in rules:
            if (each.test(data)):
                result.append({
                    'ID': each.id,
                    'Rule': each.rawrule,
                    'Amount': each.amount,
                    'Type': each.ruletype
                })
        return result
    
    def test(self, data):
        for k in Rule.context.keys():
            data[k] = Rule.context[k]
        return self.__run(data, self.testRules)