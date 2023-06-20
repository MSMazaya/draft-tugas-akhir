from configuration import COMPONENTS
import csv

class Rule:
    def __init__(self, id, ruletype, action, amount, checkperiod, rule):
        assert type(id) is str or type(id) is int or type(id) is float
        assert type(ruletype) is str and ruletype.lower() in ["cpu", "mem"]
        assert type(action) is str and action.lower() in ["add", "rem"]
        if type(amount) is str:
            try:
                amount = float(amount)
            except ValueError:
                pass
        assert type(amount) is float or type(amount) is int
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
        variableFound = False
        for each in COMPONENTS:
            if each in rule.split(" "):
                variableFound = True
                rule = rule.replace(each, f"x['{each}']")
        assert variableFound
        self.rule = eval("lambda x: " + rule)
        self.rawrule = rule
    
    def __str__(self):
        return f"Rule({self.id}, {self.ruletype}, {self.action}, {self.amount}, {self.rawrule})"

class RuleManager:
    def __init__(self):
        self.rules = []
        with open("example.rule", "r") as file:
            csvdata = csv.DictReader(file)
            for each in csvdata:
                self.rules.append(Rule(*each.values()))

rm = RuleManager()

class ResourceController:
    pass