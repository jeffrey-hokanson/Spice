#include <Python.h>
//#define NPY_NO_DEPRECATED_API NPY_1_7_API_VERSION
#include <numpy/arrayobject.h>
#include "kde.h"

/* Docstrings */
static char module_docstring[] =
    "This provides a C implementation of the kde module for kernel density estimation.";
static char hat_linear_docstring[] =
    "Linear hat kernel density estimator on a linear grid";

/* Available functions */
static PyObject *kde_hat_linear(PyObject *self, PyObject *args);

/* Module specification */
static PyMethodDef module_methods[] = {
    {"hat_linear", kde_hat_linear, METH_VARARGS, hat_linear_docstring},
    {NULL, NULL, 0, NULL}
};

/* Initialize the module */
PyMODINIT_FUNC init_kde(void)
{
    PyObject *m = Py_InitModule3("_kde", module_methods, module_docstring);
    if (m == NULL)
        return;

    /* Load `numpy` functionality. */
    import_array();
}

/* From here on, we define interfaces to objects in our module */

/* _kde.hat_linear expects 
 * data (*double)
 * bandwidth (double)
 * xmin (double)
 * xmax (double)
 * npoints (int)
 *
 * returns:
 * den (*double) 
 */
static PyObject *kde_hat_linear(PyObject *self, PyObject *args)
{
    double xmin, xmax, bandwidth;
    int npoints;
    PyObject *data_obj;

    /* Parse the input tuple */
    if (!PyArg_ParseTuple(args, "Odddi", &data_obj, &bandwidth, &xmin, &xmax,
                                         &npoints))
        return NULL;

    /* Interpret the input objects as numpy arrays. */
    PyObject *data_array = PyArray_FROM_OTF(data_obj, NPY_DOUBLE, NPY_IN_ARRAY);

    /* If that didn't work, throw an exception. */
    if (data_array == NULL ) {
        Py_XDECREF(data_array);
        return NULL;
    }

    /* How many data points are there? */
    int N = (int)PyArray_DIM(data_array, 0);

    /* Get pointers to the data as C-types. */
    double *data = (double*)PyArray_DATA(data_array);

    /* Initialize data for output. */
    npy_intp size = npoints;
    PyObject *den_obj = PyArray_SimpleNew(1, &size, NPY_DOUBLE);
    double *density = (double*) PyArray_DATA(den_obj);

    for(int j = 0; j < npoints; ++j)
	    density[j] = 0.0;
    /* Call the external C function to compute the chi-squared. */
    hat_linear(data, N, density, bandwidth, xmin, xmax, npoints);

    /* Clean up. */
    Py_DECREF(data_array);


    /* Build the output tuple */
    return den_obj;
}
