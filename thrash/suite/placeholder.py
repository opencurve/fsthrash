import copy


class Placeholder(object):
    def __init__(self, name):
        self.name = name


def substitute_placeholders(input_dict, values_dict):
    input_dict = copy.deepcopy(input_dict)

    def _substitute(input_dict, values_dict):
        for key, value in list(input_dict.items()):
            if isinstance(value, dict):
                _substitute(value, values_dict)
            elif isinstance(value, Placeholder):
                if values_dict[value.name] is None:
                    del input_dict[key]
                    continue
                # If there is a Placeholder without a corresponding entry in
                # values_dict, we will hit a KeyError - we want this.
                input_dict[key] = values_dict[value.name]
        return input_dict

    return _substitute(input_dict, values_dict)


# Template for the config that becomes the base for each generated job config
dict_templ = {
    'suite': Placeholder('suite'),
    'suite_path': Placeholder('suite_path'),
    'testdir': Placeholder('testdir'),
    'numjobs': Placeholder('numjobs'),
    'tasks': [],
}
