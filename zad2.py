import argparse
import multiprocessing
import logging
import time
import matplotlib.pyplot as plt
import numpy as np
import textwrap

list_result = multiprocessing.Queue()


def time_measur(queue):
    def inner(function):
        def wrapper(val):
            t0 = time.time()
            function(val)
            t1 = time.time()
            queue.put((val, t1-t0))
        return wrapper
    return inner


def comp(function, list_result):
    code = compile(function, '<string>', "exec")
    loc = {}
    glob = {'time_measur': time_measur, 'queue': list_result}
    exec(code, glob, loc)
    test = loc["_test_func"]
    for val in (2**i for i in range(100)):
        test(val)


class StringFormatError(Exception):
    def __init__(self, error):
        logger.error(error)


class NoResultException(Exception):
    pass

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class ComputeComplexity:
    def __init__(self, execute, name, setup="pass", clean="pass"):
        function = """
def _test_func({n}):
{setup}

    @time_measur(queue)
    def _f({n}):
{func}

    _f({n})
{clean}
"""
        function = function.format(n=name, setup="{setup}",
                                   func="{func}", clean="{clean}")

        if isinstance(setup, str):
            logger.info("checking setup: is string")
        elif callable(setup):
            logger.info("checking setup: is callable")
            self.setup = setup
            setup = "self.setup"
        else:
            raise StringFormatError("setup isn't a string nor callable")
        setup = textwrap.indent(setup, ' ' * 4)
        function = function.format(setup=setup, func="{func}", clean="{clean}")

        if isinstance(execute, str):
            logger.info("checking execute: is string")
        elif callable(execute):
            logger.info("checking execute: is callable")
            self.execute = execute
            execute = "self.execute"
        else:
            raise StringFormatError("execute isn't a string nor callable")
        execute = textwrap.indent(execute, ' ' * 8)
        function = function.format(func=execute, clean="{clean}")

        if isinstance(clean, str):
            logger.info("checking clean: is string")
        elif callable(clean):
            logger.info("checking clean: is callable")
            self.clean = clean
            clean = "self.clean"
        else:
            raise StringFormatError("clean isn't a string nor callable")
        clean = textwrap.indent(clean, ' ' * 4)
        self.function = function.format(clean=clean)
        logger.debug(self.function)

    def compute(self, timeout):
        global comp
        logger.debug("start process")
        proc_args = (self.function, list_result)
        process = multiprocessing.Process(target=comp, args=proc_args)
        process.start()

        process.join(timeout)
        if process.is_alive():
            logger.info("process is killing")
            process.terminate()

        if list_result.empty():
            raise NoResultException

        x, y = [], []
        while not list_result.empty():
            x_getted, y_getted = list_result.get()
            x.append(x_getted)
            y.append(y_getted)
        logger.debug(x)
        logger.debug(y)

        x = [float(i) for i in x]  # numpy have to get float
        x_out = np.linspace(x[0], x[-1], 20)
        weight = [y * pow(2, i) for i, y in enumerate(y)]

        # Quadratic equation
        N2 = [a, b, c] = np.polyfit(x, y, 2, w=weight)
        logger.debug('a={}, b={}, c={}'.format(a, b, c))
        if a < 0:
            logger.info('a < 0')
            a, b, c = 0, 0, 0
        y_2 = np.polyval([a, b, c], x_out)

        # Linear equation
        N1 = [a, b] = np.polyfit(x, y, 1, w=weight)
        logger.debug('a={}, b={}'.format(a, b))
        if a < 0:
            logger.info('a < 0')
            a, b = 0, 0
        y_1 = np.polyval([a, b], x_out)

        # Const equation
        N0 = [a] = np.polyfit(x, y, 0, w=weight)
        logger.debug('a={}'.format(a))
        y_0 = np.polyval(N0, x_out)

        # Logarithmic equation
        Nlog = [a, b] = np.polyfit(np.log(x), y, 1, w=weight)
        logger.debug('a={}, b={}'.format(a, b))
        if a < 0:
            logger.info('a < 0')
            a, b = 0, 0
        y_log = [a * np.log(x) + b for x in x_out]

        fig = plt.figure()
        ax1 = fig.add_subplot(111)
        ax1.plot(x, y, 'g.',
                 x_out, y_2, 'b-',
                 x_out, y_1, 'r-',
                 x_out, y_0, 'y-')

        if a > 0:
            ax2 = fig.add_subplot(111)
            ax2.plot(x_out[1:], y_log[1:], 'v-')

        def sum_of_differences(aprox_y):
            total_dif = 0
            for real, aprox in zip(y, aprox_y):
                total_dif += abs(real - aprox)
            return total_dif

        O2 = sum_of_differences(y_2)
        O1 = sum_of_differences(y_1)
        O0 = sum_of_differences(y_0)
        Olog = sum_of_differences(y_log)

        comp = {O2: "O(n^2)",
                O1: "O(n)",
                O0: "O(1)",
                Olog: "O(log(n))"}

        diff = min(O2, O1, O0, Olog)
        how_long = def how_long(x):
            return np.polyval(N2, [x])
        logger.debug(diff)
        logger.debug(comp)
        delta = 0.9
        if diff == O2 and O2 / O1 > delta:
            diff = O1
            how_long = def how_long(x):
                return np.polyval(N1, [x])
        if diff == O1 and O1 / Olog > delta:
            diff = Olog
            how_long = def how_long(x):
                return a * np.log(x) + b
        if diff == Olog and Olog / O0 > delta:
            diff = O1
            how_long = def how_long(x):
                return np.polyval(N0, [x])

        answer = "minimal complexity is {r}".format(r=comp[diff])
        logger.info(answer)
        plt.show()
        return (answer, how_long,)

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('--setup', '-s', default="pass",
                        help='Use passed code to initialize data structures')
    parser.add_argument('--execute', '-e', required=True,
                        help='Use passed code to compute complexity')
    parser.add_argument('--clean', '-c', default="pass",
                        help='Use passed code to close function')
    parser.add_argument('--timeout', '-t', type=int, default=30,
                        help='Set time limit in seconds, default=30')
    parser.add_argument('--name', '-n', required=True,
                        help='Algorithm is dependent on pointed variable')
    args = parser.parse_args()
    cc = ComputeComplexity(name=args.name, setup=args.setup,
                           execute=args.execute, clean=args.clean)
    cc.compute(args.timeout)
