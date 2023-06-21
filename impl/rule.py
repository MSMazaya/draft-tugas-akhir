from configuration import COMPONENTS, RULE_FILE_PATH
import csv
import time

class Rule:
    def __init__(self, id, ruletype, action, amount, checkperiod, rule):
        assert type(id) is str or type(id) is int or type(id) is float
        assert type(ruletype) is str and ruletype.lower() in ["cpu", "mem"]
        assert type(action) is str and action.lower() in ["add", "rem"]
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
        self.action = action
        self.amount = amount
        self.checkperiod = checkperiod
        self.nextcheck = 0
        variableFound = False
        self.rawrule = rule
        self.requiredPredictionTime = []

        ruleSplitted = rule.split(" ")
        for each in COMPONENTS:
            for each2 in ruleSplitted:
                if each in each2 and '[+' in each2 and ']' in each2:
                    variableFound = True
                    predictTime = each2.replace(each, "", 1)
                    assert predictTime.startswith("[+") and predictTime.endswith("]")
                    predictTime = predictTime.replace("[+", "", 1)
                    predictTime = predictTime[::-1].replace("]", "", 1)[::-1]
                    try:
                        predictTime = int(predictTime)
                    except ValueError:
                        print(f"Invalid rule: {self.rawrule}")
                        exit(0)
                    rule = rule.replace(each2, f"x[{predictTime}]['{each}']")
                    self.requiredPredictionTime.append(predictTime)
        assert variableFound
        self.rule = eval("lambda x: " + rule)

    def test(self, data):
        result = self.rule(data)
        assert type(result) is bool
        if result:
            if self.nextcheck < time.time():
                self.nextcheck = time.time() + self.checkperiod
            else:
                result = False
        return result
    
    def __str__(self):
        return f"Rule({self.id}, {self.ruletype}, {self.action}, {self.amount}, {self.rawrule}, {self.requiredPredictionTime}, {self.checkperiod}, {self.nextcheck})"

class RuleManager:
    def __init__(self):
        self.rules = []
        with open(RULE_FILE_PATH, "r") as file:
            csvdata = csv.DictReader(file)
            for each in csvdata:
                self.rules.append(Rule(*each.values()))
        print(f"Loaded rule: {[str(x) for x in self.rules]}")

    def get_required_prediction_time(self):
        result = set()
        for each in self.rules:
            for x in each.requiredPredictionTime:
                result.add(x)
        result = list(result)
        result.sort()
        return result
    
    def test(self, data):
        result = []
        for each in self.rules:
            if (each.test(data)):
                result.append({
                    'ID': each.id,
                    'Rule': each.rawrule,
                    'Amount': each.amount,
                    'Action': each.action,
                    'Type': each.ruletype
                })
        return result
    
rm = RuleManager()
print(rm.get_required_prediction_time())