#!/usr/bin/env python
import sys, os
from ortools.sat.python import cp_model as cm
import argparse, pickle
from terrabot_utils import time_since_midnight
import diagnosis as dg, cnf, adder

parser = argparse.ArgumentParser()
parser.add_argument('-p', '--part', default=-1, type=int,
                    help='Which part to test (defaults to all)')
parser.add_argument('-s', '--step', default=-1, type=int,
                    help='Which step to test (defaults to all)')
args = parser.parse_args()

def test_adder():
    correct = num = 0
    tests = [[0, [([0, 0, 0], [0, 0, 0])]],
             [2, [([0, 0, 0], [0, 1, 0]), ([0, 1, 0], [0, 0, 0]),
                  ([1, 0, 0], [1, 0, 0])]],
             [7, [([1, 1, 1], [0, 0, 0]), ([0, 0, 0], [1, 1, 1]),
                  ([1, 1, 0], [0, 0, 1]), ([0, 0, 1], [1, 1, 0]),
                  ([1, 0, 1], [0, 1, 0]), ([0, 1, 0], [1, 0, 1]),
                  ([1, 0, 0], [0, 1, 1]), ([0, 1, 1], [1, 0, 0])]],
             [9, [([1, 1, 1], [0, 1, 0]), ([0, 1, 1], [1, 1, 0]),
                  ([1, 0, 1], [0, 0, 1]), ([0, 0, 1], [1, 0, 1]),
                  ([1, 1, 0], [0, 1, 1]), ([0, 1, 0], [1, 1, 1])]],
             [12, [([0, 1, 1], [0, 1, 1]), ([1, 0, 1], [1, 1, 1]),
                   ([1, 1, 1], [1, 0, 1])]],
             [14, [([1, 1, 1], [1, 1, 1])]]
             ]
    for sum, answers in tests:
        num += 1
        solutions = adder.output_input_adder(adder.convert_to_bits(sum, 4))
        if (len(solutions) > 0):
            print("Solutions found for a + b = %d" %sum)
            for soln in solutions: print("  %s" %str(soln))
        else: print("No solutions found for a + b = %d" %sum)

        missing_solutions = []
        for answer in answers:
            if not any([answer == solution for solution in solutions]):
                missing_solutions.append(answer)
        if (missing_solutions):
            print("Missing solutions:")
            for solution in missing_solutions: print("  %s" %str(solution))

        extra_solutions = []
        for solution in solutions:
            if not any([answer == solution for answer in answers]):
                extra_solutions.append(solution)
        if (extra_solutions):
            print("Extra solutions:")
            for solution in extra_solutions: print("  %s" %str(solution))
        if (not missing_solutions and not extra_solutions):
            correct += 1; print("Correct!")
    return correct, num

def report_relations(type, creation_fn, desired_num, model):
    correct = 0
    variables = {}
    creation_fn(model, variables)
    if (len(variables) == desired_num):
        print("Correct number of %s relations" %type)
        return 1
    else:
        print("Incorrect number of %s relations: You have %d instead of %d"
              %(type, len(variables), desired_num))
        return 0

def test_relations():
    correct = 0
    model = cm.CpModel()
    variables = dg.create_relation_variables(model)
    relations = pickle.load(open("grader_files/relations.pkl", 'rb'))
    for relation in relations:
        if (variables.get(relation) is not None):
            correct += 1
        else:
            print("  Missing relation: %s" %relation)
    for variable in variables:
        if (not variable in relations):
            print("  Extra relation: %s" %variable)
    return correct, len(relations)

rp_relations = [dg.rasp_pi_signal('H-T0'), dg.rasp_pi_signal('Light0'),
                dg.rasp_pi_signal('Moisture0'), dg.rasp_pi_signal('H-T1'),
                dg.rasp_pi_signal('Light1'), dg.rasp_pi_signal('Moisture1'),
                dg.rasp_pi_signal('Wlevel'),
                dg.rasp_pi_signal('Fans'),  dg.rasp_pi_signal('LEDs'),
                dg.rasp_pi_signal('Pump'), dg.expected_result('Fans'),
                dg.expected_result('LEDs'), dg.expected_result('Pump'),
                dg.powered('Rasp-Pi'), dg.working('Rasp-Pi')]

def check_values(constraint, value, all_p, variables, solver):
    vals = [solver.Value(variables[cval]) == value for cval in constraint]
    return all(vals) if all_p else any(vals)

def set_vars(constraint, value, variables, model):
    return [model.Add(variables[cval] == value) for cval in constraint]

