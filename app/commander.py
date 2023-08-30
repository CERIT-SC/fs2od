from collections.abc import Callable
from typing import Any
from utils import Logger


class Command:
    """
    Self-executable command with additional possibilities
    """
    def __init__(self, function: Callable, self_object: Any = None, *args, **kwargs):
        """
        Creates new command with given parameters

        function is callable (function object) which will be later called if used
        Function is REQUIRED to support at least one parameter (later used value).
        self_object is an object, which should be passed as a first value when calling a function.
            If None parsed, it won't be used - OPTIONAL
        *args and **kwargs are arguments, which will be parsed when calling a function.

        Order of parsed arguments is described in Command::call function
        """
        self.func = function
        self.self = self_object
        self.args = args
        self.kwargs = kwargs

    def call(self, value: Any, self_object: Any = None, *args, **kwargs) -> Any:
        """
        Calls previously created command (self.function) using given parameters
        Parsing parameters has its own priority:
            - Firstly, the newest (actual) arguments are parsed (self_object, *args, **kwargs of this function)
            - Secondly, arguments used when creating a Commands are parsed

        self_object is an object, which should be passed as a first value when calling a function.
            If None parsed, it won't be used
        *args and **kwargs are arguments, which will be parsed when calling a function.
        value is an object, which is parsed after all *args, before all **kwargs.
        It must be provided and function in Command must support this value
        If self_object is None, value of self.self is used.
        If this value is also None, function is called without self object
        """
        Logger.log(4, f"commander.Command.call({self.func.__name__})")
        self_to_parse = self.self
        if self_object is not None:
            self_to_parse = self_object

        if self_to_parse is not None:  # I have now self object, which must go first
            if value is None:
                return self.func(self_to_parse, *self.args, *args, **self.kwargs, **kwargs)
            return self.func(self_to_parse, *self.args, *args, value, **self.kwargs, **kwargs)

        if value is None:
            return self.func(*self.args, *args, **self.kwargs, **kwargs)
        return self.func(*self.args, *args, value, **self.kwargs, **kwargs)


class CommandMap:
    """
    Command map used to map name of the command to Command object (or self-execution if needed)
    """
    def __init__(self, command_map: dict[str, Command]):
        self.commands = command_map

    def exec(self, command_name: str, value: Any, self_object: Any = None, *args, **kwargs) -> tuple[bool, Any]:
        """
        Executes command bind to a name (name is mapped to command).

        self_object is an object, which should be passed as a first value when calling a function.
            If None parsed, it won't be used
        *args and **kwargs are arguments, which will be parsed when calling a function.
        value is an object, which is parsed after all *args, before all **kwargs.

        Returns tuple of bool and Any.
        If command name was found in mapping directory, bool value of tuple is True, otherwise False
        Any value is a return value from called function. If bool is False (command is not found), None is returned
        """
        Logger.log(4, f"commander.CommandMap.exec({command_name})")
        if command_name not in self.commands:
            Logger.log(4, f"Command not found, skipping: {command_name}")
            return False, None

        command = self.commands.get(command_name)
        return True, command.call(value, self_object, *args, **kwargs)


def execute_command(
        command: str, command_map: CommandMap, separator: str = ":", self_object: Any = None, *args, **kwargs) -> str:
    """
    Processes given command using a provided command map.
    Commands are formatted as string, which then can be divided into a list using given separator
    More than one command can be used in the string.
    Important: the last value of the command (after splitting it is index -1) is used to be further processed.
    This value cannot contain separator in it. If a separator must be used in value, new separator should be used.
    This value is parsed to CommandMap::exec as value argument
    Commands are processed in undefined order. You SHOULDN'T rely on the order of command processing

    self_object is an object, which should be passed as a first value when calling a function.
        If None parsed, it won't be used
    *args and **kwargs are arguments, which will be parsed when calling a function.

    Returns value after command processing. If there are some commands left, they are prepended to a final value
    """
    Logger.log(4, f"commander.execute_command()")
    subcommands = command.split(separator)

    execution_value = subcommands[-1]
    subcommands = list(set(subcommands[:-1]))  # if there are duplicated values, removes them

    if len(subcommands) == 0:
        Logger.log(4, f"object has no subcommands, skipping")
        status, return_value = command_map.exec("default", execution_value, self_object, *args, **kwargs)
        if status and return_value is None:
            return ""
        return execution_value

    commands_executed = 0

    for index, subcommand in enumerate(subcommands):
        status, return_value = command_map.exec(subcommand, execution_value, self_object, *args, **kwargs)
        if status:
            execution_value = return_value
            subcommands.pop(index)
            commands_executed += 1

    if commands_executed == 0:
        Logger.log(4, f"object has no executable subcommands, skipping")
        status, return_value = command_map.exec("default", execution_value, self_object, *args, **kwargs)
        if status:
            execution_value = return_value

    if execution_value is None:
        execution_value = ""
    subcommands.append(execution_value)
    reconstructed_command = separator.join(subcommands)

    return reconstructed_command
