#!/usr/bin/python3

# Update this list of names in names.py
from names import names
import json
import math
import random

def parseArguments():
   import argparse
   parser = argparse.ArgumentParser(description='Generate 2-3 person coffee table matches, preventing repititions')
   parser.add_argument('--max', type=float, default=3,
                       help='maximum number of persons per table')
   parser.add_argument('--dry-run', action="store_true",
                       help='Do not remember the new assignment')
   parser.add_argument('--history', default="coffeetable_hist.json",
                       help='Name of the file storing previous tables')
   args = parser.parse_args()
   #print(args)
   return args.dry_run, args.max, args.history


def writeHistory(filename, history):
   with open(filename, 'w') as json_file:
      json.dump(history, json_file)

def readHistory(filename):
   history = []
   try:
      with open(filename) as json_file:
         history = json.load(json_file)
   except:
      raise
   #   pass
   return history

def buildCostMatrix(participants, history):
   costMatrix = {}
   for age in range(len(history)):
      h = history[age]
      for table in h:
         for p in table:
            if not p in participants:
               continue
            for q in table:
               if q == p:
                  break
               if not q in participants:
                  continue
               match = p + '+' + q
               if q < p:
                  match = q + '+' + p
               try:
                  costMatrix[match] += 1./(age + 1)
               except KeyError:
                  costMatrix[match] = 1./(age + 1)
   return costMatrix

def distribute(costMatrix, participants):
   numTables = math.ceil(float(len(participants)) / maxPersonsPerTable)
   tables = []
   for iTable in range(numTables):
      tables.append([])
   shuffledNames = participants
   random.shuffle(shuffledNames)
   tables[0].append(shuffledNames[0])
   shuffledNames.remove(shuffledNames[0])

   # always pick the person with the highest potential table cost
   while shuffledNames:
      highestCost = -100
      highestCostName = None
      highestCostNameMinCostITable = -1
      for p in shuffledNames:
         highestTableCost = -1
         minCost = 10
         minCostITable = None
         for itable in range(len(tables)):
            if len(tables[itable]) >= maxPersonsPerTable:
               continue
            cost = 0
            if not tables[itable]:
               cost = -1
            for q in tables[itable]:
               match = p + '+' + q
               if q < p:
                  match = q + '+' + p
               try:
                  #print(f'match {match}')
                  cost += costMatrix[match]
                  #print(f"cost {match}: {costMatrix[match]}")
               except:
                  pass
            # Favor rather empty tables
            cost -= 0.5/(1 + len(tables[itable]))
            if cost > highestTableCost:
               highestTableCost = cost
            if cost < minCost:
               minCost = cost
               minCostITable = itable
         if highestTableCost > highestCost:
               highestCost = highestTableCost
               highestCostName = p
               highestCostNameMinCostITable = minCostITable
      tables[highestCostNameMinCostITable].append(highestCostName)
      shuffledNames.remove(highestCostName)
   return tables

dryRun, maxPersonsPerTable, histFile = parseArguments()
hist = readHistory(histFile)
#print(json.dumps(hist))
cM = buildCostMatrix(names, hist)
#print(json.dumps(cM))

tables = distribute(cM, names)
for itable in range(len(tables)):
   print(f'Table {itable+1}: {" ".join(tables[itable])}')
hist.append([tables])
if dryRun:
   print(f'Dry-run mode; not storing distribution in {histFile}.')
else:
   if len(hist) > 6:
      hist = hist[-6:]
   writeHistory(histFile, hist)
