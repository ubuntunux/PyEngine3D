from pycallgraph import PyCallGraph
from pycallgraph.output import GraphvizOutput
import main

with PyCallGraph(output=GraphvizOutput()):
    main.run()
