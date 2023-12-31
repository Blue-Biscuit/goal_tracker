"""
Driver code for the Goal-tracker application.
"""

from goal import Goal
from argparse import ArgumentParser
import json

APP_VERSION = 'alpha'


def string_is_int(title: str) -> bool:
    """Returns true if the string is an integer."""
    try:
        int(title)
        return True
    except ValueError:
        return False


def create_from_specifier(goal_data: list[Goal], specifier: str) -> bool:
    """Creates given a specifier, which is formatted like this: a.b.c. Returns True if something was added.
    By default, everything before the final is set to auto-done, whereas the final is set to false.
    Throws a value error if the user tries to create a goal with an invalid title."""
    specifier_list = specifier.split('.')
    search_list = goal_data
    curr_parent: Goal | None = None
    result = False

    for idx, lookup_title in enumerate(specifier_list):
        # If the title in the specifier is an int, get the next goal by index
        if string_is_int(lookup_title):
            # The last element in the specifier cannot be an index, because you need a title to create a goal
            if idx == len(specifier_list) - 1:
                raise ValueError(f'Last element in specifier cannot be an index: {specifier}')

            idx_lookup = int(lookup_title)
            if idx_lookup not in range(len(search_list)):
                raise ValueError(f'Index not in range: {idx_lookup}')

            if curr_parent is not None:
                curr_parent.done = 'auto'
            curr_goal = search_list[idx_lookup]
            search_list = curr_goal.children
            curr_parent = curr_goal

        # If the title is a string, get the next goal by lookup
        else:
            search_result = [x for x in search_list if x.title == lookup_title]

            # Add the goal from the specifier if it does not exist
            if len(search_result) == 0:
                # If the lookup title is just an int, error out; an integer is an invalid goal title.
                if string_is_int(lookup_title):
                    raise ValueError(f'Cannot create a goal with title "{lookup_title}": name cannot be an integer.')

                if curr_parent is not None:
                    curr_parent.done = 'auto'  # Because it now, whether it did previously or not, has a child.
                curr_goal = Goal(lookup_title, False, curr_parent)

                search_list.append(curr_goal)
                search_list = curr_goal.children
                result = True
                curr_parent = curr_goal

            # If the goal exists, set up to search its children
            else:
                if curr_parent is not None:
                    curr_parent.done = 'auto'  # Because it now, whether it did previously or not, has a child.
                curr_goal = search_result[0]
                search_list = curr_goal.children
                curr_parent = curr_goal

    return result


def find_from_specifier(goal_data: list[Goal], specifier: str) -> Goal | None:
    """Returns the specified goal, or None."""
    result: Goal | None = None

    specifier = specifier.split('.')
    search_list = goal_data
    for lookup_title in specifier:
        # If given an integer, find based upon index
        if string_is_int(lookup_title):
            idx_lookup = int(lookup_title)
            if idx_lookup not in range(len(search_list)):
                raise ValueError(f'Index not in range: {idx_lookup}')

            result = search_list[idx_lookup]
            search_list = result.children

        # Else, find based on title
        else:
            search_result = [x for x in search_list if x.title == lookup_title]
            if len(search_result) == 0:
                result = None
                break
            else:
                result = search_result[0]
                search_list = result.children

    return result


def delete_from_specifier(goal_data: list[Goal], specifier: str) -> bool:
    """True if the goal was successfully deleted."""
    specifier_list = specifier.split('.')
    result = False

    search_list = goal_data
    for idx, lookup_title in enumerate(specifier_list):
        # Process a specifier given as an index
        if string_is_int(lookup_title):
            idx_lookup = int(lookup_title)
            if idx_lookup not in range(len(search_list)):
                raise ValueError(f'Index not in range: {idx_lookup}')

            if idx == len(specifier_list) - 1:
                to_remove = search_list[idx_lookup]
                search_list.remove(to_remove)
                result = True

                # We need to set the parent to a non-auto resolve state if this is the last element.
                if to_remove.parent is not None and len(search_list) == 0:
                    to_remove.parent.done = False
            else:
                search_list = search_list[idx_lookup].children

        # Process a specifier given as a title
        else:
            search_result = [x for x in search_list if x.title == lookup_title]
            if len(search_result) == 0:
                return result
            else:
                if idx == len(specifier_list) - 1:
                    search_list.remove(search_result[0])
                    result = True

                    # We need to set the parent to a non-auto resolve state if this is the last element.
                    if search_result[0].parent is not None and len(search_list) == 0:
                        search_result[0].parent.done = False

                else:
                    search_list = search_result[0].children

    return result


