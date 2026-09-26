from machine_class import Machine

class MethodLibrary:
    def __init__(self):
        self.method_callables = {}
        self.method_info = {}
        self.machine: Machine

    def call_method(self, name, args_dict):
        inputs = self.method_info[name]["inputs"]
        valid_keys = [input["name"] for input in inputs]
        args_dict = {key: value for key,
                     value in args_dict.items() if key in valid_keys}
        self.method_callables[name](machine=self.machine, **args_dict)

    def simulate_experiment(self, data) -> Plate:
        pre_sim_machine = copy.deepcopy(self.machine)
        self.machine.in_simulation = True
        self.machine.position_known = True
        pump_id = 0
        seen_reagents = []
        for form_id in data["forms"]:
            form = data["forms"][form_id]
            reagent = form.get("reagent")
            if reagent not in seen_reagents:
                seen_reagents.append(reagent)
                reagent_line = Reagent_Mix()
                reagent_line.gain_reagent(reagent, reservoir=True)
                self.machine.pump_line_contents[id] = [reagent_line]
                pump_id += 1
            name = form["method"]
            print(f"pump lines configured: {self.machine.pump_line_contents}")
            self.call_method(name, form)
        output_plate = copy.deepcopy(self.machine.plate)
        self.machine = pre_sim_machine
        return output_plate

    def run_experiment(self, data):
        for form_id in data["forms"]:
            form = data["forms"][form_id]
            name = form["method"]
            self.call_method(name, form)
        self.machine.goto_pos(self.machine.home_offset)
        return self.machine.plate

    def register_method(self,
                        method_function,
                        # TODO purity inference
                        function_purity: Literal["impure", "pure"] = "pure"):

        sig = inspect.signature(method_function)
        args = dict(sig.parameters.items())
        method_name = method_function.__name__

        if not args.get("machine") or not args["machine"].annotation == Machine:
            raise ValueError(f"method: {method_name} needs machine parameter!")

        self.method_callables[method_name] = method_function
        is_direct_input = "volume_map" in args.keys()
        has_region_select = "well_array" in args.keys()
        has_region_select = has_region_select or "well_array_dict" in args.keys()
        info = {
            "inputs": [],
            "purity": function_purity,
            "has_region_select": has_region_select,
            "is_direct_input": is_direct_input
        }

        for arg_name in args:
            param = args[arg_name]
            annotation = param.annotation
            if annotation.__name__ == "Machine":
                continue

            sub_args: tuple | None = None
            try:
                sub_args = annotation.__args__
            except AttributeError:
                print(f"param {arg_name} doesnt have any sub-arguments")

            info["inputs"].append({
                "name": arg_name,
                "type": annotation.__name__,
                "args": sub_args
            })
            self.method_info[method_name] = info

    def output_methods_outline(self):
        with open("private/methods.json", "w") as file:
            file.write(json.dumps(self.method_info))
