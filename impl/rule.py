from configuration import COMPONENTS, RULE_FILE_PATH, CONTEXT_VAR_DATA_PATH
import numpy
import re, os, json, time, csv
from utils import printd

def assign(name, value):
    Rule.context[name] = value
    return True

def assignif(name, value, condition):
    if condition:
        Rule.context[name] = value
    return condition

def declare(name, defaultValue=None):
    assign(name, defaultValue)
    return True

def has_var(name):
    return name in Rule.context.keys()

class Rule:
    context = {}
    declared = []
    contextFnVarName = ['assign', 'assignif', 'declare', 'has_var']

    def __init__(self, id, ruletype, amount, checkperiod, rule):
        assert type(id) is str or type(id) is int or type(id) is float
        assert type(ruletype) is str and ruletype.lower() in ["cpu", "mem", "init", "load", "none"]
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
        assert ruletype.lower() in ["init", "load", "none"] or (type(checkperiod) is int and checkperiod > 0)
        assert ruletype.lower() in ["init", "load", "none"] or (type(rule) is str and len(rule) > 0)
        self.id = id
        self.ruletype = ruletype
        self.amount = amount
        self.checkperiod = checkperiod
        self.nextcheck = 0
        self.rawrule = rule
        self.requiredPredictionTime = []

        ruleSplitted = rule.split(" ")
        if self.ruletype != "init" and self.ruletype != "load":
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
        
        buildfnPrefixVar = ""
        buildVarName = ""
        for fn in Rule.contextFnVarName:
            if len(buildfnPrefixVar) > 0:
                buildfnPrefixVar += "|"
            buildfnPrefixVar += f"{fn}\([^,)\s]+"
        fnPrefixVar = r'' + buildfnPrefixVar
        for fn in Rule.contextFnVarName:
            if len(buildVarName) > 0:
                buildVarName += "|"
            buildVarName += f"(?<={fn}\()[^,)\s]+"
        varName = r'' + buildVarName

        fnPrefixAll = re.findall(fnPrefixVar, rule)
        varNameAll = re.findall(varName, rule)
        assert len(fnPrefixAll) == len(varNameAll)
        Rule.declared.extend(list(set(varNameAll)))
        Rule.declared = list(set(Rule.declared))

        for fnPrefix in set(fnPrefixAll):
            for vn in set(varNameAll):
                fnPrefixReplaced = fnPrefix.replace(vn, f"'{vn}'")
                rule = rule.replace(fnPrefix, fnPrefixReplaced)
    
        numbers = r'@\$(\d+)'
        for idxkw, keyword in enumerate(Rule.declared):
            if keyword in rule:
                for fn in Rule.contextFnVarName:
                    rule = rule.replace(f"{fn}('{keyword}'", f"{fn}('@${idxkw}'")
                rule = rule.replace(f"{keyword}", f"x['{keyword}']")
                rnum = re.findall(numbers, rule)
                for n in rnum:
                    rule = rule.replace(f"@${n}", Rule.declared[int(n)])

        print(rule)
        self.rule = eval("lambda x: " + rule)

    def test(self, data):
        result = self.rule(data)
        assert type(result) is bool or type(result) is numpy.bool_
        if self.ruletype == "init" or self.ruletype == "load":
            if self.nextcheck == -1:
                return True
            
            if self.ruletype == "init" and not result:
                print(f"Rule {str(self)} failed to pass, exiting...")
                exit(0)
            self.nextcheck = -1
        else:
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
        self.testRules = filter(lambda x: x.ruletype != "init" and x.ruletype != "load", self.rules)
        self.initRules = filter(lambda x: x.ruletype == "init" and len(x.requiredPredictionTime) == 0, self.rules)
        self.loadRules = filter(lambda x: x.ruletype == "load" and len(x.requiredPredictionTime) == 0, self.rules)
        #printd(f"Loaded rule: {[str(x) for x in self.rules]}")
        self.__load()

    def __load(self):
        if os.path.exists(CONTEXT_VAR_DATA_PATH):
            with open(CONTEXT_VAR_DATA_PATH, 'r') as file:
                loaded = dict(json.load(file))
                Rule.context = loaded
            self.__run({}, self.loadRules)
            printd(f"Rule Manager Loaded, current context: {Rule.context}")
        else:
            self.__run({}, self.initRules)
            printd(f"Rule Manager Initiated, current context: {Rule.context}")

    def save():
        with open(CONTEXT_VAR_DATA_PATH, 'w') as file:
            json.dump(Rule.context, file, indent=4)

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
            for k in Rule.context.keys():
                data[k] = Rule.context[k]
            if (each.test(data)):
                result.append({
                    'ID': each.id,
                    'Rule': each.rawrule,
                    'Amount': each.amount,
                    'Type': each.ruletype
                })
        RuleManager.save()
        return result
    
    def test(self, data):
        return self.__run(data, self.testRules)

# rm = RuleManager()
# print(Rule.context)
# rm.test({
#     10: {
#         'LoadAvg1m': 0.2,
#         'MemUsedPercent': 50,
#     }
# })
# print(Rule.context)