def setup_arguments() -> ArgumentParser:
    parser = ArgumentParser(
        prog='GoalTracker',
        description='Tracks simple and composite goals.'
    )
    parser.add_argument('filename', help='The file which stores the goals.')
    parser.add_argument('-n', '--new', help='Creates a new goal, given a specifier')
    parser.add_argument('-d', '--delete', help='Deletes a goal, given a specifier')
    parser.add_argument('-s', '--show', help='Prints a goal, given its specifier')
    parser.add_argument('-l', '--list', action='store_true', help='Prints all goals in the file')
    parser.add_argument('-p', '--progress', help='Prints what percent this goal is complete')
    parser.add_argument('-c', '--complete', help='Marks a task, given its specifier, as complete')
    parser.add_argument('-i', '--incomplete', help='Marks a task as "un-done"')
    parser.add_argument(
        '--version', action='version', version=APP_VERSION, help='Prints the version of the app'
    )

    return parser


def main():
    parser = setup_arguments()
    args = parser.parse_args()

    goal_data: list[Goal] = []

    # New is special here, because we do not want to crash if the file isn't found.
    if args.new is not None:
        try:
            with open(args.filename, 'r') as in_file:
                json_data = json.load(in_file)
                goal_data = [Goal.from_dict(x) for x in json_data]
        except OSError:
            pass

        try:
            created = create_from_specifier(goal_data, args.new)
            if not created:
                print(f'{args.new} already exists')

        except ValueError as err:  # User input an invalid name
            print(err.args[0])

        with open(args.filename, 'w') as out_file:
            json_data = [x.__dict__() for x in goal_data]
            json.dump(json_data, out_file)

    try:
        with open(args.filename, 'r') as in_file:
            json_data = json.load(in_file)
            goal_data = [Goal.from_dict(x) for x in json_data]
    except OSError:
        print(f'Could not open {args.filename}')
        return

    if args.delete is not None:
        try:
            deleted = delete_from_specifier(goal_data, args.delete)
            if not deleted:
                print(f'No such goal to delete: {args.delete}')
        except ValueError as err:
            print(err.args[0])

    if args.complete is not None:
        to_mark = find_from_specifier(goal_data, args.complete)
        if to_mark.auto:
            print('Cannot mark autocomplete goal as done; must mark all children as done')
        else:
            to_mark.done = True

    if args.incomplete is not None:
        to_mark = find_from_specifier(goal_data, args.incomplete)
        if to_mark.auto:
            print('Cannot mark autocomplete goal as undone; must mark a child as undone')
        else:
            to_mark.done = False

    if args.show is not None:
        to_print = find_from_specifier(goal_data, args.show)
        if to_print is None:
            print(f'No such goal to show: {args.print}')
        else:
            print(to_print.pretty_str())

    if args.progress is not None:
        to_print = find_from_specifier(goal_data, args.progress)
        if to_print is None:
            print(f'No such goal to print progress: {args.progress}')
        else:
            if to_print.auto:
                if len(to_print.children) == 0:
                    print('100%')
                else:
                    children_done: list[Goal] = [x for x in to_print.children if x.done]
                    print(f'{len(children_done) / len(to_print.children) * 100:.0f}%')
            elif to_print.done:
                print('100%')
            else:
                print('0%')

    if args.list:
        for idx, goal in enumerate(goal_data):
            print(goal.pretty_str(idx=idx))

    try:
        with open(args.filename, 'w') as out_file:
            json_data = [x.__dict__() for x in goal_data]
            json.dump(json_data, out_file)
    except OSError:
        print(f'Could not write to file: {args.filename}')


if __name__ == '__main__':
    main()
