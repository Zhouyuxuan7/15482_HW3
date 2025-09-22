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
    conns = []

    # --- Power connections (5) ---
    conns += [
        connected('Outlet', 'Rasp-Pi'),
        connected('Outlet', 'Power-Board'),
        connected('Power-Board', 'Fans'),
        connected('Power-Board', 'LEDs'),
        connected('Power-Board', 'Pump'),
    ]
    # --- Signal connections (12) ---
    conns += [## Sensors -> Sensor-Boards (6)
        connected('H-T0', 'Sensor-Board0'),
        connected('Light0', 'Sensor-Board0'),
        connected('Moisture0', 'Sensor-Board0'),
        connected('H-T1', 'Sensor-Board1'),
        connected('Light1', 'Sensor-Board1'),
        connected('Moisture1', 'Sensor-Board1'),
        connected('Wlevel', 'Arduino'),
        ## Sensor-Boards -> Arduino (2)
        connected('Sensor-Board0', 'Arduino'),
        connected('Sensor-Board1', 'Arduino'),
        ## Arduino <-> Rasp-Pi (2) (bidirectional)
        connected('Arduino', 'Rasp-Pi'),
        connected('Rasp-Pi', 'Arduino'),
        ## Arduino -> Power-Board (1)
        connected('Arduino', 'Power-Board'),
    ]
    create_relations(conns, model, variables)
    # END STUDENT CODE
    pass

def create_powered_relations(model, variables):
    # BEGIN STUDENT CODE
    pow_rels = [
        powered('Outlet'),
        powered('Rasp-Pi'),
        powered('Power-Board'),
        powered('Fans'),
        powered('LEDs'),
        powered('Pump'),
    ]
    create_relations(pow_rels, model, variables)
    # END STUDENT CODE
    pass

def create_signal_relations(model, variables):
    # BEGIN STUDENT CODE
    sig_rels = []
    # (A) 7 sensors generate their own signals (7)
    for s in sensors:
        sig_rels.append(signal(s, s))
        sig_rels.append(signal(s, 'Arduino'))
        sig_rels.append(signal(s, 'Rasp-Pi'))
    # (B) Each sensor-board receives its 3 specific sensors (6)
    for s in ['H-T0', 'Light0', 'Moisture0']:
        sig_rels.append(signal(s, 'Sensor-Board0'))
    for s in ['H-T1', 'Light1', 'Moisture1']:
        sig_rels.append(signal(s, 'Sensor-Board1'))
    # (C, D, E, F, G) Actuator signals
    for a in ['Fans', 'LEDs', 'Pump']:
        sig_rels.append(rasp_pi_signal(a))
        sig_rels.append(signal(a, 'Arduino'))
        sig_rels.append(signal(a, 'Power-Board'))
    create_relations(sig_rels, model, variables)
    # END STUDENT CODE
    pass

def create_expected_result_relations(model, variables):
    # BEGIN STUDENT CODE
    exp_rels = [expected_result(a) for a in ['Fans','LEDs','Pump']]
    create_relations(exp_rels, model, variables)
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
    sb0 = ['H-T0', 'Light0', 'Moisture0']
    sb1 = ['H-T1', 'Light1', 'Moisture1']
    # --- Sensor signals ---
    for s in sb0 + sb1:
        # Sensor → SensorBoard
        add_constraint_to_model(
            f"IFF('{signal(s, 'Sensor-Board0' if s in sb0 else 'Sensor-Board1')}', "
            f"AND('{connected(s, 'Sensor-Board0' if s in sb0 else 'Sensor-Board1')}', "
            f"AND('{working(s)}', '{signal(s, s)}')))", model, variables
        )
        # Sensor → Arduino (through its board)
        board = 'Sensor-Board0' if s in sb0 else 'Sensor-Board1'
        add_constraint_to_model(
            f"IFF('{signal(s, 'Arduino')}', "
            f"AND('{connected(board, 'Arduino')}', "
            f"AND('{working(board)}', '{signal(s, board)}')))", model, variables
        )
    # Wlevel special case (direct to Arduino)
    add_constraint_to_model(
        f"IFF('{signal('Wlevel', 'Arduino')}', "
        f"AND('{connected('Wlevel', 'Arduino')}', "
        f"AND('{working('Wlevel')}', '{signal('Wlevel', 'Wlevel')}')))",
        model, variables
    )
    # Sensors → Rasp-Pi 
    for s in sensors:
        add_constraint_to_model(
            f"IFF('{signal(s, 'Rasp-Pi')}', "
            f"AND('{connected('Arduino', 'Rasp-Pi')}', "
            f"AND('{working('Arduino')}', '{signal(s, 'Arduino')}')))",
            model, variables
        )
    # --- Actuator signals ---
    for a in actuators:
        # Rasp-Pi → Arduino
        add_constraint_to_model(
            f"IFF('{signal(a, 'Arduino')}', "
            f"AND('{connected('Rasp-Pi', 'Arduino')}', "
            f"AND('{working('Rasp-Pi')}', '{rasp_pi_signal(a)}')))",
            model, variables
        )
        # Arduino → Power-Board
        add_constraint_to_model(
            f"IFF('{signal(a, 'Power-Board')}', "
            f"AND('{connected('Arduino', 'Power-Board')}', "
            f"AND('{working('Arduino')}', '{signal(a, 'Arduino')}')))",
            model, variables
        )
    # END STUDENT CODE
    pass

def create_sensor_generation_constraints(model, variables):
    # BEGIN STUDENT CODE
    for s in sensors:
        c = f"IFF('{signal(s, s)}', '{working(s)}')"
        add_constraint_to_model(c, model, variables)
    # END STUDENT CODE
    pass

def create_expected_result_constraints(model, variables):
    # BEGIN STUDENT CODE
    associated = {
        'Fans': ['H-T0', 'H-T1'],
        'LEDs': ['Light0', 'Light1'],
        'Pump': ['Moisture0', 'Moisture1', 'Wlevel']
    }
    for a, sens_list in associated.items():
        sensors_or = f"'{signal(sens_list[0], 'Rasp-Pi')}'"
        for s in sens_list[1:]:
            sensors_or = f"OR({sensors_or}, '{signal(s, 'Rasp-Pi')}')"
        constraint = (
            f"IFF('{expected_result(a)}', "
            f"AND('{rasp_pi_signal(a)}', "
            f"AND('{powered(a)}', AND('{working(a)}', {sensors_or}))))"
        )
        add_constraint_to_model(constraint, model, variables)
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
        self.variables = variables
        self._diagnoses = []
        self._seen = set() 
        # END STUDENT CODE

    def OnSolutionCallback(self):
        # Extract the connected and working relations that are False
        # BEGIN STUDENT CODE
        diag = set()
        for name, var in self.variables.items():
            if name.startswith('connected') or name.startswith('working'):
                if self.Value(var) == 0:
                    diag.add(name)
        f = frozenset(diag)
        if f not in self._seen:
            self._seen.add(f)
            self._diagnoses.append(diag)
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
    uniq = collector._diagnoses
    minimal = []
    for d in uniq:
        is_superset = False
        for other in uniq:
            if other < d:
                is_superset = True
                break
        if not is_superset:
            minimal.append(d)
    temp = []
    for diag in minimal:
        temp.append((sorted(list(diag)), diag))
    temp.sort()
    diagnoses = [t[1] for t in temp]
    # END STUDENT CODE
    return diagnoses