# If either the LHS or RHS is a tuple of tuples, that means it's an
#  OR constraint, and need to check each one
def test_constraint1(lhs, rhs, value, all_p, variables, model, solver,
                     term1=None, term2=None):
    if (type(rhs[0]) == tuple):
        results = [test_constraint1(lhs, rhs1, value, all_p,
                                    variables, model, solver)
                   for rhs1 in rhs]
        result = any(results) if value else all(results)
    elif (type(lhs[0]) == tuple):
        results = [test_constraint1(lhs1, rhs, value, all_p,
                                    variables, model, solver)
                   for lhs1 in lhs]
        result = all(results)
    else:
        adds = set_vars(lhs, value, variables, model)
        # Add the negation of the RHS; If the constraints are correct,
        #  then this should create an infeasible model
        if (not value):
            adds += set_vars(rhs, not value, variables, model)
        sresult = solver.Solve(model)
        if (sresult == cm.MODEL_INVALID):
            print("Model is invalid (likely contains self contradictions")
            raise Exception("Invalid model")
        else:
            result = (sresult == cm.INFEASIBLE if not value else
                      check_values(rhs, value, all_p, variables, solver))
            for add in adds: add.Proto().Clear()
    if (not result and term1):
        print("  When %s set to %s, does not infer %s is %s"
              %(term1, value, term2, value))
    return result

# For each relation, test 4 cases:
# 1. If the LHS is True, then the RHS should all be True
#    (for the "OR" case, at least one variable should be True)
# 2. If the LHS is False, then at least one of the RHS should be False
# 3. If each of the RHS is True, the LHS should be True
# 4. If each of the RHS is False, then the LHS should be False
#    (for the "OR" case, at least one variable should be False)
def test_constraint(constraint, variables, model, solver):
    lhs = constraint[0]; rhs = constraint[1]
    if (len(rhs) == 0 and variables[lhs] is not None): return 1
    lhs_tuple = (lhs,)

    return (test_constraint1(lhs_tuple, rhs, True, True, variables,
                             model, solver, lhs, "RHS") and
            test_constraint1(lhs_tuple, rhs, False, False, variables,
                             model, solver, lhs, "RHS") and
            test_constraint1(rhs, lhs_tuple, True, True, variables,
                             model, solver, "RHS", lhs) and
            test_constraint1(rhs, lhs_tuple, False, True, variables,
                             model, solver, "RHS", lhs))

def safely_create_greenhouse_model():
    try:
        return dg.create_greenhouse_model()
    except Exception as inst:
        print("  Failed to create greenhouse model: %s" %inst)
        return None, None
    
def test_constraints():
    constraints = pickle.load(open("grader_files/constraints.pkl", 'rb'))
    correct = 0; num = len(constraints)
    model, variables = safely_create_greenhouse_model()
    if (not model): return correct, num

    try:
        solver = cm.CpSolver()
        for constraint in constraints:
            correct += test_constraint(constraint, variables, model, solver)
    except Exception as inst:
        print("  Missing relation: %s - Did you complete Step 2, yet?" %inst.args)
    return correct, num

def test_model():
    correct = 0; num = 1
    model, variables = safely_create_greenhouse_model()
    if (not model): return correct, num

    try:
        for add in rp_relations: model.Add(variables[add] == True)
        solver = cm.CpSolver()
        status = solver.Solve(model)
        if (status == cm.MODEL_INVALID):
            print("Something is wrong: Model is invalid")
        if (status == cm.INFEASIBLE):
            print("Something is wrong: Model is infeasible to solve")
        elif (status in [cm.FEASIBLE, cm.OPTIMAL]):
            all_correct = True
            for var in variables:
                if (solver.BooleanValue(variables[var]) == False):
                    print("%s is False, should be True" %var)
                    all_correct = False
            if all_correct: correct += 1
            print("Full model test", "correct!" if all_correct else "failed!")
        else:
            print("Unhandled solver status:", status)

    except Exception as inst:
        print("  Missing relation: %s - Did you complete Step 2, yet?" %inst.args)
    return correct, num

