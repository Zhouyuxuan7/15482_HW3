from cnf import *
from ortools.sat.python import cp_model

objects = ['Outlet', 'Rasp-Pi', 'Power-Board',
           'Arduino', 'Sensor-Board0', 'Sensor-Board1']
actuators = ['Fans', 'LEDs', 'Pump']
sensors = ['H-T0', 'Light0', 'Moisture0', 'H-T1', 'Light1', 'Moisture1',
           'Wlevel']
relations = ['working', 'connected', 'powered', 'signal', 'expected-result']

def powered(comp): return f'powered({comp})'
def working(comp): return f'working({comp})'
def connected(from_comp, to_comp):
    return f'connected({from_comp}, {to_comp})'
def signal(signal, component): return f'signal({signal}, {component})'
def rasp_pi_signal(the_signal): return signal(the_signal, 'Rasp-Pi')
def expected_result(actuator): return f'expected-result({actuator})'

def create_relation(name, model, variables):
    variables[name] = model.NewBoolVar(name)

def create_relations(relations, model, variables):
    for relation in relations: create_relation(relation, model, variables)

def create_working_relations(model, variables):
    create_relations([working(comp) for comp in objects + actuators + sensors],
                     model, variables)

def create_connected_relations(model, variables):
    # BEGIN STUDENT CODE
    # END STUDENT CODE
    pass

def create_powered_relations(model, variables):
    # BEGIN STUDENT CODE
    # END STUDENT CODE
    pass

def create_signal_relations(model, variables):
    # BEGIN STUDENT CODE
    # END STUDENT CODE
    pass

def create_expected_result_relations(model, variables):
    # BEGIN STUDENT CODE
    # END STUDENT CODE
    pass

def create_relation_variables(model):
    variables = {}
    create_working_relations(model, variables)
    create_connected_relations(model, variables)
    create_powered_relations(model, variables)
    create_signal_relations(model, variables)
    create_expected_result_relations(model, variables)
    return variables

def add_constraint_to_model(constraint, model, variables):
    for disj in (eval(constraint) if isinstance(constraint, str) else constraint):
        conv_disj = [variables[lit] if not is_negated(lit) else
                     variables[lit[1]].Not() for lit in disj]
        model.AddBoolOr(conv_disj)

def create_powered_constraint(from_comp, to_comp, model, variables):
    constraint = f"IFF('{powered(to_comp)}', AND('{connected(from_comp, to_comp)}',\
                                                 '{working(from_comp)}'))"
    add_constraint_to_model(constraint, model, variables)

def create_powered_actuator_constraint(actuator, model, variables):
    constraint = f"IFF('{powered(actuator)}',\
                       AND('{connected('Power-Board', actuator)}',\
                           AND('{powered('Power-Board')}',\
                               AND('{working('Power-Board')}', '{signal(actuator, 'Power-Board')}'))))"
    add_constraint_to_model(constraint, model, variables)

def create_powered_constraints(model, variables):
    add_constraint_to_model(LIT(powered('Outlet')), model, variables)
    create_powered_constraint('Outlet', 'Rasp-Pi', model, variables)
    create_powered_constraint('Outlet', 'Power-Board', model, variables)
    for actuator in actuators:
        create_powered_actuator_constraint(actuator, model, variables)

def create_signal_constraints(model, variables):
    # BEGIN STUDENT CODE
    # END STUDENT CODE
    pass

def create_sensor_generation_constraints(model, variables):
    # BEGIN STUDENT CODE
    # END STUDENT CODE
    pass

def create_expected_result_constraints(model, variables):
    # BEGIN STUDENT CODE
    # END STUDENT CODE
    pass

def create_constraints(model, variables):
    create_powered_constraints(model, variables)
    create_signal_constraints(model, variables)
    create_sensor_generation_constraints(model, variables)
    create_expected_result_constraints(model, variables)

def create_greenhouse_model():
    model = cp_model.CpModel()
    variables = create_relation_variables(model)
    create_constraints(model, variables)
    return (model, variables)
    
def collect_diagnosis(solver, variables):
    return set([var for var in variables
                if ((var.startswith('connected') or var.startswith('working')) and
                    solver.BooleanValue(variables[var]) == False)])

class DiagnosesCollector(cp_model.CpSolverSolutionCallback):
    def __init__(self, variables):
        cp_model.CpSolverSolutionCallback.__init__(self)
        # BEGIN STUDENT CODE
        # END STUDENT CODE

    def OnSolutionCallback(self):
        # Extract the connected and working relations that are False
        # BEGIN STUDENT CODE
        # END STUDENT CODE
        pass

def diagnose(observations):
    model, variables = create_greenhouse_model()
    add_constraint_to_model(observations, model, variables)

    collector = DiagnosesCollector(variables)
    diagnoses = []
    solver = cp_model.CpSolver()
    solver.SearchForAllSolutions(model, collector)
    # Remove all redundant diagnoses (those that are supersets
    #   of other diagnoses).
    # BEGIN STUDENT CODE
    # END STUDENT CODE

    return diagnoses
