import argparse
import multiprocessing
import logging
import time
import matplotlib.pyplot as plt
import numpy as np

class StringFormatError(Exception):
    pass

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

list_result = multiprocessing.Queue()

class compute_complexity:   
    #tested_list = (i*10**j for j in range(8) for i in [1,2,5])
    tested_list = (2**i for i in range(100))  
    template = """
@time_measur
def test({n}):
    {func}
"""
    def time_measur(function):
        def wrapper(val):
            t0 = time.time()
            function(val)
            t1 = time.time()
            list_result.put((val,t1-t0))
        return wrapper    
    
    def __init__(self, execute, name="", setup="pass", clean="pass"):
        def check_and_compile(stmt, name=""):
            if isinstance(stmt, str):
                logger.info("checking: is string - compiling")        
                if name:
                    stmt = compute_complexity.template.format(n=name, func=stmt)                
                logger.debug(stmt)
                comp = compile(stmt, '<string>', "exec")
                return (True, comp)
            elif callable(stmt):
                logger.info("checking: is callable")
                return (False, stmt)
            else:
                logger.error("checking: is not a string")
                raise StringFormatError
        self.setup = check_and_compile(setup)
        
        self.execute = check_and_compile(execute, name)             

        self.clean = check_and_compile(clean)
        
    def compute(self, timeout):
        def comp():
            for val in compute_complexity.tested_list:
                self.test(val) 

        logger.debug("exec setup")
        if self.setup[0]:
            exec(self.setup[1], globals())
        else:
            self.setup[1]()

        logger.debug("exec execute")
        if self.execute[0]:
            loc = {'time_measur': compute_complexity.time_measur}
            exec(self.execute[1], globals(), loc)
            self.test = loc["test"]
        else:
            self.test = compute_complexity.time_measur(self.execute[1])

        logger.debug("start process")
        process = multiprocessing.Process(target=comp)
        process.start()
        process.join(timeout)

        if process.is_alive():
            logger.info("process is killing")
            process.terminate()

        logger.debug("exec clean")
        if self.clean[0]:            
            exec(self.clean[1], globals())
        else:
            self.clean[1]()


        x, y = [], []
        while not list_result.empty():
            x_getted, y_getted = list_result.get()
            x.append(x_getted)
            y.append(y_getted)
        logger.debug(x)
        logger.debug(y)
       
        x = [float(i) for i in x] # numpy problem
        x_out = np.linspace(x[0], x[-1], 20)

        a, b, c = np.polyfit(x, y, 2)
        logger.debug('a={}, b={}, c={}'.format(a, b, c))
        y_2 = np.polyval([a, b, c], x_out)
        
        a, b = np.polyfit(x, y, 1)
        logger.debug('a={}, b={}'.format(a, b))
        y_1 = np.polyval([a, b], x_out)

        [a] = np.polyfit(x, y, 0)
        logger.debug('a={}'.format(a))
        y_0 = np.polyval([a], x_out)

        a, b = np.polyfit(np.log(x), y, 1)
        logger.debug('a={}, b={}'.format(a, b))
        y_log = np.polyval(a * np.log(x) + b, x_out)

        fig = plt.figure()
        ax1 = fig.add_subplot(111)
        ax1.plot(x, y, 'g.',
                 x_out, y_2, 'b-',
                 x_out, y_1, 'r-',
                 x_out, y_0, 'y-')

        
        ax2 = fig.add_subplot(111)
        #w = y[-1] / x[-1]
        #logger.debug(w)
        #line = np.polyval([w, 0], x_out)
        ax2.plot(x_out, y_log, 'v-')
        

        plt.show()

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('--setup', '-s', default="pass",help='Use passed code to initialize data structures')
    parser.add_argument('--execute', '-e', required=True, help='Use passed code to compute complexity')
    parser.add_argument('--clean', '-c', default="pass", help='Use passed code to close function') 
    parser.add_argument('--timeout', '-t', type=int, default=30, help='Set time limit in seconds, default=30')
    parser.add_argument('--name','-n', required=True, help='Algorithm is dependent on pointed variable')
    args = parser.parse_args()
    cc = compute_complexity(name=args.name, setup=args.setup, execute=args.execute, clean=args.clean)
    cc.compute(args.timeout)