dtests = \
  [([rp_relations[0]], [set([dg.working('H-T0')]), set([dg.connected('H-T0', 'Sensor-Board0')])]),
   ([rp_relations[3], rp_relations[4], rp_relations[5]],
    [set([dg.working('Sensor-Board1')]), set([dg.connected('Sensor-Board1', 'Arduino')]),
     set([dg.connected('H-T1', 'Sensor-Board1'), dg.connected('Light1', 'Sensor-Board1'),
          dg.connected('Moisture1', 'Sensor-Board1')]),
     set([dg.connected('H-T1', 'Sensor-Board1'), dg.connected('Light1', 'Sensor-Board1'),
          dg.working('Moisture1')]),
     set([dg.connected('H-T1', 'Sensor-Board1'), dg.working('Light1'),
          dg.connected('Moisture1', 'Sensor-Board1')]),
     set([dg.connected('H-T1', 'Sensor-Board1'), dg.working('Light1'), dg.working('Moisture1')]),
     set([dg.working('H-T1'), dg.connected('Light1', 'Sensor-Board1'),
          dg.connected('Moisture1', 'Sensor-Board1')]),
     set([dg.working('H-T1'), dg.connected('Light1', 'Sensor-Board1'), dg.working('Moisture1')]),
     set([dg.working('H-T1'), dg.working('Light1'), dg.connected('Moisture1', 'Sensor-Board1')]),
     set([dg.working('H-T1'), dg.working('Light1'), dg.working('Moisture1')])]),
   ([rp_relations[10]], [set([dg.working('Fans')]), set([dg.connected('Power-Board', 'Fans')])]),
   ([rp_relations[10]], [set([dg.working('Fans')]), set([dg.connected('Power-Board', 'Fans')])]),
   ([rp_relations[10], rp_relations[11], rp_relations[12]],
    [set([dg.connected('Arduino', 'Power-Board')]), set([dg.connected('Rasp-Pi', 'Arduino')]),
     set([dg.connected('Outlet', 'Power-Board')]), set([dg.working('Power-Board')]),
     set([dg.connected('Power-Board', 'Fans'), dg.connected('Power-Board', 'LEDs'),
          dg.connected('Power-Board', 'Pump')]),
     set([dg.connected('Power-Board', 'Fans'), dg.connected('Power-Board', 'LEDs'),
          dg.working('Pump')]),
     set([dg.connected('Power-Board', 'Fans'), dg.working('LEDs'),
          dg.connected('Power-Board', 'Pump')]),
     set([dg.connected('Power-Board', 'Fans'), dg.working('LEDs'), dg.working('Pump')]),
     set([dg.working('Fans'), dg.connected('Power-Board', 'LEDs'),
          dg.connected('Power-Board', 'Pump')]),
     set([dg.working('Fans'), dg.connected('Power-Board', 'LEDs'), dg.working('Pump')]),
     set([dg.working('Fans'), dg.working('LEDs'), dg.connected('Power-Board', 'Pump')]),
     set([dg.working('Fans'), dg.working('LEDs'), dg.working('Pump')])]),
   ([rp_relations[0], rp_relations[2]],
    [set([dg.working('Moisture0'), dg.working('H-T0')]),
     set([dg.working('Moisture0'), dg.connected('H-T0', 'Sensor-Board0')]),
     set([dg.connected('Moisture0', 'Sensor-Board0'), dg.working('H-T0')]),
     set([dg.connected('Moisture0', 'Sensor-Board0'), dg.connected('H-T0', 'Sensor-Board0')])])
   ]          

def test_diagnosis():
    correct = 0; num = len(dtests)
    try:
        for negations, answers in dtests:
            model, variables = safely_create_greenhouse_model()
            if (not model): return correct, num

            observations = []
            for rel in rp_relations:
                observations.append([cnf._negate(rel) if rel in negations else rel])
            diagnoses = dg.diagnose(observations)

            print("Negated relations:")
            for rel in negations: print("  %s" %rel)
           
            print("%d diagnoses found" %len(diagnoses))
            for diagnosis in diagnoses: print("  %s" %diagnosis)

            missing_diagnoses = []
            for answer in answers:
                if not any([answer == diagnosis for diagnosis in diagnoses]):
                    missing_diagnoses.append(answer)
            if (missing_diagnoses):
                print("Missing diagnoses:")
                for diagnosis in missing_diagnoses: print("  %s" %diagnosis)

            extra_diagnoses = []
            for diagnosis in diagnoses:
                if not any([answer == diagnosis for answer in answers]):
                    extra_diagnoses.append(diagnosis)
            if (extra_diagnoses):
                print("Extra diagnoses:")
                for diagnosis in extra_diagnoses: print("  %s" %diagnosis)
            if (not missing_diagnoses and not extra_diagnoses):
                correct += 1; print("Correct!")
    except Exception as inst:
        print("  Missing relation: %s - Did you complete Step 2, yet?" %inst.args)
    return correct, num

if (args.part == 1):
    print("Part 1 needs to be tested using the TerraBot simulator")
elif (args.part > 2):
    print("Autograder handles only Part 2")

if (args.part in [-1, 2]):
    num = correct = 0
    if (args.step in [-1, 1]):
        print("Testing Part 2, Step 1")
        scorrect, snum = test_adder()
        print("Part 2, Step 1: %d correct out of %d\n" %(scorrect, snum))
        correct += scorrect; num += snum
    if (args.step in [-1, 2]):
        print("Testing Part 2, Step 2")
        scorrect, snum = test_relations()
        print("Part 2, Step 2: %d correct out of %d\n" %(scorrect, snum))
        correct += scorrect; num += snum
    if (args.step in [-1, 3]):
        print("Testing Part 2, Step 3")
        scorrect, snum = test_constraints()
        print("Part 2, Step 3: %d correct out of %d\n" %(scorrect, snum))
        correct += scorrect; num += snum
    if (args.step in [-1, 4]):
        print("Testing Part 2, Step 4")
        scorrect, snum = test_model()
        print("Part 2, Step 4: %d correct out of %d\n" %(scorrect, snum))
        correct += scorrect; num += snum
    if (args.step in [-1, 5]):
        print("Testing Part 2, Step 5")
        scorrect, snum = test_diagnosis()
        print("Part 2, Step 5: %d correct out of %d\n" %(scorrect, snum))
        correct += scorrect; num += snum
    print("Total for Part 2: %d correct out of %d" %(correct, num))
