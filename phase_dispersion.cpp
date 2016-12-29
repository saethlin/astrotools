#include <iostream>
#include <vector>
#include <algorithm>
#include <Python.h>
#define NPY_NO_DEPRECATED_API NPY_1_11_API_VERSION
#include <numpy/arrayobject.h>


typedef struct observation {
    double time;
    double flux;
} observation;


bool compare_observations(const observation& a, const observation& b) {
    return a.time < b.time;
}


std::vector<double> inplace_phase_fold(std::vector<observation>& data, std::vector<double>& periods) {
    if (data.size() == 0) {
        return std::vector<double>(periods.size());
    }
    auto dispersion = std::vector<double>();
    dispersion.reserve(periods.size());

    auto phased = std::vector<observation>(data.size());
    auto bounds = std::vector<std::vector<observation>::iterator>();

    for (auto& period : periods) {
        bounds.clear();

        phased[0] = {fmod(data[0].time, period), data[0].flux};
        for (auto i = 1; i < data.size(); i++) {
            phased[i] = {fmod(data[i].time, period), data[i].flux};
            if (phased[i].time < phased[i - 1].time) {
                bounds.push_back(phased.begin() + i);
            }
        }
        bounds.push_back(phased.end());

        for (auto i = 0; i < bounds.size()-1; i++) {
            auto middle = bounds[i];
            auto end = bounds[i + 1];
            std::inplace_merge(phased.begin(), middle, end, compare_observations);
        }

        auto disp = 0.0;
        for (auto i = 0; i < phased.size()-1; i++) {
            disp += fabs(phased[i].flux - phased[i + 1].flux);
        }
        dispersion.push_back(disp);
    }
    return dispersion;
}


static PyObject* phase_dispersion(PyObject* self, PyObject *args, PyObject* kwargs) {
    PyArrayObject* timeArg = NULL;
    PyArrayObject* fluxArg = NULL;
    PyArrayObject* periodsArg = NULL;
    static char* kwdlist[] = {"time", "flux", "periods", NULL};

    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "O!O!O!", kwdlist,
                                     &PyArray_Type, &timeArg,
                                     &PyArray_Type, &fluxArg,
                                     &PyArray_Type, &periodsArg)) {
        return NULL;
    }

    npy_intp* dims = PyArray_DIMS(timeArg);
    auto timeData = (double*)PyArray_DATA(timeArg);
    auto fluxData = (double*)PyArray_DATA(fluxArg);

    auto data = std::vector<observation>();
    data.reserve(dims[0]);
    for (auto i = 0; i < dims[0]; i++) {
        data.push_back({timeData[i], fluxData[i]});
    }

    dims = PyArray_DIMS(periodsArg);
    auto periodsData = (double*)PyArray_DATA(periodsArg);
    auto periods = std::vector<double>(periodsData, periodsData+dims[0]);

    auto dispersion = inplace_phase_fold(data, periods);

    PyObject* output = PyArray_SimpleNew(1, dims, NPY_DOUBLE);
    auto output_data = (double*)PyArray_DATA((PyArrayObject*)output);
    for (auto i = 0; i < dispersion.size(); i++) {
        output_data[i] = dispersion[i];
    }

    return output;
}



static PyMethodDef methods[] = {
        {"phase_dispersion",  (PyCFunction)phase_dispersion, METH_VARARGS | METH_KEYWORDS,
         "Compute the phase dispersion of time and flux data at given periods"},
        {NULL, NULL, 0, NULL}        /* Sentinel */
};


static struct PyModuleDef module = {
        PyModuleDef_HEAD_INIT,
        "ctools",   /* name of module */
        NULL, /* module documentation, may be NULL */
        -1,       /* size of per-interpreter state of the module,
                or -1 if the module keeps state in global variables. */
        methods
};


PyMODINIT_FUNC PyInit_ctools(void) {
    import_array();
    return PyModule_Create(&module);
}