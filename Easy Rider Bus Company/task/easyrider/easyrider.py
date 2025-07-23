import json
import re
import itertools

def count_errors(json_str, expected_types:dict, errors:dict, required:list):
    """Return a dictionary with the count of the number of type errors,
    differentiating between required and not required fields"""

    name_pattern = re.compile(r'^[A-Z].* (Road|Avenue|Boulevard|Street)$')
    time_pattern = re.compile(r'^([01][0-9]|2[0-3]):[0-5][0-9]$')

    for i in range(len(json_str)):
        for field_name, field_type in expected_types.items():
            field = json_str[i][field_name]
            # extra check to not miscount an int with value 0
            if field_name in required and not field:
                    if not(field_type == int and field == 0):
                        errors[field_name] += 1
            elif not isinstance(field, field_type):
                errors[field_name] += 1
            elif field_name == 'stop_name' and not re.match(name_pattern, field):
                errors[field_name] += 1
            elif field_name == 'a_time' and not re.match(time_pattern, field):
                errors[field_name] += 1
            # special case due to stop_type being 'char' type and optional
            elif field_name == 'stop_type' and field and (len(field) > 1 or field not in ['S', 'O', 'F']):
                    errors[field_name] += 1

    # check that the a_times are sequential
    for bus_id, group in itertools.groupby(json_str, key=lambda x: x['bus_id']):
        stop_times = [item['a_time'] for item in group]

        for i in range(len(stop_times)-1):
            if stop_times[i] >= stop_times[i+1]:
                errors['a_time'] += 1
                break  # stop checking this bus line and continue with the next

    return errors

def count_stops(json_str):
    """Return a dictionary with the bus line IDs and number of stops"""

    stops = dict()

    for i in range(len(json_str)):
        if json_str[i]['bus_id'] in stops:
            stops[json_str[i]['bus_id']].add(json_str[i]['stop_name'])
        else:
            stops[json_str[i]['bus_id']] = {json_str[i]['stop_name']}

    return stops


def verify_stops(json_str, bus_stops):
    """Return information about the stop lines after verifying that they have one Start stop and one Final stop"""

    stop_info = {'Start': set(), 'Transfer': set(), 'Finish': set(), 'On demand': set()}

    # get Transfer stops, i.e. stops that appear in more than one bus line
    for key_a, key_b in itertools.combinations(bus_stops, 2):
        stop_info['Transfer'].update(bus_stops[key_a] & bus_stops[key_b])

    # check start and finish stops for each line
    for bus_line in bus_stops:
        has_start = False
        has_finish = False

        for i in range(len(json_str)):
            stop_type = json_str[i]['stop_type']

            if json_str[i]['bus_id'] == bus_line:
                if stop_type == 'S':
                    if not has_start:
                        has_start = True
                        stop_info['Start'].add(json_str[i]['stop_name'])
                    else:
                        return f"There is more than one start for the line: {bus_line}"
                elif stop_type == 'F':
                    if not has_finish:
                        has_finish = True
                        stop_info['Finish'].add(json_str[i]['stop_name'])
                    else:
                        return f"There is more than one end for the line: {bus_line}"

        if not (has_start and has_finish):
            return f"There is no start or end stop for the line: {bus_line}"

    # check On Demand stops. They cannot be the same as Start, Final or Transfer stops.
    for i in range(len(json_str)):
        if json_str[i]['stop_type'] == 'O' and json_str[i]['stop_name'] not in itertools.chain(*stop_info.values()):
            stop_info['On demand'].add(json_str[i]['stop_name'])

    return stop_info


def main():
    # constant definition
    expected_types = {'bus_id': int, 'stop_id': int, 'stop_name': str, 'next_stop': int,
                      'stop_type': str, 'a_time': str}
    required_fields = ['bus_id', 'stop_id', 'stop_name', 'next_stop', 'a_time']

    # initialize error counter
    error_count = {'bus_id': 0, 'stop_id': 0, 'stop_name': 0, 'next_stop': 0,
                   'stop_type': 0, 'a_time': 0}

    # get data
    json_str = json.loads(input())

    error_count = count_errors(json_str, expected_types, error_count, required_fields)
    bus_line_stops = count_stops(json_str)
    stop_details = verify_stops(json_str, bus_line_stops)

    print(f"Type and field validation {sum(error_count.values())} errors")
    for key, value in error_count.items():
        print(f"{key}: {value}")

    print("\nLine names and number of stops:")
    for key, value in bus_line_stops.items():
        print(f"bus_id: {key} stops {len(value)}")

    if isinstance(stop_details, str):
        print(stop_details)
    else:
        for key, value in stop_details.items():
            print(f"{key} stops: {len(value)} {sorted(list(value))}")


if __name__ == "__main__":
    main()