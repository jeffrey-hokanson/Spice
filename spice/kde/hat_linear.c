#include "kde.h"
#include "math.h"
#include <stdlib.h>

/* NB: The current implementation is O(# of data points) because we determine the window of which points are actually
 * affected by the sparse kernel.  
 *
 */

void hat_linear(double *data, int N, double *density, double bandwidth, double xmin, double xmax, int npoints) {
	int bottom, top;
	int j,k;
	double xgrid;
	double h = (xmax - xmin)/(npoints - 1);

	for(j = 0; j< N; ++j){
		bottom = (int) ceil( (data[j] - bandwidth - xmin)/h);
		if(bottom<0)
			bottom=0;

		top = (int) floor( (data[j] + bandwidth -xmin)/h);
		if(top > npoints - 1)
			top = npoints -1;

		for(k = bottom; k <= top; ++k){
			xgrid = k*h + xmin;
			density[k] += (1 - ( fabs(data[j] - xgrid)/bandwidth))/(bandwidth*N);
		}
	}
}
