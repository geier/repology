# Copyright (C) 2016 Dmitry Marakasov <amdmi3@amdmi3.ru>
#
# This file is part of repology
#
# repology is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# repology is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with repology.  If not, see <http://www.gnu.org/licenses/>.

import yaml
import re
from enum import Enum

import sys

class MatchResult(Enum):
    none = 0,
    match = 1,
    ignore = 2

class NameTransformer:
    def __init__(self, rulespath):
        with open(rulespath) as file:
            self.rules = yaml.safe_load(file)

        # some fields are always lists
        for rule in self.rules:
            for field in ('repo', 'category'):
                if field in rule and not isinstance(rule[field], list):
                    rule[field] = [ rule[field] ]

    def IsRuleMatching(self, rule, package):
        # match categories
        if 'category' in rule:
            catmatch = False
            for category in rule['category']:
                if category == package.category:
                    catmatch = True
                    break

            if not catmatch:
                return False

        # match name patterns
        if 'name' in rule:
            if package.name != rule['name']:
                return False

        # match name patterns
        if 'namepat' in rule:
            if not re.match(rule['namepat'], package.name):
                return False

        return True

    def ApplyRule(self, rule, package):
        if not self.IsRuleMatching(rule, package):
            return MatchResult.none, None

        if 'ignore' in rule:
            return MatchResult.ignore, None

        if 'setname' in rule:
            match = None
            if 'namepat' in rule:
                match = re.match(rule['namepat'], package.name)
            if match:
                return MatchResult.match, re.sub("\$([0-9]+)", lambda x: match.group(int(x.group(1))), rule['setname'])
            else:
                return MatchResult.match, re.sub("\$0", package.name, rule['setname'])

        return MatchResult.none, None

    def TransformName(self, package, repotype):
        match = False

        # apply first matching rule
        for rule in self.rules:
            if 'repo' in rule and not repotype in rule['repo']:
                continue

            result, name = self.ApplyRule(rule, package)
            if result == MatchResult.ignore:
                return None
            elif result == MatchResult.match:
                return name.lower().replace('_', '-')

        # default processing
        return package.name.lower().replace('_', '-')