

Stage 1
-------
In this phase, I focus primarily on questions of user interaction.  


- Pandas backend for fast gating, a good editing of FlowData is probabily necessary.
- GUI interface for adding gates
	- Pop-up inequality gating
	- Selecting a region graphically
- Two interfaces open simultaneously, sharing data
	- Selecting a gate on one region and seeing the application on the other in real time.
- SPADE tree view graph (preferably interactive, a la [d3js](http://bl.ocks.org/mbostock/4062045))
- 2D KDE plots
- 2D viSNE


Stage 2
-------
Now, with most of the user interface complete, I turn towards accelerating existing methods.
The goal is to be able to interactively explore flow data.

- GPU Computation of KDEs
- OCCA implementation of BH t-SNE.
- Other accelerations that seem necessary

Stage 3
-------
Now, with the software fast enough to be in
