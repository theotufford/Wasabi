import json
import copy
import inspect
from typing import Literal
from .containers import Plate, Reagent_Mix
from .method_arg_classes import special_constructors


class MethodLibrary:
    def __init__(self):
        self.method_callables = {}
        self.method_info = {}
        self.machine = None

    def call_method(self, name, form_data):
        print(f"calling method: {name}")
        method_data = self.method_info[name]
        argument_names = method_data.keys()
        form_data = {key: value for key,
                     value in form_data.items() if key in argument_names}

        # call special constructors if they are found
        for argname, argvalue in form_data.items():
            argdata = method_data[argname]
            typename_str = argdata["type"]
            special_constructor = special_constructors.get(typename_str)
            if special_constructor is not None:
                form_data[argname] = special_constructor(form_data[argname])

        self.method_callables[name](machine=self.machine, **form_data)

    def simulate_experiment(self, data, until: int | None = None) -> dict:
        mach = self.machine
        if mach.in_simulation:
            raise Exception("trying to oversimulate!!")
            return
        initial_position_state = mach.position_known
        mach.save_mutables()
        mach.pump_map = {pumpid: f"unknown_reagent_of_pump{
            pumpid}" for pumpid in range(mach.pump_count)}
        mach.pump_lines = {pumpid: [f"unknown_reagent_of_pump{
            pumpid}"] for pumpid in range(mach.pump_count)}
        mach.fixture.plate.reset()
        mach.in_simulation = True
        mach.position_known = True

        for formid in data["forms"]:
            if formid == until:
                break
            form = data["forms"][formid]
            method_name = form["method"]
            self.call_method(method_name, form)

        output_data = {wellid: mix.contents for wellid,
                       mix in mach.fixture.plate.wells.items()}
        output_data.update({name: mix.contents for name,
                           mix in mach.fixture.named_containers.items()})
        output_resource_data = mach.simulation_resource_accumulator
        mach.simulation_resource_accumulator = []
        mach.restore_mutables()
        mach.in_simulation = False
        mach.position_known = initial_position_state
        return {"plate": output_data, "resources": output_resource_data}

    def run_experiment(self, data):
        initial_position = copy.deepcopy(self.machine.current_position)
        for form_id in data["forms"]:
            form = data["forms"][form_id]
            name = form["method"]
            self.call_method(name, form)
        self.machine.goto_pos(initial_position)
        return self.machine.fixture

    def register_method(self, method_function):
        sig = inspect.signature(method_function)
        args = dict(sig.parameters.items())
        method_name = method_function.__name__
        self.method_callables[method_name] = method_function
        info = {}
        # populate argument info
        for arg_name in args:
            param = args[arg_name]
            annotation = param.annotation

            if annotation.__name__ == "Machine":
                continue

            stringified_subargs = []
            print(f"handling {param}")
            try:
                sub_args = annotation.__args__
                for sub_arg in sub_args:
                    if hasattr(sub_arg, "__name__"):
                        stringified = sub_arg.__name__
                    stringified_subargs.append(stringified)
            except AttributeError:
                pass

            info[arg_name] = {
                "name": arg_name,
                "type": annotation.__name__,
                "sub_args": stringified_subargs
            }
        self.method_info[method_name] = info

    def output_methods_outline(self):
        with open("private/methods.json", "w") as file:
            file.write(json.dumps(self.method_info))
