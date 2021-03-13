#!/usr/bin/python3

"""
Generate 2-3 person coffee table matches, preventing repititions.
"""

# Update this list of names in names.py
import json
import math
import random

def parse_arguments():
    """
    Parse invocation arguments.
    """
    import argparse
    parser = argparse.ArgumentParser(
        description='Generate 2-3 person coffee table matches, preventing repititions')
    parser.add_argument('--max', type=float, default=3,
                        help='maximum number of persons per table')
    parser.add_argument('--dry-run', action="store_true",
                        help='Do not remember the new assignment')
    parser.add_argument('--history', default="coffeetable_hist.json",
                        help='Name of the file storing previous tables')
    parser.add_argument('--test', action="store_true",
                        help='Run the tests')
    args = parser.parse_args()
    # print(args)
    return args.dry_run, args.max, args.history, args.test

def write_history(filename, history):
    """
    Update (re-write, actually) the history file.
    """
    with open(filename, 'w') as json_file:
        json.dump(history, json_file)


def read_history(filename):
    """
    Read the historu file, if it exists.
    """
    history = []
    try:
        with open(filename) as json_file:
            history = json.load(json_file)
    except FileNotFoundError:
        pass
    return history


def build_cost_matrix(participants, history):
    """
    Calculate the cost of all possible participant pairings.
    """
    cost_matrix = {}
    for age, row in enumerate(history):
        for table in row:
            for person in table:
                if not person in participants:
                    continue
                for qerson in table:
                    if qerson == person:
                        break
                    if not qerson in participants:
                        continue
                    match = person + '+' + qerson
                    if qerson < person:
                        match = qerson + '+' + person
                    try:
                        cost_matrix[match] += 1./(age + 1)
                    except KeyError:
                        cost_matrix[match] = 1./(age + 1)
    return cost_matrix


def cost_for_participant(person, tables, cost_matrix, max_persons_per_table):
    """
    Calgulate the participants highest table cost, and while we're at it, find
    the most suitable table.
    """
    highest_table_cost = -1
    min_cost = 10
    min_cost_itable = None
    for itable, table in enumerate(tables):
        if len(table) >= max_persons_per_table:
            continue
        cost = 0
        if not table:
            cost = -1
        for qerson in table:
            match = person + '+' + qerson
            if qerson < person:
                match = qerson + '+' + person
            try:
                # print(f'match {match}')
                cost += cost_matrix[match]
                # print(f"cost {match}: {cost_matrix[match]}")
            except KeyError:
                pass
        # Favor rather empty tables
        cost -= 0.5/(1 + len(table))
        if cost > highest_table_cost:
            highest_table_cost = cost
        if cost < min_cost:
            min_cost = cost
            min_cost_itable = itable
    return min_cost_itable, highest_table_cost


def distribute(cost_matrix, participants, max_persons_per_table):
    """
    Assign participants to tables, reducing the cost per participant.
    """
    num_tables = math.ceil(float(len(participants)) / max_persons_per_table)
    tables = []
    for _ in range(num_tables):
        tables.append([])
    shuffled_names = participants
    random.shuffle(shuffled_names)
    tables[0].append(shuffled_names[0])
    shuffled_names.remove(shuffled_names[0])

    # always pick the person with the highest potential table cost
    while shuffled_names:
        highest_cost = -100
        highest_cost_name = None
        highest_cost_name_min_cost_itable = -1
        for person in shuffled_names:
            min_cost_itable, highest_table_cost = cost_for_participant(
                person, tables, cost_matrix, max_persons_per_table)
            if highest_table_cost > highest_cost:
                highest_cost = highest_table_cost
                highest_cost_name = person
                highest_cost_name_min_cost_itable = min_cost_itable
        tables[highest_cost_name_min_cost_itable].append(highest_cost_name)
        shuffled_names.remove(highest_cost_name)
    return tables

def coffeetable():
    """
    Generate tables that
    - seat all participants, as imported from "names.py"
    - minimize recent re-encounters
    - have max_persons_per_table - which can be a float, defining the number of tables
    - balance the number of participants per table
    """
    dry_run, max_persons_per_table, hist_file, test = parse_arguments()
    if test:
        from test.names import names
        dry_run = True
        hist_file = 'test/' + hist_file
    else:
        from names import names
    hist = read_history(hist_file)
    # print(json.dumps(hist))
    cost_matrix = build_cost_matrix(names, hist)
    # print(json.dumps(cost_matrix))

    tables = distribute(cost_matrix, names, max_persons_per_table)
    for itable, table in enumerate(tables):
        print(f'Table {itable + 1}: {" ".join(table)}')
    hist.append([tables])
    if dry_run:
        print(f'Dry-run mode; not storing distribution in {hist_file}.')
    else:
        if len(hist) > 6:
            hist = hist[-6:]
        write_history(hist_file, hist)
    return tables

if __name__ == "__main__":
    coffeetable()
